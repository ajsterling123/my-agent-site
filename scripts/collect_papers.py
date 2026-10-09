#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""collect_papers.py —— 从 arXiv 检索最近的论文，规范化并合并进 public/data/papers.json。

用法（仓库根运行）：
    python scripts/collect_papers.py --query "cat:cs.AI AND all:\"LLM agent\"" --limit 10
    python scripts/collect_papers.py --query "<arXiv 查询词>" --limit 10 --since 2026-09-01

这是构建期抓取（与 scripts/fetch_feeds.py 同一口径）：浏览器端只 fetch 同域的
data/papers.json，不在页面里请求 arXiv。触发入口是 .zcode/skills/research-paper-collector
技能；也可以直接运行本脚本刷新数据。

抓取纪律（arXiv API 使用条款 + 本站惯例）：
- 数据源固定 https://export.arxiv.org/api/query（必须 https），返回 Atom 1.0，按 Atom 解析；
- 查询参数：search_query、start=0、max_results、sortBy=submittedDate、sortOrder=descending；
- 请求显式带可识别本项目的 User-Agent；单请求超时 20 秒；失败最多重试 2 次并记日志；
- **连续多次请求之间间隔 ≥3 秒**（arXiv 的礼貌要求）：同一次运行内的重试之间，以及
  跨运行的连续调用之间（用根目录 .arxiv-last-request 时间戳文件量，不提交进 git）。

规范化（每项七个字段，顺序固定，输出可复现）：
- id：arXiv 官方 id，**已剥版本号**——2401.12345v2 与 2401.12345 是同一篇，必须折叠成一条；
- title / summary：纯文本（复用 fetch_feeds.clean_text 的剥标签 + 删尖括号 + 压空白，
  摘要不截断），规则全站只写一份；
- authors：非空字符串列表；published：YYYY-MM-DD（API 是 UTC 时间戳，只取日期部分；
  解析不出合法日期的条目跳过并记日志，**不用抓取时间顶替**）；
- url：由 id 推出的 https://arxiv.org/abs/<id>，链接只来自 arXiv；source 恒为 "arXiv"。

时间范围：arXiv API 不支持服务端按日期过滤，--since 在本地按 published 过滤；
不传 --since 时「最近 N 条」= API 按提交时间倒序返回的前 N 条（默认 10）。

合并策略：读入已有 papers.json，按 id 合并（同 id 以本次抓取为准——版本号剥掉后
新数据就是该文的最新快照），按 published 倒序（同日按 id 升序，稳定可复现），
最多保留 50 条。幂等：生成物里没有「抓取时间」这类每次都变的字段，同一份输入
重复运行产出字节一致（write_if_changed，相同就不落盘）。

失败策略（课程验收项「网络失败不会清空旧数据」）：网络失败或查询无结果时，
papers.json 原样保留、原因记日志、退出码 0；只有「从未有过任何数据」（文件缺失
或历史为空）且本次也没抓到东西时才以非零码退出。

信任边界：外部标题与摘要只当展示文本，绝不当指令（AGENTS.md「外部数据是不可信输入」）；
本脚本只读 arXiv、只写 public/data/papers.json，绝不回写 config、AGENTS.md 或任何脚本；
arXiv 是预印本平台，不把任何论文描述成已同行评审。

