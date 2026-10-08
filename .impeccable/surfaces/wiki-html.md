---
version: 1
slug: "wiki-html"
primary_target: "public/wiki/index.html"
related_targets: ["public/index.html", "public/papers/index.html"]
---

# Surface brief: public/wiki/index.html —— Wiki（诚实占位）

## Scope & visitor mode

整站五个页面之一：无 JS、无外部资源、共用 `public/styles.css`。访客模式 Read，**本轮没有词条**——本页说明词条目录会在课程第几步建立。

## Audience, job, action, proof, constraints

- 受众：课程任课老师/助教（核对是否诚实占位）、同学、本人回访。
- 任务：看出本页尚未启用、以及填充时点（Step 8：建立 Wiki 知识库）。
- 证明：页面写明「一个词条一条记录、可检索可回溯，用同一套档案语法登记」。
- 约束：不建空词条骨架、不放搜索框等假控件；与其余四页共用报头带与页脚。

## Chosen direction & memorable moment

沿用「实验档案」世界：本页是一册还没编目的索引——页名 `.folio` + 栏目「本页内容」+ 一条标注「Step 8 接入」的待办条目。
难忘点：把「不放条目骨架冒充内容」写进页面，空得理直气壮。

## Direction contract

THESIS: 索引页的秩序感来自真实条目；没有条目时，如实说明比装满骨架更诚实。

OWN-WORLD: 与首页同一个世界；本页零新样式、零新颜色、零动效。

STORY: 访客点「Wiki」进来，看到页名、说明与一条待办，知道知识库会在 Step 8 建立，届时词条按同一套档案语法逐条登记。

FIRST VIEWPORT: 报头带 + `.folio` 页名「Wiki」+「本页内容」栏目题 + 说明句 + 一条待办条目，一屏读完。

FORM: 复用 `.sec` / `.intro` / `.ledger` / `.dir` / `.tag`，不新增任何 CSS 类。

FINISH: 与整站同批完成 finish review、DESIGN.md 与 design.json。

## Signature interaction

无。

## Unresolved decisions

- 词条的命名规则、目录结构与是否分页待 Step 8 确定。
