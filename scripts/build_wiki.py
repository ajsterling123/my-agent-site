#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 content/wiki/*.md 生成为 public/wiki/ 下的静态页面（Step 8：文件化个人 Wiki）：

  public/wiki/index.html    栏目页兼索引（源 content/wiki/index.md；正文之后自动附
                            「页面清单」——每个 Wiki 页的标题、updated、tags）
  public/wiki/<slug>.html   每个词条一页（源 content/wiki/<slug>.md）

用法（仓库根运行）：python scripts/build_wiki.py

骨架外科改写与 Markdown 转换复用 scripts/page_build.py（与 build_blog.py 同一份实现，
全站不再有第二份）：把 public/index.html 当骨架，只改 <title>、description、样式前缀、
标题区、导航块（href 前缀与 aria-current 落点）、<main>、页脚说明句，其余逐字节保留；
栏目页把导航 aria-current 从「首页」移到「Wiki」，词条页与文章页同为 1 层深、前缀 ../、
一个 aria-current 都不设。

[[双向链接]] 规则（详见 content/wiki/README.md）：
  - [[slug]] 渲染成指向同目录词条页的内部链接，显示文字默认取目标页 frontmatter 的
    title；[[slug|别名]] 自定义显示文字。行内代码里的 [[…]] 原样保留、不参与解析。
  - 死链即构建失败：[[target]] 必须对应 content/wiki/ 下真实存在的 <target>.md，
    否则非零退出并指出是哪个文件里的哪个链接；不成对的 [[ 或 ]] 同样判失败。
  - 反向链接自动算：每页底部「链接到此页的页面」由本脚本从各页正文的 [[链接]] 反查
    得出（不计入自动生成的清单行，也不计本页指向自身的链接）；没有被任何页面引用的
    页面不显示该节。清单与反向链接都由脚本生成、不手维护，与内容永不错位。

frontmatter：每页必填 title / updated / tags；updated 是合法 YYYY-MM-DD；
tags 逗号分隔。README.md 是规则文件，按名跳过、不登记为词条。

