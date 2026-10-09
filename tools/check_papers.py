#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""机械校验 Step 7 的论文收集：papers.json、渲染脚本 papers.js、页面骨架，
以及一次「坏数据」负向测试（临时文件实跑本校验器，确认非零码报出，测试自清理）。

用法（仓库根运行）：
    python tools/check_papers.py            # 校验 public/data/papers.json
    python tools/check_papers.py --data p.json   # 改校验别处的 JSON（负向测试用）

退出码 0 = 全部通过，1 = 有失败项。

断言什么（与 tools/check_feeds.py 同一口径，只是对象换成论文）：
- public/data/papers.json：结构合法（schema + papers 列表）；每项七个字段齐全且无多余
  （id / title / authors / published / summary / url / source）；id 全局唯一且**不含版本后缀**
  （2401.12345v2 与 2401.12345 是同一篇，必须折叠）；published 是合法 YYYY-MM-DD；
  url 是 https、指向 arxiv.org 的 /abs/ 路径、且能由 id 逐字推出（链接只来自 arXiv）；
  summary 与 title 是纯文本（不含尖括号）；authors 是非空字符串列表；source 恒为 "arXiv"；
  整表按 published 倒序、同日按 id 升序（顺序可复现）。
- public/papers/papers.js：逐字扫描禁用 API（innerHTML / outerHTML / insertAdjacentHTML /
  document.write / eval），命中任何一个即失败（连注释里写都不行——所以本断言的名单只出现在
  这里，不重复写进 papers.js）；要求外链带 rel="noopener noreferrer" 与 target="_blank"、
  数据路径是同域的 ../data/papers.json、href 赋值全脚本只许一处、整份脚本不含任何绝对 URL。
- public/papers/index.html：同域 defer 引入 papers.js、有 <noscript> 回退；
  **骨架里不得出现任何论文标题**——条目只能来自 papers.json，页面不写死数据。

