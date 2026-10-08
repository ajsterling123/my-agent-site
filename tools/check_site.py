#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""机械校验 public/ 站点：导航一致性、aria-current、相对路径与链接可达性。

用法（仓库根运行）：python tools/check_site.py
退出码 0 = 全部通过，1 = 有失败项。
"""

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
PAGES = [
    "index.html",
    "about/index.html",
    "blog/index.html",
    "papers/index.html",
    "wiki/index.html",
]
NAV_RE = re.compile(r"<nav\b.*?</nav>", re.S)
LI_RE = re.compile(r"<li>.*?</li>", re.S)
HREF_RE = re.compile(r"""\b(?:href|src)\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.I)
SCRIPT_RE = re.compile(r"<script\b", re.I)

failures = []
notes = []


def fail(msg):
    failures.append(msg)


def load(page):
    return (PUBLIC / page).read_text(encoding="utf-8")


def normalize_nav(nav_html, prefix):
    """抹掉页面前缀与当前项标记，留下可逐字节比较的骨架。"""
    text = nav_html
    if prefix:
        text = text.replace('href="%s' % prefix, 'href="')
    text = re.sub(r'\s+aria-current="page"', "", text)
    return re.sub(r"\s+", " ", text).strip()


def main():
    # --- 1. 五个页面存在 ---
    for page in PAGES:
        if not (PUBLIC / page).is_file():
            fail("缺少页面文件：public/%s" % page)
    if failures:
        return report()

    # --- 2. 导航块一致性 ---
    navs, navs_norm = {}, {}
    for page in PAGES:
        found = NAV_RE.findall(load(page))
        if len(found) != 1:
            fail("public/%s 的 <nav> 数量为 %d，应为 1" % (page, len(found)))
            continue
        navs[page] = found[0]
        prefix = "" if page.count("/") == 0 else "../" * page.count("/")
        navs_norm[page] = normalize_nav(found[0], prefix)

    reference = navs_norm[PAGES[0]]
    for page in PAGES[1:]:
        if navs_norm.get(page) != reference:
            fail("public/%s 的导航块与其他页不一致（归一化后仍不同）" % page)
        if navs.get(page, "").count("<li>") != 5:
            fail("public/%s 的菜单项不是 5 个" % page)

    # --- 3. aria-current 唯一且指向本页 ---
    for page in PAGES:
        html = load(page)
        marks = re.findall(r'<a\b[^>]*aria-current="page"[^>]*>', html)
        if len(marks) != 1:
            fail("public/%s 的 aria-current=\"page\" 出现 %d 次，应为 1" % (page, len(marks)))
            continue
        href = HREF_RE.search(marks[0])
        if not href:
            fail("public/%s 的当前项没有 href" % page)
            continue
        target = (PUBLIC / page).parent / unquote(href.group(1) or href.group(2))
        if target.resolve() != (PUBLIC / page).resolve():
            fail("public/%s 的 aria-current 标在了 %s，不是本页" % (page, href.group(1)))

    # --- 4/5/6. 引用审计：无根绝对路径、无外部资源、链接目标存在 ---
    for page in PAGES:
        html = load(page)
        base = (PUBLIC / page).parent
        if SCRIPT_RE.search(html):
            fail("public/%s 含 <script>" % page)
        for m in HREF_RE.finditer(html):
            raw = (m.group(1) or m.group(2) or "").strip()
            if not raw:
                continue
            low = raw.lower()
            if low.startswith("data:"):
                notes.append("%s: 内联 data-URI（favicon），非外部资源" % page)
                continue
            if low.startswith("mailto:"):
                continue
            if low.startswith(("http://", "https://", "//")):
                fail("public/%s 引用了外部资源：%s" % (page, raw))
                continue
            if raw.startswith("/"):
                fail("public/%s 用了根绝对路径（Pages 子路径下会 404）：%s" % (page, raw))
                continue
            clean = unquote(urlsplit(raw).path)
            if not clean:
                continue
            target = (base / clean).resolve()
            if not target.exists():
                fail("public/%s 的链接目标不存在：%s" % (page, raw))
            elif target.is_dir():
                fail("public/%s 的链接指向目录而非文件：%s" % (page, raw))

    # --- 7. 步数与日期 ---
    for page in PAGES:
        html = load(page)
        if "STEP 3/12" not in html:
            fail("public/%s 的页脚步数不是 STEP 3/12" % page)
        if "2026-10-08" not in html:
            fail("public/%s 的「最后更新」不是 2026-10-08" % page)

    return report()


def report():
    for n in sorted(set(notes)):
        print("  提示 %s" % n)
    if failures:
        print("\n失败 %d 项：" % len(failures))
        for f in failures:
            print("  ✗ %s" % f)
        return 1
    print("\n全部通过：5 页导航一致、每页单个 aria-current、零根绝对路径、零外部资源、所有链接目标存在。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
