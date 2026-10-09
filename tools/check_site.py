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

外部引用分两级（Step 6 起，Step 7 扩展，口径同时写在 AGENTS.md「站点与目录」与 DESIGN.md）：
- 外部「资源」——script/img/iframe/video/audio/source/track 的 src、srcset、form 的 action、
  object/embed 的 data、link 的 href（样式表/字体/preconnect），以及 CSS 里的 @import 与 url(//…)：
  **所有页面一律禁止**。零外部请求是 Step 1 起的资产。
- 外部「导航」——`<a href>`：只有**外部内容页**（public/rss/ 与 public/papers/ 下的页面）允许，
  且必须是 https、必须带 rel="noopener noreferrer" 与 target="_blank"；其余页面出现任何
  站外引用仍然失败。

脚本：全站只有两处外部内容页各允许恰好一个同域 defer 脚本——public/rss/index.html 引
reader.js、public/papers/index.html 引 papers.js（均无内联代码）；其余页面出现 <script>
一律失败。任何页面都不允许内联事件处理属性（on…=）。

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
# 属性名与值一起捕获：href 与 src 的「外部」性质不同——<a href> 是导航、<link href> 是资源，
# 所以判据必须同时知道属性名与所在元素名（见 audit_references）。
ATTR_RE = re.compile(r"""(?<![\w-])(href|src|srcset|action|data)\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.I)
ANY_ATTR_RE = re.compile(r"""(?<![\w-])([a-zA-Z][\w:-]*)\s*=\s*(?:"([^"]*)"|'([^']*)')""")
TAG_RE = re.compile(r"<([a-zA-Z][\w:-]*)((?:\s+[^<>]*?)?)/?>", re.S)
SCRIPT_RE = re.compile(r"<script\b([^>]*)>(.*?)</script\s*>", re.I | re.S)
ON_ATTR_RE = re.compile(r"""\son[a-z]+\s*=\s*["']""", re.I)
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
DESC_RE = re.compile(r'<meta name="description" content="([^"]*)">')
H1_RE = re.compile(r"<h1\b", re.I)
DOC_META_RE = re.compile(r'<p class="doc-meta">.*?</p>', re.S)
DOC_DATE_RE = re.compile(r'<time class="doc-date" datetime="([^"]+)">')
FOOT_STEP_RE = re.compile(r'<p class="foot-step">.*?</p>', re.S)
STEP_RE = re.compile(r"^<p class=\"foot-step\">STEP \d+/\d+</p>$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# 一律禁止外部引用的属性：资源就是资源，不分页面
RESOURCE_ATTRS = ("src", "srcset", "action", "data")
# 允许出现站外导航链接的「外部内容页」前缀，以及它们各自唯一允许的脚本
EXTERNAL_PREFIXES = ("rss/", "papers/")
SCRIPT_PAGES = {
    "rss/index.html": "reader.js",
    "papers/index.html": "papers.js",
}
# 站外导航链接的三个硬性条件
NAV_REL_TOKENS = ("noopener", "noreferrer")
NAV_TARGET = "_blank"
# CSS 里的外部引用（本仓库现状：零 url()、零 @import）
EXTERNAL_CSS_RE = re.compile(r"""@import|url\(\s*["']?(?:https?:)?//""", re.I)

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


def strip_comments(html):
    """注释不是渲染内容：注释里写 <a href> 之类的示例不该被当成真引用。"""
    return COMMENT_RE.sub("", html)


def attr_value(match):
    return match.group(2) if match.group(2) is not None else match.group(3)


def attrs_of(attrs_text):
    return {m.group(1).lower(): attr_value(m) for m in ANY_ATTR_RE.finditer(attrs_text or "")}


def is_external(raw):
    """站外引用：带 scheme（http:、https:、mailto:、javascript: …）或以 // 开头。"""
    low = raw.lower()
    return low.startswith("//") or bool(re.match(r"^[a-z][a-z0-9+.-]*:", low))


def check_local_target(base, page, raw):
    clean = unquote(urlsplit(raw).path)
    if not clean:
        return
    target = (base / clean).resolve()
    if not target.exists():
        fail("public/%s 的链接目标不存在：%s" % (page, raw))
    elif target.is_dir():
        fail("public/%s 的链接指向目录而非文件：%s" % (page, raw))


def check_nav_link(page, element, attrs, raw):
    """站外导航链接：只有外部内容页（rss/ 与 papers/）允许，且必须 https + rel + target 三件齐。"""
    if not page.startswith(EXTERNAL_PREFIXES):
        fail("public/%s 出现站外链接（只有外部内容页 public/%s 允许外链，其余页面必须站内自洽）：%s"
             % (page, " 与 public/".join(EXTERNAL_PREFIXES), raw))
        return
    if not raw.lower().startswith("https://"):
        fail("public/%s 的站外链接必须是 https:// 开头：%s" % (page, raw))
        return
    values = attrs_of(attrs)
    missing = []
    rel = (values.get("rel") or "").lower().split()
    if not all(token in rel for token in NAV_REL_TOKENS):
        missing.append('rel="noopener noreferrer"')
    if values.get("target") != NAV_TARGET:
        missing.append('target="%s"' % NAV_TARGET)
    if missing:
        fail("public/%s 的站外链接缺少 %s：%s（外链只是导航，必须显式声明，避免被当成资源或拿到 opener）"
             % (page, "、".join(missing), raw))


def audit_references(page, html):
    """两级外部引用规则 + 根绝对路径 + 相对引用可达性。判据见模块 docstring。"""
    base = (PUBLIC / page).parent
    for tag in TAG_RE.finditer(html):
        element = tag.group(1).lower()
        attrs = tag.group(2) or ""
        for m in ATTR_RE.finditer(attrs):
            name = m.group(1).lower()
            raw = attr_value(m).strip()
            if not raw:
                continue
            low = raw.lower()
            if low.startswith("data:"):
                note("%s: 内联 data-URI（favicon），非外部资源" % page)
                continue
            if low.startswith("mailto:"):
                if element == "a" and name == "href":
                    continue
                fail("public/%s 把 mailto: 用在了 <%s %s> 上" % (page, element, name))
                continue
            if low.startswith(("javascript:", "vbscript:")):
                fail("public/%s 出现可执行 scheme：%s" % (page, raw))
                continue

            # 资源引用：一律禁止外部；站内的照旧检查目标文件是否存在
            if name in RESOURCE_ATTRS or (name == "href" and element != "a"):
                if is_external(raw):
                    fail("public/%s 引用了外部资源（<%s %s>）：%s（零外部请求是本站资产）"
                         % (page, element, name, raw))
                elif name != "srcset":
                    check_local_target(base, page, raw)
                continue

            # 剩下的只有 <a href>：站外是「导航」，按导航规则判
            if is_external(raw):
                check_nav_link(page, element, attrs, raw)
                continue
            if raw.startswith("/"):
                fail("public/%s 用了根绝对路径（Pages 子路径下会 404）：%s" % (page, raw))
                continue
            check_local_target(base, page, raw)


def audit_scripts(page, html):
    """全站仅有的两处同域脚本：rss/index.html 引 reader.js、papers/index.html 引 papers.js
    （各恰好一个，defer、无内联代码）；其余页面出现 <script> 一律失败。"""
    scripts = SCRIPT_RE.findall(html)
    expected = SCRIPT_PAGES.get(page)
    if expected is None:
        if scripts:
            fail("public/%s 含 <script>；全站只有外部内容页 %s 各允许一个同域脚本"
                 % (page, " 与 ".join("public/%s" % p for p in sorted(SCRIPT_PAGES))))
        return
    if len(scripts) != 1:
        fail("public/%s 的 <script> 有 %d 个，应恰好 1 个（同域 %s、defer）"
             % (page, len(scripts), expected))
        return
    attrs, body = scripts[0]
    values = attrs_of(attrs)
    if values.get("src") != expected:
        fail('public/%s 的脚本必须写成 src="%s"（同域），实际 %r'
             % (page, expected, values.get("src")))
    if "defer" not in attrs.lower():
        fail("public/%s 的 %s 必须带 defer" % (page, expected))
    if body.strip():
        fail("public/%s 的 <script> 里有内联代码；脚本内容只能放在 %s 里" % (page, expected))


def audit_styles():
    """样式表里的外部引用（@import / url(//…)）同样算外部资源。"""
    for path in sorted(PUBLIC.rglob("*.css")):
        text = load(path)
        for m in EXTERNAL_CSS_RE.finditer(text):
            fail("public/%s 出现外部样式引用：%s" % (rel(path), m.group(0)))


def audit_page(page, html, canonical_nav, canonical_nav_raw, menu_targets):
    prefix = prefix_of(page)
    clean = strip_comments(html)          # 注释不算渲染内容

    # --- 页面级元数据 ---
    title = one(TITLE_RE, html, "<title>", page)
    if title is not None and not title.strip():
        fail("public/%s 的 <title> 是空的" % page)
    desc = one(DESC_RE, html, 'meta name="description"', page)
    if desc is not None and not desc.strip():
        fail("public/%s 的 meta description 是空的" % page)
    one(H1_RE, clean, "<h1>", page)
    audit_scripts(page, clean)
    if ON_ATTR_RE.search(clean):
        fail("public/%s 出现内联事件处理属性（on…=）：脚本只能走 reader.js，别在标签上挂代码" % page)

    # --- 在册章只在首页 ---
    if 'class="stamp"' in clean and page != "index.html":
        fail("public/%s 出现「在册」章；章只属于 public/index.html" % page)

    # --- 引用审计 ---
    audit_references(page, clean)

    # --- 导航块：除前缀与 aria-current 外与参照页逐字节一致 ---
    nav = one(NAV_RE, html, 'class="site-nav" 的导航块', page)
    if nav is not None:
        if normalize_nav(nav, prefix) != canonical_nav:
            fail("public/%s 的导航块与 public/index.html 不一致（归一化前缀与 aria-current 后仍不同）" % page)
        if len(LI_RE.findall(nav)) != len(LI_RE.findall(canonical_nav_raw)):
            fail("public/%s 的菜单项不是 %d 个" % (page, len(LI_RE.findall(canonical_nav_raw))))

    # --- aria-current：菜单页恰好一次且指向本页；非菜单页（文章页）一次都不许有 ---
    marks = A_RE.findall(html)
    marked = [tag for tag in marks if 'aria-current="page"' in tag]
    if page in menu_targets:
        if len(marked) != 1:
            fail('public/%s 的 aria-current="page" 出现 %d 次，应为 1 次' % (page, len(marked)))
        else:
            href = ATTR_RE.search(marked[0])
            if not href:
                fail("public/%s 的当前项没有 href" % page)
            else:
                target = ((PUBLIC / page).parent / unquote(attr_value(href))).resolve()
                if target != (PUBLIC / page).resolve():
                    fail("public/%s 的 aria-current 标在了 %s，不是本页" % (page, attr_value(href)))
    elif marked:
        fail("public/%s 不是任何菜单项，不该出现 aria-current（文章页不设当前项）" % page)

    # --- 生成页的标记与结构 ---
    if page.startswith("posts/"):
        if MARKER not in html:
            fail("public/%s 缺少生成标记：public/posts/ 下的页面应由 scripts/build_blog.py 生成" % page)
        if '<article class="post-body">' not in clean:
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
          "每页恰好一个 h1、aria-current 落点正确、零根绝对路径、零外部资源引用、"
          "站外链接只在外部内容页 %s 下且均带 rel/target、所有链接目标存在。"
          % (total, menu_count, post_count,
             " 与 ".join("public/%s" % p for p in EXTERNAL_PREFIXES)))
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
        m = ATTR_RE.search(tag)
        if m:
            menu_targets.add((PUBLIC / unquote(attr_value(m))).resolve().relative_to(PUBLIC).as_posix())

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
        audit_page(rel(path), load(path), canonical_nav_norm, canonical_nav, menu_targets)

    # --- 样式表里的外部引用 ---
    audit_styles()

    post_count = len([p for p in all_pages if rel(p).startswith("posts/")])
    return report(len(all_pages), len(menu_targets), post_count)


if __name__ == "__main__":
    sys.exit(main())
