#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""probe_feed.py —— 只读探查外部订阅源（RSS 2.0 / Atom 1.0）的可用性。

用法（仓库根运行）：

    python scripts/probe_feed.py <url> [<url> ...]
    python scripts/probe_feed.py --json <url> ...          # 机器可读，便于汇总
    python scripts/probe_feed.py --samples 3 <url> ...     # 每个源多看几条样例

这是 Step 6 的选源工具，不是抓取器：只对候选地址各发一次 GET，不写任何文件、
不产出聚合结果。它回答的是「这个源能不能用、是什么格式、字段齐不齐」：

  - 地址是否 HTTPS（含重定向后的最终地址与跳转次数）；
  - 返回内容能否解析为 RSS 2.0 或 Atom 1.0（分别识别，也认 RSS 1.0 / HTML / 非 XML）；
  - feed 标题、站点域名、语言、条目数量、最新条目日期；
  - 单个条目的字段样例（标题、链接、发布时间、摘要长度、guid/id 有无）；
  - 响应体积、耗时（首字节与总时长）、内容类型与服务器/缓存响应头。

多个源一起传时会额外比较：条目链接、规范化标题、站点域名是否重复——「两个源内容
重复」必须靠真实条目比对，不能靠猜。

请求纪律（对应课程对「来源限制」的要求）：显式 User-Agent（不少源拒绝默认的
Python-urllib）、超时 10 秒、响应上限 2MB（超过即截断并明确报告）。除标准库外无依赖。

