---
version: 1
slug: "blog-html"
primary_target: "public/blog/index.html"
related_targets: ["public/index.html", "public/about/index.html"]
---

# Surface brief: public/blog/index.html —— 博客（诚实占位）

## Scope & visitor mode

整站五个页面之一：无 JS、无外部资源、共用 `public/styles.css`。访客模式 Read，但**本轮没有可读内容**——本页的职责是把「何时会有内容」说清楚。

## Audience, job, action, proof, constraints

- 受众：课程任课老师/助教（核对本页是否为诚实占位而非装饰堆砌）、同学、本人回访。
- 任务：一眼看出本页尚未启用、以及它会在课程第几步被填充；没有行动点（不放空链接）。
- 证明：页面自己就是证明——写明了 Step 4 建文章列表（Markdown 撰写 + 脚本生成页面）、Step 5 接入 RSS。
- 约束：不编造文章、不写「敬请期待」式营销句、不用装饰填充高度；与其余四页共用报头带与页脚。

## Chosen direction & memorable moment

沿用「实验档案」世界：本页是档案里一册还没写字的卷宗——页名 `.folio` + 一个栏目「本页内容」+ 两条登记在账本上的待办条目（`.tag` 普通档标注「Step 4 接入」「Step 5 接入」）。
难忘点：直说「本页现在没有文章，这是实情而不是故障」。

## Direction contract

THESIS: 空白也要如实登记——占位页的诚实本身就是内容，不用占位文章充数。

OWN-WORLD: 与首页同一个世界；本页零新样式、零新颜色、零动效。

STORY: 访客点「博客」进来，看到页名、一句话说明、两条标注了接入步数的待办，明白现在还没有文章、以及什么时候会有。

FIRST VIEWPORT: 报头带 + `.folio` 页名「博客」+「本页内容」栏目题 + 说明句 + 两条待办条目，一屏读完。

FORM: 复用 `.sec` / `.intro` / `.ledger` / `.dir` / `.tag`，不新增任何 CSS 类。

FINISH: 与整站同批完成 finish review、DESIGN.md 与 design.json。

## Signature interaction

无。

## Unresolved decisions

- Step 4 文章列表与 Step 5 的 feed 地址均为未来事实，本页只承诺步骤号，不承诺文件名与 URL。
