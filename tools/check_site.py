#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""机械校验 public/ 站点：页面骨架一致性、导航、aria-current、相对路径与链接可达性。

用法（仓库根运行）：python tools/check_site.py
退出码 0 = 全部通过，1 = 有失败项。

深度感知：每个页面的链接前缀由它相对 public/ 的深度算出——public/index.html 深度 0 用空串、
public/about/index.html 与 public/posts/x.html 深度 1 用 ../、更深再叠一层。手写页与
scripts/build_blog.py 生成的文章页因此用同一套判据：除链接前缀与 aria-current 落在哪一项
之外，导航块必须与 public/index.html 的导航块逐字节一致；报头带的元信息行与页脚步数
在所有页面逐字节一致。

页面清单不写死：public/ 下所有 .html 都在校验范围内，将来加页面自动纳入。
"""

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
CANONICAL = PUBLIC / "index.html"          # 骨架与导航的参照页
MARKER = "<!-- 由 scripts/build_blog.py 生成"   # 生成页的标记，见 scripts/build_blog.py

NAV_RE = re.compile(r'<nav class="site-nav".*?</nav>', re.S)
LI_RE = re.compile(r"<li>.*?</li>", re.S)
A_RE = re.compile(r"<a\b[^>]*>", re.I)
HREF_RE = re.compile(r"""\b(?:href|src)\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.I)
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
DESC_RE = re.compile(r'<meta name="description" content="([^"]*)">')
H1_RE = re.compile(r"<h1\b", re.I)
SCRIPT_RE = re.compile(r"<script\b", re.I)
DOC_META_RE = re.compile(r'<p class="doc-meta">.*?</p>', re.S)
DOC_DATE_RE = re.compile(r'<time class="doc-date" datetime="([^"]+)">')
FOOT_STEP_RE = re.compile(r'<p class="foot-step">.*?</p>', re.S)
STEP_RE = re.compile(r"^<p class=\"foot-step\">STEP \d+/\d+</p>$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

failures = []
notes = []


def fail(msg):
    failures.append(msg)


def note(msg):
    notes.append(msg)


def rel(path):
    return path.relative_to(PUBLIC).as_posix()


def depth(page):
    """页面相对 public/ 的目录层数：index.html 为 0，about/index.html 与 posts/x.html 为 1。"""
    return len(Path(page).parts) - 1


def prefix_of(page):
    return "../" * depth(page)


def pages():
    found = sorted(PUBLIC.rglob("*.html"))
    return [p for p in found if p.is_file()]


def load(path):
    return path.read_text(encoding="utf-8")


def normalize_nav(nav_html, prefix):
    """抹掉链接前缀与当前项标记，留下可逐字节比较的骨架。"""
    text = nav_html
    if prefix:
        text = text.replace('href="%s' % prefix, 'href="')
    text = re.sub(r'\s+aria-current="page"', "", text)
    return re.sub(r"\s+", " ", text).strip()


def one(pattern, text, what, page):
    found = pattern.findall(text)
    if len(found) != 1:
        fail("public/%s 的 %s 出现 %d 次，应为 1 次" % (page, what, len(found)))
        return None
    return found[0]


def audit_references(page, html):
    """无根绝对路径、无外部资源、每个相对引用都指向真实存在的文件。"""
    base = (PUBLIC / page).parent
    for m in HREF_RE.finditer(html):
        raw = (m.group(1) or m.group(2) or "").strip()
        if not raw:
            continue
        low = raw.lower()
        if low.startswith("data:"):
            note("%s: 内联 data-URI（favicon），非外部资源" % page)
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


def audit_page(page, html, canonical_nav, menu_targets):
    prefix = prefix_of(page)

    # --- 页面级元数据 ---
    title = one(TITLE_RE, html, "<title>", page)
    if title is not None and not title.strip():
        fail("public/%s 的 <title> 是空的" % page)
    desc = one(DESC_RE, html, 'meta name="description"', page)
    if desc is not None and not desc.strip():
        fail("public/%s 的 meta description 是空的" % page)
    one(H1_RE, html, "<h1>", page)
    if SCRIPT_RE.search(html):
        fail("public/%s 含 <script>" % page)

    # --- 在册章只在首页 ---
    if 'class="stamp"' in html and page != "index.html":
        fail("public/%s 出现「在册」章；章只属于 public/index.html" % page)

    # --- 引用审计 ---
    audit_references(page, html)

    # --- 导航块：除前缀与 aria-current 外与参照页逐字节一致 ---
    nav = one(NAV_RE, html, 'class="site-nav" 的导航块', page)
    if nav is not None:
        if normalize_nav(nav, prefix) != canonical_nav:
            fail("public/%s 的导航块与 public/index.html 不一致（归一化前缀与 aria-current 后仍不同）" % page)
        if len(LI_RE.findall(nav)) != 5:
            fail("public/%s 的菜单项不是 5 个" % page)

    # --- aria-current：菜单页恰好一次且指向本页；非菜单页（文章页）一次都不许有 ---
    marks = A_RE.findall(html)
    marked = [tag for tag in marks if 'aria-current="page"' in tag]
    if page in menu_targets:
        if len(marked) != 1:
            fail('public/%s 的 aria-current="page" 出现 %d 次，应为 1 次' % (page, len(marked)))
        else:
            href = HREF_RE.search(marked[0])
            if not href:
                fail("public/%s 的当前项没有 href" % page)
            else:
                target = ((PUBLIC / page).parent / unquote(href.group(1) or href.group(2))).resolve()
                if target != (PUBLIC / page).resolve():
                    fail("public/%s 的 aria-current 标在了 %s，不是本页" % (page, href.group(1)))
    elif marked:
        fail("public/%s 不是任何菜单项，不该出现 aria-current（文章页不设当前项）" % page)

    # --- 生成页的标记与结构 ---
    if page.startswith("posts/"):
        if MARKER not in html:
            fail("public/%s 缺少生成标记：public/posts/ 下的页面应由 scripts/build_blog.py 生成" % page)
        if '<article class="post-body">' not in html:
            fail('public/%s 缺少 <article class="post-body">' % page)


def report(total, menu_count, post_count):
    for n in sorted(set(notes)):
        print("  提示 %s" % n)
    if failures:
        print("\n失败 %d 项：" % len(failures))
        for f in failures:
            print("  ✗ %s" % f)
        return 1
    print("\n全部通过：%d 页（%d 个菜单页 + %d 篇生成的文章页）导航骨架一致、"
          "每页恰好一个 h1、aria-current 落点正确、零根绝对路径、零外部资源、所有链接目标存在。"
          % (total, menu_count, post_count))
    return 0


def main():
    all_pages = pages()
    if not CANONICAL.is_file():
        fail("缺少骨架参照页 public/index.html")
        return report(0, 0, 0)
    if not all_pages:
        fail("public/ 下一个 .html 都没有")
        return report(0, 0, 0)

    canonical_html = load(CANONICAL)
    canonical_nav = one(NAV_RE, canonical_html, 'class="site-nav" 的导航块', "index.html")
    if canonical_nav is None:
        return report(0, 0, 0)
    canonical_nav_norm = normalize_nav(canonical_nav, "")

    # 菜单指向的页面（相对 public/ 的路径）：由参照页导航解析
    menu_targets = set()
    for tag in A_RE.findall(canonical_nav):
        m = HREF_RE.search(tag)
        if m:
            menu_targets.add((PUBLIC / unquote(m.group(1))).resolve().relative_to(PUBLIC).as_posix())

    # --- 报头带元信息行与页脚步数：全站逐字节一致 ---
    doc_meta, foot_step = {}, {}
    for path in all_pages:
        page = rel(path)
        html = load(path)
        meta = one(DOC_META_RE, html, 'class="doc-meta" 的元信息行', page)
        step = one(FOOT_STEP_RE, html, 'class="foot-step" 的页脚步数', page)
        if meta is not None:
            doc_meta[page] = meta
            stamp_date = DOC_DATE_RE.search(meta)
            if not stamp_date:
                fail('public/%s 的元信息行缺少 <time class="doc-date">' % page)
            elif not DATE_RE.match(stamp_date.group(1)):
                fail("public/%s 的「最后更新」不是 YYYY-MM-DD：%s" % (page, stamp_date.group(1)))
        if step is not None:
            foot_step[page] = step
            if not STEP_RE.match(step):
                fail("public/%s 的页脚步数不是 STEP n/12 的形式：%s" % (page, step))

    for label, collected in (("报头带元信息行", doc_meta), ("页脚步数", foot_step)):
        values = sorted(set(collected.values()))
        if len(values) > 1:
            detail = "；".join("%s=%r" % (p, v) for p, v in sorted(collected.items()))
            fail("%s在所有页面必须逐字节一致，实测 %d 种：%s" % (label, len(values), detail))

    # --- 逐页 ---
    for path in all_pages:
        audit_page(rel(path), load(path), canonical_nav_norm, menu_targets)

    post_count = len([p for p in all_pages if rel(p).startswith("posts/")])
    return report(len(all_pages), len(menu_targets), post_count)


if __name__ == "__main__":
    sys.exit(main())
