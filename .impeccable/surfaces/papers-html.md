---
version: 1
slug: "papers-html"
primary_target: "public/papers/index.html"
related_targets: ["public/index.html", "public/blog/index.html"]
---

# Surface brief: public/papers/index.html —— Research Papers（诚实占位）

## Scope & visitor mode

整站五个页面之一：无 JS、无外部资源、共用 `public/styles.css`。访客模式 Read，**本轮没有论文记录**——本页说明它会在课程第几步被填充、以及登记时会写哪些字段。

## Audience, job, action, proof, constraints

- 受众：课程任课老师/助教（核对是否诚实占位）、同学、本人回访。
- 任务：看出本页尚未启用、以及填充时点（Step 7：arXiv 论文检索 Skill）。
- 证明：页面写明「只登记本人实际读过并核对过出处的论文」，把「不写什么」也讲清楚。
- 约束：不编造论文条目、不放论文标题骨架、不出现外部链接；与其余四页共用报头带与页脚。

## Chosen direction & memorable moment

沿用「实验档案」世界：本页是等着登记引文的账本——页名 `.folio` + 栏目「本页内容」+ 一条标注「Step 7 接入」的待办条目，并写明登记字段（标题 / 作者 / 年份 / 原文链接）。
难忘点：宁可留空也不放未核对出处的条目——「不编造引用」被写进了页面本身。

## Direction contract

THESIS: 论文栏的价值在出处可核对；宁缺毋滥，空着也是登记状态。

OWN-WORLD: 与首页同一个世界；本页零新样式、零新颜色、零动效、零外部资源。

STORY: 访客点「Research Papers」进来，看到页名、说明与一条待办，知道本页会在 Step 7 接入 arXiv 检索后开始登记，且只登记核对过出处的条目。

FIRST VIEWPORT: 报头带 + `.folio` 页名「Research Papers」+「本页内容」栏目题 + 说明句 + 一条待办条目，一屏读完。

FORM: 复用 `.sec` / `.intro` / `.ledger` / `.dir` / `.tag`，不新增任何 CSS 类。

FINISH: 与整站同批完成 finish review、DESIGN.md 与 design.json。

## Signature interaction

无。

## Unresolved decisions

- Step 7 的检索范围、论文数量与呈现字段顺序待该 Step 确定；本页只承诺字段名。
