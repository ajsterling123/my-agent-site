#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_status.py —— 生成站点状态面板（Step 10：状态登记 + 可观测性）：

  public/data/status.json     机读的状态数据（计数 + 对账结果）
  public/status/index.html    状态页（菜单「状态」的落点，零 JavaScript）

用法（仓库根运行）：python scripts/build_status.py

页面骨架外科改写复用 scripts/page_build.py（与 build_blog.py / build_wiki.py 同一份
实现）：把 public/index.html 当骨架，只改 <title>、description、样式前缀、标题区、
导航块（aria-current 落「状态」）、<main>、页脚说明句，其余逐字节保留；生成页带
生成标记，由 tools/check_site.py 校验。视觉上复用首页「身份登记」的 .register
登记行语法做「状态登记表」，分三段：站点（页面数/最近构建/最近更新）、内容
（文章/Wiki/论文/RSS）、数据健康（对账的 ✓/✗ 列表）——零新色、零卡片、零图标、
不用红（对不上账是事实陈述，不是「活动」）。

计数从内容源重算，不和数据文件对不上账：
  页面数        public/**/*.html 的个数（含状态页自身——它也是一页）；
  文章数        content/posts/*.md 的个数；
  Wiki 词条数   content/wiki/*.md 去掉规则文件 README.md 与索引 index.md；
  论文数        public/data/papers.json 的 papers 条数；
  RSS 源数      config/feeds.json 的 sources 个数；
  RSS 聚合条目数 public/data/rss-items.json 各源 items 的总条数。

检查 = 对账，每项一行 ✓/✗（结果同时写进 status.json 的 checks，页面如实展示，
构建不因对不上账而失败——把差异亮出来比假装健康更诚实）：
  论文数据      papers.json 可解析 + 每条七字段齐全 + url 由 id 推出；
  订阅聚合      rss-items.json 可解析 + 分组数与订阅源数一致 + 条目字段齐全；
  订阅源 feed   feed.xml 可解析 + item 数与文章数一致；
  Wiki 生成页   每个 content/wiki/*.md（除 README.md）都有带生成标记的词条页。

时间字段（不写「当前时间」，否则每次构建都有 diff、破坏幂等验收）：
  最近构建  git HEAD 的提交时间（git log -1 --format=%cI；无 git 环境记「未知」）；
  最近更新  内容源 frontmatter 日期（posts 的 date 与 wiki 的 updated）的最大值。

幂等：同一份仓库状态重复构建字节一致（时间字段只取自 git 与内容源，生成物里
没有「生成时间」这类每次都变的字段；数字与文本全部由重算得出）。

运行日志：各阶段（重算 / 对账 / 落盘）走 scripts/runlog.py 写 JSONL 事件。
"""

import html
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_data import (CONTENT, PUBLIC, ROOT, SKELETON, WIKI_CONTENT, WIKI_RULES,
                       BuildError, fail, rel, write_if_changed)
from page_build import folio_head, indent, render_page
from runlog import wrap_main

# 字段与标记的规则只写一份：直接复用各数据脚本导出的常量。
from build_wiki import MARKER as WIKI_PAGE_MARKER        # noqa: E402
from collect_papers import PAPER_FIELDS, ABS_PREFIX      # noqa: E402
from fetch_feeds import ITEM_FIELDS as RSS_ITEM_FIELDS   # noqa: E402

MARKER = ("<!-- 由 scripts/build_status.py 生成：数据在构建期从内容源重算，"
          "改站点请改内容源后重新构建 -->")

STATUS_JSON = PUBLIC / "data" / "status.json"
STATUS_PAGE = PUBLIC / "status" / "index.html"
FEEDS_CONFIG = ROOT / "config" / "feeds.json"
PAPERS_JSON = PUBLIC / "data" / "papers.json"
RSS_ITEMS_JSON = PUBLIC / "data" / "rss-items.json"
FEED_XML = PUBLIC / "feed.xml"

STATUS_TITLE = "状态 · 张易孝实验档案"
STATUS_DESCRIPTION = ("张易孝实验档案的状态页：页面、内容与数据文件的计数从内容源重算，"
                      "对账结果在此登记。")
STATUS_FOOT = "本页是课程实验档案的「状态」页，数据在构建期从内容源重算，页面零 JavaScript。"

DATE_LINE_RE = re.compile(r"^(date|updated):\s*(\d{4}-\d{2}-\d{2})\s*$", re.M)
UNKNOWN = "未知"


# ---------------------------------------------------------------- 时间字段

def git_head_time():
    """最近构建 = git HEAD 的提交时间；没有 git 环境就如实记「未知」。"""
    try:
        proc = subprocess.run(["git", "log", "-1", "--format=%cI"], cwd=str(ROOT),
                              capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return UNKNOWN
    stamp = (proc.stdout or "").strip()
    if proc.returncode != 0 or not stamp:
        return UNKNOWN
    return stamp


def content_last_update():
    """最近更新 = 内容源 frontmatter 日期的最大值（posts 的 date、wiki 的 updated）。"""
    latest = None
    for folder in (CONTENT, WIKI_CONTENT):
        for path in sorted(folder.glob("*.md")):
            try:
                text = path.read_text(encoding="utf-8-sig")
            except OSError:
                continue
            for m in DATE_LINE_RE.finditer(text):
                if latest is None or m.group(2) > latest:
                    latest = m.group(2)
    return latest or UNKNOWN


# ---------------------------------------------------------------- 重算

def load_json(path):
    """读一个 JSON 数据文件：返回 (doc, error)；读不到或解析不了时 doc 为 None。"""
    if not path.is_file():
        return None, "%s 不存在" % rel(path)
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, json.JSONDecodeError) as exc:
        return None, "%s 解析失败：%s" % (rel(path), exc)


def recompute():
    """从内容源重算全部计数。返回 (counts, papers_doc, papers_error, rss_doc, rss_error)。"""
    pages = len(list(PUBLIC.rglob("*.html")))
    posts = len(list(CONTENT.glob("*.md")))
    wiki = len([p for p in WIKI_CONTENT.glob("*.md")
                if p.name != WIKI_RULES and p.stem != "index"])

    rss_sources = 0
    if FEEDS_CONFIG.is_file():
        try:
            cfg = json.loads(FEEDS_CONFIG.read_text(encoding="utf-8"))
            rss_sources = len(cfg.get("sources", [])) if isinstance(cfg, dict) else 0
        except (OSError, json.JSONDecodeError):
            rss_sources = 0

    papers_doc, papers_error = load_json(PAPERS_JSON)
    papers = len(papers_doc.get("papers", [])) \
        if isinstance(papers_doc, dict) and isinstance(papers_doc.get("papers"), list) else 0

    rss_doc, rss_error = load_json(RSS_ITEMS_JSON)
    rss_items = sum(len(g.get("items", [])) for g in rss_doc.get("sources", [])) \
        if isinstance(rss_doc, dict) and isinstance(rss_doc.get("sources"), list) else 0

    counts = {
        "pages": pages,
        "posts": posts,
        "wiki_entries": wiki,
        "papers": papers,
        "rss_sources": rss_sources,
        "rss_items": rss_items,
    }
    return counts, papers_doc, papers_error, rss_doc, rss_error


# ---------------------------------------------------------------- 对账

def check_papers(doc, error, count):
    """论文数据对账：可解析 + 每条七字段齐全 + url 由 id 推出。"""
    if error:
        return False, error
    papers = doc.get("papers")
    if not isinstance(papers, list):
        return False, "papers.json 里没有 papers 数组"
    malformed = [str(p.get("id", "?")) for p in papers
                 if not (isinstance(p, dict) and set(p.keys()) == set(PAPER_FIELDS))]
    if malformed:
        return False, "%d 条字段不齐（%s）" % (len(malformed), "、".join(malformed[:3]))
    bad_url = [str(p.get("id", "?")) for p in papers
               if not isinstance(p.get("url"), str)
               or p["url"] != ABS_PREFIX + str(p.get("id"))]
    if bad_url:
        return False, "url 不是由 id 推出的 %s<id>（%s）" % (ABS_PREFIX, "、".join(bad_url[:3]))
    if len(papers) != count:
        return False, "实际 %d 条与登记的 %d 条不一致" % (len(papers), count)
    return True, "可解析，%d 条，七字段与 arXiv 链接齐全" % count


def check_rss(doc, error, count, sources):
    """订阅聚合对账：可解析 + 分组数与订阅源数一致 + 条目七字段齐全。"""
    if error:
        return False, error
    groups = doc.get("sources")
    if not isinstance(groups, list):
        return False, "rss-items.json 里没有 sources 数组"
    if len(groups) != sources:
        return False, "分组 %d 个与 config 的订阅源 %d 个不一致" % (len(groups), sources)
    total = 0
    malformed = 0
    for group in groups:
        for item in group.get("items", []):
            total += 1
            if not (isinstance(item, dict) and set(item.keys()) == set(RSS_ITEM_FIELDS)):
                malformed += 1
    if total != count:
        return False, "实际 %d 条与登记的 %d 条不一致" % (total, count)
    if malformed:
        return False, "%d 条字段不齐" % malformed
    return True, "可解析，%d 源 %d 条，字段齐全" % (len(groups), total)


def check_feed(posts_count):
    """订阅源对账：feed.xml 可解析 + item 数与文章数一致（feed 与博客同源）。"""
    if not FEED_XML.is_file():
        return False, "public/feed.xml 不存在"
    try:
        root = ET.parse(str(FEED_XML)).getroot()
    except (ET.ParseError, OSError) as exc:
        return False, "feed.xml 解析失败：%s" % exc
    items = root.findall("./channel/item")
    if len(items) != posts_count:
        return False, "feed 有 %d 个 item，与文章数 %d 不一致" % (len(items), posts_count)
    return True, "RSS 2.0 可解析，%d 个 item 与文章数一致" % len(items)


def check_wiki_pages():
    """Wiki 生成页对账：每个词条（含 index）都有带生成标记的 public/wiki/<slug>.html。"""
    missing, unmarked = [], []
    total = 0
    for path in sorted(WIKI_CONTENT.glob("*.md")):
        if path.name == WIKI_RULES:
            continue
        total += 1
        page = PUBLIC / "wiki" / ("%s.html" % path.stem)
        if not page.is_file():
            missing.append("%s.html" % path.stem)
            continue
        try:
            marked = WIKI_PAGE_MARKER in page.read_text(encoding="utf-8")
        except OSError:
            marked = False
        if not marked:
            unmarked.append("%s.html" % path.stem)
    if missing:
        return False, "缺少生成页：%s" % "、".join(missing)
    if unmarked:
        return False, "缺生成标记：%s" % "、".join(unmarked)
    return True, "%d 个词条（含索引）的生成页齐全且带标记" % total


# ---------------------------------------------------------------- 页面组装

def num(value):
    """机读数据（计数、时间戳）用等宽档：Consolas + tabular-nums。"""
    return '<span class="num">%s</span>' % html.escape(str(value), quote=False)


def reg_row(label, value_html):
    return ['<div class="reg-row">',
            '  <dt>%s</dt>' % html.escape(label, quote=False),
            '  <dd>%s</dd>' % value_html,
            '</div>']


def check_row(check):
    """一行对账结果：✓/✗ 是普通文字字符，沿用正文墨蓝——不上红（差异是事实，不是活动）。"""
    mark = "✓" if check["ok"] else "✗"
    return reg_row(check["name"], '<span class="mark">%s</span> %s'
                   % (mark, html.escape(check["detail"], quote=False)))


def status_main(doc):
    site, content, checks = doc["site"], doc["content"], doc["checks"]
    lines = ['<p class="intro">本页由构建脚本在每次构建时从内容源重算并登记：'
             '页面、内容与数据文件是否对得上账，一眼可查。✓ 表示账目相符，'
             '✗ 表示有差异，差异详情照实写出。</p>']

    lines.append('<section class="sec" aria-labelledby="t-status-site">')
    lines.append('  <h2 id="t-status-site">站点登记</h2>')
    lines.append('  <dl class="register">')
    lines += indent(reg_row("页面总数", "%s 页" % num(site["pages"])), 4)
    lines += indent(reg_row("最近构建", num(site["last_build"])), 4)
    lines += indent(reg_row("最近更新", num(site["last_update"])), 4)
    lines.append('  </dl>')
    lines.append('</section>')

    lines.append('<section class="sec" aria-labelledby="t-status-content">')
    lines.append('  <h2 id="t-status-content">内容登记</h2>')
    lines.append('  <dl class="register">')
    lines += indent(reg_row("文章", "%s 篇" % num(content["posts"])), 4)
    lines += indent(reg_row("Wiki 词条", "%s 篇" % num(content["wiki_entries"])), 4)
    lines += indent(reg_row("论文", "%s 条" % num(content["papers"])), 4)
    lines += indent(reg_row("RSS 订阅源", "%s 个" % num(content["rss_sources"])), 4)
    lines += indent(reg_row("RSS 聚合条目", "%s 条" % num(content["rss_items"])), 4)
    lines.append('  </dl>')
    lines.append('</section>')

    lines.append('<section class="sec" aria-labelledby="t-status-health">')
    lines.append('  <h2 id="t-status-health">数据健康</h2>')
    lines.append('  <dl class="register">')
    for check in checks:
        lines += indent(check_row(check), 4)
    lines.append('  </dl>')
    lines.append('</section>')

    return "\n".join(indent(lines, 6))


def render_status_page(skel, doc):
    return render_page(skel, STATUS_TITLE, STATUS_DESCRIPTION, "../",
                       folio_head("状态"), status_main(doc), STATUS_FOOT,
                       "../status/index.html", MARKER)


# ---------------------------------------------------------------- 主流程

def main(log, argv=None):
    if not SKELETON.is_file():
        fail("找不到骨架页面 public/index.html")
    skel = SKELETON.read_text(encoding="utf-8")

    counts, papers_doc, papers_error, rss_doc, rss_error = recompute()
    log.event("read_input", input={**counts, "骨架": rel(SKELETON)})

    checks = [
        {"name": "论文数据", "ok": None, "detail": ""},
        {"name": "订阅聚合", "ok": None, "detail": ""},
        {"name": "订阅源 feed", "ok": None, "detail": ""},
        {"name": "Wiki 生成页", "ok": None, "detail": ""},
    ]
    checks[0]["ok"], checks[0]["detail"] = check_papers(papers_doc, papers_error, counts["papers"])
    checks[1]["ok"], checks[1]["detail"] = check_rss(rss_doc, rss_error, counts["rss_items"],
                                                     counts["rss_sources"])
    checks[2]["ok"], checks[2]["detail"] = check_feed(counts["posts"])
    checks[3]["ok"], checks[3]["detail"] = check_wiki_pages()
    for check in checks:
        log.event("reconcile", result="ok" if check["ok"] else "fail",
                  input={"检查": check["name"], "详情": check["detail"]})

    doc = {
        "schema": 1,
        "site": {"pages": counts["pages"],
                 "last_build": git_head_time(),
                 "last_update": content_last_update()},
        "content": {k: counts[k] for k in ("posts", "wiki_entries", "papers",
                                           "rss_sources", "rss_items")},
        "checks": checks,
    }

    page = render_status_page(skel, doc)
    json_text = json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
    wrote_json = write_if_changed(STATUS_JSON, json_text)
    wrote_page = write_if_changed(STATUS_PAGE, page)
    log.event("write_outputs", input={"status.json 写入": int(wrote_json),
                                      "status/index.html 写入": int(wrote_page)})

    passed = sum(1 for c in checks if c["ok"])
    print("状态面板构建完成：%d 项对账，%d 项相符" % (len(checks), passed))
    for check in checks:
        print("  %s %s：%s" % ("✓" if check["ok"] else "✗", check["name"], check["detail"]))
    print("  页面 %d 页 · 文章 %d 篇 · Wiki %d 篇 · 论文 %d 条 · RSS %d 源 %d 条"
          % (doc["site"]["pages"], doc["content"]["posts"], doc["content"]["wiki_entries"],
             doc["content"]["papers"], doc["content"]["rss_sources"], doc["content"]["rss_items"]))
    print("  最近构建 %s（git HEAD 提交时间）· 最近更新 %s（内容源 frontmatter 最大值）"
          % (doc["site"]["last_build"], doc["site"]["last_update"]))
    for path, wrote in ((rel(STATUS_JSON), wrote_json), (rel(STATUS_PAGE), wrote_page)):
        print("  %s %s" % (path, "写入" if wrote else "未变化"))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(wrap_main("build_status", main))
    except BuildError as exc:
        print("构建失败：%s" % exc)
        sys.exit(1)
