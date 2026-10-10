#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""check_status.py —— 校验状态面板与运行日志（Step 10）。

用法（仓库根运行）：python tools/check_status.py
退出码 0 = 全部通过，1 = 有失败项。

六类断言：
1. status.json 结构合法（schema / site / content / checks 的字段与类型）；
2. **对账（核心断言）**：status.json 里每个计数与从内容源重算的结果一致——重算
   直接复用 scripts/build_status.py 的 recompute() 与各 check_* 函数，校验器与
   构建器永远用同一套规则，不会各算各的；「最近更新」（内容源 frontmatter 日期的
   最大值，内容派生、跨提交稳定）同样重算比对。**不校验也不存在「最近构建」**——
   构建时刻的归宿是每次运行的 run_id 日志，一个文件写不下包含它自己的那次提交的时刻
   （取 HEAD 提交时间是自指的：干净 clone 上对账必失败、提交后重建必脏）；
3. 页面-数据交叉核对：解析 public/status/index.html，页面登记表上的每个数字、
   时间戳与 ✓/✗ 都必须与 status.json 一致；
4. 六个构建/抓取脚本（build_blog / build_feed / build_wiki / build_status /
   fetch_feeds / collect_papers）都 import 了 runlog（grep 级断言）；
5. 日志行验证：实跑一次 build_wiki.py，logs/build.log 里本次 run_id 的每行都是
   可 json.loads 的 JSONL，且七要素字段齐全（time 为带 +08:00 的 ISO 8601、
   run_id / task / input / action / result 齐全，result 为 fail 时必有 error）；
6. 脱敏单元测试：给 logger 喂含 "api_token": "sk-xxx" 的字典，输出里必须是 "***"；
   外加一次负向测试：临时把 status.json 改坏一个计数，确认本校验器以非零码报出，
   测完还原（负向测试以子进程方式调本校验器的 --negative-probe 模式——该模式只做
   第 1–3 类断言、不再触发负向测试，避免递归）。
