---
name: 张易孝 · 实验档案
description: 课程实验记录站首页——像一份在册公文档案：冷白纸面、墨蓝线、宋体标题，红只标「当前/活跃」。
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
- 唯一动效：载入时盖章一次（0.5s, ease-out），reduced-motion 下静止常显。

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
**The Red Discipline Rule（红色纪律）.** 红是「活动」的语义色，不是装饰色。静止红只允许出现在「当前/活跃」标记上（现构建为「在册」章与「进行中」标两处）；hover 与 focus 可借用红作瞬时响应；禁止红底、红面、大面积红，禁止给非活跃元素上静止红。

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
- **Body**（400, 16px, 1.9）：全站正文基调；档案自述 17px / 2.05（≤38em）；条目描述 15px / 1.95（≤40em，深蓝灰）；登记值 16.5px。
- **Label**（700, 13px, 字距 0.35em）：宋体档案小签「个人实验档案」；登记 dt 12.5px / 0.3em（黑体，小屏 0.2em）；tag 12px / 0.22em（黑体）。
- **Mono**（400, 12px, 字距 0.05em, tabular-nums）：「最后更新」日期；登记邮箱链接 15.5px 带下划线；页脚 STEP n/12 字距 0.08em。

### Named Rules
**The Three-Voice Rule（三声部）.** 一段文字只有一种声音：身份与结构（姓名、栏目题、条目题、章、档案小签）用宋体加粗；叙述用系统黑体；日期、邮箱、步数计数器等机读数据用 Consolas 并开 tabular-nums。不引入第四个字族。

**The Wide-Tracking Rule（宽字距）.** 宋体的公文感来自放宽的字距：标题 0.08–0.14em，小签与章 0.22–0.35em；等宽 0.04–0.08em；黑体正文不额外加字距。480px 小屏下 h1 字距收至 0.1em 防溢出。

## Layout

单栏版心：`.page` max-width 800px，水平居中，左右 padding clamp(20px, 5vw, 36px)，底部 56px。所有结构线（双线、实线、发丝线）都是全宽贯穿这 800px 版心——线的宽度就是版心的宽度，这是「公文」而非「卡片」的关键。

垂直节奏（styles.css 实测值；构建未使用间距变量，frontmatter 的 `spacing` 只是常用档位摘要，值以本节为准）：公文头 padding 12px 2px → 档案头 padding 56px 0 44px（小屏 44px 0 36px）→ 栏目题 padding 22px 0 4px + margin-bottom 6px → 登记行 padding 13px 2px → 自述 margin-top 14px → 条目 padding 20px 2px → 页脚 margin-top 64px、padding 16px 2px 0。行内文字统一从线上水平缩进 2px。

基线行：公文头、条目头、页脚都是 `display: flex; align-items: baseline` + `flex-wrap: wrap`，gap 16px（条目头 14px / row-gap 8px）；tag 靠 `margin-left: auto` 推到行尾。

响应式：唯一断点 max-width 480px——正文降到 15.5px，档案头收紧，h1 字距收至 0.1em，章缩小（14px、top 48px、padding 6px 7px 6px 12px），登记列 7em → 5.5em，dt 字距收至 0.2em。390/320px 防溢出是组合拳：clamp() 字号、所有基线行可换行、`white-space: nowrap` 只用于原子短数据（日期、tag）——换行时它们作为整体下移，不在中间断开。

### Named Rules
**The Three-Weight Rule（三级线）.** 线分三档，各司其职：3px double 墨蓝双线只用于文档头尾（`.doc-meta` 上边、`.doc-foot` 上边）——它是档案的装订线；1px solid 墨蓝实线开栏目（`.sec h2` 上边）；rgba(28,43,58,.24) 发丝线分隔同级行（登记行、条目之间）；rgba(28,43,58,.45) 浓发丝线只作 tag 边框、链接下划线与滚动条拇指。不发明第四档线，也不把双线用到头尾之外。

## Elevation & Depth

全系统平面：没有任何投影式 elevation，没有 tonal 层叠。深度由三样东西表达：线的粗细层级（双线 > 实线 > 发丝线）、宋体宽字距带来的「印制感」、以及红章的 0.92 不透明度（微透纸面，像真盖的章）。唯一的 box-shadow 是章的内嵌双环 `inset 0 0 0 2px var(--paper), inset 0 0 0 3px var(--red)`——在 2px 红边框内再画一圈细红环，是「画」出来的印章纹样，不是「抬」起来的阴影。

