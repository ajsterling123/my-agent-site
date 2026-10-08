#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 content/posts/*.md 生成为两处页面：

  public/blog/index.html        文章列表（日期倒序）
  public/posts/<slug>.html      每篇文章页（slug = md 文件名，ASCII）

用法（仓库根运行）：python scripts/build_blog.py

页面骨架（报头带、导航行、页脚步数、favicon、样式表引用）直接从 public/index.html
提取并改写，所以生成页与手写页除「链接前缀」与「aria-current」之外逐字节一致；
手写页将来改了报头带或页码，重新构建即自动跟上。

幂等：同一批 md 重复运行产出字节一致的输出，且只在内容变化时落盘；
只清理自己生成的 public/posts/*.html，不碰 content/，也不碰任何手写页。

正文支持的 Markdown：## / ### 标题、段落、无序与有序列表、**粗体**、
`行内代码`、[链接](地址)、> 引用。正文开头的 # 一行若与 frontmatter 的 title
相同则忽略（页面 h1 已由 title 提供），出现别的一级标题直接报错。
"""

import html
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
CONTENT = ROOT / "content" / "posts"
POSTS_OUT = PUBLIC / "posts"
BLOG_OUT = PUBLIC / "blog" / "index.html"
SKELETON = PUBLIC / "index.html"

SITE_NAME = "张易孝实验档案"
MARKER = "<!-- 由 scripts/build_blog.py 生成：改内容请改 content/posts/*.md -->"

BLOG_TITLE = "博客 · %s" % SITE_NAME
BLOG_DESCRIPTION = "张易孝实验档案的博客栏：按日期倒序列出全部文章，每篇附一句摘要。"
BLOG_FOOT = "本页是课程实验档案的「博客」页，文章按日期倒序登记。"
POST_FOOT = "本页是课程实验档案的一篇博客文章。"

FRONTMATTER_KEYS = ("title", "date", "description")
SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
HEAD_RE = re.compile(r"^(#{1,6})\s+(.*)$")
ITEM_RE = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
QUOTE_RE = re.compile(r"^>\s?(.*)$")
HREF_RE = re.compile(r"""\bhref\s*=\s*"([^"]*)\"""")


class BuildError(Exception):
    pass


def fail(msg):
    raise BuildError(msg)


def rel(path):
    return path.relative_to(ROOT).as_posix()


def sub_once(pattern, repl, text, what):
    """替换恰好一处；0 处或多于 1 处都算骨架漂移，直接报错而不是产出坏页面。"""
    hits = len(re.findall(pattern, text, re.S))
    if hits != 1:
        fail("页面骨架异常：%s 预期 1 处，实测 %d 处（pattern=%s）" % (what, hits, pattern))
    if not callable(repl):
        literal = repl
        repl = lambda m: literal
    return re.sub(pattern, repl, text, count=1, flags=re.S)


# ---------------------------------------------------------------- Markdown

def inline(text):
    """行内语法。先把代码与链接取走，再整体转义，最后放回（避免二次解析）。"""
    stash = []

    def keep(fragment):
        stash.append(fragment)
        return "\x00%d\x00" % (len(stash) - 1)

    def take_code(m):
        return keep("<code>%s</code>" % html.escape(m.group(1), quote=False))

    def take_link(m):
        label, href = m.group(1), m.group(2).strip()
        return keep('<a href="%s">%s</a>' % (html.escape(href, quote=True),
                                             html.escape(label, quote=False)))

    text = re.sub(r"`([^`]+)`", take_code, text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", take_link, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__(.+?)__", r"<strong>\1</strong>", text)
    return re.sub(r"\x00(\d+)\x00", lambda m: stash[int(m.group(1))], text)


def quote_block(inner_blocks):
    lines = ["<blockquote>"]
    for block in inner_blocks:
        lines += ["  " + l if l.strip() else "" for l in block]
    lines.append("</blockquote>")
    return lines


def parse_blocks(lines, title):
    """把正文行切成块；返回「行列表」的列表，块内相对缩进 2 空格一级。"""
    out = []
    i = 0
    at_start = True
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        m = HEAD_RE.match(line)
        if m:
            level, text = len(m.group(1)), m.group(2).strip()
            if level == 1:
                if at_start and text == title:
                    i += 1          # 与 frontmatter 重复的那一行：页面 h1 已由 title 提供
                    at_start = False
                    continue
                fail("正文出现第二个一级标题 %r：每页只能有一个 h1，"
                     "开头那行需与 frontmatter 的 title 一致，其余标题请用 ## 或 ###" % text)
            tag = "h2" if level == 2 else "h3"
            out.append(["<%s>%s</%s>" % (tag, inline(text), tag)])
            i += 1
            at_start = False
            continue

        if QUOTE_RE.match(line):
            inner = []
            while i < len(lines) and QUOTE_RE.match(lines[i]):
                inner.append(QUOTE_RE.match(lines[i]).group(1))
                i += 1
            out.append(quote_block(parse_blocks(inner, title)))
            at_start = False
            continue

        m = ITEM_RE.match(line)
        if m:
            ordered = m.group(2)[0] not in "-*+"
            items = []
            while i < len(lines):
                cur = lines[i]
                im = ITEM_RE.match(cur)
                if im:
                    if (im.group(2)[0] not in "-*+") != ordered:
                        break                      # 有序/无序切换：这是另一个列表
                    items.append([im.group(3)])
                    i += 1
                    continue
                if not cur.strip() or HEAD_RE.match(cur) or QUOTE_RE.match(cur):
                    break                          # 空行或块级语法：当前列表结束
                items[-1].append(cur.strip())      # 续行并入上一条
                i += 1
            tag = "ol" if ordered else "ul"
            block = ["<%s>" % tag]
            block += ["  <li>%s</li>" % inline(" ".join(it)) for it in items]
            block.append("</%s>" % tag)
            out.append(block)
            at_start = False
            continue

        para = [line.strip()]
        i += 1
        while i < len(lines) and lines[i].strip() \
                and not HEAD_RE.match(lines[i]) and not ITEM_RE.match(lines[i]) \
                and not QUOTE_RE.match(lines[i]):
            para.append(lines[i].strip())
            i += 1
        out.append(["<p>%s</p>" % inline(" ".join(para))])
        at_start = False
    return out


# ---------------------------------------------------------------- frontmatter

def parse_post(path):
    raw = path.read_text(encoding="utf-8-sig")
    lines = raw.split("\n")
    if not lines or lines[0].strip() != "---":
        fail("%s：文件必须以 frontmatter（首行 ---）开头" % path.name)
    end = None
    for i, l in enumerate(lines[1:], 1):
        if l.strip() == "---":
            end = i
            break
    if end is None:
        fail("%s：frontmatter 缺少收尾的 ---" % path.name)

    meta = {}
    for l in lines[1:end]:
        if not l.strip():
            continue
        if ":" not in l:
            fail("%s：frontmatter 行没有冒号：%r" % (path.name, l))
        key, value = l.split(":", 1)
        meta[key.strip()] = value.strip()

    for key in FRONTMATTER_KEYS:
        if not meta.get(key):
            fail("%s：frontmatter 缺少 %s" % (path.name, key))
    unknown = sorted(set(meta) - set(FRONTMATTER_KEYS))
    if unknown:
        fail("%s：frontmatter 有未支持的字段 %s（只支持 %s）"
             % (path.name, "、".join(unknown), " / ".join(FRONTMATTER_KEYS)))
    if not DATE_RE.match(meta["date"]):
        fail("%s：date 必须写成 YYYY-MM-DD，现在是 %r" % (path.name, meta["date"]))
    try:
        date.fromisoformat(meta["date"])
    except ValueError:
        fail("%s：date 不是合法日期：%s" % (path.name, meta["date"]))

    slug = path.stem
    if not SLUG_RE.match(slug):
        fail("%s：文件名必须用 ASCII 字母/数字与 . - _（slug 直接成为 URL，不用中文名）" % path.name)

    return {
        "slug": slug,
        "title": meta["title"],
        "date": meta["date"],
        "description": meta["description"],
        "blocks": parse_blocks(lines[end + 1:], meta["title"]),
    }


# ---------------------------------------------------------------- 页面组装

def indent(lines, base):
    return [(" " * base + l) if l.strip() else "" for l in lines]


def nav_block(skel, prefix, current_rel):
    """按输出深度改写导航 href；current_rel 非空时把 aria-current 放到对应菜单项。"""
    nav = re.search(r'<nav class="site-nav".*?</nav>', skel, re.S)
    if not nav:
        fail("public/index.html 里找不到 <nav class=\"site-nav\">")
    text = nav.group(0)
    text = re.sub(r'\s+aria-current="page"', "", text)   # 先摘掉骨架自带的当前项标记

    def fix(m):
        tag = m.group(0)
        href = HREF_RE.search(tag).group(1)
        new_href = prefix + href
        tag = tag.replace('href="%s"' % href, 'href="%s"' % new_href, 1)
        if current_rel is not None and new_href == current_rel:
            tag = tag.replace('<a href="%s"' % new_href,
                              '<a href="%s" aria-current="page"' % new_href, 1)
        return tag

    return re.sub(r"<a\b[^>]*>", fix, text)


def render_page(skel, title, description, prefix, head_block, main_block, foot_note, current_rel):
    page = sub_once(r"<title>.*?</title>",
                    "<title>%s</title>" % html.escape(title, quote=False), skel, "<title>")
    page = sub_once(r'<meta name="description" content="[^"]*">',
                    '<meta name="description" content="%s">' % html.escape(description, quote=True),
                    page, "meta description")
    page = sub_once(r'<link rel="stylesheet" href="[^"]*">',
                    '<link rel="stylesheet" href="%sstyles.css">' % prefix, page, "样式表引用")
    page = sub_once(r'<div class="doc-title">.*?</div>', head_block, page, "首页标题块")
    page = sub_once(r'<nav class="site-nav".*?</nav>', nav_block(skel, prefix, current_rel),
                    page, "导航块")
    page = sub_once(r"<main>.*?</main>",
                    "<main>\n%s\n    </main>" % main_block, page, "主内容区")
    foot = re.search(r'<footer class="doc-foot">.*?</footer>', page, re.S).group(0)
    page = page.replace(foot, sub_once(r"<p>.*?</p>", "<p>%s</p>" % html.escape(foot_note),
                                       foot, "页脚说明句"), 1)
    return sub_once(r"<!DOCTYPE html>", "<!DOCTYPE html>\n%s" % MARKER, page, "文档类型声明")


def folio_head(title):
    return '\n'.join(['<div class="folio">',
                      '        <h1>%s</h1>' % html.escape(title, quote=False),
                      '      </div>'])


def post_head(post):
    return '\n'.join(['<div class="post-head">',
                      '        <h1>%s</h1>' % html.escape(post["title"], quote=False),
                      '        <time class="post-date" datetime="%s">登记于 %s</time>'
                      % (post["date"], post["date"]),
                      '      </div>'])


def blog_main(posts, prefix):
    lines = ['<section class="sec" aria-labelledby="t-posts">',
             '  <h2 id="t-posts">文章登记</h2>']
    if posts:
        lines.append('  <ul class="post-list">')
        for p in posts:
            lines.append('    <li class="post-row">')
            lines.append('      <time class="post-date" datetime="%s">%s</time>' % (p["date"], p["date"]))
            lines.append('      <div class="post-item">')
            lines.append('        <h3><a href="%sposts/%s.html">%s</a></h3>'
                         % (prefix, p["slug"], html.escape(p["title"], quote=False)))
            lines.append('        <p>%s</p>' % html.escape(p["description"], quote=False))
            lines.append('      </div>')
            lines.append('    </li>')
        lines.append('  </ul>')
    else:
        lines.append('  <p class="intro">本页还没有文章：文章写在 content/posts/ 的 .md 里，'
                     '构建后自动登记在此。</p>')
    lines.append('</section>')
    return '\n'.join(indent(lines, 6))


def post_main(post):
    lines = ['<article class="post-body">']
    for block in post["blocks"]:
        lines += ["  " + l if l.strip() else "" for l in block]
    lines.append('</article>')
    return '\n'.join(indent(lines, 6))


def write_if_changed(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = text.encode("utf-8")
    if path.is_file() and path.read_bytes() == data:
        return False
    path.write_bytes(data)
    return True


def main():
    if not SKELETON.is_file():
        fail("找不到骨架页面 public/index.html")
    skel = SKELETON.read_text(encoding="utf-8")

    posts = [parse_post(p) for p in sorted(CONTENT.glob("*.md"))]
    posts.sort(key=lambda p: p["slug"])
    posts.sort(key=lambda p: p["date"], reverse=True)      # 日期倒序；同日按 slug 稳定

    outputs = {BLOG_OUT: render_page(skel, BLOG_TITLE, BLOG_DESCRIPTION, "../",
                                     folio_head("博客"), blog_main(posts, "../"),
                                     BLOG_FOOT, "../blog/index.html")}
    for p in posts:
        outputs[POSTS_OUT / ("%s.html" % p["slug"])] = render_page(
            skel, "%s · %s" % (p["title"], SITE_NAME), p["description"], "../",
            post_head(p), post_main(p), POST_FOOT, None)

    written, unchanged = [], []
    for path, text in sorted(outputs.items(), key=lambda kv: rel(kv[0])):
        (written if write_if_changed(path, text) else unchanged).append(rel(path))

    removed = []
    for stale in sorted(POSTS_OUT.glob("*.html")):
        if stale not in outputs and MARKER in stale.read_text(encoding="utf-8"):
            stale.unlink()
            removed.append(rel(stale))

    print("构建完成：%d 篇文章" % len(posts))
    for path in written:
        print("  写入 %s" % path)
    for path in unchanged:
        print("  未变化 %s" % path)
    for path in removed:
        print("  清理 %s（源文件已不在 content/posts/）" % path)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BuildError as exc:
        print("构建失败：%s" % exc)
        sys.exit(1)