"""

import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_status            # noqa: E402  复用同一份重算与对账实现
import runlog                  # noqa: E402

STATUS_JSON = build_status.STATUS_JSON
STATUS_PAGE = build_status.STATUS_PAGE
LOG_PATH = runlog.LOG_PATH

# 结构断言的字段清单（site 没有「最近构建」：构建时刻的归宿是 run_id 日志，不是文件）
SITE_FIELDS = {"pages": int, "last_update": str}
CONTENT_FIELDS = {"posts": int, "wiki_entries": int, "papers": int,
                  "rss_sources": int, "rss_items": int}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ROW_RE = re.compile(r'<div class="reg-row">\s*<dt>(.*?)</dt>\s*<dd>(.*?)</dd>\s*</div>', re.S)
NUM_RE = re.compile(r'<span class="num">(.*?)</span>', re.S)
MARK_RE = re.compile(r'<span class="mark">(.*?)</span>')

# 六个必须走 runlog 的构建/抓取脚本
RUNLOG_SCRIPTS = ("build_blog.py", "build_feed.py", "build_wiki.py", "build_status.py",
                  "fetch_feeds.py", "collect_papers.py")

failures = []


def fail(msg):
    failures.append(msg)


# ---------------------------------------------------------------- 1. 结构

def check_structure(doc):
    if not isinstance(doc, dict):
        fail("status.json 不是 JSON 对象")
        return False
    if doc.get("schema") != 1:
        fail("status.json 的 schema 应为 1，实际 %r" % doc.get("schema"))
    site = doc.get("site")
    if not isinstance(site, dict) or set(site.keys()) != set(SITE_FIELDS):
        fail("status.json 的 site 应含且仅含 %s" % " / ".join(SITE_FIELDS))
    else:
        for key, kind in SITE_FIELDS.items():
            if not isinstance(site[key], kind):
                fail("status.json 的 site.%s 应为 %s，实际 %r" % (key, kind.__name__, site[key]))
    content = doc.get("content")
    if not isinstance(content, dict) or set(content.keys()) != set(CONTENT_FIELDS):
        fail("status.json 的 content 应含且仅含 %s" % " / ".join(CONTENT_FIELDS))
        return False
    for key, kind in CONTENT_FIELDS.items():
        if not isinstance(content[key], kind) or isinstance(content[key], bool):
            fail("status.json 的 content.%s 应为 %s，实际 %r" % (key, kind.__name__, content[key]))
    checks = doc.get("checks")
    if not isinstance(checks, list) or not checks:
        fail("status.json 的 checks 应为非空数组")
        return False
    for check in checks:
        if not (isinstance(check, dict) and set(check.keys()) == {"name", "ok", "detail"}
                and isinstance(check["name"], str) and isinstance(check["ok"], bool)
                and isinstance(check["detail"], str)):
            fail("status.json 的 checks 每项应为 {name: str, ok: bool, detail: str}，实际 %r"
                 % check)
            return False
    return True


# ---------------------------------------------------------------- 2. 对账（核心）

def check_counts(doc):
    """status.json 的每个计数 / 时间字段与从内容源重算的结果对账。"""
    counts, papers_doc, papers_error, rss_doc, rss_error = build_status.recompute()
    pairs = [("site.pages", doc["site"]["pages"], counts["pages"])] if isinstance(doc.get("site"), dict) else []
    if isinstance(doc.get("content"), dict):
        pairs += [("content.%s" % k, doc["content"][k], counts[k]) for k in CONTENT_FIELDS]
    for what, stored, recomputed in pairs:
        if stored != recomputed:
            fail("对账失败：status.json 的 %s = %r，与内容源重算的 %r 不一致"
                 % (what, stored, recomputed))

    if isinstance(doc.get("site"), dict):
        # 「最近更新」内容派生、跨提交稳定，可对账；「最近构建」不存在也不校验（见 docstring）。
        for key, recomputed in (("last_update", build_status.content_last_update()),):
            stored = doc["site"].get(key)
            if stored != recomputed:
                fail("对账失败：status.json 的 site.%s = %r，与重算的 %r 不一致"
                     % (key, stored, recomputed))
    # 时间字段的格式断言在 check_time_format

    # 四项对账检查重跑一遍，与 status.json 记录的 ✓/✗ 对照
    recomputed_checks = [
        ("论文数据", build_status.check_papers(papers_doc, papers_error, counts["papers"])),
        ("订阅聚合", build_status.check_rss(rss_doc, rss_error, counts["rss_items"],
                                            counts["rss_sources"])),
        ("订阅源 feed", build_status.check_feed(counts["posts"])),
        ("Wiki 生成页", build_status.check_wiki_pages()),
    ]
    stored_checks = {c["name"]: c for c in doc.get("checks", []) if isinstance(c, dict)}
    for name, (ok, detail) in recomputed_checks:
        stored = stored_checks.get(name)
        if stored is None:
            fail("status.json 缺少对账项「%s」" % name)
        elif stored["ok"] != ok:
            fail("对账项「%s」的 ok = %s，与重算的 %s 不一致（重算详情：%s）"
                 % (name, stored["ok"], ok, detail))
        elif stored["detail"] != detail:
            fail("对账项「%s」的 detail 与重算不一致：status.json 写 %r，重算 %r"
                 % (name, stored["detail"], detail))


def stored_ok(doc):
    return isinstance(doc.get("site"), dict)


def check_time_format(doc):
    if not stored_ok(doc):
        return
    last_update = doc["site"]["last_update"]
    if last_update != "未知" and not DATE_RE.match(last_update):
        fail("status.json 的 site.last_update 不是 YYYY-MM-DD：%r" % last_update)


# ---------------------------------------------------------------- 3. 页面交叉核对

def page_rows(html):
    return {unescape(m.group(1)): m.group(2) for m in ROW_RE.finditer(html)}


def row_number(rows, label):
    dd = rows.get(label)
    if dd is None:
        fail("public/status/index.html 缺少「%s」登记行" % label)
        return None
    m = NUM_RE.search(dd)
    if not m:
        fail("public/status/index.html 的「%s」行没有等宽数字" % label)
        return None
    return unescape(m.group(1))


def check_page(doc):
    if not STATUS_PAGE.is_file():
        fail("public/status/index.html 不存在（先跑 python scripts/build_status.py）")
        return
    html = STATUS_PAGE.read_text(encoding="utf-8")
    if build_status.MARKER not in html:
        fail("public/status/index.html 缺少生成标记")
    rows = page_rows(html)

    expect = [("页面总数", str(doc["site"]["pages"])),
              ("最近更新", doc["site"]["last_update"])]
    expect += [("文章", str(doc["content"]["posts"])),
               ("Wiki 词条", str(doc["content"]["wiki_entries"])),
               ("论文", str(doc["content"]["papers"])),
               ("RSS 订阅源", str(doc["content"]["rss_sources"])),
               ("RSS 聚合条目", str(doc["content"]["rss_items"]))]
    for label, want in expect:
        got = row_number(rows, label)
        if got is not None and got != want:
            fail("页面-数据不一致：「%s」页面写 %r，status.json 是 %r" % (label, got, want))

    for check in doc.get("checks", []):
        dd = rows.get(check["name"])
        if dd is None:
            fail("public/status/index.html 缺少对账行「%s」" % check["name"])
            continue
        m = MARK_RE.search(dd)
        if not m:
            fail("public/status/index.html 的「%s」行没有 ✓/✗ 标记" % check["name"])
            continue
        mark = m.group(1)
        if (mark == "✓") != check["ok"]:
            fail("页面-数据不一致：「%s」页面标 %s，status.json 的 ok = %s"
                 % (check["name"], mark, check["ok"]))
        detail = unescape(MARK_RE.sub("", dd, count=1)).strip()
        if detail != check["detail"]:
            fail("页面-数据不一致：「%s」页面详情 %r，status.json 是 %r"
                 % (check["name"], detail, check["detail"]))


# ---------------------------------------------------------------- 4. 六脚本都走 runlog

def check_runlog_imports():
    for name in RUNLOG_SCRIPTS:
        path = ROOT / "scripts" / name
        if not path.is_file():
            fail("scripts/%s 不存在" % name)
            continue
        if "from runlog import" not in path.read_text(encoding="utf-8"):
            fail("scripts/%s 没有 import runlog（Step 10 起六个构建/抓取脚本必须统一走它）" % name)


# ---------------------------------------------------------------- 5. 日志行验证

def check_log_lines():
    if not (ROOT / "scripts" / "build_wiki.py").is_file():
        fail("scripts/build_wiki.py 不存在，日志行验证无从跑起")
        return
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_wiki.py")],
                          cwd=str(ROOT), capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        fail("日志行验证：实跑 build_wiki.py 失败（退出码 %d）" % proc.returncode)
        return
    if not LOG_PATH.is_file():
        fail("logs/build.log 不存在：build_wiki.py 应通过 runlog 追加日志")
        return
    lines = [l for l in LOG_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not lines:
        fail("logs/build.log 是空的")
        return
    try:
        last = json.loads(lines[-1])
        run_id = last["run_id"]
    except (json.JSONDecodeError, KeyError) as exc:
        fail("logs/build.log 最后一行不是含 run_id 的 JSON：%s" % exc)
        return
    mine = [l for l in lines if ('"run_id": "%s"' % run_id) in l]
    if len(mine) < 2:
        fail("logs/build.log 里 run_id %s 只有 %d 行，至少应有读取输入与落盘两条" % (run_id, len(mine)))
    for line in mine:
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            fail("日志行不是合法 JSON：%s（%s）" % (line[:80], exc))
            continue
        for key in ("time", "run_id", "task", "input", "action", "result"):
            if key not in record or record[key] in ("", None):
                fail("日志行缺七要素字段 %s：%s" % (key, line[:80]))
        if record.get("task") != "build_wiki":
            fail("日志行的 task 应为 build_wiki，实际 %r" % record.get("task"))
        if record.get("result") not in ("ok", "fail"):
            fail("日志行的 result 应为 ok/fail，实际 %r" % record.get("result"))
        if record.get("result") == "fail" and not record.get("error"):
            fail("result 为 fail 的日志行必须有 error")
        if "time" in record:
            if not record["time"].endswith("+08:00"):
                fail("日志 time 应为带 +08:00 的 ISO 8601：%r" % record["time"])
            else:
                try:
                    datetime.fromisoformat(record["time"])
                except ValueError:
                    fail("日志 time 不是合法 ISO 8601：%r" % record["time"])
    print("  日志行验证：run_id %s 共 %d 行，七要素齐全、全部可解析" % (run_id, len(mine)))


# ---------------------------------------------------------------- 6. 脱敏单元测试

def check_sanitization():
    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        probe = Path(tmp) / "probe.log"
        rl = runlog.RunLog("unit-test", path=probe)
        rl.event("probe", input={"api_token": "sk-xxx", "password": "hunter2",
                                 "webhook": "https://hooks.example.com/TOKEN123",
                                 "note": "联系 bob@example.com",
                                 "普通字段": "原样保留"})
        line = probe.read_text(encoding="utf-8").strip()
        record = json.loads(line)
        if record["input"].get("api_token") != "***":
            problems.append("api_token 未遮蔽：%r" % record["input"].get("api_token"))
        if record["input"].get("password") != "***":
            problems.append("password 未遮蔽")
        if "hooks.example.com" in line:
            problems.append("Webhook 地址写进了日志")
        if "bob@example.com" in line:
            problems.append("邮箱地址写进了日志")
        if record["input"].get("普通字段") != "原样保留":
            problems.append("普通字段被误伤")
        if "sk-xxx" in line or "hunter2" in line:
            problems.append("敏感原文出现在日志行里")
    for p in problems:
        fail("脱敏单元测试：%s" % p)
    if not problems:
        print("  脱敏单元测试：api_token/password → \"***\"，邮箱与 Webhook 已遮蔽，普通字段不受影响")


# ---------------------------------------------------------------- 负向测试

def negative_probe_only():
    """--negative-probe 模式：只做第 1–3 类断言，给负向测试当探针（不递归）。"""
    return "--negative-probe" in sys.argv[1:]


def check_negative():
    """把 status.json 的一个计数改坏 → 本校验器（探针模式）必须以非零码报出 → 还原。"""
    original = STATUS_JSON.read_bytes()
    try:
        doc = json.loads(original.decode("utf-8"))
        doc["content"]["posts"] = doc["content"]["posts"] + 100
        STATUS_JSON.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()),
                               "--negative-probe"],
                              cwd=str(ROOT), capture_output=True, text=True, timeout=60)
        output = proc.stdout + proc.stderr
        if proc.returncode == 0:
            fail("负向测试：改坏 content.posts 后校验器竟以 0 退出，对账断言失效")
        elif "不一致" not in output:
            fail("负向测试：校验器报了非零码，但输出里没有指出计数不一致（输出：%s）"
                 % output.strip()[:200])
        else:
            print("  负向测试：改坏 content.posts → 校验器以非零码报出计数不一致（符合预期）")
    finally:
        STATUS_JSON.write_bytes(original)
    if STATUS_JSON.read_bytes() != original:
        fail("负向测试：status.json 没有还原成原样")


# ---------------------------------------------------------------- 主流程

def main():
    if not STATUS_JSON.is_file():
        fail("public/data/status.json 不存在（先跑 python scripts/build_status.py）")
        return report()

    try:
        doc = json.loads(STATUS_JSON.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail("status.json 解析失败：%s" % exc)
        return report()

    structure_ok = check_structure(doc)
    if structure_ok:
        check_counts(doc)
        check_time_format(doc)
        check_page(doc)
    if negative_probe_only():
        return report()

    check_runlog_imports()
    check_log_lines()
    check_sanitization()
    check_negative()
    return report()


def report():
    if failures:
        print("失败 %d 项：" % len(failures))
        for f in failures:
            print("  ✗ %s" % f)
        return 1
    print("全部通过：status.json 结构合法、六个计数与时间字段与内容源重算一致（对账）、"
          "四项对账检查与重算一致、状态页与 status.json 逐项一致、"
          "六个构建/抓取脚本都 import runlog、日志行七要素齐全、脱敏与负向测试通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