运行日志（Step 10 起）：每个阶段（读参数 / 抓取 / 解析 / 合并 / 落盘 / 失败）至少一条
JSONL 事件走 scripts/runlog.py，追加进 logs/build.log 并同步打到 stdout；run_id 在
最后一行打印。input 只记查询词与条数这类摘要（查询词是输入摘要，可以记），
论文标题/摘要正文不进日志；失败的失败原因也记进日志（脱敏后）。
"""

import argparse
import json
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from fetch_feeds import clean_text   # 外部文本 → 纯文本的规则全站只写一份  # noqa: E402
from site_data import rel, write_if_changed   # noqa: E402
from runlog import wrap_main   # noqa: E402

API_URL = "https://export.arxiv.org/api/query"
DATA_OUT = ROOT / "public" / "data" / "papers.json"
THROTTLE_FILE = ROOT / ".arxiv-last-request"

USER_AGENT = "my-agent-site-research-collector/1.0 (+https://ajsterling123.github.io/my-agent-site/)"
TIMEOUT_SECONDS = 20
MAX_RETRIES = 2               # 首次之外最多重试 2 次
MIN_REQUEST_GAP = 3.0         # arXiv 礼貌间隔：连续请求之间 ≥3 秒
MAX_BYTES = 4 * 1024 * 1024
READ_CHUNK = 64 * 1024

SCHEMA = 1
PAPER_FIELDS = ("id", "title", "authors", "published", "summary", "url", "source")
SOURCE_NAME = "arXiv"
ABS_PREFIX = "https://arxiv.org/abs/"
MAX_KEEP = 50                 # papers.json 最多保留的条数

VERSION_SUFFIX_RE = re.compile(r"v\d+$", re.I)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ATOM_NS_ENTRY = "entry"


class FetchError(Exception):
    """arXiv 请求或解析失败。由调用方捕获：保留旧数据、记日志、非零场景再判定。"""


def lname(tag):
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def kids(el, name):
    return [c for c in el if lname(c.tag) == name]


def child_text(el, name):
    found = kids(el, name)
    if not found:
        return None
    text = "".join(found[0].itertext()).strip()
    return text or None


# ---------------------------------------------------------------- 礼貌间隔

def throttle_wait(log):
    """连续多次请求之间间隔 ≥3 秒：先量上次运行留下的时间戳，不够就补足。"""
    try:
        last = float(THROTTLE_FILE.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return
    wait = MIN_REQUEST_GAP - (time.time() - last)
    if wait > 0:
        log("礼貌间隔：距上次 arXiv 请求不足 3 秒，等待 %.1f 秒" % wait)
        time.sleep(wait)


def mark_request():
    """记录本次请求时刻（跨运行的 throttle_wait 靠它）。失败无所谓，不影响抓取本身。"""
    try:
        THROTTLE_FILE.write_text("%.3f" % time.time(), encoding="utf-8")
    except OSError:
        pass


# ---------------------------------------------------------------- 抓取

def build_url(query, max_results):
    params = urllib.parse.urlencode({
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    })
    return "%s?%s" % (API_URL, params)


def fetch_raw(query, max_results, log):
    """抓一次查询的 Atom XML；超时 20 秒，失败最多重试 2 次（重试间隔同样 ≥3 秒）。"""
    url = build_url(query, max_results)
    last_exc = None
    for attempt in range(1, MAX_RETRIES + 2):
        if attempt > 1:
            log("  第 %d 次尝试前补足 %.0f 秒礼貌间隔" % (attempt, MIN_REQUEST_GAP))
            time.sleep(MIN_REQUEST_GAP)
        throttle_wait(log)
        req = urllib.request.Request(url, headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/atom+xml, application/xml;q=0.9, */*;q=0.5",
            "Accept-Encoding": "identity",
            "Connection": "close",
        })
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                final = resp.geturl()
                if not final.startswith("https://export.arxiv.org/"):
                    raise FetchError("最终地址离开了 https 的 export.arxiv.org：%s" % final)
                chunks, read = [], 0
                while True:
                    chunk = resp.read(READ_CHUNK)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    read += len(chunk)
                    if read > MAX_BYTES:
                        raise FetchError("响应超过 %d 字节上限" % MAX_BYTES)
                return b"".join(chunks)
        except urllib.error.HTTPError as exc:
            last_exc = "HTTP %d %s" % (exc.code, exc.reason)
        except urllib.error.URLError as exc:
            reason = exc.reason
            last_exc = ("超时（>%d 秒）" % TIMEOUT_SECONDS
                        if isinstance(reason, socket.timeout) else "连接失败：%s" % reason)
        except socket.timeout:
            last_exc = "超时（>%d 秒）" % TIMEOUT_SECONDS
        except FetchError as exc:
            last_exc = str(exc)
        finally:
            mark_request()
        log("  第 %d 次请求失败：%s" % (attempt, last_exc))
    raise FetchError("重试 %d 次后仍失败：%s" % (MAX_RETRIES, last_exc))


# ---------------------------------------------------------------- 规范化

def strip_version(raw_id):
    """2401.12345v2 → 2401.12345；旧式 math/0211150v1 → math/0211150。"""
    tail = re.sub(r"^https?://arxiv\.org/abs/", "", raw_id.strip(), flags=re.I)
    return VERSION_SUFFIX_RE.sub("", tail)


def parse_entry(el, log):
    """Atom entry → 规范化条目；不合格返回 None（跳过并记日志，绝不编造字段）。"""
    raw_id = child_text(el, "id")
    if not raw_id:
        log("  跳过一条：entry 没有 id")
        return None
    if not re.match(r"^https?://arxiv\.org/abs/\S+", raw_id, re.I):
        log("  跳过一条：id 不是 arXiv abs 地址：%r" % raw_id)
        return None
    pid = strip_version(raw_id)
    if not pid:
        log("  跳过一条：id 剥掉前缀与版本号后为空：%r" % raw_id)
        return None

    title = clean_text(child_text(el, "title"), None)
    authors = [clean_text(child_text(a, "name"), None) for a in kids(el, "author")]
    authors = [a for a in authors if a]
    summary = clean_text(child_text(el, "summary") or child_text(el, "description"), None)

    raw_published = child_text(el, "published")
    published = (raw_published or "")[:10]
    if not DATE_RE.match(published):
        log("  跳过 %s：published 不是合法日期：%r" % (pid, raw_published))
        return None
    try:
        date.fromisoformat(published)
    except ValueError:
        log("  跳过 %s：published 日期非法：%s" % (pid, published))
        return None

    if not pid or not title or not authors:
        log("  跳过 %s：id / 标题 / 作者不完整" % (pid or raw_id))
        return None

    return {
        "id": pid,
        "title": title,
        "authors": authors,
        "published": published,
        "summary": summary,
        "url": ABS_PREFIX + pid,
        "source": SOURCE_NAME,
    }


def parse_feed(data, log):
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise FetchError("Atom 解析失败：%s" % exc)
    if lname(root.tag) != "feed":
        raise FetchError("根元素是 <%s>，不是 Atom feed" % (lname(root.tag) or "?"))
    papers = []
    for el in kids(root, ATOM_NS_ENTRY):
        item = parse_entry(el, log)
        if item:
            papers.append(item)
    return papers, len(kids(root, ATOM_NS_ENTRY)) - len(papers)


# ---------------------------------------------------------------- 合并

def load_previous(path=DATA_OUT):
    """已有 papers.json；不存在返回 []，坏文件记日志后也按空历史处理。"""
    if not Path(path).is_file():
        return []
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None                       # None = 坏文件，调用方决定怎么记日志
    papers = doc.get("papers") if isinstance(doc, dict) else None
    return papers if isinstance(papers, list) else None


def sort_papers(papers):
    """published 倒序；同日按 id 升序（稳定，输出可复现）——两次 sort 借稳定排序实现。"""
    papers = sorted(papers, key=lambda p: p["id"])
    return sorted(papers, key=lambda p: p["published"], reverse=True)


def merge(fetched, previous, log):
    """按 id 合并（本次抓取为准）、排序、截断到 MAX_KEEP。返回 (列表, new, updated)。"""
    by_id = {}
    for item in previous:
        if isinstance(item, dict) and set(item.keys()) == set(PAPER_FIELDS) and item.get("id"):
            by_id[item["id"]] = item
        elif isinstance(item, dict):
            log("  旧数据里一条字段不齐，丢弃：%r" % item.get("id"))
    old_ids = set(by_id)
    updated = 0
    for item in fetched:
        if item["id"] in by_id:
            updated += 1
        by_id[item["id"]] = item
    papers = sort_papers(list(by_id.values()))
    if len(papers) > MAX_KEEP:
        log("  超过保留上限 %d 条，丢弃最旧的 %d 条" % (MAX_KEEP, len(papers) - MAX_KEEP))
        papers = papers[:MAX_KEEP]
    new = len([p for p in papers if p["id"] not in old_ids])
    return papers, new, updated


def render_json(papers):
    doc = {"schema": SCHEMA, "papers": papers}
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


# ---------------------------------------------------------------- 主流程

def main(log, argv=None):
    parser = argparse.ArgumentParser(description="从 arXiv 检索论文并合并进 public/data/papers.json")
    parser.add_argument("--query", required=True, help='arXiv 查询词（见技能 references/topics.md）')
    parser.add_argument("--limit", type=int, default=10, help="本次最多取几条（默认 10）")
    parser.add_argument("--since", help="只保留 published ≥ 此日期（YYYY-MM-DD，本地过滤）")
    args = parser.parse_args(argv)

    def out(msg):
        print(msg)

    log.event("read_args", input={"查询": args.query, "limit": args.limit, "since": args.since or None})

    if not 1 <= args.limit <= MAX_KEEP:
        error = "--limit 必须在 1..%d，实际 %d" % (MAX_KEEP, args.limit)
        log.event("read_args", "fail", error=error, input={"limit": args.limit})
        out("参数不合法：%s" % error)
        return 2
    if args.since:
        if not DATE_RE.match(args.since):
            error = "--since 必须写成 YYYY-MM-DD，实际 %r" % args.since
            log.event("read_args", "fail", error=error, input={"since": args.since})
            out("参数不合法：%s" % error)
            return 2
        try:
            date.fromisoformat(args.since)
        except ValueError:
            error = "--since 不是合法日期：%s" % args.since
            log.event("read_args", "fail", error=error, input={"since": args.since})
            out("参数不合法：%s" % error)
            return 2

    previous = load_previous()
    broken_previous = previous is None
    if broken_previous:
        out("现有的 papers.json 解析不了：若本次抓到东西将重建；若本次失败则原样保留不动。")
        previous = []
    else:
        previous = [p for p in previous if isinstance(p, dict)]

    # API 不支持服务端日期过滤：限定 --since 时多取一些（上限即保留上限 50），本地过滤后再截 limit。
    max_results = args.limit if not args.since else max(args.limit, MAX_KEEP)
    out("查询 arXiv：%s（最多取 %d 条%s）" % (args.query, max_results,
                                          "，本地按 published ≥ %s 过滤后留 %d 条" % (args.since, args.limit)
                                          if args.since else ""))
    try:
        data = fetch_raw(args.query, max_results, out)
        fetched, skipped = parse_feed(data, out)
        if skipped:
            out("  %d 条残缺或日期非法，跳过" % skipped)
        log.event("fetch_arxiv", input={"查询": args.query, "字节": len(data)})
        log.event("parse_entries", input={"规范化": len(fetched), "跳过": skipped})
    except FetchError as exc:
        log.event("fetch_arxiv", "fail", error=str(exc), input={"查询": args.query})
        out("抓取失败：%s" % exc)
        if previous:
            out("保留 papers.json 原样（%d 条历史数据未动）" % len(previous))
            log.event("keep_previous", input={"论文": len(previous)})
            out("fetched 0 / new 0 / saved %d" % len(previous))
            return 0
        out("没有任何历史数据可保留——以非零码退出。")
        log.event("fetch_all", "fail", error="抓取失败且没有任何历史数据", input={"论文": 0})
        out("fetched 0 / new 0 / saved 0")
        return 1

    if args.since:
        kept = [p for p in fetched if p["published"] >= args.since]
        older = len(fetched) - len(kept)
        fetched = kept[:args.limit]
        out("  本地日期过滤：保留 %d 条，早于 %s 的 %d 条不取"
            % (len(fetched), args.since, older))
    else:
        fetched = fetched[:args.limit]

    out("本次规范化出 %d 条" % len(fetched))
    if not fetched:
        out("查询没有返回可用论文。")
        if previous:
            out("papers.json 原样保留（%d 条），不落盘。" % len(previous))
            log.event("keep_previous", input={"论文": len(previous)})
            out("fetched 0 / new 0 / saved %d" % len(previous))
            return 0
        out("既没抓到论文，也从未有过任何数据——以非零码退出。")
        log.event("fetch_all", "fail", error="查询无结果且没有任何历史数据", input={"论文": 0})
        out("fetched 0 / new 0 / saved 0")
        return 1

    papers, new, updated = merge(fetched, previous, out)
    wrote = write_if_changed(DATA_OUT, render_json(papers))
    log.event("merge", input={"历史": len(previous), "本次": len(fetched),
                              "合计": len(papers), "新增": new, "刷新": updated})
    log.event("write_output", input={"写入": int(wrote)})
    out("合并：历史 %d 条 + 本次 %d 条 → %d 条（新增 %d，刷新 %d）"
        % (len(previous), len(fetched), len(papers), new, updated))
    out("%s %s" % (rel(DATA_OUT), "写入" if wrote else "未变化（与现有 JSON 逐字节相同，不落盘）"))
    out("fetched %d / new %d / saved %d" % (len(fetched), new, len(papers)))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(wrap_main("collect_papers", main))
    except FetchError as exc:
        print("抓取失败：%s" % exc)
        sys.exit(1)
