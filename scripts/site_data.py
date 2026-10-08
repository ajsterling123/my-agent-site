#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""site_data.py —— 站点内容源、路径与 URL 规则的唯一实现。

build_blog.py（生成 public/blog/index.html 与 public/posts/<slug>.html）与
build_feed.py（生成 public/feed.xml）都 import 本模块，因此下面这些规则全站只有一份：

  slug 命名规则、frontmatter 解析与校验、文章页在 public/ 下的相对路径、
  文章页的绝对 URL、文章排序（日期倒序 + 同日按 slug 稳定）。

站点基址（GitHub Pages 的项目子路径）只在 SITE_BASE_URL 出现一次，其余地址由它拼出；
改目录结构、改 slug 规则、改排序，都只改这一个文件。
"""

import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
CONTENT = ROOT / "content" / "posts"
POSTS_OUT = PUBLIC / "posts"
BLOG_OUT = PUBLIC / "blog" / "index.html"
FEED_OUT = PUBLIC / "feed.xml"
SKELETON = PUBLIC / "index.html"

SITE_NAME = "张易孝实验档案"
SITE_BASE_URL = "https://ajsterling123.github.io/my-agent-site/"

FRONTMATTER_KEYS = ("title", "date", "description")
SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class BuildError(Exception):
    """内容源写错了：构建应当失败，而不是产出一份坏页面或坏订阅源。"""


def fail(msg):
    raise BuildError(msg)


def rel(path):
    return Path(path).relative_to(ROOT).as_posix()


# ---------------------------------------------------------------- 地址

def post_rel(slug):
    """文章页相对 public/ 的路径。"""
    return "posts/%s.html" % slug


def post_url(slug):
    """文章页的绝对地址（RSS 的 link / guid 与将来任何对外引用都用它）。"""
    return SITE_BASE_URL + post_rel(slug)


def home_url():
    return SITE_BASE_URL


def blog_url():
    return SITE_BASE_URL + "blog/index.html"


def feed_url():
    return SITE_BASE_URL + "feed.xml"


# ---------------------------------------------------------------- 内容源

def read_post(path):
    """读一篇 md：返回 slug / title / date / description / body（正文行列表）。

    校验首行必须是 frontmatter（`---`）、必须有收尾的 `---`、三个字段齐全且非空、
    date 是合法的 YYYY-MM-DD、文件名（即 slug）是 ASCII。正文不在这里解析——
    Markdown 只有 build_blog.py 需要，RSS 只用 frontmatter。
    """
    raw = path.read_text(encoding="utf-8-sig")
    lines = raw.split("\n")
    if not lines or lines[0].strip() != "---":
        fail("%s：文件必须以 frontmatter（首行 ---）开头" % path.name)

    end = None
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            end = i
            break
    if end is None:
        fail("%s：frontmatter 缺少收尾的 ---" % path.name)

    meta = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        if ":" not in line:
            fail("%s：frontmatter 行没有冒号：%r" % (path.name, line))
        key, value = line.split(":", 1)
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
        "path": path,
        "body": lines[end + 1:],
    }


def sort_posts(posts):
    """就地排序：日期倒序；同一天多篇按 slug 升序（稳定，输出可复现）。"""
    posts.sort(key=lambda p: p["slug"])
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def load_posts():
    """按 slug 升序读入 content/posts/*.md，返回排好序的文章列表。"""
    return sort_posts([read_post(p) for p in sorted(CONTENT.glob("*.md"))])


# ---------------------------------------------------------------- 落盘

def write_if_changed(path, text):
    """写文件；内容与现值一致时不落盘（连 mtime 都不动），返回是否真的写了。

    这是两个构建脚本幂等的基础：同一批输入重复运行，第二次一个字节都不写。
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    data = text.encode("utf-8")
    if path.is_file() and path.read_bytes() == data:
        return False
    path.write_bytes(data)
    return True
