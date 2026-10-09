# 中文主题 → arXiv 查询词映射

`SKILL.md` 工作流的第 1 步查这张表。查询词直接用 `--query "<表里的值>"` 传给
`scripts/collect_papers.py`；表里没有的主题，选一个 arXiv 上真有东西的英文检索词
补进本表再用——**arXiv 的语料是英文论文，不要用中文词直接查**（查不到不等于
没有论文，只是词不对）。查询词已在本机对 `export.arxiv.org` 实测可命中（2026-10-09）。

| 中文主题 | arXiv 查询词 | 备注 |
|---|---|---|
| AI Agent（**默认**） | `cat:cs.AI AND (all:"LLM agent" OR all:"AI agent" OR all:"autonomous agent")` | 本站声明方向之一；课程主线 |
| 数据警务 | `(all:"predictive policing" OR all:"crime prediction" OR all:"crime data mining" OR all:"public safety analytics")` | 本站声明方向之二；必须用这些英文检索词，命中量本来就不大，limit 收小（5–10）即可 |
| 知识管理 | `(all:"knowledge management" OR all:"personal knowledge management" OR all:"knowledge organization")` | 本站声明方向之三 |
| 软件工程 | `cat:cs.SE` | 直接按分类取最近提交 |
| 人机协作 | `(all:"human-AI collaboration" OR all:"human-AI interaction" OR cat:cs.HC)` | 前两个短语是近几年的说法，兜底给 HCI 分类 |

## 写法注意

- 布尔算子用大写 `AND` / `OR`，短语加双引号，`all:` 查全部字段、`ti:` 只查标题。
  混合 AND/OR 时**必须用括号分组**，否则优先级会和预期不符。
- 结果按 `submittedDate` 倒序返回（抓取脚本固定带 `sortBy=submittedDate&sortOrder=descending`），
  所以「最近的 N 篇」= 前 N 条；日期范围用 `--since` 在本地过滤，API 端不支持。
- 连续抓取多个主题时，抓取脚本自带 ≥3 秒的请求间隔（arXiv 礼貌要求），
  不需要在两次运行之间手动等待。
