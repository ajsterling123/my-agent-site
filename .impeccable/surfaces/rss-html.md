---
version: 1
slug: "rss-html"
primary_target: "public/rss/index.html"
related_targets: ["public/rss/reader.js", "public/data/rss-items.json", "public/subscriptions.opml", "public/blog/index.html", "public/index.html"]
---

# Surface brief: public/rss/index.html —— RSS订阅（已实现）

## Scope & visitor mode

整站页面之一，六项导航里插在「博客」之后的那一项。与其它页面不同，本页条目由 `public/rss/reader.js` 读同域 `../data/rss-items.json` 后逐节点渲染（构建期由 `scripts/fetch_feeds.py` 抓取并规范化）。访客模式 **Read**：读者要在几秒内看清「订了哪几个源、每个源最近写了什么」，并点进原文。

## Audience, job, action, proof, constraints

- 受众：读者（本人与同学）、以及按 Step 验收的老师/助教——他们要看的是「外部源真的接上了、而且只当文本」。
- 任务：按源浏览最近的条目，点标题去源站读全文。唯一行动点是条目标题外链；次级行动点是页尾的 OPML 下载。
- 证明：页面本身就是证明——6 个源分栏、69 条真实条目（2026-10-08 抓取），每条带源站绝对地址；`tools/check_feeds.py` 会机械核对数据、OPML 与渲染脚本，并跑一次敌意样本负向测试。
- 约束：外部内容只当纯文本（`textContent` 逐节点渲染）；不加卡片、图标、阴影、徽章；外部内容静止态不用红；禁 JS 时不白屏；480px 单列、320px 无横向滚动。

## Chosen direction & memorable moment

沿用「实验档案」世界，本页是档案里的**订阅登记册**：每个源是一栏，栏目题（源标题）压在 1px 墨蓝实线上，栏内每一条登记一行——等宽日期、宋体标题（外链）、一句深蓝灰摘要，行间发丝线。它不是「信息流」，不给外部内容任何特殊待遇：别人的文章和本站文章在同一张账本上、用同一套字与线。
难忘点：外部世界被压进公文账本的秩序里——红依然只属于「在册」章，别人的内容再热闹也不许让页面上色。

## Direction contract

THESIS: 订阅不是流，是登记册——日期是机读数据（Consolas + tabular-nums），标题是档案条目（宋体加粗），摘要是次级说明（#5F6E7D）。

OWN-WORLD: 与首页同一个世界。本页复用 `.sec h2`（栏目题压 1px 实线）与博客列表那四个账本类（`.post-list` / `.post-row` / `.post-date` / `.post-item`），只新增一条 CSS：`.rss-reader .post-date span { display: block; }`，供同一栏同一天多条时在日期格内多显示一行时刻。零新色、零新字体、零新圆角、零动效。

STORY: 访客点「RSS订阅」→ 看到页名与一段说明 → 逐栏读到各源最近的条目 → 点标题去源站原文（新窗口）→ 需要订阅这些源就看页尾的 `subscriptions.opml`。

FIRST VIEWPORT: 报头带（导航当前项「RSS订阅」墨蓝加粗下划线）→ `.folio` 页名「RSS订阅」→ 一段 `.intro` 说明 → 第一栏（腾讯安全响应中心）的栏目题与登记行。

FORM: 页面骨架手工写成（与其它五个手写页同构，导航块逐字节一致）；条目内容运行时由同域 JSON 渲染；数据与清单由构建脚本生成，不手改。

FINISH: 与整站同批通过 `tools/check_site.py`（本页在 `public/rss/` 下，是唯一允许站外导航链接的页面）与 `tools/check_feeds.py`（含敌意样本负向测试）；DESIGN.md 已补「订阅阅读器」组件与两条 Named Rules。

## Signature interaction

无。全站唯一动效仍是首页的盖章。`reader.js` 只在载入时渲染一次，没有任何动画、过渡或滚动效果；条目标题 hover 沿用全局链接的变红响应（瞬时，无缓动）。

## Unresolved decisions

- 退出码与新鲜度：`rss-items.json` 是提交进仓库的生成物，部署工作流按用户明确要求**不改动**，因此线上数据是「最后一次本地抓取」的快照，不是每次部署都重抓。要变成每次部署自动刷新，只需在主部署工作流里加一行 `python3 scripts/fetch_feeds.py`。
- 条目总数会随各源 feed 长度变化（少数派/美团/云风都是 10–20 条）；目前不设每栏上限、不分页，因为总量（69 条）在一页内还读得完。
- 同一栏同一天多条的判定是按「源内同一日期出现两次以上」整栏切换到「日期 + 时刻」两行显示，而不是只给冲突的那几条加时刻——同一栏里日期格式不混排比省一行更重要。
- 每栏目前不显示源站首页链接（`html_url` 仍在 `rss-items.json` 里备查）；若读者反馈需要，可在栏内加一行 `.intro`，但那是新增内容而非新组件。
