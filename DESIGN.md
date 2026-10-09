---
name: 张易孝 · 实验档案
description: 课程实验记录站——像一份在册公文档案：冷白纸面、墨蓝线、宋体标题，红只标「当前/活跃」。
colors:
  paper: "#F5F6F4"
  ink: "#1C2B3A"
  slate: "#6B7A89"
  slate-ink: "#5F6E7D"
  red: "#B5322C"
  hairline: "rgba(28, 43, 58, 0.24)"
  hairline-strong: "rgba(28, 43, 58, 0.45)"
typography:
  display:
    fontFamily: 'SimSun, "Songti SC", STSong, NSimSun, serif'
    fontSize: "clamp(2.75rem, 9vw, 3.75rem)"
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: "0.14em"
  headline:
    fontFamily: 'SimSun, "Songti SC", STSong, NSimSun, serif'
    fontSize: "1.375rem"
    fontWeight: 700
    lineHeight: 1.4
    letterSpacing: "0.1em"
  title:
    fontFamily: 'SimSun, "Songti SC", STSong, NSimSun, serif'
    fontSize: "1.3125rem"
    fontWeight: 700
    lineHeight: 1.4
    letterSpacing: "0.08em"
  body:
    fontFamily: 'system-ui, -apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif'
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.9
    letterSpacing: "normal"
  label:
    fontFamily: 'SimSun, "Songti SC", STSong, NSimSun, serif'
    fontSize: "13px"
    fontWeight: 700
    lineHeight: 1.9
    letterSpacing: "0.35em"
  mono:
    fontFamily: 'Consolas, "SF Mono", Menlo, "Liberation Mono", "Courier New", monospace'
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.9
    letterSpacing: "0.05em"
rounded:
  tag: "2px"
  seal: "3px"
  scrollbar-thumb: "6px"
spacing:
  inset: "2px"
  xs: "12px"
  sm: "16px"
  md: "20px"
  lg: "22px"
  xl: "56px"
  xxl: "64px"
components:
  doc-meta:
    padding: "12px 2px"
  site-nav:
    padding: "9px 2px"
  folio:
    padding: "44px 0 30px"
  doc-foot:
    padding: "16px 2px 0"
  reg-row:
    padding: "13px 2px"
  stamp:
    textColor: "{colors.red}"
    rounded: "{rounded.seal}"
    padding: "8px 9px 8px 14px"
  tag:
    textColor: "{colors.slate-ink}"
    rounded: "{rounded.tag}"
    padding: "5px 8px 5px 12px"
  tag-live:
    textColor: "{colors.red}"
    rounded: "{rounded.tag}"
    padding: "5px 8px 5px 12px"
---

# Design System: 张易孝 · 实验档案（The Living Dossier）

## Overview

**Creative North Star: "在册档案 · The Living Dossier"**

这个系统不是「个人主页」的视觉语言，而是一份正在持续更新的公文档案：冷白纸面上，墨蓝的字与线登记身份、罗列条目、盖章确认。层级不靠装饰，靠字号、字重、字距与三档粗细的线；页面唯一的「花活」是一枚旋转 -6° 的红章，以及它落下时的那一次动效。

气质三词：克制、在册、随时可归档。没有渐变、没有卡片阴影、没有图标库、没有外部字体——三个系统字族（宋体 / 黑体 / 等宽）就是全部排版资源。红 #B5322C 是全页最稀缺的颜色，按纪律只出现在「当前/活跃」的标记上；它的稀有就是它的含义。PRODUCT.md 已将此方向钉死为品牌承诺（「实验档案」概念、配色、字体、克制原则），未来所有 Step 都在同一份档案上续页，而不是另起炉灶。

**Key Characteristics:**
- 页面即档案：信息用登记行（dl）、条目（ledger）、状态标记（tag）组织，拒绝卡片阵列与技能罗列。
- 三级线公文章法：3px 双细线框定页首/页尾，1px 实线开栏目，0.24 发丝线分行。
- 红色即活动：静止红全页仅两处（「在册」章、「进行中」标），其余只作 hover/focus 响应。
- 冷白纸面 × 墨蓝 × 蓝灰；零渐变、零阴影、零图标、零外部资源。
- 宋体标题 × 系统黑体正文 × Consolas 数据，全部系统自带，file:// 可开。
- 全站共一份档案：报头带（3px 双线 → 元信息行 → 导航行 → 1px 实线）在所有页面完全同构——六个菜单页（首页 / 关于我 / 博客 / RSS订阅 / Research Papers / Wiki）与脚本生成的文章页都从 `public/index.html` 的骨架改写而来，当前项用墨蓝加粗下划线指认；红色仍只在首页的两处出现。
- 唯一动效：载入时盖章一次（0.5s, ease-out），reduced-motion 下静止常显；子页没有章，也**不加任何入场动效**。
- 机器出口三处：向外发布自己的 `public/feed.xml`（RSS 2.0，与博客列表页同源同序），向内收取别人的 `public/data/rss-items.json`（Step 6 的阅读器数据）与 arXiv 论文 `public/data/papers.json`（Step 7 的论文页数据），外加订阅清单 `public/subscriptions.opml`。这些都不是「页面」，不参与报头带与导航的一致性检查。