幂等：同一批 md 重复运行产出字节一致的输出，且只在内容变化时落盘；
只清理自己生成的 public/wiki/*.html（以本脚本生成标记为凭），不碰 content/，
不碰任何手写页。生成页带生成标记，由 tools/check_site.py 校验。

Wiki 页面零 JavaScript：[[链接]] 与反向链接都在构建期解决，产物是纯静态 HTML。
"""

import html
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_data import (DATE_RE, SKELETON, SITE_NAME, SLUG_RE, WIKI_CONTENT, WIKI_OUT, WIKI_RULES,
                       BuildError, fail, rel, write_if_changed)
from page_build import article_body, folio_head, indent, parse_blocks, render_page, WIKI_RE

MARKER = ("<!-- 由 scripts/build_wiki.py 生成：改内容请改 content/wiki/*.md，"
          "规则见 content/wiki/README.md -->")

WIKI_INDEX_DESCRIPTION = ("张易孝实验档案的 Wiki 栏：文件化个人知识库；一个知识点一页，"
                          "双向链接与反向链接在构建期解析。")
WIKI_INDEX_FOOT = "本页是课程实验档案的「Wiki」页，词条源文件在 content/wiki/。"
WIKI_PAGE_FOOT = "本页是课程实验档案 Wiki 的一个词条，源文件在 content/wiki/%s.md。"

CODE_SPAN_RE = re.compile(r"`[^`]*`")
TAGS_SPLIT_RE = re.compile(r"[,，]")
INDEX_SLUG = "index"


# ---------------------------------------------------------------- 内容源

def read_wiki_page(path):
    """读一页 md：校验 frontmatter（title / updated / tags 必填且合法）与 ASCII slug。

    结构校验与 build_blog 的 read_post 同一套纪律：写错了就构建失败，不产出坏页面。
    CRLF 在读入时就归一成 LF，Windows 记事本改过的文件不会引入伪 diff。
    """
    raw = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    lines = raw.split("\n")
    if not lines or lines[0].strip() != "---":
        fail("%s：文件必须以 frontmatter（首行 ---）开头" % rel(path))

    end = None
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            end = i
            break
    if end is None:
        fail("%s：frontmatter 缺少收尾的 ---" % rel(path))

    meta = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        if ":" not in line:
            fail("%s：frontmatter 行没有冒号：%r" % (rel(path), line))
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip()

    for key in ("title", "updated", "tags"):
        if not meta.get(key):
            fail("%s：frontmatter 缺少 %s" % (rel(path), key))
    unknown = sorted(set(meta) - {"title", "updated", "tags"})
    if unknown:
        fail("%s：frontmatter 有未支持的字段 %s（只支持 title / updated / tags）"
             % (rel(path), "、".join(unknown)))
    if not DATE_RE.match(meta["updated"]):
        fail("%s：updated 必须写成 YYYY-MM-DD，现在是 %r" % (rel(path), meta["updated"]))
    try:
        date.fromisoformat(meta["updated"])
    except ValueError:
        fail("%s：updated 不是合法日期：%s" % (rel(path), meta["updated"]))

    tags = [t.strip() for t in TAGS_SPLIT_RE.split(meta["tags"]) if t.strip()]
    if not tags:
        fail("%s：tags 不能为空（逗号分隔，如 `tags: agent, 协作`）" % rel(path))

    slug = path.stem
    if not SLUG_RE.match(slug):
        fail("%s：文件名必须用 ASCII 字母/数字与 . - _（slug 直接成为 URL，不用中文名）" % rel(path))

    return {
        "slug": slug,
        "title": meta["title"],
        "updated": meta["updated"],
        "tags": tags,
        "path": rel(path),
        "body": lines[end + 1:],
    }


def sort_pages(pages):
    """就地排序：updated 倒序；同一天多篇按 slug 升序（稳定，输出可复现）。"""
    pages.sort(key=lambda p: p["slug"])
    pages.sort(key=lambda p: p["updated"], reverse=True)
    return pages


def load_pages():
    """读入 content/wiki/*.md（跳过规则文件 README.md），返回排好序的页面列表。"""
    if not WIKI_CONTENT.is_dir():
        fail("找不到内容源目录 content/wiki/（规则与词条都写在这里）")
    pages = [read_wiki_page(p) for p in sorted(WIKI_CONTENT.glob("*.md"))
             if p.name != WIKI_RULES]
    if not any(p["slug"] == INDEX_SLUG for p in pages):
        fail("content/wiki/ 必须有 index.md：它是 Wiki 栏目页（导航「Wiki」的落点）")
    return sort_pages(pages)


# ---------------------------------------------------------------- [[双向链接]]

def outgoing_links(page, registry):
    """返回本页正文里 [[链接]] 指向的 slug 列表（去代码段后检查，死链即失败）。"""
    stripped = CODE_SPAN_RE.sub("", "\n".join(page["body"]))
    targets = []
    for m in WIKI_RE.finditer(stripped):
        target = m.group(1).strip()
        if not target:
            fail("%s：[[…]] 的链接目标是空的" % page["path"])
        if target not in registry:
            fail("%s：[[%s]] 指向不存在的页面——content/wiki/ 下没有 %s.md，死链即构建失败"
                 % (page["path"], target, target))
        targets.append(target)
    leftover = WIKI_RE.sub("", stripped)
    if "[[" in leftover or "]]" in leftover:
        fail("%s：出现不成对的 [[ 或 ]]——Wiki 链接的合法写法是 [[slug]] 或 [[slug|别名]]；"
             "想原样提及这种语法请放进行内代码" % page["path"])
    return targets


def make_resolver(page, registry):
    """给 parse_blocks 的 wiki 回调：把 [[slug]] 解析成同目录词条页的内部链接。

    outgoing_links 已预检过目标存在，这里的不存在分支只是双保险。
    """
    def resolve(target, alias):
        if target not in registry:
            fail("%s：[[%s]] 指向不存在的页面" % (page["path"], target))
        label = alias if alias is not None else registry[target]["title"]
        return '<a href="%s.html">%s</a>' % (html.escape(target, quote=True),
                                             html.escape(label, quote=False))
    return resolve


def compute_backlinks(pages):
    """slug -> 反向链接页列表（正文 [[链接]] 指向本页的其它页面）。

    pages 已按 updated 倒序 / slug 升序排好，按序过滤即得确定顺序；
    同一页重复引用只列一次；本页指向自身的链接不进反向链接。
    """
    forward = {}
    for page in pages:
        for target in page["links"]:
            if target != page["slug"]:
                forward.setdefault(target, set()).add(page["slug"])
    backlinks = {}
    for target, sources in forward.items():
        backlinks[target] = [p for p in pages if p["slug"] in sources]
    return backlinks


# ---------------------------------------------------------------- 页面组装

def ledger_rows(pages):
    """一组账本行（.post-list 同一张账本：左列等宽 updated，右列宋体标题链接）。

    缩进与 listing_section 同一档（2 空格基准，再由调用方 indent 到位）；
    Wiki 页面都在 public/wiki/ 一层，页间链接同目录直写 <slug>.html。
    """
    lines = ['  <ul class="post-list">']
    for p in pages:
        lines.append('    <li class="post-row">')
        lines.append('      <time class="post-date" datetime="%s">%s</time>' % (p["updated"], p["updated"]))
        lines.append('      <div class="post-item">')
        lines.append('        <h3><a href="%s.html">%s</a></h3>'
                     % (html.escape(p["slug"], quote=True),
                        html.escape(p["title"], quote=False)))
        lines.append('      </div>')
        lines.append('    </li>')
    lines.append('  </ul>')
    return lines


def listing_section(pages):
    """索引页正文之后的「页面清单」：每个 Wiki 页的标题、updated、tags，脚本生成。"""
    lines = ['<section class="sec" aria-labelledby="t-pages">',
             '  <h2 id="t-pages">页面清单</h2>']
    lines.append('  <ul class="post-list">')
    for p in pages:
        lines.append('    <li class="post-row">')
        lines.append('      <time class="post-date" datetime="%s">%s</time>' % (p["updated"], p["updated"]))
        lines.append('      <div class="post-item">')
        lines.append('        <h3><a href="%s.html">%s</a></h3>'
                     % (html.escape(p["slug"], quote=True), html.escape(p["title"], quote=False)))
        lines.append('        <p>标签：%s</p>' % html.escape("、".join(p["tags"]), quote=False))
        lines.append('      </div>')
        lines.append('    </li>')
    lines.append('  </ul>')
    lines.append('</section>')
    return '\n'.join(indent(lines, 6))


def backlinks_section(page, backlinks):
    """页底「链接到此页的页面」；没有任何页面引用本页时返回 None（不显示该节）。"""
    sources = backlinks.get(page["slug"])
    if not sources:
        return None
    lines = ['<section class="sec" aria-labelledby="t-back">',
             '  <h2 id="t-back">链接到此页的页面</h2>']
    lines += ledger_rows(sources)
    lines.append('</section>')
    return '\n'.join(indent(lines, 6))


def wiki_head(page):
    return '\n'.join(['<div class="post-head">',
                      '        <h1>%s</h1>' % html.escape(page["title"], quote=False),
                      '        <time class="post-date" datetime="%s">更新于 %s</time>'
                      % (page["updated"], page["updated"]),
                      '        <span class="wiki-meta">标签：%s</span>'
                      % html.escape("、".join(page["tags"]), quote=False),
                      '      </div>'])


def render_wiki_page(skel, page, pages, backlinks):
    """一页 Wiki → 完整 HTML。index 是栏目页（aria-current 指自身），词条页不设当前项。"""
    is_index = page["slug"] == INDEX_SLUG
    body = article_body(page["blocks"])
    parts = [body]
    if is_index:
        parts.append(listing_section(pages))
    back = backlinks_section(page, backlinks)
    if back:
        parts.append(back)
    main_block = '\n\n'.join(parts)
    head = folio_head(page["title"]) if is_index else wiki_head(page)
    description = WIKI_INDEX_DESCRIPTION if is_index else \
        "张易孝实验档案 Wiki 词条：《%s》。" % page["title"]
    foot = WIKI_INDEX_FOOT if is_index else WIKI_PAGE_FOOT % page["slug"]
    # current_rel 与骨架导航的 href 同口径：带上 1 层深的 ../ 前缀（与 build_blog 一致）。
    current_rel = "../wiki/index.html" if is_index else None
    return render_page(skel, "%s · %s" % (page["title"], SITE_NAME), description,
                       "../", head, main_block, foot, current_rel, MARKER)


# ---------------------------------------------------------------- 主流程

def main():
    if not SKELETON.is_file():
        fail("找不到骨架页面 public/index.html")
    skel = SKELETON.read_text(encoding="utf-8")

    pages = load_pages()
    registry = {p["slug"]: p for p in pages}

    # 第一遍：死链预检（指出是哪个文件里的哪个链接）+ 记录正向链接。
    for page in pages:
        page["links"] = outgoing_links(page, registry)
    # 第二遍：解析正文（[[链接]] 换成站内锚点；行内代码不参与）。
    for page in pages:
        page["blocks"] = parse_blocks(page["body"], page["title"], make_resolver(page, registry))

    backlinks = compute_backlinks(pages)

    outputs = {}
    for page in pages:
        out = WIKI_OUT / ("%s.html" % page["slug"])
        outputs[out] = render_wiki_page(skel, page, pages, backlinks)

    written, unchanged = [], []
    for path, text in sorted(outputs.items(), key=lambda kv: rel(kv[0])):
        (written if write_if_changed(path, text) else unchanged).append(rel(path))

    removed = []
    for stale in sorted(WIKI_OUT.glob("*.html")):
        if stale not in outputs and MARKER in stale.read_text(encoding="utf-8"):
            stale.unlink()
            removed.append(rel(stale))

    print("构建完成：%d 个 Wiki 页面" % len(pages))
    for path in written:
        print("  写入 %s" % path)
    for path in unchanged:
        print("  未变化 %s" % path)
    for path in removed:
        print("  清理 %s（源文件已不在 content/wiki/）" % path)
    for page in pages:
        src = backlinks.get(page["slug"]) or []
        print("  反向链接 %s ← %s" % (page["slug"],
              "、".join(s["slug"] for s in src) if src else "（无页面引用，不显示该节）"))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BuildError as exc:
        print("构建失败：%s" % exc)
        sys.exit(1)
