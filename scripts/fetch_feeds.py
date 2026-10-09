#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓取 config/feeds.json 里的外部订阅源，规范化成两件生成物：

  public/data/rss-items.json   阅读器页的数据（按订阅源分组）
  public/subscriptions.opml    订阅清单（只含标题 + xmlUrl + htmlUrl）

用法（仓库根运行）：python scripts/fetch_feeds.py

这是构建期抓取：浏览器端只 fetch 同域的 rss-items.json，不发任何第三方请求。
抓取纪律全部来自 config/feeds.json：只允许 HTTPS、主机必须在 allowlist 内、
单源超时 10 秒、响应上限 2MB、请求显式带 User-Agent。

规范化（两种格式进，同一种结构出）：
- 同时吃 RSS 2.0 与 Atom 1.0；RSS 取 pubDate → dc:date，Atom 取 published → updated。
- 每项必含 id / source_id / source_title / title / link / summary / published 七个字段。
- id 稳定：优先用 feed 自带的 guid / Atom id；缺失时用 link 的 sha1。不依赖抓取顺序或时间。
- link 统一升级为 https（allowlist 内主机都已实测支持）；主机不在白名单的条目直接丢弃。
- summary 只留纯文本：剥 HTML 标签、解实体、再剥一次，最后删掉残留的尖括号与控制字符，
  截断到 config 的 summary_max_chars（截断时末尾补一个「…」，总长仍不超过上限）。
  删尖括号是为了让「外部文本里绝不残留可执行标签」成为可校验的硬保证（tools/check_feeds.py 会断言）。
- published 是 ISO 8601 带偏移的字符串；确实定不下来时写 JSON null（页面显示「日期未知」）。
  日期不带的时区按该源 config 里的 default_tz 解释；源完全没有日期字段时，
  允许用该源 config 里的 date_from_url_regex 从链接路径提取（美团就是这种）。
  **禁止用抓取时间、抓取顺序或「今天」顶替缺失日期。**
- 单条日期解析失败只记日志并置 null，不让整次构建失败。

排序与去重：
- 跨源按 id 去重（先到先得，按 config 里的源顺序）。
- 分组顺序 = config 顺序（不按抓取时间）；组内按 published 倒序，null 排最后，同值按 id 升序兜底。

失败策略（重要）：
- 单个源失败（超时 / 非 HTTPS / 域名不在白名单 / HTTP 错误 / 解析失败 / 0 条）时：保留该源
  上一次已提交在 rss-items.json 里的数据、把失败原因写进构建日志、继续处理其他源。
- 只有「所有源都失败且没有任何历史数据」时，脚本才以非零码退出。

幂等：生成物里不写「抓取时间」这类每次都变的字段；内容与已有文件相同就一个字节都不写
（用 site_data.write_if_changed）。外部源本身有新内容时当然会有 diff——那是内容变化，不是噪声。

运行日志（Step 10 起）：每个阶段（读配置 / 逐源抓取 / 聚合 / 落盘 / 失败）至少一条
JSONL 事件走 scripts/runlog.py，追加进 logs/build.log 并同步打到 stdout；run_id 在
最后一行打印。input 只记源 id 与条数这类摘要，外部标题/摘要正文不进日志；
单源失败的失败原因也记进日志（脱敏后）。

