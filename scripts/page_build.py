#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""page_build.py —— 页面构建的共用实现：极简 Markdown 转换 + public/index.html 骨架
外科改写。build_blog.py（博客列表与文章页）与 build_wiki.py（Wiki 栏目页与词条页）
都从这里取用，全站只有这一份实现，不要再写第三份。

Markdown 支持：## / ### 标题、段落、无序与有序列表、**粗体**、`行内代码`、
[链接](地址)、> 引用。正文开头的 # 一行若与 frontmatter 的 title 相同则忽略
（页面 h1 已由 title 提供），出现别的一级标题直接报错。
传入 wiki=回调 时额外支持 [[双向链接]]：[[slug]] 与 [[slug|别名]] 交给回调解决；
行内代码里的 [[…]] 先被抽走，不会被当成链接解析。

骨架改写：把 public/index.html 当骨架，只替换 <title>、description、样式表前缀、
标题区、导航块（href 前缀与 aria-current 落点）、<main>、页脚说明句，并在
<!DOCTYPE html> 后插入生成标记——除此之外的模板部分逐字节保留。手写页将来改了
报头带或页码，重新构建即自动跟上。sub_once 替换恰好一处：0 处或多于 1 处都算
骨架漂移，直接报错而不是产出坏页面。

校验失败一律走 site_data.fail（BuildError）：内容源写错了应当构建失败，
而不是产出一份坏页面。
"""

import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_data import fail

HEAD_RE = re.compile(r"^(#{1,6})\s+(.*)$")
ITEM_RE = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
QUOTE_RE = re.compile(r"^>\s?(.*)$")
HREF_RE = re.compile(r"""\bhref\s*=\s*"([^"]*)\"""")
WIKI_RE = re.compile(r"\[\[([^\[\]|]+)(?:\|([^\[\]]*))?\]\]")


# ---------------------------------------------------------------- Markdown

def inline(text, wiki=None):
    """行内语法。先把代码与链接取走，再整体转义，最后放回（避免二次解析）。

    wiki 为回调 target, alias -> 成品 HTML 片段（自己负责转义）；None 时 [[…]]
    原样走文本。顺序：代码最先抽走，因此 `` `[[…]]` `` 不参与链接解析。
    """
    stash = []

    def keep(fragment):
        stash.append(fragment)
        return "\x00%d\x00" % (len(stash) - 1)

    def take_code(m):
        return keep("<code>%s</code>" % html.escape(m.group(1), quote=False))

    def take_wiki(m):
        target, alias = m.group(1).strip(), (m.group(2) or "").strip()
        return keep(wiki(target, alias or None))

    def take_link(m):
        label, href = m.group(1), m.group(2).strip()
        return keep('<a href="%s">%s</a>' % (html.escape(href, quote=True),
                                             html.escape(label, quote=False)))

    text = re.sub(r"`([^`]+)`", take_code, text)
    if wiki is not None:
        text = re.sub(WIKI_RE, take_wiki, text)
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


def parse_blocks(lines, title, wiki=None):
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
            out.append(["<%s>%s</%s>" % (tag, inline(text, wiki), tag)])
            i += 1
            at_start = False
            continue

        if QUOTE_RE.match(line):
            inner = []
            while i < len(lines) and QUOTE_RE.match(lines[i]):
                inner.append(QUOTE_RE.match(lines[i]).group(1))
                i += 1
            out.append(quote_block(parse_blocks(inner, title, wiki)))
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
            block += ["  <li>%s</li>" % inline(" ".join(it), wiki) for it in items]
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
        out.append(["<p>%s</p>" % inline(" ".join(para), wiki)])
        at_start = False
    return out


# ---------------------------------------------------------------- 骨架外科改写

def sub_once(pattern, repl, text, what):
    """替换恰好一处；0 处或多于 1 处都算骨架漂移，直接报错而不是产出坏页面。"""
    hits = len(re.findall(pattern, text, re.S))
    if hits != 1:
        fail("页面骨架异常：%s 预期 1 处，实测 %d 处（pattern=%s）" % (what, hits, pattern))
    if not callable(repl):
        literal = repl
        repl = lambda m: literal
    return re.sub(pattern, repl, text, count=1, flags=re.S)


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


def render_page(skel, title, description, prefix, head_block, main_block, foot_note, current_rel,
                marker, extra_head=""):
    """从骨架改写出一页；marker 是本页的生成标记注释（各构建脚本自带一份）。"""
    page = sub_once(r"<title>.*?</title>",
                    "<title>%s</title>" % html.escape(title, quote=False), skel, "<title>")
    page = sub_once(r'<meta name="description" content="[^"]*">',
                    '<meta name="description" content="%s">' % html.escape(description, quote=True),
                    page, "meta description")
    page = sub_once(r'<link rel="stylesheet" href="[^"]*">',
                    '<link rel="stylesheet" href="%sstyles.css">%s' % (prefix, extra_head),
                    page, "样式表引用")
    page = sub_once(r'<div class="doc-title">.*?</div>', head_block, page, "首页标题块")
    page = sub_once(r'<nav class="site-nav".*?</nav>', nav_block(skel, prefix, current_rel),
                    page, "导航块")
    page = sub_once(r"<main>.*?</main>",
                    "<main>\n%s\n    </main>" % main_block, page, "主内容区")
    foot = re.search(r'<footer class="doc-foot">.*?</footer>', page, re.S).group(0)
    page = page.replace(foot, sub_once(r"<p>.*?</p>", "<p>%s</p>" % html.escape(foot_note),
                                       foot, "页脚说明句"), 1)
    return sub_once(r"<!DOCTYPE html>", "<!DOCTYPE html>\n%s" % marker, page, "文档类型声明")


def folio_head(title):
    return '\n'.join(['<div class="folio">',
                      '        <h1>%s</h1>' % html.escape(title, quote=False),
                      '      </div>'])


def article_body(blocks):
    """正文块列表包成 <article class="post-body">（缩进与手写页的 <main> 对齐）。"""
    lines = ['<article class="post-body">']
    for block in blocks:
        lines += ["  " + l if l.strip() else "" for l in block]
    lines.append('</article>')
    return '\n'.join(indent(lines, 6))
