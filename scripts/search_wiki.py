#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""content/wiki/ 的离线检索器（Step 9：Wiki 检索 + 基于资料的问答）：

用法（仓库根运行）：
  python scripts/search_wiki.py "<查询词>"              默认显示 5 条
  python scripts/search_wiki.py "<查询词>" --top 3      指定显示条数
  python scripts/search_wiki.py "<查询词>" --include-rules
                                                        把规则文件 README.md 也纳入检索
  python scripts/search_wiki.py "<查询词>" --json       机器可读输出（json.loads 可解析）

离线、只读、确定性，纯标准库，不写任何文件：同一输入重复运行输出逐字节一致，
跑完 git status 无变化。README.md 是规则文件，默认排除（--include-rules 覆盖）。

中文检索不引入 jieba 之类的外部分词库——查询先分词：ASCII 词按空白/标点切；
CJK 连续段切成 2-gram，同时把整段保留为一个高权重词（权重 ×2，整段原文命中
比零散 2-gram 更能说明问题）。

计分：标题命中 ×3、tags 命中 ×2、正文命中 ×1，命中次数参与累加，
词权重再乘上去；同值排序稳定（得分降序 → slug 升序）。
输出 top N（默认 5）：序号、文件名、页面标题、得分、命中片段——原文摘录、
含前后约 40 字上下文、压缩空白。无命中时输出「0 个结果」并正常退出（退出码 0）。

frontmatter 解析与 build_wiki.py 同一套字段（title / updated / tags）；本脚本只读，
词条写错了由构建脚本拒绝，这里宽容读取：没有 frontmatter 的文件（如规则文件）
标题取首个 `# ` 标题、tags 记空。
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_data import WIKI_CONTENT, WIKI_RULES

TOP_DEFAULT = 5
CONTEXT = 40  # 命中片段前后各取约 40 字上下文
WHITESPACE_RE = re.compile(r"\s+")
CJK_RANGES = (
    (0x3400, 0x4DBF),  # CJK 统一表意文字扩展 A
    (0x4E00, 0x9FFF),  # CJK 统一表意文字基本区
    (0xF900, 0xFAFF),  # CJK 兼容表意文字
)
FIELD_WEIGHTS = (("title", 3), ("tags", 2), ("body", 1))


def is_cjk(ch):
    cp = ord(ch)
    return any(lo <= cp <= hi for lo, hi in CJK_RANGES)


def segments(query):
    """把查询切成连续段：[(文本, "cjk" | "ascii")]，其余字符是分隔符。"""
    out = []
    run, kind = "", None
    for ch in query:
        if is_cjk(ch):
            seg = "cjk"
        elif ch.isascii() and ch.isalnum():
            seg = "ascii"
        else:
            seg = None
        if seg is None or (kind is not None and seg != kind):
            if run:
                out.append((run, kind))
            run, kind = "", None
        if seg is not None:
            run, kind = run + (ch.lower() if seg == "ascii" else ch), seg
    if run:
        out.append((run, kind))
    return out


def tokenize(query):
    """查询分词：返回按词形升序的 [(词, 权重)]。

    ASCII 词按空白/标点切（权重 1）；CJK 连续段切成 2-gram（权重 1），
    整段另保留为一个高权重词（权重 2）。段长为 1 的 CJK 只留单字。
    同形词只记一次、取更高权重。先排序再返回，保证输出可复现。
    """
    terms = {}
    for seg, kind in segments(query):
        if kind == "cjk":
            if len(seg) == 1:
                terms[seg] = max(terms.get(seg, 0), 1)
                continue
            for i in range(len(seg) - 1):
                terms[seg[i:i + 2]] = max(terms.get(seg[i:i + 2], 0), 1)
            terms[seg] = max(terms.get(seg, 0), 2)
        else:
            terms[seg] = max(terms.get(seg, 0), 1)
    return sorted(terms.items())


def read_page(path):
    """读一页 md（宽容）：返回 title / tags / body 文本。

    与 build_wiki.py 同一套 frontmatter 字段；缺 frontmatter 或字段的文件
    （如规则文件）照常读入——检索器只读，不负责校验词条结构。
    """
    raw = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    lines = raw.split("\n")
    title, tags_text, body_start = None, "", 0
    if lines and lines[0].strip() == "---":
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                body_start = i + 1
                break
        for line in lines[1:body_start - 1]:
            if ":" in line:
                key, value = line.split(":", 1)
                if key.strip() == "title":
                    title = value.strip()
                elif key.strip() == "tags":
                    tags_text = value.strip()
    body = "\n".join(lines[body_start:])
    if not title:
        heading = next((l.lstrip("# ").strip() for l in lines if l.startswith("# ")), None)
        title = heading or path.stem
    return {
        "slug": path.stem,
        "file": path.name,
        "title": title,
        "tags": tags_text,
        "body": body,
        "path": path,
    }