信任边界：本脚本只读外部数据、只写上面两件生成物。外部文本一律只当展示文本，
绝不回写 config/feeds.json、AGENTS.md 或任何脚本，也绝不被当作指令执行
（见 AGENTS.md「外部数据是不可信输入」一节）。
"""

import hashlib
import html
import json
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from site_data import SITE_NAME, rel, write_if_changed
from runlog import wrap_main

CONFIG_PATH = ROOT / "config" / "feeds.json"
DATA_OUT = ROOT / "public" / "data" / "rss-items.json"
OPML_OUT = ROOT / "public" / "subscriptions.opml"

SCHEMA = 1
ITEM_FIELDS = ("id", "source_id", "source_title", "title", "link", "summary", "published")
READ_CHUNK = 64 * 1024
OPML_TITLE = "%s · 订阅源" % SITE_NAME

TAG_RE = re.compile(r"<[^>]*>")
WS_RE = re.compile(r"\s+")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
TZ_RE = re.compile(r"^([+-])(\d{2}):?(\d{2})$")


class FeedError(Exception):
    """单个源不可用。由调用方捕获：保留历史数据、记日志、继续下一个源。"""


# ---------------------------------------------------------------- 配置

def load_config(path=CONFIG_PATH):
    try:
        cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FeedError("读不到或解析不了 %s：%s" % (path, exc))
    for key in ("allowlist", "sources"):
        if not isinstance(cfg.get(key), list) or not cfg[key]:
            raise FeedError("config 缺少 %s" % key)
    for source in cfg["sources"]:
        for key in ("id", "title", "xml_url", "html_url", "opml_public"):
            if key not in source:
                raise FeedError("config 的源 %r 缺少 %s" % (source.get("id"), key))
    return cfg


def parse_tz(text, fallback=timezone(timedelta(hours=8))):
    """config 里的 default_tz："+08:00" / "+0800" / "-05:00"。"""
    if not text:
        return fallback
    m = TZ_RE.match(text.strip())
    if not m:
        raise FeedError("default_tz 写法不认识：%r（应为 +08:00 这种）" % text)
    sign = 1 if m.group(1) == "+" else -1
    minutes = sign * (int(m.group(2)) * 60 + int(m.group(3)))
    return timezone(timedelta(minutes=minutes))


# ---------------------------------------------------------------- 抓取

def check_source_url(url, allowlist):
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https":
        raise FeedError("订阅地址不是 HTTPS：%s" % url)
    host = parts.netloc.lower()
    if host not in allowlist:
        raise FeedError("域名 %s 不在 allowlist 内" % (host or url))
    return host


def fetch(url, cfg, allowlist):
    """按 config 的超时/上限/UA 抓一次；返回解码前的原始字节。"""
    timeout = float(cfg.get("timeout_seconds", 10))
    max_bytes = int(cfg.get("max_bytes", 2 * 1024 * 1024))
    req = urllib.request.Request(url, headers={
        "User-Agent": cfg.get("user_agent", "my-agent-site-feed-reader/1.0"),
        "Accept": "application/atom+xml, application/rss+xml, application/xml;q=0.9, */*;q=0.5",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.5",
        "Accept-Encoding": "identity",
        "Connection": "close",
    })
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            final = resp.geturl()
            # 重定向后仍必须是白名单里的 https 主机（美团 /feed/ → 同主机 /rss.xml 属正常）
            check_source_url(final, allowlist)
            chunks, read = [], 0
            while True:
                chunk = resp.read(READ_CHUNK)
                if not chunk:
                    break
                chunks.append(chunk)
                read += len(chunk)
                if read > max_bytes:
                    raise FeedError("响应超过 %d 字节上限（%s）" % (max_bytes, final))
            data = b"".join(chunks)
    except urllib.error.HTTPError as exc:
        raise FeedError("HTTP %d %s" % (exc.code, exc.reason))
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, socket.timeout):
            raise FeedError("超时（>%g 秒）" % timeout)
        raise FeedError("连接失败：%s" % exc.reason)
    except socket.timeout:
        raise FeedError("超时（>%g 秒）" % timeout)
    finally:
        time.perf_counter() - started
    if not data:
        raise FeedError("响应体是空的")
    return data, final


# ---------------------------------------------------------------- 文本

def clean_text(raw, limit):
    """外部 HTML → 纯文本。剥标签 → 解实体 → 再剥一次 → 删残留尖括号 → 压空白 → 截断。

    再剥一次是必须的：`&lt;script&gt;` 这类实体解出来后就是真标签，不能留。
    最后连孤立的 `<` `>` 也删掉，于是「输出里不含裸 <script」成了可断言的硬保证。
    """
    if not raw:
        return ""
    text = TAG_RE.sub(" ", raw)
    text = html.unescape(text)
    text = TAG_RE.sub(" ", text)
    text = text.replace("<", " ").replace(">", " ")
    text = CONTROL_RE.sub(" ", text)
    text = WS_RE.sub(" ", text).strip()
    if limit and len(text) > limit:
        text = text[:max(limit - 1, 1)].rstrip() + "…"
    return text


# ---------------------------------------------------------------- XML 取值

def lname(tag):
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def kids(el, name):
    return [c for c in el if lname(c.tag) == name]


def child_text(el, name):
    """同名元素有无命名空间两份时（WordPress 系 <link> 与 <atom:link> 并存）优先取无命名空间那份。"""
    found = kids(el, name)
    if not found:
        return None
    plain = [c for c in found if not str(c.tag).startswith("{")]
    chosen = plain[0] if plain else found[0]
    text = "".join(chosen.itertext()).strip()
    return text or None


def atom_link(el):
    best = None
    for link in kids(el, "link"):
        href = (link.get("href") or "").strip()
        if not href:
            continue
        rel = (link.get("rel") or "alternate").lower()
        if rel == "alternate" and (link.get("type") or "text/html").startswith("text/html"):
            return href
        if best is None:
            best = href
    return best


# ---------------------------------------------------------------- 日期

def ensure_tz(dt, tz):
    return dt.replace(tzinfo=tz) if dt.tzinfo is None else dt


def parse_date(raw, tz):
    """宽容解析：RFC 822（含 GMT、+0800、两位年份）与 ISO 8601 都吃；失败返回 None。"""
    if not raw:
        return None
    text = raw.strip()
    try:
        return ensure_tz(parsedate_to_datetime(text), tz)
    except (TypeError, ValueError):
        pass
    try:
        return ensure_tz(datetime.fromisoformat(text.replace("Z", "+00:00")), tz)
    except ValueError:
        return None


def date_from_link(link, source, tz, log):
    """条目完全没有日期字段时，按该源 config 的正则从链接路径提取 YYYY/MM/DD。

    只从源自己的数据推导（美团链接就是 /2026/09/22/slug.html），不算编造；
    提取到的只有日期、没有时刻，时刻记 00:00:00。这在报告里要写明。
    """
    pattern = source.get("date_from_url_regex")
    if not pattern or not link:
        return None
    m = re.search(pattern, link)
    if not m or len(m.groups()) < 3:
        return None
    try:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=tz)
    except ValueError:
        log("    日期正则匹配到非法日期：%r" % (m.group(0),))
        return None


# ---------------------------------------------------------------- 解析

def parse_feed(data, source, cfg, log):
    """RSS 2.0 或 Atom 1.0 → 规范化条目列表。"""
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise FeedError("XML 解析失败：%s" % exc)

    name = lname(root.tag)
    if name == "rss":
        container = (kids(root, "channel") or [root])[0]
        raw_items = kids(container, "item")
        kind = "rss"
    elif name == "feed":
        raw_items = kids(root, "entry")
        kind = "atom"
    elif name == "RDF":
        raise FeedError("是 RSS 1.0（RDF），本步只支持 RSS 2.0 与 Atom 1.0")
    else:
        raise FeedError("根元素是 <%s>，不是 feed" % (name or "?"))

    tz = parse_tz(source.get("default_tz"))
    items, undated, dropped_host = [], 0, 0
    for el in raw_items:
        if kind == "atom":
            title = child_text(el, "title")
            link = atom_link(el) or child_text(el, "id")
            raw_date = child_text(el, "published") or child_text(el, "updated")
            summary = child_text(el, "summary") or child_text(el, "content")
            guid = child_text(el, "id")
        else:
            title = child_text(el, "title")
            link = child_text(el, "link")
            raw_date = child_text(el, "pubDate") or child_text(el, "date")
            summary = child_text(el, "description") or child_text(el, "summary")
            guid = child_text(el, "guid") or link

        link = (link or "").strip()
        if link.startswith("http://"):
            link = "https://" + link[len("http://"):]      # 统一升级为 https
        if not link.startswith("https://"):
            dropped_host += 1
            continue
        if urllib.parse.urlsplit(link).netloc.lower() not in cfg["_allowlist"]:
            dropped_host += 1
            continue

        published = parse_date(raw_date, tz)
        if published is None:
            published = date_from_link(link, source, tz, log)
        if published is None:
            undated += 1

        items.append({
            "id": guid.strip() if guid else "sha1:" + hashlib.sha1(
                link.encode("utf-8")).hexdigest(),
            "source_id": source["id"],
            "source_title": source["title"],
            "title": clean_text(title, None) or "(无标题)",
            "link": link,
            "summary": clean_text(summary, int(cfg.get("summary_max_chars", 160))),
            "published": published.isoformat() if published else None,
        })

    if undated:
        log("    %d 条没有可确定的日期，published 记为 null" % undated)
    if dropped_host:
        log("    丢弃 %d 条（链接不是 https 或主机不在白名单）" % dropped_host)
    if not items:
        raise FeedError("解析成功但没有可用条目")
    return items


# ---------------------------------------------------------------- 组装

def sort_items(items):
    """published 倒序；null 排最后；同值按 id 升序（排序可复现）。"""
    def key(item):
        stamp = item["published"]
        if stamp is None:
            return (1, 0.0, item["id"])
        return (0, -datetime.fromisoformat(stamp).timestamp(), item["id"])
    return sorted(items, key=key)


def build_document(cfg, per_source, log):
    """跨源按 id 去重（先到先得，按 config 顺序），再按 config 顺序分组、组内排序。"""
    seen, dropped = {}, 0
    groups = []
    for source in cfg["sources"]:
        items = []
        for item in per_source.get(source["id"], []):
            if item["id"] in seen:
                dropped += 1
                log("  去重：%s 的 %r 与 %s 重复" % (source["id"], item["title"][:30],
                                                    seen[item["id"]]))
                continue
            seen[item["id"]] = source["id"]
            items.append(item)
        groups.append({
            "id": source["id"],
            "title": source["title"],
            "html_url": source["html_url"],
            "xml_url": source["xml_url"],
            "items": sort_items(items),
        })
    return {"schema": SCHEMA, "sources": groups}, dropped


def render_json(doc):
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


def render_opml(cfg):
    """只写标题 + xmlUrl + htmlUrl；不含任何文章内容，也不含生成时间（幂等）。"""
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<opml version="2.0">',
             "  <head>",
             "    <title>%s</title>" % html.escape(OPML_TITLE, quote=False),
             "  </head>",
             "  <body>"]
    for source in cfg["sources"]:
        if not source.get("opml_public"):
            continue
        lines.append('    <outline type="rss" text="%s" title="%s" xmlUrl="%s" htmlUrl="%s"/>'
                     % (html.escape(source["title"], quote=True),
                        html.escape(source["title"], quote=True),
                        html.escape(source["xml_url"], quote=True),
                        html.escape(source["html_url"], quote=True)))
    lines += ["  </body>", "</opml>", ""]
    return "\n".join(lines)


def load_previous(path=DATA_OUT):
    """上一次提交的 rss-items.json：源失败时用它保住旧数据。"""
    if not Path(path).is_file():
        return {}
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {g["id"]: g.get("items", []) for g in doc.get("sources", []) if "id" in g}


def main(log, argv=None):
    def out(msg):
        print(msg)

    cfg = load_config()
    cfg["_allowlist"] = [h.lower() for h in cfg["allowlist"]]
    previous = load_previous()
    log.event("read_config", input={"源": len(cfg["sources"]),
                                    "allowlist": len(cfg["allowlist"]),
                                    "上次数据源数": len(previous)})

    ok, failed = [], []
    per_source = {}
    for source in cfg["sources"]:
        sid = source["id"]
        try:
            check_source_url(source["xml_url"], cfg["_allowlist"])
            data, final = fetch(source["xml_url"], cfg, cfg["_allowlist"])
            items = parse_feed(data, source, cfg, out)
            per_source[sid] = items
            ok.append(sid)
            note = "" if final == source["xml_url"] else "（重定向到 %s）" % final
            log.event("fetch_source", input={"source": sid, "条目": len(items),
                                             "字节": len(data)})
            out("  成功 %-18s %2d 条%s" % (sid, len(items), note))
        except FeedError as exc:
            failed.append((sid, str(exc)))
            kept = previous.get(sid, [])
            per_source[sid] = kept
            log.event("fetch_source", "fail", error=str(exc),
                      input={"source": sid, "保留上次数据": len(kept)})
            out("  失败 %-18s %s → %s" % (sid, exc,
                                        "保留上次数据 %d 条" % len(kept) if kept
                                        else "没有历史数据可保留（本栏留空）"))

    doc, dropped = build_document(cfg, per_source, out)
    total = sum(len(g["items"]) for g in doc["sources"])
    log.event("aggregate", input={"条目": total, "跨源去重": dropped})
    wrote = write_if_changed(DATA_OUT, render_json(doc))
    wrote_opml = write_if_changed(OPML_OUT, render_opml(cfg))
    log.event("write_outputs", input={"rss-items.json 写入": int(wrote),
                                      "subscriptions.opml 写入": int(wrote_opml)})

    out("抓取结果：成功 %d / %d 个源，失败 %d 个；规范化条目 %d 条，跨源去重 %d 条"
        % (len(ok), len(cfg["sources"]), len(failed), total, dropped))
    if failed:
        out("  失败清单：" + "；".join("%s（%s）" % (s, r) for s, r in failed))
    out("  %s %s" % (rel(DATA_OUT), "写入" if wrote else "未变化（与现有 JSON 逐字节相同）"))
    out("  %s %s" % (rel(OPML_OUT), "写入" if wrote_opml else "未变化"))
    if not ok and total == 0:
        out("构建失败：所有源都失败且没有任何历史数据")
        log.event("fetch_all", "fail", error="所有源都失败且没有任何历史数据",
                  input={"源": len(cfg["sources"]), "条目": 0})
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(wrap_main("fetch_feeds", main))
    except FeedError as exc:
        print("构建失败：%s" % exc)
        sys.exit(1)