负向测试：把一条「id 带 v2、url 是 http、summary 含 <script>」的坏数据写进系统临时文件，
用子进程真实运行本校验器，断言退出码非零且三类坏点（版本后缀 / https / 尖括号）都被报出；
finally 删除临时文件（自清理，仓库里不留探针）。
"""

import argparse
import json
import re
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from collect_papers import (ABS_PREFIX, PAPER_FIELDS, SCHEMA,   # noqa: E402
                            SOURCE_NAME, sort_papers)
from site_data import rel  # noqa: E402

DATA_PATH = ROOT / "public" / "data" / "papers.json"
PAPERS_JS = ROOT / "public" / "papers" / "papers.js"
PAPERS_PAGE = ROOT / "public" / "papers" / "index.html"

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
VERSION_SUFFIX_RE = re.compile(r"v\d+$", re.I)


def disp(path):
    """仓库内路径显示相对路径；负向测试的临时文件在仓库外，原样显示（site_data.rel 会拒绝）。"""
    try:
        return rel(path)
    except ValueError:
        return str(path)

# 前端渲染外部内容时禁止出现的 API（出现即失败）——名单只写在这一处
BANNED_JS = (
    ("innerHTML", r"innerHTML"),
    ("outerHTML", r"outerHTML"),
    ("insertAdjacentHTML", r"insertAdjacentHTML"),
    ("document.write", r"document\s*\.\s*write"),
    ("eval", r"\beval\s*\("),
)
REQUIRED_JS = (
    ("textContent", r"textContent"),
    ('rel="noopener noreferrer"', r'rel\s*=\s*"noopener noreferrer"'),
    ('target="_blank"', r'target\s*=\s*"_blank"'),
    ("同域数据路径", r"\.\./data/papers\.json"),
)
ABSOLUTE_URL_RE = re.compile(r"https?://", re.I)
HREF_ASSIGN_RE = re.compile(r"\.href\s*=")


def load_json(path, what, errors):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append("缺少 %s：先跑 python scripts/collect_papers.py --query \"<查询词>\"" % disp(path))
    except json.JSONDecodeError as exc:
        errors.append("%s 不是合法 JSON：%s" % (what, exc))
    return None


def validate_doc(doc, errors):
    """对 papers.json 的数据结构逐条断言；返回论文列表（可能为空）。"""
    if doc.get("schema") != SCHEMA:
        errors.append("papers.json 的 schema 应为 %r，实际 %r" % (SCHEMA, doc.get("schema")))
    papers = doc.get("papers")
    if not isinstance(papers, list):
        errors.append("papers.json 缺少 papers 列表")
        return []

    seen_ids = {}
    for i, item in enumerate(papers):
        where = "papers[%d]" % i
        if not isinstance(item, dict):
            errors.append("%s 不是对象" % where)
            continue
        if set(item.keys()) != set(PAPER_FIELDS):
            errors.append("%s 的字段集不是七项：%s" % (where, sorted(item.keys())))
            continue
        pid = item["id"]
        if not isinstance(pid, str) or not pid.strip():
            errors.append("%s 的 id 必须是非空字符串：%r" % (where, pid))
            continue
        if VERSION_SUFFIX_RE.search(pid):
            errors.append("%s（%s）的 id 带版本后缀：去重键必须是剥掉版本号的 arXiv id" % (where, pid))
        if pid in seen_ids:
            errors.append("%s 的 id 与 %s 重复：%r" % (where, seen_ids[pid], pid))
        seen_ids[pid] = where

        for field in ("title", "summary", "source"):
            value = item[field]
            if not isinstance(value, str) or not value.strip():
                errors.append("%s（%s）的 %s 必须是非空字符串：%r" % (where, pid, field, value))
            elif "<" in value or ">" in value:
                errors.append("%s（%s）的 %s 残留尖括号（外部文本必须剥成纯文本）：%r"
                              % (where, pid, field, value[:60]))
        if item.get("source") != SOURCE_NAME:
            errors.append("%s（%s）的 source 应恒为 %r，实际 %r" % (where, pid, SOURCE_NAME, item.get("source")))

        authors = item["authors"]
        if not isinstance(authors, list) or not authors:
            errors.append("%s（%s）的 authors 必须是非空列表：%r" % (where, pid, authors))
        elif not all(isinstance(a, str) and a.strip() for a in authors):
            errors.append("%s（%s）的 authors 含空值或非字符串：%r" % (where, pid, authors[:3]))

        published = item["published"]
        ok_date = isinstance(published, str) and DATE_RE.match(published)
        if ok_date:
            try:
                date.fromisoformat(published)
            except ValueError:
                ok_date = False
        if not ok_date:
            errors.append("%s（%s）的 published 必须是合法 YYYY-MM-DD：%r" % (where, pid, published))

        url = item["url"]
        if not isinstance(url, str) or not url.startswith("https://"):
            errors.append("%s（%s）的 url 必须是 https 绝对地址：%r" % (where, pid, url))
        elif not url.startswith(ABS_PREFIX):
            errors.append("%s（%s）的 url 必须指向 arxiv.org 的 /abs/ 路径：%r" % (where, pid, url))
        elif url != ABS_PREFIX + str(pid):
            errors.append("%s 的 url 无法由 id 逐字推出：%r ≠ %s%s" % (where, url, ABS_PREFIX, pid))

    # 排序：published 倒序、同日按 id 升序（与 collect_papers.sort_papers 相同的判法——可复现）
    expected = [p["id"] for p in sort_papers([p for p in papers if isinstance(p, dict)
                                              and set(p.keys()) == set(PAPER_FIELDS)])]
    got = [p["id"] for p in papers if isinstance(p, dict) and set(p.keys()) == set(PAPER_FIELDS)]
    if got != expected:
        errors.append("papers 顺序必须按 published 倒序、同日按 id 升序（可复现），实际顺序不符")
    return papers


def check_js(errors):
    if not PAPERS_JS.is_file():
        errors.append("缺少 %s" % rel(PAPERS_JS))
        return
    js = PAPERS_JS.read_text(encoding="utf-8")
    hits = 0
    for label, pattern in BANNED_JS:
        for m in re.finditer(pattern, js):
            hits += 1
            line = js[:m.start()].count("\n") + 1
            errors.append("%s 第 %d 行出现禁用 API %s：外部内容只能用 DOM API + textContent 渲染"
                          % (rel(PAPERS_JS), line, label))
    for label, pattern in REQUIRED_JS:
        if not re.search(pattern, js):
            errors.append("%s 里找不到必须的写法：%s" % (rel(PAPERS_JS), label))
    href_assigns = len(HREF_ASSIGN_RE.findall(js))
    if href_assigns != 1:
        errors.append("%s 里的 href 赋值有 %d 处：所有链接必须只经一处出口（外链在该处统一带 rel/target）"
                      % (rel(PAPERS_JS), href_assigns))
    if ABSOLUTE_URL_RE.search(js):
        errors.append("%s 里出现了绝对 URL（页面只许请求同域数据，论文地址只能来自 papers.json）"
                      % rel(PAPERS_JS))
    return js, hits


def check_page(papers, errors):
    if not PAPERS_PAGE.is_file():
        errors.append("缺少 %s" % rel(PAPERS_PAGE))
        return
    page = PAPERS_PAGE.read_text(encoding="utf-8")
    for needle, why in (('<script src="papers.js" defer></script>', "同域 defer 引入 papers.js"),
                        ("<noscript>", "<noscript> 回退（禁用 JS 时不白屏）")):
        if needle not in page:
            errors.append("public/papers/index.html 缺少%s：%s" % (why, needle))
    stripped = re.sub(r"<!--.*?-->", "", page, flags=re.S)
    written = [p["id"] for p in papers if p.get("id") and p["id"] in stripped]
    if written:
        errors.append("public/papers/index.html 里手写了论文（%s）：骨架只放容器，条目要从 papers.json 生成"
                      % "、".join(written[:3]))


def negative_test():
    """坏数据实跑负向测试：临时 json 里塞一条三重违规的记录，子进程跑本校验器，
    要求非零退出且三类坏点都被报出；finally 删除临时文件（自清理）。"""
    bad = {
        "schema": SCHEMA,
        "papers": [{
            "id": "2401.12345v2",                       # 违规 1：id 带版本后缀
            "title": "Bad Sample Paper",
            "authors": ["Some Author"],
            "published": "2026-10-01",
            "summary": "<script>alert(1)</script>外部内容只当文本。",   # 违规 2：残留尖括号
            "url": "http://arxiv.org/abs/2401.12345v2",  # 违规 3：不是 https、且推不出自 id
            "source": SOURCE_NAME,
        }],
    }
    fd, tmp = tempfile.mkstemp(prefix="check_papers_negative_", suffix=".json")
    try:
        with open(fd, "w", encoding="utf-8") as f:
            json.dump(bad, f, ensure_ascii=False)
        proc = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--data", tmp],
            capture_output=True, text=True, timeout=120)
        out = proc.stdout + proc.stderr
        problems = []
        if proc.returncode == 0:
            problems.append("坏数据竟然通过了校验（退出码 0）")
        for needle, why in (("版本后缀", "id 带 v2"), ("https", "url 是 http"), ("尖括号", "summary 含 <script>")):
            if needle not in out:
                problems.append("输出没有报出「%s」（%s）" % (why, needle))
        if problems:
            return False, "负向测试失败：" + "；".join(problems) + "\n---- 子进程输出 ----\n" + out
        reported = [line.strip() for line in out.splitlines() if line.strip().startswith("✗")]
        return True, ("负向测试通过：坏数据（id 带 v2、url 是 http、summary 含 <script>）被子进程"
                      "以退出码 %d 报出 %d 项；临时文件已删除，仓库里不留探针"
                      % (proc.returncode, len(reported)))
    finally:
        try:
            Path(tmp).unlink(missing_ok=True)
        except OSError:
            pass


def main():
    parser = argparse.ArgumentParser(description="校验 public/data/papers.json 与论文页渲染链路")
    parser.add_argument("--data", help="改校验指定 JSON（负向测试内部用，平时不传）")
    args = parser.parse_args()

    errors = []
    notes = []

    path = Path(args.data) if args.data else DATA_PATH
    doc = load_json(path, disp(path), errors)
    if doc is not None:
        papers = validate_doc(doc, errors)
        if not errors:
            notes.append("%s：%d 条论文，七字段齐全、id 唯一无版本后缀、url 全部由 id 推出的 "
                         "https arXiv abs 地址、published 合法且倒序可复现、纯文本零尖括号"
                         % (disp(path), len(papers)))
    if args.data:
        # 负向测试的子进程模式：只校验数据，不查前端，也不再做负向测试（否则无限递归）
        if errors:
            print("失败 %d 项：" % len(errors))
            for msg in errors:
                print("  ✗ %s" % msg)
            return 1
        print("通过：%s 未发现问题" % disp(path))
        return 0

    js_and_hits = check_js(errors)
    if js_and_hits and js_and_hits[1] == 0:
        notes.append("%s：零禁用 API、href 只有一个出口（外链统一带 rel/target）、"
                     "整份脚本不含任何绝对 URL" % rel(PAPERS_JS))
    check_page(doc.get("papers", []) if isinstance(doc, dict) else [], errors)
    if not errors:
        notes.append("public/papers/index.html：同域 defer 引入 papers.js、有 <noscript> 回退、"
                     "骨架里没有手写任何论文条目")

    passed, msg = negative_test()
    if passed:
        notes.append(msg)
    else:
        errors.append(msg)

    for n in notes:
        print("  提示 %s" % n)
    if errors:
        print("\n失败 %d 项：" % len(errors))
        for msg in errors:
            print("  ✗ %s" % msg)
        return 1
    print("\n全部通过：papers.json 每项七个字段齐全、id 唯一且已剥版本号、url 是可由 id 推出的 "
          "https arXiv 地址、published 为合法 YYYY-MM-DD 且按时间倒序可复现、摘要与标题纯文本零尖括号、"
          "authors 非空、source 恒为 arXiv；papers.js 零禁用 API、外链单出口带 rel/target、无绝对 URL；"
          "页面骨架只有容器与回退说明、不写死条目；坏数据负向测试以非零码如实报出且已自清理。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
