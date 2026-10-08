#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""机械校验 public/feed.xml：RSS 2.0 Schema、字段齐全、绝对地址、RFC 822 与排序。

用法（仓库根运行）：python tools/check_feed.py
退出码 0 = 全部通过，1 = 有失败项。

期望值不写死：文章清单、slug、文章页路径与绝对 URL 都由 scripts/site_data.py 从
content/posts/*.md 现算（与两个构建脚本同一份规则），所以校验脚本不会和生成脚本各说各话。

最后一关是转义负向测试：临时在 content/posts/ 造一篇标题与摘要含 & < > 的文章 → 重新构建
feed.xml → 用 xml.etree 解析回来并断言标题/摘要原样还原（证明转义无损、且没有用 CDATA）→
无论成败都在 finally 里删掉临时文件并重新构建，把 feed.xml 恢复成原字节。
"""

import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from site_data import (CONTENT, FEED_OUT, POSTS_OUT, home_url, load_posts, post_url, rel)

BUILD_FEED = ROOT / "scripts" / "build_feed.py"

XML_DECL = '<?xml version="1.0" encoding="UTF-8"?>'
BOM = b"\xef\xbb\xbf"
CDATA = b"<![CDATA["

REQUIRED_CHANNEL = ("title", "link", "description", "language", "lastBuildDate")
REQUIRED_ITEM = ("title", "link", "guid", "pubDate", "description")

WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
RFC822_RE = re.compile(r"^([A-Z][a-z]{2}), (\d{2}) ([A-Z][a-z]{2}) (\d{4}) "
                       r"(\d{2}):(\d{2}):(\d{2}) ([+-]\d{4})$")

# 负向测试用的临时文章：日期取得比现有文章都早，所以它只考转义，不影响 lastBuildDate。
PROBE_NAME = "zz-feed-escape-probe.md"
PROBE_DATE = "2026-01-01"
PROBE_TITLE = "转义探针：A & B < C > D"
PROBE_DESCRIPTION = "摘要里的 & < > 也要原样还原：5 < 6 & 7 > 4。"

failures = []
notes = []


def fail(msg):
    failures.append(msg)


def note(msg):
    notes.append(msg)


def run_build_feed():
    """跑一次 build_feed.py；失败即判校验失败（负向测试也要能重新构建）。"""
    done = subprocess.run([sys.executable, str(BUILD_FEED)],
                          capture_output=True, text=True, encoding="utf-8")
    if done.returncode != 0:
        fail("重新构建 feed 失败（退出码 %d）：%s" % (done.returncode, (done.stdout or "").strip()))
        return False
    return True


def parse_feed(data, where):
    try:
        return ET.fromstring(data)
    except ET.ParseError as exc:
        fail("%s 解析失败：%s" % (where, exc))
        return None


def one_child(el, tag, where):
    """取恰好一个、且非空的子元素文本；缺失/重复/空都算失败。"""
    found = el.findall(tag)
    if len(found) != 1:
        fail("%s 的 <%s> 出现 %d 次，应为 1 次（item 与 channel 的必填字段一个都不能少、也不能重复）"
             % (where, tag, len(found)))
        return None
    text = (found[0].text or "").strip()
    if not text:
        fail("%s 的 <%s> 是空的" % (where, tag))
        return None
    return text


def check_rfc822(text, iso_date, where):
    """pubDate / lastBuildDate 必须是 RFC 822、英文星期与月份、时区 +0800、日期对得上。"""
    if text is None:
        return None
    m = RFC822_RE.match(text)
    if not m:
        fail("%s 不是 RFC 822 形式（星期与月份必须是英文缩写）：%r" % (where, text))
        return None
    try:
        dt = parsedate_to_datetime(text)
    except (TypeError, ValueError) as exc:
        fail("%s 用 parsedate_to_datetime 解析失败：%r（%s）" % (where, text, exc))
        return None
    if dt.tzinfo is None or dt.utcoffset() != timedelta(hours=8):
        fail("%s 的时区不是 +0800：%r" % (where, text))
        return None
    if dt.date().isoformat() != iso_date:
        fail("%s 的日期 %s 与 frontmatter 的 %s 不一致" % (where, dt.date().isoformat(), iso_date))
        return None
    if m.group(1) != WEEKDAYS[dt.weekday()]:
        fail("%s 的星期写错了：%r，%s 应是 %s（星期要用 email.utils.format_datetime 生成，"
             "中文 locale 下 strftime('%%a') 会输出「周三」）"
             % (where, m.group(1), iso_date, WEEKDAYS[dt.weekday()]))
        return None
    if m.group(3) != MONTHS[dt.month - 1]:
        fail("%s 的月份不是英文缩写：%r" % (where, m.group(3)))
        return None
    if m.group(8) != "+0800":
        fail("%s 的时区写法应为 +0800：%r" % (where, m.group(8)))
        return None
    return dt


def check_feed_bytes(data):
    """文件层面的硬要求：无 BOM、XML 声明在首字节、UTF-8 可解码、不用 CDATA。"""
    if data.startswith(BOM):
        fail("feed.xml 带 BOM（必须以 <?xml 开头，UTF-8 不带 BOM）")
    if not data.startswith(XML_DECL.encode("ascii")):
        fail("feed.xml 的首行不是 %s，而是 %r" % (XML_DECL, data[:60]))
    if CDATA in data:
        fail("feed.xml 用了 CDATA；本 feed 要求用实体转义（&amp; &lt; &gt;）")
    try:
        data.decode("utf-8")
    except UnicodeDecodeError as exc:
        fail("feed.xml 不是合法 UTF-8：%s" % exc)
    if b"&amp;" not in data and b"&" in data:
        fail("feed.xml 里出现了没转义的裸 &")


def check_channel(root, posts):
    channels = root.findall("channel")
    if len(channels) != 1:
        fail("<rss> 下的 <channel> 有 %d 个，应为 1 个" % len(channels))
        return None
    channel = channels[0]
    values = {tag: one_child(channel, tag, "channel") for tag in REQUIRED_CHANNEL}
    if values["language"] is not None and values["language"] != "zh-CN":
        fail("channel 的 language 应为 zh-CN，实际 %r" % values["language"])
    if values["link"] is not None and values["link"] != home_url():
        fail("channel 的 link 应为站点首页 %s，实际 %s" % (home_url(), values["link"]))
    return channel, values


def check_items(channel, posts):
    """item 数量、五项字段、绝对地址、与文章页一一对应、顺序。"""
    items = channel.findall("item")
    if len(items) != len(posts):
        fail("item 有 %d 个，content/posts/ 里的文章有 %d 篇，两者必须相等"
             % (len(items), len(posts)))

    seen_slugs = []
    keys = []
    for i, item in enumerate(items):
        link = item.findtext("link") or ""
        slug = link.rsplit("/", 1)[-1][:-len(".html")] if link.endswith(".html") else link
        where = "item[%d]（%s）" % (i, slug or "链接无法识别")
        values = {tag: one_child(item, tag, where) for tag in REQUIRED_ITEM}

        expect = post_url(slug) if slug else None
        for tag in ("link", "guid"):
            value = values[tag]
            if value is None:
                continue
            if not value.startswith("https://"):
                fail("%s 的 <%s> 必须是 https:// 开头的绝对地址：%s" % (where, tag, value))
            elif expect is not None and value != expect:
                fail("%s 的 <%s> 与生成的文章页不一致：%s ≠ %s" % (where, tag, value, expect))
        page = POSTS_OUT / ("%s.html" % slug)
        if slug and not page.is_file():
            fail("%s 指向的文章页不存在：public/posts/%s.html" % (where, slug))
        if slug in seen_slugs:
            fail("%s 的文章重复登记了两次" % where)
        seen_slugs.append(slug)

        post = next((p for p in posts if p["slug"] == slug), None)
        if post is None:
            fail("%s 在 content/posts/ 里找不到对应的源文件（feed 里多出了文章）" % where)
            continue
        if values["title"] is not None and values["title"] != post["title"]:
            fail("%s 的 title 与 frontmatter 不一致（转义应当无损）：%r ≠ %r"
                 % (where, values["title"], post["title"]))
        if values["description"] is not None and values["description"] != post["description"]:
            fail("%s 的 description 与 frontmatter 不一致：%r ≠ %r"
                 % (where, values["description"], post["description"]))
        if values["guid"] is not None and values["link"] is not None \
                and values["guid"] != values["link"]:
            fail("%s 的 guid 没有指向文章自身页面：%s ≠ %s"
                 % (where, values["guid"], values["link"]))
        dt = check_rfc822(values["pubDate"], post["date"], where)
        if dt is not None:
            keys.append((dt.date().isoformat(), slug))

    # 顺序：日期倒序；同一天按 slug 升序（稳定，输出可复现）
    for (date_a, slug_a), (date_b, slug_b) in zip(keys, keys[1:]):
        if date_b > date_a:
            fail("item 顺序不是日期倒序：%s（%s）排在了 %s（%s）后面"
                 % (slug_b, date_b, slug_a, date_a))
        elif date_b == date_a and slug_b <= slug_a:
            fail("同一天的两篇顺序不稳定：%s 与 %s 未按 slug 升序" % (slug_a, slug_b))
    return items


def escape_probe(expected_items):
    """负向测试：标题与摘要含 & < > 的临时文章，feed 仍必须能被解析器解析且内容无损。"""
    probe = CONTENT / PROBE_NAME
    if probe.exists():
        fail("转义负向测试无法进行：%s 已存在（本脚本不覆盖已有内容，请改名）" % rel(probe))
        return
    before = FEED_OUT.read_bytes()
    before_latest = ET.fromstring(before).findtext("channel/lastBuildDate")
    try:
        probe.write_bytes((
            "---\n"
            "title: %s\n"
            "date: %s\n"
            "description: %s\n"
            "---\n\n"
            "# %s\n\n"
            "临时文件：由 tools/check_feed.py 的转义负向测试创建，验证完自己删掉。\n"
            % (PROBE_TITLE, PROBE_DATE, PROBE_DESCRIPTION, PROBE_TITLE)
        ).encode("utf-8"))
        if not run_build_feed():
            return
        data = FEED_OUT.read_bytes()
        check_feed_bytes(data)
        root = parse_feed(data, "含 & < > 的文章参与构建后的 feed.xml")
        if root is None:
            return
        items = root.findall("channel/item")
        if len(items) != expected_items + 1:
            fail("负向测试：item 应为 %d 个，实际 %d 个" % (expected_items + 1, len(items)))
        titles = [(it.findtext("title") or "") for it in items]
        if PROBE_TITLE not in titles:
            fail("负向测试：含 & < > 的标题没有原样还原，读回的是 %r" % titles)
        else:
            note("转义负向测试通过：%r 与摘要里的 & < > 原样还原，解析器未报错"
                 % PROBE_TITLE)
        latest = root.findtext("channel/lastBuildDate")
        if latest != before_latest:
            fail("负向测试：更早的文章不该改变 lastBuildDate（%s → %s）" % (before_latest, latest))
    finally:
        if probe.exists():
            probe.unlink()
        run_build_feed()

    after = FEED_OUT.read_bytes()
    if after != before:
        fail("负向测试后 feed.xml 没恢复成原字节（临时文章已删除，重新构建应当字节一致）")
    else:
        note("负向测试后现场已还原：%s 已删除，feed.xml 与测试前逐字节相同" % rel(probe))


def report():
    for msg in notes:
        print("  提示 %s" % msg)
    if failures:
        print("\n失败 %d 项：" % len(failures))
        for msg in failures:
            print("  ✗ %s" % msg)
        return 1
    return 0


def main():
    if not FEED_OUT.is_file():
        fail("缺少 %s：先跑 python scripts/build_feed.py" % rel(FEED_OUT))
        return report()
    if not CONTENT.is_dir() or not list(CONTENT.glob("*.md")):
        fail("content/posts/ 里一篇文章都没有，无法校验 item 数量与顺序")
        return report()

    posts = load_posts()
    data = FEED_OUT.read_bytes()
    check_feed_bytes(data)
    root = parse_feed(data, rel(FEED_OUT))
    if root is None:
        return report()
    if root.tag != "rss":
        fail("根元素是 <%s>，应为 <rss>" % root.tag)
        return report()
    if root.get("version") != "2.0":
        fail("根元素 <rss> 的 version 是 %r，应为 2.0" % root.get("version"))
        return report()

    channel_and_values = check_channel(root, posts)
    if channel_and_values is None:
        return report()
    channel, values = channel_and_values
    check_items(channel, posts)

    newest = posts[0]["date"]                        # posts 已按日期倒序
    if values["lastBuildDate"] is not None:
        dt = check_rfc822(values["lastBuildDate"], newest, "channel 的 lastBuildDate")
        if dt is not None:
            newest_item = channel.findall("item")[0].findtext("pubDate") \
                if channel.findall("item") else None
            if newest_item is not None and values["lastBuildDate"] != newest_item:
                fail("lastBuildDate（%s）应等于最新一篇的 pubDate（%s）——它必须从文章日期推导，"
                     "取当前时间会破坏幂等" % (values["lastBuildDate"], newest_item))

    escape_probe(len(posts))

    code = report()
    if code == 0:
        print("\n全部通过：%s 是合法 RSS 2.0，channel 五个字段齐全，%d 个 item 五项齐全、"
              "地址为绝对地址并与文章页一致、pubDate 均为 RFC 822（+0800）可解析、"
              "顺序为日期倒序（同日按 slug 稳定）；含 & < > 的负向测试通过且现场已还原。"
              % (rel(FEED_OUT), len(posts)))
    return code


if __name__ == "__main__":
    sys.exit(main())
