#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 content/posts/*.md 的 frontmatter 生成为 public/feed.xml（RSS 2.0）。

用法（仓库根运行）：python scripts/build_feed.py

部署后可订阅：https://ajsterling123.github.io/my-agent-site/feed.xml
（地址由 site_data.SITE_BASE_URL 拼出，全仓库只在那里写一次。）

规则：
- slug、文章页路径、文章页绝对 URL、排序（日期倒序 + 同日按 slug）全部来自
  scripts/site_data.py，与 build_blog.py 共用一份实现——RSS 的 link 与博客列表的链接
  因此不可能指向不同的地址。
- pubDate / lastBuildDate 用 email.utils.format_datetime 生成 RFC 822：它用硬编码的
  英文星期与月份表，不受中文 locale 影响（strftime('%a') 在这里会输出「周三」，阅读器解析失败）。
  时区固定 +0800；文章只有日期没有时刻，时刻统一取当天 00:00:00。
- 幂等：lastBuildDate 取最新一篇文章的日期，不用当前时间——否则每次构建都产生 diff。
- 文本节点用 html.escape 转义 & < >（不用 CDATA）；UTF-8 写出、不带 BOM。

运行日志（Step 10 起）：每个阶段（读取输入 / 渲染 / 校验 / 落盘 / 失败）至少一条
JSONL 事件走 scripts/runlog.py，追加进 logs/build.log 并同步打到 stdout；run_id 在
最后一行打印。校验 = 把渲染出的 XML 解析回来，item 数与文章数对账。
"""

import html
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_data import (FEED_OUT, SITE_NAME, BuildError, feed_url, home_url, load_posts, post_url,
                       rel, write_if_changed)
from runlog import wrap_main

CHANNEL_TITLE = "%s · 博客" % SITE_NAME
CHANNEL_DESCRIPTION = ("张易孝（江苏警官学院 · 数据警务技术）的课程实验档案：博客栏文章登记，"
                       "按文章日期倒序。")
CHANNEL_LANGUAGE = "zh-CN"

# 文章日期只有年月日；站点在中国，固定 +0800（不用本机时区，构建机在 UTC 也一样）。
FEED_TZ = timezone(timedelta(hours=8))

# 一篇文章都没有时的 lastBuildDate 兜底：仍必须是确定值，不能是「当前时间」。
EMPTY_FEED_DATE = "1970-01-01"

MARKER = "<!-- 由 scripts/build_feed.py 生成：改内容请改 content/posts/*.md -->"


def esc(text):
    """文本节点转义 & < > 三种字符（引号在文本节点里无需转义，保留中文原样）。"""
    return html.escape(text, quote=False)


def rfc822(iso_date):
    """YYYY-MM-DD → RFC 822，例如 Wed, 02 Sep 2026 00:00:00 +0800。"""
    return format_datetime(datetime.fromisoformat(iso_date).replace(tzinfo=FEED_TZ))


def render_item(post):
    url = post_url(post["slug"])
    return "\n".join([
        "    <item>",
        "      <title>%s</title>" % esc(post["title"]),
        "      <link>%s</link>" % esc(url),
        '      <guid isPermaLink="true">%s</guid>' % esc(url),
        "      <pubDate>%s</pubDate>" % rfc822(post["date"]),
        "      <description>%s</description>" % esc(post["description"]),
        "    </item>",
    ])


def render_feed(posts):
    """posts 已按日期倒序（site_data 排的），item 顺序即 feed 顺序。"""
    latest = posts[0]["date"] if posts else EMPTY_FEED_DATE
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        MARKER,
        '<rss version="2.0">',
        "  <channel>",
        "    <title>%s</title>" % esc(CHANNEL_TITLE),
        "    <link>%s</link>" % esc(home_url()),
        "    <description>%s</description>" % esc(CHANNEL_DESCRIPTION),
        "    <language>%s</language>" % CHANNEL_LANGUAGE,
        "    <lastBuildDate>%s</lastBuildDate>" % rfc822(latest),
    ]
    lines += [render_item(p) for p in posts]
    lines += ["  </channel>", "</rss>", ""]
    return "\n".join(lines)


def main(log, argv=None):
    posts = load_posts()
    log.event("read_input", input={"文章": len(posts)})
    xml = render_feed(posts)

    # 校验：渲染出的 XML 必须能解析回来，且 item 数与文章数对账——坏 feed 不落盘。
    root = ET.fromstring(xml)
    items = root.findall("./channel/item")
    if len(items) != len(posts):
        fail("feed 里解析出 %d 个 item，与文章数 %d 不一致" % (len(items), len(posts)))
    log.event("verify", input={"item": len(items)})

    wrote = write_if_changed(FEED_OUT, xml)
    log.event("write_outputs", input={"写入": int(wrote)})
    print("构建完成：%d 篇文章 → %s" % (len(posts), rel(FEED_OUT)))
    print("  %s" % ("写入" if wrote else "未变化"))
    print("  lastBuildDate %s（取自最新一篇的日期，不取当前时间）" % rfc822(posts[0]["date"] if posts else EMPTY_FEED_DATE))
    print("  订阅地址 %s" % feed_url())
    return 0


if __name__ == "__main__":
    try:
        sys.exit(wrap_main("build_feed", main))
    except BuildError as exc:
        print("构建失败：%s" % exc)
        sys.exit(1)