### Named Rules
**The Flat Archive Rule（平面档案）.** 禁止投影。盒阴影在这个系统里只有一个合法形态：印章的内嵌双环，用来画纹样。任何用 shadow 表达「浮起」「卡片」「弹层」的写法都不属于这个世界。

## Shapes

形状语言是「纸与线」，不是「圆角卡片」。全站只有三个圆角值：tag 2px、章 3px、滚动条拇指 6px（浏览器 chrome，不算组件）。没有卡片容器、没有面板、没有大圆角。边框词汇：2px 红实线（章）+ 内嵌双环、1px 边框（tag）。整体轮廓由全宽横线切分，垂直方向没有分隔柱或侧栏。

## Components

### 公文头 Document Header Bar（.doc-meta / .doc-label / .doc-date）
- 全宽档案条：左「个人实验档案」宋体小签（13px / 0.35em），右「最后更新」等宽日期（12px / 0.05em / tabular-nums / nowrap）。
- 上边 3px double 墨蓝（装订线），下边 1px solid 墨蓝；flex 基线对齐，gap 16px，可换行。

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

### 公文尾 Document Footer（.doc-foot / .foot-step）
- 上边 3px double 墨蓝（与公文头呼应，装订线收口），flex 基线，gap 16px，可换行。
- 左说明 12.5px / 0.04em 深蓝灰；右「STEP 1/12」等宽 0.08em / tabular-nums——12 步迭代的进度印记。

### 全局镀铬 Global Chrome
- `::selection`：墨蓝底、纸白字。
- `:focus-visible`：2px solid 红、offset 3px（键盘焦点可见性承诺）。
- 链接：继承墨蓝、1px 下划线、offset 3px，hover 变红。
- 滚动条：12px 宽，透明轨道，拇指浓发丝色 + 3px 纸色边框 + 6px 圆角。
- `color-scheme: light`；body `accent-color` 墨蓝；favicon 为内联 SVG（墨蓝方块 + 纸色宋体「档」字）；`@media print` 底色转纯白 #fff——档案随时可打印归档。

## Do's and Don'ts

### Do:
- **Do** 保住三件 finish review 确认的资产，未来 Step 在不改变它们的前提下扩展：全宽墨蓝公文双线（.doc-meta/.doc-foot 的 3px double）、登记 dl 账本（.register/.reg-row）、双处红色纪律（静止红仅「在册」章与「进行中」标）。
- **Do** 新记录沿用档案语法：字段用 dl + .reg-row 账本行，并列条目用发丝线分隔的 ledger 条目，状态用 .tag / .tag-live。
- **Do** 新页保持 800px 单栏 + clamp(20px, 5vw, 36px) 侧距 + 底部 56px，线全宽贯穿版心。
- **Do** 小字次级用 #5F6E7D（≥4.5:1）；宋体标题带 0.08–0.14em 字距，小签 0.22–0.35em；等宽数据开 tabular-nums。
- **Do** 正文行高保持 1.9（自述 2.05），行内文字离线 2px。
- **Do** 状态变化保持瞬时（无 transition）；新增动效须包在 `prefers-reduced-motion: no-preference` 内，且不破坏「盖章是唯一动效」的格局。
- **Do** 保持双文件原生 HTML/CSS、无外部资源、file:// 可开（PRODUCT.md 栈约束）。

### Don't:
- **Don't** 加渐变、投影、卡片阴影或图标库——层级只来自字号、字重、字距与线。
- **Don't** 把红用于装饰、红底、大面积红，或给任何静止的非活跃元素上红。
- **Don't** 用 #6B7A89 写小于约 16px 的文字——小字一律 #5F6E7D。
- **Don't** 在栏目 h2 上方加眉题/kicker/eyebrow——栏目直接坐在 1px 实线上；宽字距小签只属于档案元数据位（公文头小签、登记 dt、状态 tag、章）。
- **Don't** 给 hover/focus 加过渡缓动；除 stamp-in 外不引入第二处动画。
- **Don't** 引入第四个字族或外部字体 CDN；不把版心放宽到 800px 以外。
- **Don't** 引入照片、logo 墙、获奖徽章等证明性视觉装饰——本档案的证据就是登记行本身。
