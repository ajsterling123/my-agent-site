#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 content/posts/*.md 生成为三处页面/文件：

  public/blog/index.html        文章列表（日期倒序）+ RSS 订阅入口
  public/posts/<slug>.html      每篇文章页（slug = md 文件名，ASCII）

用法（仓库根运行）：python scripts/build_blog.py

页面骨架（报头带、导航行、页脚步数、favicon、样式表引用）直接从 public/index.html
提取并改写，所以生成页与手写页除「链接前缀」与「aria-current」之外逐字节一致；
手写页将来改了报头带或页码，重新构建即自动跟上。骨架改写与 Markdown 转换的
实现在 scripts/page_build.py，与 scripts/build_wiki.py（Step 8 的 Wiki 页）共用一份，
本脚本不再自带。

幂等：同一批 md 重复运行产出字节一致的输出，且只在内容变化时落盘；
只清理自己生成的 public/posts/*.html，不碰 content/，也不碰任何手写页。

slug 命名、frontmatter 解析、文章页路径与排序来自 scripts/site_data.py（与
scripts/build_feed.py 共用一份实现，RSS 的链接因此与列表页的链接必然一致）。
public/feed.xml 由 scripts/build_feed.py 生成，本脚本不碰它。

正文支持的 Markdown：## / ### 标题、段落、无序与有序列表、**粗体**、
`行内代码`、[链接](地址)、> 引用（实现见 page_build.py；博客正文不支持
[[双向链接]]，那是 content/wiki/ 的语法）。
"""

import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_data import (BLOG_OUT, POSTS_OUT, SKELETON, SITE_NAME, BuildError, fail, load_posts,
                       post_rel, rel, write_if_changed)
from page_build import article_body, folio_head, indent, parse_blocks, render_page

MARKER = "<!-- 由 scripts/build_blog.py 生成：改内容请改 content/posts/*.md -->"

BLOG_TITLE = "博客 · %s" % SITE_NAME
BLOG_DESCRIPTION = "张易孝实验档案的博客栏：按日期倒序列出全部文章，每篇附一句摘要。"
BLOG_FOOT = "本页是课程实验档案的「博客」页，文章按日期倒序登记。"
POST_FOOT = "本页是课程实验档案的一篇博客文章。"

# 点击浏览器地址栏右侧的订阅按钮、或阅读器贴 URL 时，靠这一行找到 feed；相对路径，
# 与页面里其它站内引用同一套规则（禁止以 / 开头的根绝对路径）。
FEED_LINK = ('\n  <link rel="alternate" type="application/rss+xml" '
             'title="%s · 博客" href="../feed.xml">' % SITE_NAME)


# ---------------------------------------------------------------- frontmatter

def load_post_pages():
    """site_data 负责读内容源与排序（与 build_feed.py 同一份规则）；这里补 Markdown 正文块。"""
    posts = load_posts()
    for post in posts:
        post["blocks"] = parse_blocks(post.pop("body"), post["title"])
        post.pop("path", None)
    return posts


# ---------------------------------------------------------------- 页面组装

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
            lines.append('        <h3><a href="%s%s">%s</a></h3>'
                         % (prefix, post_rel(p["slug"]), html.escape(p["title"], quote=False)))
            lines.append('        <p>%s</p>' % html.escape(p["description"], quote=False))
            lines.append('      </div>')
            lines.append('    </li>')
        lines.append('  </ul>')
    else:
        lines.append('  <p class="intro">本页还没有文章：文章写在 content/posts/ 的 .md 里，'
                     '构建后自动登记在此。</p>')
    # 订阅入口：账本之外的一条附注，沿用 .intro 一句陈述，不新增卡片/图标/组件。
    lines.append('  <p class="intro">订阅：<a href="%sfeed.xml">feed.xml</a>（RSS 2.0），'
                 '新文章登记后同步进订阅源。</p>' % prefix)
    lines.append('</section>')
    return '\n'.join(indent(lines, 6))


def post_main(post):
    return article_body(post["blocks"])


def main():
    if not SKELETON.is_file():
        fail("找不到骨架页面 public/index.html")
    skel = SKELETON.read_text(encoding="utf-8")

    posts = load_post_pages()

    outputs = {BLOG_OUT: render_page(skel, BLOG_TITLE, BLOG_DESCRIPTION, "../",
                                     folio_head("博客"), blog_main(posts, "../"),
                                     BLOG_FOOT, "../blog/index.html", MARKER,
                                     extra_head=FEED_LINK)}
    for p in posts:
        outputs[POSTS_OUT / ("%s.html" % p["slug"])] = render_page(
            skel, "%s · %s" % (p["title"], SITE_NAME), p["description"], "../",
            post_head(p), post_main(p), POST_FOOT, None, MARKER)

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