## Colors

一句话：公文纸面的三色秩序——墨蓝是唯一的「声音」，蓝灰是低声部，红是唯一的强调，且只在「活着」的地方出现。

### Primary
- **墨蓝 Ink Navy** (#1C2B3A)：正文文字、全部结构线（双线/实线）、`::selection` 底色、body 的 `accent-color`。它是页面唯一的默认前景色，链接也继承它。

### Secondary
- **档案红 Archive Red** (#B5322C)：「活动」专用色。静止状态仅两处——「在册」章（红字 + 2px 红边 + 内嵌双环）与 `.tag-live`「进行中」标（红字 + 红边 + 加粗）。短暂状态复用红作响应：`a:hover` 文字变红、登记邮箱下划线变红、`:focus-visible` 2px 红色轮廓。

### Tertiary
- **蓝灰（基）Blue-Grey Slate** (#6B7A89)：声明的次级基色，定位是装饰线与较大字号的次级文字。当前构建中尚未被任何规则直接引用（所有小字次级都走了达标变体），作为色族的浅端保留。
- **深蓝灰 Deep Slate** (#5F6E7D)：小号次级文字的达标变体（对纸面 ≥ 4.5:1）。登记 dt、条目描述、页脚说明、普通 tag 全用它。

### Neutral
- **冷白纸 Cold Paper** (#F5F6F4)：全站底色；打印时切到纯白 #fff，其余不动。
- **发丝线 Hairline** (rgba(28, 43, 58, 0.24))：登记行、条目之间的分隔线。
- **浓发丝线 Strong Hairline** (rgba(28, 43, 58, 0.45))：tag 边框、邮箱链接下划线、滚动条拇指。

### Named Rules
**The Red Discipline Rule（红色纪律）.** 红是「活动」的语义色，不是装饰色。静止红只允许出现在「当前/活跃」标记上（现构建为「在册」章与「进行中」标两处，且两者都只在首页）；hover 与 focus 可借用红作瞬时响应；禁止红底、红面、大面积红，禁止给非活跃元素上静止红。**导航当前项不用红**——它回答的是「你在哪一页」，不是「哪件事在活动」，两件事在语义上不同档；当前项用墨蓝加粗与 2px 墨蓝下划线指认，红色留给真正的「活动」。

**The Two-Slate Rule（双蓝灰）.** 蓝灰一族两个音高：#6B7A89 只作装饰线与较大字号次级；任何小号（≲16px）次级文字必须用 #5F6E7D——它对 #F5F6F4 的对比度 ≥ 4.5:1，前者不达标。

## Typography

**Display Font:** 宋体系 SimSun / Songti SC（回退 STSong、NSimSun、serif），全部加粗
**Body Font:** 系统黑体 system-ui / -apple-system / Segoe UI / PingFang SC / Microsoft YaHei / Noto Sans CJK SC
**Label/Mono Font:** Consolas（回退 SF Mono、Menlo、Liberation Mono、Courier New）

**Character:** 宋体负责「公文的脸」，黑体负责「可读的正文」，等宽负责「机器可查的数据」——三个声部各管一行，不混用。

### Hierarchy
- **Display**（700, clamp(2.75rem, 9vw, 3.75rem), 1.15, 字距 0.14em）：巨幅宋体姓名 h1，档案的封面字。
- **Headline**（700, 1.375rem, 1.4, 字距 0.1em）：栏目 h2，坐在 1px 墨蓝实线上。
- **Title**（700, 1.3125rem, 1.4, 字距 0.08em）：条目 h3，与状态 tag 同行基线对齐。
- **Body**（400, 16px, 1.9）：全站正文基调；档案自述与文章正文 17px / 2.05（≤38em）；条目描述与博客列表摘要 15px / 1.95（≤40em，深蓝灰）；登记值 16.5px。
- **Label**（700, 13px, 字距 0.35em）：宋体档案小签「个人实验档案」；登记 dt 12.5px / 0.3em（黑体，小屏 0.2em）；tag 12px / 0.22em（黑体）。
- **Mono**（400, 12px, 字距 0.05em, tabular-nums）：「最后更新」日期；登记邮箱链接 15.5px 带下划线；页脚 STEP n/12 字距 0.08em。

### Named Rules
**The Three-Voice Rule（三声部）.** 一段文字只有一种声音：身份与结构（姓名、栏目题、条目题、章、档案小签）用宋体加粗；叙述用系统黑体；日期、邮箱、步数计数器等机读数据用 Consolas 并开 tabular-nums。不引入第四个字族。

**The Wide-Tracking Rule（宽字距）.** 宋体的公文感来自放宽的字距：标题 0.08–0.14em，小签与章 0.22–0.35em；等宽 0.04–0.08em；黑体正文不额外加字距。480px 小屏下 h1 字距收至 0.1em 防溢出。

## Layout

单栏版心：`.page` max-width 800px，水平居中，左右 padding clamp(20px, 5vw, 36px)，底部 56px。所有结构线（双线、实线、发丝线）都是全宽贯穿这 800px 版心——线的宽度就是版心的宽度，这是「公文」而非「卡片」的关键。

垂直节奏（styles.css 实测值；构建未使用间距变量，frontmatter 的 `spacing` 只是常用档位摘要，值以本节为准）：公文头 padding 12px 2px → 导航行 padding 9px 2px（小屏 8px 2px）→ 档案头 padding 56px 0 44px（小屏 44px 0 36px；子页页名块 `.folio` 44px 0 30px，小屏 34px 0 24px）→ 栏目题 padding 22px 0 4px + margin-bottom 6px → 登记行 padding 13px 2px → 自述 margin-top 14px → 条目 padding 20px 2px → 页脚 margin-top 64px、padding 16px 2px 0。行内文字统一从线上水平缩进 2px。

基线行：公文头、条目头、页脚都是 `display: flex; align-items: baseline` + `flex-wrap: wrap`，gap 16px（条目头 14px / row-gap 8px）；tag 靠 `margin-left: auto` 推到行尾。

响应式：唯一断点 max-width 480px——正文降到 15.5px，档案头收紧，h1 字距收至 0.1em，章缩小（14px、top 48px、padding 6px 7px 6px 12px），登记列 7em → 5.5em，dt 字距收至 0.2em。390/320px 防溢出是组合拳：clamp() 字号、所有基线行可换行、`white-space: nowrap` 只用于原子短数据（日期、tag）——换行时它们作为整体下移，不在中间断开。

### Named Rules
**The Three-Weight Rule（三级线）.** 线分三档，各司其职：3px double 墨蓝双线只用于文档头尾（`.doc-meta` 上边、`.doc-foot` 上边）——它是档案的装订线；1px solid 墨蓝实线开栏目（`.sec h2` 上边），同一个 1px 实线档也负责给报头带收口——Step 3 起这条收口线挂在 `.site-nav` 下边（原来是 `.doc-meta` 下边，为给导航行让位而下移一行，线档与职责不变）；rgba(28,43,58,.24) 发丝线分隔同级行（登记行、条目之间）；rgba(28,43,58,.45) 浓发丝线只作 tag 边框、链接下划线与滚动条拇指。不发明第四档线，也不把双线用到头尾之外。

**The Nav Band Rule（报头带与全站复用）.** 报头带是档案的装订头，全站所有页面（六个菜单页 + 脚本生成的文章页）完全同构：3px double → 元信息行 → 导航行 → 1px solid 收口。导航块（`<nav class="site-nav" aria-label="主导航">` + `ul` + 六个 `li`）在所有页面共用同一份标记，**除链接前缀（首页空串、子页 `../`）与 `aria-current="page"` 落在哪一项之外逐字节相同**——一致性靠这条规则，不靠复制粘贴的运气。页面结构同样复用：`.doc-head`（元信息 + 导航 + 标题区）与 `.doc-foot` 全站一致，只有页脚左侧说明句按页改写。子页标题用 `.folio` 档（宋体 700，`clamp(1.75rem, 6vw, 2.5rem)`，字距 0.14em，padding 44px 0 30px），首页保留巨幅姓名 `.doc-title` 与「在册」章——**章只在首页出现**。

## Elevation & Depth

全系统平面：没有任何投影式 elevation，没有 tonal 层叠。深度由三样东西表达：线的粗细层级（双线 > 实线 > 发丝线）、宋体宽字距带来的「印制感」、以及红章的 0.92 不透明度（微透纸面，像真盖的章）。唯一的 box-shadow 是章的内嵌双环 `inset 0 0 0 2px var(--paper), inset 0 0 0 3px var(--red)`——在 2px 红边框内再画一圈细红环，是「画」出来的印章纹样，不是「抬」起来的阴影。

### Named Rules
**The Flat Archive Rule（平面档案）.** 禁止投影。盒阴影在这个系统里只有一个合法形态：印章的内嵌双环，用来画纹样。任何用 shadow 表达「浮起」「卡片」「弹层」的写法都不属于这个世界。

## Shapes

形状语言是「纸与线」，不是「圆角卡片」。全站只有三个圆角值：tag 2px、章 3px、滚动条拇指 6px（浏览器 chrome，不算组件）。没有卡片容器、没有面板、没有大圆角。边框词汇：2px 红实线（章）+ 内嵌双环、1px 边框（tag）。整体轮廓由全宽横线切分，垂直方向没有分隔柱或侧栏。

## Components

### 公文头 Document Header Bar（.doc-meta / .doc-label / .doc-date）
- 全宽档案条：左「个人实验档案」宋体小签（13px / 0.35em），右「最后更新」等宽日期（12px / 0.05em / tabular-nums / nowrap）。五页文案与结构完全相同。
- 上边 3px double 墨蓝（装订线）；下边不再画线——收口的那条 1px solid 墨蓝自 Step 3 起由 `.site-nav` 下边承担，报头带因此是「双线 → 元信息 → 导航 → 实线」四层。
- flex 基线对齐，gap 16px，可换行。

### 站点导航 Site Navigation（.site-nav / .site-nav a[aria-current]）
- 报头带的第三行，紧跟元信息行；`<nav aria-label="主导航">` + `ul` + 六个菜单项：首页 / 关于我 / 博客 / RSS订阅 / Research Papers / Wiki，此顺序即页面顺序（「RSS订阅」自 Step 6 起插在「博客」之后）。
- 下边 1px solid 墨蓝，是报头带的收口线；`ul` 为 flex 基线行，padding 9px 2px（小屏 8px 2px），gap 6px 20px（小屏 4px 14px），`flex-wrap: wrap`——小屏允许折行，不允许横向滚动。
- 菜单项：宋体 15px / 0.1em（小屏 14px / 0.06em），非当前项 `var(--slate-ink)`（小字次级达标色），无下划线。
- **当前项不用红**：`color: var(--ink)` + `font-weight: 700` + 2px 墨蓝下划线（offset 7px），并带 `aria-current="page"`。红色只留给「活动」语义（见红色纪律）。hover 仍沿用全局 `a:hover` 变红，属交互态。

### 副页页名 Folio Title（.folio / .folio h1）
- 子页的标题区，替代首页的 `.doc-title`：宋体 700，`clamp(1.75rem, 6vw, 2.5rem)`，行高 1.25，字距 0.14em（小屏 0.1em），padding 44px 0 30px（小屏 34px 0 24px）。
- 只放页名，不放状态标、不放章、不放副题——子页没有「在册」章，页名下面直接接栏目题的 1px 实线。
- 文章页的页名用 `.post-head`，与 `.folio` 同一字号档，只在页名下多一行等宽登记日期（见下文「文章页」）。

### 档案头与章 Dossier Title & Seal（.doc-title / h1 / .stamp）
- 巨幅宋体姓名；右上角「在册」章：绝对定位 top 58px / right 2px，rotate(-6deg)，红字红 2px 边框 + 内嵌双环，radius 3px，padding 8px 9px 8px 14px，line-height 1，opacity 0.92。
- 唯一动效 stamp-in：0.5s cubic-bezier(0.22, 1, 0.36, 1) 延迟 0.35s，从 opacity 0 / scale(1.7) 落到 0.92 / scale(1)；包在 `prefers-reduced-motion: no-preference` 内，reduced-motion 下静止常显。

### 身份登记 Registry（.register / .reg-row）
- dl 账本：每行 grid 7em / 1fr（小屏 5.5em），基线对齐，padding 13px 2px，行间发丝线。
- dt 12.5px / 0.3em 深蓝灰；dd 16.5px 墨蓝；`address` 归一为正常字型。
- 邮箱是页面唯一行动点：等宽 15.5px、1px 下划线（浓发丝色、offset 3px）；hover 文字与下划线齐变红；`:focus-visible` 2px 红轮廓 offset 3px。

### 栏目题 Section Heading（.sec h2）
- 坐在 1px solid 墨蓝实线上：padding 22px 0 4px，margin-bottom 6px，1.375rem 宋体加粗 0.1em。上方不允许再插任何眉题/kicker。

### 档案自述 Intro（.intro）
- 17px / 2.05，max-width 38em，margin-top 14px。全站最松的行高，给「档案自述」以陈述语气。

### 条目账本 Ledger Entry（.ledger / .dir / .dir-head）
- 无序列表去点，条目间发丝线，padding 20px 2px。
- 条目头 flex 基线：h3 宋体 1.3125rem / 0.08em + tag（margin-left auto 推至行尾），gap 14px 可换行。
- 描述 15px / 1.95 深蓝灰，max-width 40em，margin-top 6px。

### 状态标 Status Tag（.tag / .tag-live）
- 12px / 0.22em / nowrap，padding 5px 8px 5px 12px，1px 浓发丝边框，radius 2px，深蓝灰；非交互组件，无 hover。
- `.tag-live`「进行中」：红字红边加粗——红色纪律的两处静止红之一。

### 博客列表 Post Index（.post-list / .post-row / .post-date / .post-item）
- 由 `scripts/build_blog.py` 从 `content/posts/*.md` 生成，日期倒序；页面骨架（报头带、导航块、页脚）与手写页逐字节一致，只有链接前缀与 `aria-current` 落在「博客」项不同。
- 栏目题「文章登记」压 1px 墨蓝实线（`.sec h2` 同档）；其下 `.post-list` 是一张账本：每行 `.post-row` 为 `grid-template-columns: 7em 1fr`、`align-items: baseline`、`padding: 14px 2px`，行间 1px 发丝线——与「身份登记」同栏宽、同节奏。
- 左列 `.post-date`：Consolas 12.5px / 0.04em / tabular-nums / nowrap、深蓝灰；日期是机读数据，用等宽档。
- 右列 `.post-item`：`h3` 宋体 700 1.3125rem / 0.08em，标题本身就是链接（1px 下划线走浓发丝色，hover 变红）；摘要 15px / 1.95 深蓝灰、≤40em（与条目描述同档）。
- 没有文章时渲染一句 `.intro` 说明（文章写在 `content/posts/`，构建后自动登记），不留假条目。
- 480px 下 `.post-row` 收成单列：日期移到标题上方，`row-gap: 4px`——7em 的日期列在 320px 会把标题挤窄。
- 列表末尾挂一行订阅入口：`<p class="intro">订阅：<a href="../feed.xml">feed.xml</a>（RSS 2.0）…</p>`——**复用既有的 `.intro` 与全局链接样式，不新增组件、不加卡片、不加图标**。站内订阅不是「活动」，因此不碰红色；它是列表的附属说明，所以也不用 `.sec h2` 另开栏目。`.intro` 是全站最松的陈述行高，用它收尾正合适。
- 页面 `<head>` 里加一行 `<link rel="alternate" type="application/rss+xml" title="张易孝实验档案 · 博客" href="../feed.xml">`：给浏览器与阅读器指认订阅地址。这一行由 `scripts/build_blog.py` 生成（列表页是产物，不手改输出）。

### 订阅源 Feed（public/feed.xml）
- 由 `scripts/build_feed.py` 从 `content/posts/*.md` 的 frontmatter 生成，与列表页同源同序（日期倒序，同日按 slug 升序稳定排列）。它不是「页面」，没有 HTML 骨架、不参与报头带与导航的一致性检查——它是同一份档案的机读出口。
- 站内没有任何指向它的视觉入口新样式：唯一的展示面就是列表页末尾那一行 `.intro` 订阅句（见上）。
- 字段与硬性约定见 README；设计侧只有一条纪律：**feed 里的中文字与 `& < >` 原样保留/转义，不用 CDATA**，这样读者看到的标题与列表页逐字一致。

### 订阅阅读器 Feed Reader（public/rss/index.html / .rss-reader）
- 菜单项「RSS订阅」指向的页面，语义是一张「订阅登记册」：**按源分栏**，每个源一个 `<section class="sec">`，源标题坐在 1px 墨蓝实线上——与「文章登记」同档，栏目题语法不另发明。
- 栏内直接复用博客列表那套账本，结构样式一行不加：`.post-list` / `.post-row`（`grid-template-columns: 7em 1fr`、基线对齐、行间发丝线）/ `.post-date`（Consolas 12.5px / 0.04em / tabular-nums / 深蓝灰）/ `.post-item`（`h3` 宋体 700 1.3125rem 标题 + 15px / 1.95 深蓝灰摘要 ≤40em）。
- 条目标题是外链（`target="_blank"` + `rel="noopener noreferrer"`），1px 下划线走浓发丝色、hover 变红——与站内链接同一套响应；**静止态不用红**，外部内容不是「活动」，红色纪律不变。
- 日期默认只显示 `YYYY-MM-DD`；**同一栏同一天有多条时**该栏日期格内多一行 `HH:MM`（`.rss-reader .post-date span { display: block; }`，7em 的等宽列刚好放得下两行）——否则同日条目看起来像没排序。日期定不下来时显示「日期未知」。
- **订阅目录 Subscription Index（`.rss-toc`）**：页首的索引，栏目题「订阅目录」压在 1px 墨蓝实线上，与各源栏目同档；其下是一张六行账本——左列等宽最新日期，右列源名（`h3` 档）与**推到行尾的等宽条数**（`.rss-toc .rss-toc-count` 用 `margin-left: auto`，像目录里页码都停在同一道右边界上），整行是页内锚点，跳到对应栏目。索引行的日期只占一行（不像内容栏那样在同日冲突时补时刻），行距也紧一档（`.rss-toc .post-row { padding: 11px 2px; }`）——六行索引刚好一屏读完，第一栏的栏目题落在首屏之内。它是目录不是内容：**不显示摘要、不显示外链**，源站的地址留给栏内的出处行。条数随筛选变化，因为它是从同一份 JSON 算出来的，不是写死在页面里的。
- **出处 Provenance（`.rss-source`）**：每栏栏目题下压一行源站地址（`.rss-source`，Consolas 12.5px / 0.04em / 深蓝灰，链接静止态也走深蓝灰、hover 变红），取自数据里的 `html_url`，只显示主机名。这是公文式的来源引注：读者的问题是「这条登记是从哪来的」，一行地址比一枚按钮答得更直接。取不到 `html_url` 时整行不渲染，绝不编造地址。
- **筛选 Filter（`.rss-filter`）**：目录之上的一条填空线——标签「筛选条目」走登记 dt 那一档小字（12.5px / 0.3em / 深蓝灰），输入框只有 1px 浓发丝下边框（无边框盒、无底色、无圆角），像公文表格里一道待填的横线；`font: inherit` 让输入的文字与正文同声部，focus 沿用全局 2px 红轮廓。输入即筛（标题 + 摘要，大小写不敏感），命中的源与其条目留在页面上，没命中的整栏移除，目录同步只剩命中项——**目录与内容永远一致**。筛选状态由一行 `.rss-note` 说明（`aria-live`）：有命中写「匹配 N 条，来自 M 个源。」，没命中写「没有匹配「…」的条目；清空筛选框可看全部 N 条。」——空状态说清问题与出路，不留白屏。它属于「读」的一件工具，不是新世界：没有下拉、没有复选框、没有按钮、没有第二个输入框。
- **回到目录 Return Link（`.rss-back`）**：每栏末尾一行 12.5px / 0.04em 深蓝灰小字（与页脚说明句同档），回到页首目录——73 条往下读时，这是「读完了，去下一栏」的那一步。六条同文案链接各带 `aria-label`（「回到订阅目录（腾讯安全响应中心栏读完了）」），屏幕阅读器不会听到六个一模一样的链接。目录、栏目、出处都带 `scroll-margin-top: 14px`，锚点落点不会让 1px 实线贴着视口顶边。
- 渲染逻辑单独放在 `public/rss/reader.js`，页面用 `defer` 同域引入；页面唯一的网络请求是同域的 `../data/rss-items.json`（构建期由 `scripts/fetch_feeds.py` 抓好），页面里没有任何跨域请求。栏目锚点是运行时生成的，因此脚本在首次渲染后会按 `location.hash` 自己跳一次（瞬间定位，不做缓动）。目录、出处、筛选、计数、空状态全部由脚本从同一份 JSON 生成——**页面骨架里不写死任何源名或条数**，`tools/check_feeds.py` 会机械核对这一点。条目在 JS 执行前位置为空，因此禁 JS 时另有 `<noscript>` 回退说明（说明目录与筛选框同样不显示）；页尾一行 `.intro` 给出 OPML 与本站自己的 `feed.xml`。
- 本页的 CSS 全部收在 `styles.css` 的「RSS订阅」注释块里：目录行距与行尾条数、锚点落点（`scroll-margin-top`）、出处那一行等宽地址、填空线式筛选、说明与回跳小字，加上原来的 `.post-date span`。全部落在既有词汇里：等宽小字是机读数据、蓝灰是次级说明、1px 浓发丝线是填空线——零新色、零新字体、零新圆角、零阴影、零动效。
- 480px 下 `.post-row` 收成单列（日期移到标题上方），沿用博客列表同一条断点规则；筛选那一行在 320px 仍是一行（标签 nowrap、输入框 `min-width: 0` 让位）。

### 论文账本 Papers（public/papers/index.html / .paper-*）
- 菜单项「Research Papers」指向的页面，语义是档案里的**论文引文登记册**：与博客列表同一张账本——`.post-list` / `.post-row`（`grid-template-columns: 7em 1fr`、基线对齐、行间发丝线）/ `.post-date`（Consolas 12.5px / 0.04em / tabular-nums / 深蓝灰）/ `.post-item`（`h3` 宋体 700 1.3125rem 标题 + 次级说明行），一行一条 arXiv 论文，按提交日期倒序。
- 每条显示：等宽日期（`<time datetime>`）→ 宋体标题（指向 `https://arxiv.org/abs/<id>` 的外链，`target="_blank"` + `rel="noopener noreferrer"`，1px 下划线走浓发丝色、hover 变红——与站内链接同一套响应）→ 作者行（直接落 `.post-item p` 的次级档 15px / 1.95 深蓝灰；**多于 3 位时列前三位 + 「等 N 人」**）→ 摘要（**原生 `<details>` / `<summary>` 默认折叠**，浏览器既有 affordance，不加 JS 逻辑）→ 来源标记（等宽小字「arXiv · 预印本，未经同行评审」）。不渲染任何图片。
- **The Untrusted Content Rule 对论文同样适用**：arXiv 是预印本平台，来源标记写明「未经同行评审」，不把任何条目描述成已发表；标题与摘要只当文本逐节点渲染；外链只是导航，本页对外的网络请求只有同域 `../data/papers.json` 这一份。
- 渲染逻辑单独放在 `public/papers/papers.js`，页面用 `defer` 同域引入（与 `reader.js` 同一模式）：页面唯一的网络请求是同域的 `../data/papers.json`（构建期由 `scripts/collect_papers.py` 抓好，触发入口是 `.zcode/skills/research-paper-collector` 技能）。条目、计数、空状态全部由脚本从同一份 JSON 生成——**页面骨架里不写死任何论文**，`tools/check_papers.py` 会机械核对这一点；禁 JS 时另有 `<noscript>` 回退说明（含机读数据入口）。
- 本页自己的 CSS 收在 `styles.css` 的「Research Papers」注释块里，仅四条小规则且全在既有词汇内：摘要折叠的 `details.paper-summary`（summary 是页脚说明句那一档小字 + `cursor: pointer`）、来源标记 `p.paper-source`（与出处行同一副等宽小字）、尾注 `.paper-note`（与 `.rss-note` 同档）。作者行与摘要正文直接落 `.post-item p` 的次级档，零新规则。零新色、零新字体、零新圆角、零阴影、零动效；预印本不是「活动」，静止态不用红。
- 480px 下 `.post-row` 收成单列（日期移到标题上方），沿用博客列表同一条断点规则；长英文标题靠 `.post-item` 的 `overflow-wrap: break-word` 折行，390/320px 无横向滚动（已实测）。

### 文章页 Article（.post-head / .post-body）
- `.post-head` 占 `.folio` 的位置（报头带之下）：与 `.folio` 同一字号档（宋体 700，`clamp(1.75rem, 6vw, 2.5rem)`，行高 1.25，字距 0.14em，padding 44px 0 30px；小屏 34px 0 24px / 0.1em），`h1` 由 frontmatter 的 title 提供；页名下压一行 `.post-date`（`display: block` / `margin-top: 12px`）写「登记于 YYYY-MM-DD」。文章页没有「在册」章，也没有任何入场动效。
- `.post-body` 是正文容器（`<article>`）：`max-width: 38em`、`overflow-wrap: break-word`（长串不撑破 320px）。
- 段落 17px / 2.05、下间距 22px——与「档案自述」同档，档案里最松的行距；`h2` 与 `.sec h2` 同档（压在 1px 墨蓝实线上，padding 22px 0 4px、下间距 6px），`h3` 与条目题同档（宋体 700 1.3125rem / 0.08em，上间距 26px）。
- 列表：`ul` 圆点、`ol` 数字，`padding-left: 1.5em`、行高 2、条目距 4px；`li::marker` 用 Consolas + 深蓝灰——标记属于机读编号，不进正文色。
- 行内代码：Consolas 0.9em + 1px 浓发丝边框 + 2px 圆角 + 1px 5px 内距，复用 tag 的边框词汇；不加底色，本系统没有 tonal 层叠，也不设 `nowrap`（宁可在长串处折行，也不横向滚动）。
- 引用：`blockquote` 上下各 1px 发丝线、左右各 22px 内距、正文换深蓝灰并收到 16.5px / 1.95——夹在两条线之间的摘录，不做竖线、不做底色（Shapes 一节禁竖分隔柱）。
- 强调只加字重（`strong` 700），不换字族；链接沿用全局 1px 下划线 + hover 变红。
- 正文语法限于构建脚本支持的那几类（见 README「如何新增一篇博客」）：段落、`##`/`###` 标题、无序与有序列表、粗体、行内代码、链接、引用。

### 公文尾 Document Footer（.doc-foot / .foot-step）
- 上边 3px double 墨蓝（与公文头呼应，装订线收口），flex 基线，gap 16px，可换行。
- 左说明 12.5px / 0.04em 深蓝灰，按页改写（首页写首页，子页写「本页是课程实验档案的〈页名〉页」）；右「STEP 7/12」等宽 0.08em / tabular-nums——12 步迭代的进度印记，六个菜单页与生成页一致。
- 打印时 `.site-nav` 隐藏（`@media print`）：纸质归档件不需要浏览器导航。

### 全局镀铬 Global Chrome
- `::selection`：墨蓝底、纸白字。
- `:focus-visible`：2px solid 红、offset 3px（键盘焦点可见性承诺）。
- 链接：继承墨蓝、1px 下划线、offset 3px，hover 变红。
- 滚动条：12px 宽，透明轨道，拇指浓发丝色 + 3px 纸色边框 + 6px 圆角。
- `color-scheme: light`；body `accent-color` 墨蓝；favicon 为内联 SVG（墨蓝方块 + 纸色宋体「档」字）；`@media print` 底色转纯白 #fff——档案随时可打印归档。

### Named Rules
**The Two-Tier External Reference Rule（外部引用两级）.** 外部引用分两类判，由 `tools/check_site.py` 机械执行，口径同时写在 AGENTS.md「站点与目录」：外部**资源**（`script`/`img`/`iframe`/`video`/`audio`/`source`/`track` 的 `src`、`srcset`、`form` 的 `action`、`object`/`embed` 的 `data`、`link` 的 `href`，以及 CSS 里的 `@import` 与 `url(//…)`）**所有页面一律禁止**——零外部请求从 Step 1 起就是本站资产；外部**导航**（`<a href>`）只有**外部内容页**（`public/rss/` 与 `public/papers/` 下的页面，Step 7 起）允许，且必须 https + `target="_blank"` + `rel="noopener noreferrer"` 三件齐。这条规则管的是「页面文件里静态写着什么」；阅读器页与论文页的条目链接由 `reader.js` / `papers.js` 运行时生成，所以 `tools/check_feeds.py` 与 `tools/check_papers.py` 另外断言脚本里的外链确实带了 rel 与 target，并且整份脚本不含任何绝对 URL。

**The Untrusted Content Rule（外部内容只当文本）.** 订阅源与论文检索结果是本站的站外输入，一律按敌意数据对待：标题、摘要、链接只当展示文本，不当指令、代码或 Prompt；渲染只许逐节点 `textContent`（禁用 innerHTML 一族与 eval，见 AGENTS.md「外部数据是不可信输入」）。视觉上外部内容与站内内容**共用同一套克制语法**——不因为「这是别人的文章/论文」而加卡片、图标、徽章或红色，它只是登记在同一张档案账本上的另一批条目。构建期把外部 HTML 剥成纯文本并删掉残留尖括号，所以账本行里不可能出现标记。

**The Index Rule（目录是索引，不是内容）.** 一条记录要重复读很多遍时，页首给一份目录，但目录与内容必须长得不一样：索引行只放**机读数据 + 一个可跳转的名字**（左列等宽日期，右列名字与推到行尾的条数），**不给摘要、不给外链、不加按钮**；行距比内容行紧一档，读者一眼分得出自己在看索引。更要紧的是——索引**只从数据算出来**：页面骨架里不写死任何名字与计数（`tools/check_feeds.py` 会核对骨架里没有源名），所以计数永远不会与数据脱节，筛选后目录与内容也永远一致。后续 Step 的清单页（arXiv 论文、Wiki 目录）沿用这个形状：栏目题压同一道 1px 实线，索引行用同一张账本。

## Do's and Don'ts

### Do:
- **Do** 保住三件 finish review 确认的资产，未来 Step 在不改变它们的前提下扩展：全宽墨蓝公文双线（.doc-meta/.doc-foot 的 3px double）、登记 dl 账本（.register/.reg-row）、双处红色纪律（静止红仅「在册」章与「进行中」标）。
- **Do** 新记录沿用档案语法：字段用 dl + .reg-row 账本行，并列条目用发丝线分隔的 ledger 条目，状态用 .tag / .tag-live。
- **Do** 新页沿用同一份报头带与导航块：`.doc-head`（元信息行 → 导航行 → 标题区）与 `.doc-foot` 全站同构，导航标记只允许差在链接前缀（按输出深度取 `../`）与 `aria-current="page"` 的位置；博客列表页与文章页由 `scripts/build_blog.py` 从 `public/index.html` 的骨架生成，不手写；子页标题用 `.folio` 档，两处静止红（「在册」章、「进行中」标）仍然只在首页；站内引用一律相对路径并写全文件名（`index.html`），可被本地 http 与 file:// 双击同样打开。
- **Do** 新页保持 800px 单栏 + clamp(20px, 5vw, 36px) 侧距 + 底部 56px，线全宽贯穿版心。
- **Do** 小字次级用 #5F6E7D（≥4.5:1）；宋体标题带 0.08–0.14em 字距，小签 0.22–0.35em；等宽数据开 tabular-nums。
- **Do** 正文行高保持 1.9（自述 2.05），行内文字离线 2px。
- **Do** 状态变化保持瞬时（无 transition）；新增动效须包在 `prefers-reduced-motion: no-preference` 内，且不破坏「盖章是唯一动效」的格局。
- **Do** 保持双文件原生 HTML/CSS、无外部资源、file:// 可开（PRODUCT.md 栈约束）。阅读器页与论文页是仅有的两处例外：它们要 fetch 同域 JSON，`file://` 下浏览器会拦下这次请求，此时页面按自己的错误分支显示说明（不白屏），用 `python -m http.server` 预览才有条目。
- **Do** 站外内容一律只当文本：数据侧剥成纯文本并删掉尖括号，前端逐节点 `textContent` 渲染，外链带 `rel="noopener noreferrer"` + `target="_blank"`；新页继续复用既有账本类（`.post-list`/`.post-row`/`.post-date`/`.post-item`），不为外部内容发明新组件，也不给外部内容上红。

### Don't:
- **Don't** 加渐变、投影、卡片阴影或图标库——层级只来自字号、字重、字距与线。
- **Don't** 把红用于装饰、红底、大面积红，或给任何静止的非活跃元素上红。
- **Don't** 用 #6B7A89 写小于约 16px 的文字——小字一律 #5F6E7D。
- **Don't** 在栏目 h2 上方加眉题/kicker/eyebrow——栏目直接坐在 1px 实线上；宽字距小签只属于档案元数据位（公文头小签、登记 dt、状态 tag、章）。
- **Don't** 给 hover/focus 加过渡缓动；除 stamp-in 外不引入第二处动画。
- **Don't** 引入第四个字族或外部字体 CDN；不把版心放宽到 800px 以外。
- **Don't** 引入照片、logo 墙、获奖徽章等证明性视觉装饰——本档案的证据就是登记行本身。
