---
version: 2
slug: "wiki-html"
primary_target: "public/wiki/index.html"
related_targets: ["public/wiki/agent-experiment.html", "public/blog/index.html", "public/index.html"]
---

# Surface brief: public/wiki/index.html —— Wiki 栏目页（已实现）

## Scope & visitor mode

整站页面之一，由 `scripts/build_wiki.py` 从 `content/wiki/*.md` 生成（无 JS、无外部资源、共用 `public/styles.css`；词条页 `public/wiki/<slug>.html` 与本页同一批生成）。访客模式 Read：老师/同学要在几秒内看清「这份 Wiki 收了哪些知识点、怎么互链」。

## Audience, job, action, proof, constraints

- 受众：课程任课老师/助教（核对 [[双向链接]] 与反向链接是否真的落在构建产物里）、同学、本人回访。
- 任务：看懂这份 Wiki 的定位与规则入口，看清全部页面与标签（页面清单），点进任意词条；行动点是词条标题链接与正文里的 [[链接]]。
- 证明：页面本身就是证明——「页面清单」由脚本从 frontmatter 生成（updated 倒序、slug 升序），「链接到此页的页面」由脚本从正文反向查出；报头带与页脚和手写页逐字节一致，由 `tools/check_site.py` 机械校验（本页恰好 1 个 aria-current 落「Wiki」项）。
- 约束：不写「敬请期待」式营销句、不编造知识点、不用卡片阵列；480px 收成单列；320px 不出现横向滚动；页面零 JavaScript。

## Chosen direction & memorable moment

沿用「实验档案」世界：Wiki 不是卡片墙，是一份「词条账本」——先用 `.folio` 页名 + `.post-body` 定位正文说清这份账本怎么用（规则在 `content/wiki/README.md`），再以「页面清单」与「链接到此页的页面」两张账本收尾，都复用 `.post-list` 行（等宽日期 + 宋体标题）。词条页头部复用 `.post-head`（h1 + 更新于 + `.wiki-meta` 等宽标签行），正文里「我的原话」用 `.post-body blockquote` 双发丝线夹摘录。
难忘点：一页底部自己长出「链接到此页的页面」——反向链接不手维护，是构建期从正文反查出来的账；[[链接]] 写向不存在的页面会让构建直接失败，所以这里不存在坏链。

## Direction contract

THESIS: 双向链接是构建期算出的账——`[[slug]]` 解析成站内链接，反向链接从正文反查；清单与反链都不手维护，与内容永不错位。

OWN-WORLD: 与整站同一个世界；本批页面用到的样式只有 `.folio` / `.post-head` / `.post-body` / `.post-list` / `.post-row` / `.post-date` / `.post-item` / `.wiki-meta`（唯一新增的一条：词条页头的等宽标签行），零新色、零新字体、零动效。

STORY: 访客点「Wiki」进来 → 看到页名与定位正文 → 页面清单点进词条 → 词条底部顺着反向链接走回索引。

FIRST VIEWPORT: 报头带（导航当前项「Wiki」墨蓝加粗下划线）→ `.folio` 页名 → 定位正文首段，一屏读完。

FORM: 骨架（报头带、导航块、页脚、favicon、样式表引用）从 `public/index.html` 改写（`scripts/page_build.py` 共用实现），内容由构建脚本生成；不手写这一页。

FINISH: 与整站同批通过 `tools/check_site.py`（wiki/ 已纳入全站判据，含生成页标记）与四个校验器；DESIGN.md 已补「Wiki 账本」组件规格。

## Signature interaction

无。全站唯一动效仍是首页的盖章，本页没有任何动效。

## Unresolved decisions

- 词条多起来之后 index 页是否需要按标签筛选未定（当前按 updated 倒序全量列出，2026-10-09 有 2 页）。
- 外部来源类词条的登记方式（先登记进 RSS订阅 / Research Papers 页再引用的站内口径）在词条变多后是否要更顺手的入口，未定。