def load_pages(include_rules):
    """读入 content/wiki/*.md；规则文件默认排除。"""
    if not WIKI_CONTENT.is_dir():
        print("找不到内容源目录 content/wiki/（规则与词条都写在这里）", file=sys.stderr)
        return None
    names = sorted(p.name for p in WIKI_CONTENT.glob("*.md"))
    if not include_rules:
        names = [n for n in names if n != WIKI_RULES]
    return [read_page(WIKI_CONTENT / n) for n in names]


def compress(text):
    """压缩空白：换行与连续空白归一成单个空格（片段允许这样压缩）。"""
    return WHITESPACE_RE.sub(" ", text).strip()


def excerpt(text, pos, term):
    """命中片段：term 在 text 的 pos 处，前后各取约 CONTEXT 字，截断处补省略号。"""
    start = max(0, pos - CONTEXT)
    end = min(len(text), pos + len(term) + CONTEXT)
    left = "…" if start > 0 else ""
    right = "…" if end < len(text) else ""
    return "%s%s%s" % (left, text[start:end], right)


def search(query, pages):
    """检索并返回确定顺序的结果列表（已含 rank）。"""
    tokens = tokenize(query)
    if not tokens:
        return []
    results = []
    for page in pages:
        fields = {"title": compress(page["title"]),
                  "tags": compress(page["tags"]),
                  "body": compress(page["body"])}
        lowered = {k: v.lower() for k, v in fields.items()}
        score, hit_fields = 0, set()
        for term, weight in tokens:
            for fname, fw in FIELD_WEIGHTS:
                count = lowered[fname].count(term.lower())
                if count:
                    score += count * fw * weight
                    hit_fields.add(fname)
        if not score:
            continue
        # 片段取正文中最早命中的词（同位置取更长的词，信息量更大）；
        # 正文没命中（只中了标题/tags）时片段退回标题或 tags 本身。
        best = None
        for term, _ in tokens:
            pos = lowered["body"].find(term.lower())
            if pos == -1:
                continue
            if best is None or pos < best[0] or (pos == best[0] and len(term) > len(best[1])):
                best = (pos, term)
        if best is not None:
            snippet = excerpt(fields["body"], best[0], best[1])
        elif "title" in hit_fields:
            snippet = fields["title"]
        else:
            snippet = fields["tags"]
        results.append({"file": page["file"], "slug": page["slug"],
                        "title": page["title"], "score": score, "snippet": snippet})
    # 同值排序稳定：得分降序 → slug 升序。
    results.sort(key=lambda r: r["slug"])
    results.sort(key=lambda r: r["score"], reverse=True)
    for rank, r in enumerate(results, 1):
        r["rank"] = rank
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="content/wiki/ 的离线检索器（只读、确定性、纯标准库，不写任何文件）")
    parser.add_argument("query", help="查询词（ASCII 词按空白/标点切；CJK 段切 2-gram + 整段高权重词）")
    parser.add_argument("--top", type=int, default=TOP_DEFAULT,
                        help="显示前几条结果（默认 %d）" % TOP_DEFAULT)
    parser.add_argument("--include-rules", action="store_true",
                        help="把规则文件 README.md 也纳入检索（默认排除）")
    parser.add_argument("--json", action="store_true", help="输出机器可读的 JSON")
    args = parser.parse_args(argv)
    if args.top < 1:
        parser.error("--top 必须是正整数")

    pages = load_pages(args.include_rules)
    if pages is None:
        return 1
    results = search(args.query, pages)[:args.top]

    if args.json:
        payload = {"query": args.query, "top": args.top,
                   "matched": len(results), "results": results}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if not results:
        print("0 个结果")
        return 0
    print("共 %d 个结果（得分降序，同分按文件名升序）" % len(results))
    for r in results:
        print("%d. %s    %s    得分 %d" % (r["rank"], r["file"], r["title"], r["score"]))
        print("   片段：%s" % r["snippet"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