退出码：0 = 全部源可用；1 = 至少一个源抓取或解析失败；2 = 用法错误。
"""

import argparse
import gzip
import json
import re
import socket
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zlib
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

# 显式 UA：站点地址给源站一个可追溯的出处；不带 UA 或带默认 Python-urllib 常被 403。
USER_AGENT = ("my-agent-site-feed-probe/0.1 (+https://ajsterling123.github.io/my-agent-site/)")

TIMEOUT = 10.0                      # 秒
MAX_BYTES = 2 * 1024 * 1024         # 2MB
READ_CHUNK = 64 * 1024

ACCEPT = ("application/atom+xml, application/rss+xml, application/xml;q=0.9, "
          "text/xml;q=0.8, */*;q=0.5")

FORMAT_RSS2 = "RSS 2.0"
FORMAT_ATOM1 = "Atom 1.0"
FORMAT_RSS1 = "RSS 1.0 (RDF)"
FORMAT_HTML = "HTML 页面（不是 feed）"
FORMAT_UNKNOWN = "无法识别"

ENTITIES_MIN = {"&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"', "&apos;": "'",
                "&#39;": "'", "&nbsp;": " "}
TAG_RE = re.compile(r"<[^>]*>")

# RSS 的 pubDate 规范要求 RFC 822（英文星期/月份缩写 + 时区）。这条正则只认规范写法：
# 腾讯安全那个源写的是 "2026-08-06 15:34:26"（无时区），能解析但不规范，必须报出来。
RFC822_STRICT_RE = re.compile(
    r"^[A-Z][a-z]{2}, \d{1,2} [A-Z][a-z]{2} \d{2,4} \d{2}:\d{2}(:\d{2})? "
    r"([+-]\d{4}|UT|GMT|EST|EDT|CST|CDT|MST|MDT|PST|PDT)$")
TZ_RE = re.compile(r"[+-]\d{4}$|\b(UT|GMT|EST|EDT|CST|CDT|MST|MDT|PST|PDT)\b|Z$")
# 部分源条目里没有日期，但链接路径带日期（美团 /2026/09/22/xxx.html），可作兜底
LINK_DATE_RE = re.compile(r"/(20\d{2})/(\d{1,2})/(\d{1,2})(?:/|$)")


# ---------------------------------------------------------------- 抓取

def build_request(url):
    return urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": ACCEPT,
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.5",
        # 不请求压缩：脚本要如实报「响应体积」，也让 2MB 上限对得上实际字节
        "Accept-Encoding": "identity",
        "Connection": "close",
    })


def decompress(body, encoding):
    """服务器无视 Accept-Encoding 仍然压缩时，自己解回来（gzip / deflate）。"""
    enc = (encoding or "").lower()
    try:
        if "gzip" in enc:
            return gzip.decompress(body), "gzip"
        if "deflate" in enc:
            try:
                return zlib.decompress(body), "deflate"
            except zlib.error:
                return zlib.decompress(body, -zlib.MAX_WBITS), "deflate"
    except (OSError, zlib.error) as exc:
        return body, "解压失败（%s）" % exc
    return body, None


def fetch(url):
    """发一次 GET。返回 dict：成功与否都返回，把失败原因写成字段而不是抛异常。"""
    result = {"url": url, "final_url": None, "status": None, "headers": {}, "body": b"",
              "size": 0, "truncated": False, "ttfb": None, "elapsed": None,
              "content_type": None, "encoding_note": None, "error": None, "redirects": 0}
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(build_request(url), timeout=TIMEOUT) as resp:
            result["ttfb"] = time.perf_counter() - started
            result["status"] = resp.status
            result["final_url"] = resp.geturl()
            result["headers"] = {k.lower(): v for k, v in resp.headers.items()}
            result["content_type"] = result["headers"].get("content-type")

            chunks = []
            read = 0
            while True:
                chunk = resp.read(READ_CHUNK)
                if not chunk:
                    break
                chunks.append(chunk)
                read += len(chunk)
                if read > MAX_BYTES:          # 超过上限：丢掉多余部分，标明截断
                    result["truncated"] = True
                    break
            body = b"".join(chunks)[:MAX_BYTES]
            result["body"] = body
            result["size"] = len(body)
    except urllib.error.HTTPError as exc:
        result["status"] = exc.code
        result["headers"] = {k.lower(): v for k, v in exc.headers.items()}
        result["content_type"] = result["headers"].get("content-type")
        try:
            result["body"] = exc.read(READ_CHUNK)
        except Exception:
            pass
        result["error"] = "HTTP %d %s" % (exc.code, exc.reason)
    except urllib.error.URLError as exc:
        reason = exc.reason
        if isinstance(reason, socket.timeout):
            result["error"] = "超时（>%.0f 秒）" % TIMEOUT
        elif isinstance(reason, ssl.SSLError):
            result["error"] = "TLS 握手失败：%s" % reason
        else:
            result["error"] = "连接失败：%s" % reason
    except socket.timeout:
        result["error"] = "超时（>%.0f 秒）" % TIMEOUT
    except Exception as exc:                  # 兜底：绝不让探查脚本自己崩掉
        result["error"] = "%s: %s" % (type(exc).__name__, exc)
    finally:
        result["elapsed"] = time.perf_counter() - started

    if result["body"]:
        body, note = decompress(result["body"], result["headers"].get("content-encoding"))
        result["body"] = body
        result["encoding_note"] = note
        if note and not note.startswith("解压失败"):
            result["size"] = len(body)
    return result


# ---------------------------------------------------------------- 解码

CHARSET_RE = re.compile(r"charset\s*=\s*[\"']?([\w.-]+)", re.I)


def decode_text(data, content_type):
    """按 Content-Type → XML 声明 → UTF-8 → GB18030 依次试，返回 (文本, 用了哪种编码)。"""
    candidates = []
    if content_type:
        m = CHARSET_RE.search(content_type)
        if m:
            candidates.append(m.group(1))
    head = data[:200].decode("ascii", errors="ignore")
    m = re.search(r'encoding\s*=\s*["\']([\w.-]+)["\']', head, re.I)
    if m:
        candidates.append(m.group(1))
    candidates += ["utf-8", "gb18030"]

    seen = []
    for enc in candidates:
        enc = enc.lower()
        if enc in seen:
            continue
        seen.append(enc)
        try:
            return data.decode(enc), enc
        except (UnicodeDecodeError, LookupError):
            continue
    return data.decode("utf-8", errors="replace"), "utf-8(replace，有坏字节)"


# ---------------------------------------------------------------- XML 帮助函数

def lname(tag):
    """去命名空间取本地名：Atom 在 {http://www.w3.org/2005/Atom} 命名空间下。"""
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def kids(el, name):
    """按本地名找直接子元素（同时兼容带/不带命名空间的写法）。"""
    return [c for c in el if lname(c.tag) == name]


def child_text(el, name):
    """按本地名取子元素文本。同名元素同时存在「无命名空间」和「带命名空间」两份时
    （WordPress 系 RSS 常见：<link> 与 <atom:link rel="self"> 并存），优先取无命名空间的那份，
    否则会把 atom:link 的空文本当成 channel 的站点地址。"""
    found = kids(el, name)
    if not found:
        return None
    plain = [c for c in found if not str(c.tag).startswith("{")]
    chosen = plain[0] if plain else found[0]
    text = "".join(chosen.itertext()).strip()
    return text or None


def atom_link(el):
    """Atom 的链接在 <link href> 属性里，优先 rel=alternate / 无 rel。"""
    best = None
    for link in kids(el, "link"):
        href = (link.get("href") or "").strip()
        if not href:
            continue
        rel = (link.get("rel") or "alternate").lower()
        if rel == "alternate" and link.get("type", "text/html").startswith("text/html"):
            return href
        if best is None and rel in ("alternate", ""):
            best = href
    return best


def plain_text(markup):
    """剥掉标签与实体，得到读者真正看到的字符数（RSS 的 description 常含 HTML）。"""
    if not markup:
        return ""
    text = TAG_RE.sub(" ", markup)
    for entity, char in ENTITIES_MIN.items():
        text = text.replace(entity, char)
    text = re.sub(r"&#\d+;", "", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_date(raw):
    """RSS 用 RFC 822、Atom 用 ISO 8601；两种都试，返回 (原始, 归一化 ISO, 错误)。"""
    if not raw:
        return None, None, "字段缺失"
    text = raw.strip()
    try:
        dt = parsedate_to_datetime(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return text, dt.isoformat(), None
    except (TypeError, ValueError):
        pass
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return text, dt.isoformat(), None
    except ValueError:
        return text, None, "无法解析为 RFC 822 或 ISO 8601"


# ---------------------------------------------------------------- 解析

def detect_format(root, data):
    """分别识别 RSS 2.0 与 Atom 1.0；顺带认出 RSS 1.0、HTML 和非 XML。"""
    name = lname(root.tag)
    ns = root.tag.split("}", 1)[0][1:] if "}" in root.tag else ""

    if name == "rss":
        version = (root.get("version") or "").strip()
        label = FORMAT_RSS2 if version == "2.0" else "RSS（version=%s）" % (version or "未声明")
        return label, "rss", version, ns
    if name == "feed":
        if ns == "http://www.w3.org/2005/Atom":
            return FORMAT_ATOM1, "atom", "1.0", ns
        return "%s（命名空间 %s）" % (FORMAT_ATOM1, ns or "缺失"), "atom", "1.0", ns
    if name == "RDF":
        return FORMAT_RSS1, "rdf", "1.0", ns
    if name == "html":
        return FORMAT_HTML, "html", None, ns
    return "%s（根元素 <%s>）" % (FORMAT_UNKNOWN, name or "?"), "other", None, ns


def parse_items(root, kind):
    """取条目列表及其字段（RSS 的 item / Atom 的 entry），字段名统一成内部名。"""
    if kind in ("rss", "rdf"):
        containers = kids(root, "channel") or [root]
        raw_items = []
        for c in containers:
            raw_items += kids(c, "item")
    elif kind == "atom":
        raw_items = kids(root, "entry")
    else:
        return []

    items = []
    for el in raw_items:
        if kind == "atom":
            title = child_text(el, "title")
            link = atom_link(el) or child_text(el, "id")
            date_field = "published" if child_text(el, "published") else "updated"
            raw_date = child_text(el, "published") or child_text(el, "updated")
            summary = child_text(el, "summary")
            content = child_text(el, "content")
            summary_kind = "summary" if summary else ("content" if content else None)
            summary = summary or content
            ident = child_text(el, "id")
        else:
            title = child_text(el, "title")
            link = child_text(el, "link")
            date_field = "pubDate" if child_text(el, "pubDate") else ("dc:date" if child_text(el, "date") else None)
            raw_date = child_text(el, "pubDate") or child_text(el, "date")
            summary = child_text(el, "description") or child_text(el, "summary")
            summary_kind = "description" if child_text(el, "description") else ("summary" if summary else None)
            ident = child_text(el, "guid") or link
        raw, iso, err = parse_date(raw_date)
        items.append({
            "title": title,
            "link": link,
            "date_field": date_field,
            "date_raw": raw,
            "date_iso": iso,
            "date_error": err,
            "summary_field": summary_kind,
            "summary_chars": len(plain_text(summary)),
            "summary_bytes": len(summary.encode("utf-8")) if summary else 0,
            "has_id": bool(ident),
        })
    return items


def latest_item(items):
    dated = [it for it in items if it["date_iso"]]
    if not dated:
        return None
    return max(dated, key=lambda it: it["date_iso"])


def analyze(url, samples):
    """探查一个地址，返回结构化报告。"""
    rep = {"url": url, "samples": samples}
    got = fetch(url)
    scheme = urllib.parse.urlsplit(url).scheme
    final_scheme = urllib.parse.urlsplit(got["final_url"] or "").scheme
    rep["https"] = (scheme == "https")
    rep["final_https"] = (final_scheme == "https")
    rep["fetch"] = {k: got[k] for k in ("final_url", "status", "size", "truncated",
                                        "ttfb", "elapsed", "content_type", "error",
                                        "encoding_note")}
    rep["fetch"]["headers"] = {k: v for k, v in got["headers"].items()
                               if k in ("server", "content-type", "cache-control", "age",
                                        "x-cache", "via", "cf-cache-status", "location",
                                        "content-encoding", "last-modified", "etag")}
    rep["format"] = None
    rep["items"] = []
    rep["item_count"] = 0
    rep["title"] = None
    rep["domain"] = None
    rep["language"] = None
    rep["latest"] = None
    rep["problems"] = []
    rep["warnings"] = []

    if got["error"]:
        rep["problems"].append("抓取失败：%s" % got["error"])
        return rep
    if got["status"] != 200:
        rep["problems"].append("HTTP 状态不是 200")
        return rep
    if not got["body"]:
        rep["problems"].append("响应体是空的")
        return rep

    try:
        root = ET.fromstring(got["body"])
    except ET.ParseError as exc:
        text, enc = decode_text(got["body"], got["content_type"])
        rep["format"] = "不是合法 XML：%s" % exc
        rep["problems"].append("XML 解析失败（%s）；前 120 字：%s"
                               % (exc, repr(text[:120])))
        rep["bytes_hint"] = {"encoding_used": enc}
        return rep

    label, kind, version, ns = detect_format(root, got["body"])
    rep["format"] = label
    rep["format_kind"] = kind
    rep["format_version"] = version
    rep["format_namespace"] = ns
    if kind in ("other", "html"):
        rep["problems"].append("根元素不是 RSS/Atom feed（%s）" % label)
        return rep

    text, enc = decode_text(got["body"], got["content_type"])
    rep["encoding_used"] = enc
    if kind == "rdf":
        rep["problems"].append("是 RSS 1.0（RDF），不是课程要的 RSS 2.0 / Atom 1.0")

    if kind == "atom":
        rep["title"] = child_text(root, "title")
        rep["domain"] = atom_link(root) or child_text(root, "id")
        rep["language"] = root.get("{http://www.w3.org/XML/1998/namespace}lang") or root.get("lang")
    else:
        channel = (kids(root, "channel") or [root])[0]
        rep["title"] = child_text(channel, "title")
        site = child_text(channel, "link")
        raw_site = channel.find("link")            # 无命名空间的 <link> 才是站点地址
        if raw_site is not None and raw_site.get("href"):
            site = raw_site.get("href")
        rep["domain"] = site
        rep["language"] = child_text(channel, "language")

    items = parse_items(root, kind)
    rep["items"] = items
    rep["item_count"] = len(items)
    if not items:
        rep["problems"].append("解析成功但一个条目都没有")
    latest = latest_item(items)
    rep["latest"] = latest and {"title": latest["title"], "date_field": latest["date_field"],
                                "date_raw": latest["date_raw"], "date_iso": latest["date_iso"]}

    undated = [it for it in items if not it["date_iso"]]
    if undated:
        rep["problems"].append("%d 个条目没有可解析的日期" % len(undated))
    nolink = [it for it in items if not it["link"]]
    if nolink:
        rep["problems"].append("%d 个条目没有链接" % len(nolink))

    check_dates(rep, kind, items)

    titles = [plain_text(it["title"]) for it in items if it["title"]]
    dupes = sorted({t for t in titles if titles.count(t) > 1})
    rep["duplicate_titles_inside"] = dupes
    return rep


def check_dates(rep, kind, items):
    """日期规范性的提醒：能解析 ≠ 规范。这些都进 warnings，不影响「可用」判定。"""
    if kind in ("rss", "rdf"):
        odd = [it for it in items if it["date_raw"] and not RFC822_STRICT_RE.match(it["date_raw"])]
        if odd:
            rep["warnings"].append(
                "%d/%d 个条目的日期不是标准 RFC 822（规范要求英文星期/月份缩写 + 时区），"
                "例如 %r；严格阅读器可能拒收或把时刻算错"
                % (len(odd), len(items), odd[0]["date_raw"]))
    naive = [it for it in items if it["date_raw"] and not TZ_RE.search(it["date_raw"].strip())]
    if naive:
        rep["warnings"].append(
            "%d/%d 个条目的日期不带时区（例如 %r）——读取方只能自行假定时区，"
            "本脚本按 UTC 归一化，实际多为 +0800，会差 8 小时"
            % (len(naive), len(items), naive[0]["date_raw"]))

    no_date = [it for it in items if not it["date_iso"]]
    if no_date:
        derivable = [it for it in no_date if it["link"] and LINK_DATE_RE.search(it["link"])]
        if derivable:
            stamps = []
            for it in derivable:
                m = LINK_DATE_RE.search(it["link"])
                stamps.append("%04d-%02d-%02d" % (int(m.group(1)), int(m.group(2)), int(m.group(3))))
            stamps.sort()
            rep["warnings"].append(
                "条目级没有日期字段，但 %d/%d 条能从链接路径推出日期（如 %s；推出范围 %s ~ %s）"
                % (len(derivable), len(no_date), derivable[0]["link"], stamps[0], stamps[-1]))
        else:
            rep["warnings"].append("条目级没有日期字段，链接里也推不出日期，只能按抓取顺序排")


# ---------------------------------------------------------------- 多源比较

def compare(reports):
    """条目链接、标题、站点域名三处比对重复——判「两个源内容是否重复」的证据。"""
    def norm_link(u):
        if not u:
            return None
        parts = urllib.parse.urlsplit(u)
        host = parts.netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        path = parts.path.rstrip("/") or "/"
        return "%s%s" % (host, path.lower())

    def norm_title(t):
        return re.sub(r"[\s\W_]+", "", plain_text(t or "")).lower()

    links, titles, hosts = {}, {}, {}
    for rep in reports:
        if not rep.get("items"):
            continue
        origin = urllib.parse.urlsplit(rep["url"]).netloc.lower()
        for it in rep["items"]:
            if norm_link(it["link"]):
                links.setdefault(norm_link(it["link"]), []).append(rep["url"])
            if norm_title(it["title"]):
                titles.setdefault(norm_title(it["title"]), []).append(rep["url"])
        if rep.get("domain"):
            hosts.setdefault(urllib.parse.urlsplit(rep["domain"]).netloc.lower(), []).append(rep["url"])
        hosts.setdefault(origin, []).append(rep["url"])

    def pairs(index):
        out = []
        for key, urls in sorted(index.items()):
            uniq = sorted(set(urls))
            if len(uniq) > 1:
                out.append((key, uniq))
        return out

    return {"shared_item_links": pairs(links), "shared_titles": pairs(titles),
            "shared_hosts": pairs(hosts)}


# ---------------------------------------------------------------- 输出

def fmt_size(n):
    if n >= 1024 * 1024:
        return "%.2f MB" % (n / 1024 / 1024)
    if n >= 1024:
        return "%.1f KB" % (n / 1024)
    return "%d B" % n


def fmt_sec(v):
    return "—" if v is None else "%.2f s" % v


def render(rep):
    out = []
    out.append("=" * 78)
    out.append("源  %s" % rep["url"])
    out.append("=" * 78)

    if rep["https"]:
        line = "HTTPS   ✓ 地址是 https"
    else:
        line = "HTTPS   ✗ 地址不是 https（%s）" % (urllib.parse.urlsplit(rep["url"]).scheme or "无 scheme")
    if rep["fetch"].get("final_url") and rep["fetch"]["final_url"] != rep["url"]:
        line += "；重定向到 %s（%s）" % (rep["fetch"]["final_url"],
                                        "仍是 https" if rep["final_https"] else "已不再是 https")
    out.append(line)

    f = rep["fetch"]
    if f.get("error"):
        out.append("请求    ✗ %s（耗时 %s）" % (f["error"], fmt_sec(f["elapsed"])))
    else:
        flags = []
        if f["truncated"]:
            flags.append("已按 2MB 上限截断")
        if f.get("encoding_note"):
            flags.append("响应被压缩：%s（已解回，体积按解压后算）" % f["encoding_note"])
        out.append("请求    HTTP %s · %s · %s · 首字节 %s · 总耗时 %s%s"
                   % (f["status"], f["content_type"] or "无 content-type", fmt_size(f["size"]),
                      fmt_sec(f["ttfb"]), fmt_sec(f["elapsed"]),
                      ("；" + "；".join(flags)) if flags else ""))

    out.append("解析    %s" % (rep["format"] or "未解析"))
    if rep.get("encoding_used"):
        out.append("编码    %s" % rep["encoding_used"])
    if rep.get("title"):
        out.append("标题    %s" % rep["title"])
    if rep.get("domain"):
        host = urllib.parse.urlsplit(rep["domain"]).netloc
        out.append("站点    %s   （feeds 里声明的站点地址：%s）" % (host or rep["domain"], rep["domain"]))
    if rep.get("language"):
        out.append("语言    %s" % rep["language"])
    if rep.get("item_count"):
        out.append("条目    %d 条" % rep["item_count"])
    if rep.get("latest"):
        out.append("最新    %s（字段 %s，原文 %r）"
                   % (rep["latest"]["date_iso"], rep["latest"]["date_field"], rep["latest"]["date_raw"]))

    for i, it in enumerate(rep["items"][:rep.get("samples", 1)]):
        out.append("样例条目[%d]" % i)
        out.append("    标题    %s" % (it["title"] or "（缺失）"))
        out.append("    链接    %s" % (it["link"] or "（缺失）"))
        out.append("    时间    %s%s" % (it["date_iso"] or "（无）",
                                        "" if it["date_iso"] or not it["date_raw"]
                                        else "  ← %s" % it["date_error"]))
        out.append("    摘要    %s" % ("（缺失）" if it["summary_field"] is None else
                                       "%d 字符（去标签后；字段 %s，%s）"
                                       % (it["summary_chars"], it["summary_field"],
                                          fmt_size(it["summary_bytes"]))))
        out.append("    标识    %s" % ("有 id/guid" if it["has_id"] else "无 id/guid"))
    if rep.get("duplicate_titles_inside"):
        out.append("同源内重复标题  %d 个：%s" % (len(rep["duplicate_titles_inside"]),
                                            "；".join(rep["duplicate_titles_inside"][:5])))

    hdr = rep["fetch"].get("headers") or {}
    show = [(k, v) for k, v in sorted(hdr.items()) if k in
            ("server", "via", "x-cache", "cf-cache-status", "age", "cache-control", "last-modified")]
    if show:
        out.append("响应头  %s" % " · ".join("%s: %s" % (k, v) for k, v in show))

    if rep["problems"]:
        for p in rep["problems"]:
            out.append("问题    ✗ %s" % p)
    else:
        out.append("结论    ✓ 可用")
    for w in rep.get("warnings", []):
        out.append("注意    ⚠ %s" % w)
    out.append("")
    return "\n".join(out)


def render_compare(cmp):
    out = ["=" * 78, "重复性检查（按真实条目比对，不看标题像不像）", "=" * 78]
    if cmp["shared_item_links"]:
        for key, urls in cmp["shared_item_links"]:
            out.append("条目链接重复  %s  ← %s" % (key, " 与 ".join(urls)))
    else:
        out.append("条目链接重复  无")
    if cmp["shared_titles"]:
        out.append("标题重复（去掉空白与标点后相同）")
        for key, urls in cmp["shared_titles"][:20]:
            out.append("    %s  ← %s" % (key[:40], " 与 ".join(urls)))
    else:
        out.append("标题重复      无")
    if cmp["shared_hosts"]:
        for key, urls in cmp["shared_hosts"]:
            if len(urls) > 1:
                out.append("同一域名      %s  ← %s" % (key, " 与 ".join(urls)))
    else:
        out.append("同一域名      无")
    out.append("")
    return "\n".join(out)


def render_summary(reports):
    out = ["=" * 78, "汇总", "=" * 78, "%-4s %-12s %-7s %5s %10s %8s %4s  %s"
           % ("状态", "格式", "HTTPS", "条目", "体积", "耗时", "注意", "地址")]
    for rep in reports:
        ok = not rep["problems"]
        kind = rep.get("format_kind")
        label = {"rss": "RSS 2.0", "atom": "Atom 1.0", "rdf": "RSS 1.0", "html": "HTML",
                 "other": "非 feed"}.get(kind, "—")
        f = rep["fetch"]
        out.append("%-4s %-12s %-7s %5s %10s %8s %4s  %s"
                   % ("✓" if ok else "✗", label,
                      "✓" if rep["https"] and rep["final_https"] else ("✗" if not rep["https"] else "→✗"),
                      rep.get("item_count") or "—",
                      fmt_size(f["size"]) if not f.get("error") else "—",
                      fmt_sec(f["elapsed"]),
                      len(rep.get("warnings", [])) or "—",
                      rep["url"]))
    out.append("")
    return "\n".join(out)


def main(argv=None):
    global TIMEOUT, MAX_BYTES

    parser = argparse.ArgumentParser(
        description="只读探查 RSS 2.0 / Atom 1.0 订阅源（不写文件、无第三方依赖）")
    parser.add_argument("urls", nargs="+", help="一个或多个 feed 地址")
    parser.add_argument("--json", action="store_true", help="输出机器可读的 JSON")
    parser.add_argument("--samples", type=int, default=1, help="每个源打印几条样例条目（默认 1）")
    parser.add_argument("--timeout", type=float, default=TIMEOUT, help="超时秒数（默认 %.0f）" % TIMEOUT)
    parser.add_argument("--max-bytes", type=int, default=MAX_BYTES,
                        help="响应上限字节数（默认 %d = 2MB）" % MAX_BYTES)
    args = parser.parse_args(argv)

    TIMEOUT = args.timeout
    MAX_BYTES = args.max_bytes

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    reports = [analyze(u, max(args.samples, 1)) for u in args.urls]
    cmp = compare(reports) if len(reports) > 1 else None

    if args.json:
        payload = {"user_agent": USER_AGENT, "timeout": TIMEOUT, "max_bytes": MAX_BYTES,
                   "sources": reports, "comparison": cmp}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for rep in reports:
            print(render(rep))
        if cmp:
            print(render_compare(cmp))
        print(render_summary(reports))

    usable = [r for r in reports if not r["problems"]]
    kinds = {}
    for r in usable:
        kinds.setdefault(r.get("format_kind"), []).append(r["url"])
    if not args.json:
        print("可用 %d / %d 个源" % (len(usable), len(reports)))
        for kind, label in (("rss", "RSS 2.0"), ("atom", "Atom 1.0")):
            if kinds.get(kind):
                print("  %s：%d 个" % (label, len(kinds[kind])))
    return 0 if len(usable) == len(reports) else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
