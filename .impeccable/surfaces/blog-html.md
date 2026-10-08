---
version: 1
slug: "blog-html"
primary_target: "public/blog/index.html"
related_targets: ["public/index.html", "public/posts/hello-agent.html", "public/about/index.html"]
---

# Surface brief: public/blog/index.html —— 博客列表（已实现）

## Scope & visitor mode

整站页面之一，由 `scripts/build_blog.py` 生成（无 JS、无外部资源、共用 `public/styles.css`）。访客模式 Read：老师/同学要在几秒内看清「这门课写过哪几篇、各自讲了什么」。

## Audience, job, action, proof, constraints

- 受众：课程任课老师/助教（核对博客是否真的接上了内容、以及是不是脚本生成）、同学、本人回访。
- 任务：看清全部文章与顺序（日期倒序），点进任意一篇；唯一行动点是文章标题链接。
- 证明：页面本身就是证明——每条登记了等宽日期、标题与一句摘要，且与 `content/posts/` 一一对应；报头带与页脚和手写页逐字节一致，由 `tools/check_site.py` 机械校验。
- 约束：不写「敬请期待」式营销句、不编造文章、不用卡片阵列；480px 收成单列；320px 不出现横向滚动。

## Chosen direction & memorable moment

沿用「实验档案」世界：博客不是信息流，是一张账本——栏目题「文章登记」压在 1px 墨蓝实线上，其下每篇文章是一行登记（等宽日期 + 宋体标题 + 一句摘要），行间发丝线，与首页「身份登记」同栏宽、同节奏。
难忘点：日期与标题基线对齐的账本行——像档案登记，不像常见的文章列表。

## Direction contract

THESIS: 文章按登记簿排列——日期是机读数据（等宽），标题是档案条目（宋体），摘要是次级说明（深蓝灰）。

OWN-WORLD: 与首页同一个世界；本页用到的生成物样式只有 `.post-list` / `.post-row` / `.post-date` / `.post-item` 四个类，零新色、零新字体、零动效。

STORY: 访客点「博客」进来 → 看到页名、栏目题「文章登记」与逐条登记的文章行 → 点标题进入文章页。

FIRST VIEWPORT: 报头带（导航当前项「博客」墨蓝加粗下划线）→ `.folio` 页名 → 「文章登记」栏目题与其下的账本行，一屏读完。

FORM: 骨架（报头带、导航块、页脚、favicon、样式表引用）从 `public/index.html` 改写，内容由构建脚本生成；不手写这一页。

FINISH: 与整站同批通过 `tools/check_site.py`（已覆盖本页）与 impeccable detect；DESIGN.md 已补「博客列表」组件规格。

## Signature interaction

无。全站唯一动效仍是首页的盖章，本页没有任何动效。

## Unresolved decisions

- RSS（Step 5）会加到这一页；届时本页结构不变，只多一个订阅入口。
- 文章多到一屏放不下之后的分页/归档策略未定（当前全量列出，2026-10-08 只有 1 篇）。
