# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

原生静态 HTML + CSS（用户简报钉死，2026-10-07）：只用原生 HTML/CSS；index.html 与 styles.css 分离；语义化标签；不引入框架、外部库和字体 CDN；必须能双击打开（file://）也能被 `python -m http.server 8080` 访问。无构建步骤。

## Users

- 主要用户：课程任课老师与助教——按各 Step 验收清单核对页面（个人信息齐全、可打开、手机不破版）。
- 次要用户：张易孝本人与同学——把本站当作课程实验记录的入口，随课程推进回访。

## Product Purpose

AI Agent 课程 12 步迭代作业的第 3 步：在首页之外建起全站菜单栏与四个子页面（关于我 / 博客 / Research Papers / Wiki），整站仍是一份持续更新的档案。成功 = 五个页面双击与本地服务器均可打开、菜单从任意页面都能互相跳转且当前项高亮正确、390px 手机宽度不出现横向滚动、首页原有个人信息一字未改。

## Positioning

学生本人持续更新的「实验档案」：不像模板化个人主页那样罗列技能卡片，而是像一份在册档案那样登记身份、登记研究方向，并用红色只标记当前活跃的实验。

## Operating Context

- 工作目录 D:\作业（Windows，python 命令不带 3）。
- 站点发布目录 `public/`，由 GitHub Actions 发布到 GitHub Pages 的项目子路径 `https://ajsterling123.github.io/my-agent-site/`——因此站内引用一律用相对路径，禁止以 `/` 开头的根绝对路径。
- 页面结构（Step 3 起）：`public/index.html` 首页 + `public/{about,blog,papers,wiki}/index.html` 四个子页；每页都是「自己目录下的 index.html」，链接显式写全文件名（`about/index.html`），三种打开方式（本地 http / Pages 子路径 / file:// 双击）行为一致。
- 博客、Research Papers、Wiki 三页当前为诚实占位：写明本页将在课程第几步被填充，不编造内容。
- 后续 Step 将加入 Markdown 博客、RSS、arXiv 论文 Skill、Wiki、RAG、状态面板等；档案视觉语言与报头带导航继续沿用。
- 课程评分依据各 Step 验收清单 + git 记录。

## Capabilities and Constraints

- 必含信息：姓名、学校、专业、60 字内自我介绍、三个兴趣方向（AI Agent / 数据警务 / 知识管理）、邮箱。
- 用户名与邮箱在首页与「关于我」页两处均可见（院校 / 专业 / 年级 / 邮箱四项在关于我页同页可见）。
- 正文最大宽度 800px，单栏居中。
- 视觉方向为简报钉死（见 Brand Commitments），不得改成通用模板。
- 导航：五个菜单项顺序固定（首页 / 关于我 / 博客 / Research Papers / Wiki），五页共用同一份标记，当前项加 `aria-current="page"` 并用墨蓝加粗下划线指认（不用红）；`<nav>` 带可访问名称「主导航」。
- 邮箱一栏现为占位文本「【填你的真实邮箱】」（Step 3 按用户指定替换原示例地址），待本人填入真实地址后生效。

## Brand Commitments

- 概念「实验档案」——整站像一份持续更新的个人档案。
- 配色：冷白 #F5F6F4 打底；墨蓝 #1C2B3A 做文字与分隔线；蓝灰 #6B7A89 做次级文字；红 #B5322C 只用于「当前/活跃」标记。
- 字体：大标题宋体系（SimSun/Songti SC）加粗；正文系统黑体；日期用 Consolas 等宽小字。
- 页首一行等宽小字「最后更新：<日期>」。
- 克制：不用渐变、卡片阴影和图标库。

## Evidence on Hand

- 身份信息（2026-10-07 用户当面确认）：姓名 张易孝；学校 江苏警官学院；专业 数据警务技术；年级 大四。
- 兴趣方向为简报示例值，用户未另给：AI Agent、数据警务、知识管理。
- 关于我页的「在学课程」栏暂无真实课表，按事实留「待补」占位，未编造。
- 技能工具链一栏只写本项目可得证据的三项（原生 HTML/CSS、Git + Actions + Pages、AI Agent 协作），不写熟练度评级。
- 无照片、无 logo、无获奖/项目/链接等证明材料；不得虚构此类内容。

## Product Principles

1. 档案语言优先：用登记行、条目、状态标记组织信息，不做营销式分区。
2. 红色纪律：#B5322C 只出现在「当前/活跃」标记上。
3. 克制即风格：层级靠字号、字重与细线，不靠装饰。
4. 为 12 步迭代留缝：语义结构清晰，后续 Step 能沿用同一套档案语言。

## Accessibility & Inclusion

- 正文与小号次级文字对比度 ≥ 4.5:1（蓝灰做小字时需加深至达标变体）。
- 键盘焦点可见；prefers-reduced-motion 下无动画。
- 手机 390px 宽不破版。
