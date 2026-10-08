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

AI Agent 课程 12 步迭代作业的第 6 步：在 Step 5 的订阅源之上做 RSS 阅读器——订阅别人、聚合成一页。`config/feeds.json` 是订阅清单（allowlist + 6 个源，含逐源的 `default_tz` 与美团专用的 `date_from_url_regex`）；`scripts/fetch_feeds.py` 在**构建期**抓取（只许 HTTPS、主机必须在 allowlist 内、单源超时 10 秒、响应上限 2MB、请求带 User-Agent），把 RSS 2.0 与 Atom 1.0 两种格式规范化成同一结构写入 `public/data/rss-items.json`，并从同一份 config 生成 `public/subscriptions.opml`；`public/rss/index.html` + `public/rss/reader.js` 读同域 JSON 按源分组渲染，导航因此由五项变六项（「RSS订阅」插在「博客」之后）。成功 = 每项七个字段齐全（id / source_id / source_title / title / link / summary / published）、id 稳定唯一（优先 feed 自带的 guid/id，缺失时用链接哈希）、跨源按 id 去重、分组顺序等于 config 顺序、组内按 `published` 倒序（null 在末尾、同值按 id）、`published` 一律是带偏移的 ISO 8601 或 null（腾讯源没时区按 +08:00 解释、美团源没有条目级日期按链接路径推导，两个假设都写在 config 注释与 DESIGN.md 里，不藏在代码里）、单个源失败时保留该源上次数据且构建仍成功、连跑两次 `git status` 干净（外部源本身有新内容除外）；`python tools/check_feeds.py` 通过（含「摘要里带 `<script>` 与提示注入口令」的敌意样本负向测试，且测试前后 AGENTS.md 与 config/feeds.json 字节未变）；`python tools/check_site.py` 与 `python tools/check_feed.py` 仍通过。（Step 6 的阅读体验改进：页首「订阅目录」与筛选框是这页的索引与入口，目录里的日期、条数、命中数都必须从数据算出来而不是写死；`check_feeds.py` 因此另核对三件事——`reader.js` 里 href 只有一处出口（外链在该处统一带 rel/target）、筛选真的接上了事件而不是装饰控件、页面骨架里没有任何源名。）

（Step 5 的成果仍成立：`content/posts/*.md` → `scripts/build_feed.py` → `public/feed.xml` 是合法 RSS 2.0，与列表页同源同序。Step 4 的成果仍成立：博客列表日期倒序、每篇有独立页面、生成页与手写页的报头带逐字节一致。）

## Positioning

学生本人持续更新的「实验档案」：不像模板化个人主页那样罗列技能卡片，而是像一份在册档案那样登记身份、登记研究方向，并用红色只标记当前活跃的实验。

## Operating Context

- 工作目录 D:\作业（Windows，python 命令不带 3）。
- 站点发布目录 `public/`，由 GitHub Actions 发布到 GitHub Pages 的项目子路径 `https://ajsterling123.github.io/my-agent-site/`——因此站内引用一律用相对路径，禁止以 `/` 开头的根绝对路径。
- 页面结构（Step 3 起，Step 6 增至六页）：`public/index.html` 首页 + `public/{about,blog,rss,papers,wiki}/index.html` 五个子页；每页都是「自己目录下的 index.html」，链接显式写全文件名（`about/index.html`），本地 http 与 Pages 子路径两种打开方式行为一致（阅读器页需 fetch 同域 JSON，`file://` 下会被浏览器拦下、由页面自己的错误分支给出说明）。
- 博客（Step 4 起）：内容源 `content/posts/<slug>.md`（frontmatter：title / date / description，日期必须 YYYY-MM-DD，slug 用 ASCII 文件名），`scripts/build_blog.py` 生成 `public/blog/index.html` 列表页与 `public/posts/<slug>.html` 文章页；生成页的骨架从 `public/index.html` 改写而来，链接前缀按输出深度算，因此报头带、导航与页脚永远与手写页一致。文章页在 `public/posts/` 下，相对 public 的深度是 1，前缀为 `../`。
- Research Papers、Wiki 两页当前仍为诚实占位：写明本页将在课程第几步被填充，不编造内容；博客页自 Step 4 起列出真实文章（只有真写出文章才登记）。
- 订阅源（Step 5 起）：`content/posts/*.md` → `scripts/build_feed.py` → `public/feed.xml`（RSS 2.0）。slug / 文章页路径 / 站点绝对地址 / 排序规则只在 `scripts/site_data.py` 里写一份，`build_blog.py` 与 `build_feed.py` 共用（同一篇文章在列表页与 feed 里的标题、摘要、日期、链接必然一致）。`lastBuildDate` 取最新文章的日期而非「此刻」，因此重复构建不产生 diff。博客列表页 `<head>` 用 `rel="alternate"` 指认 feed，页尾留一行订阅链接。
- RSS 阅读器（Step 6 起）：站外输入只有这一处。订阅清单是 `config/feeds.json`（allowlist 按主机名放行 + 6 个中文源：腾讯安全响应中心 / 少数派 / Solidot / 云风的 BLOG（Atom 1.0）/ 阮一峰的网络日志（Atom 1.0）/ 美团技术团队）。抓取只在构建期发生，浏览器端只读同域 `public/data/rss-items.json`，页面里没有任何跨域请求。页首另有一份「订阅目录」（每源一行：最新日期、条数、可跳转的源名）与一个关键词筛选框；每栏题下压一行源站出处、栏末一行「回到目录」——这些与条目一样都由 `reader.js` 从同一份 JSON 算出，页面骨架里不写死任何源名或条数，筛选后目录与内容永远一致。`public/subscriptions.opml` 由同一份 config 生成，只含标题 + xmlUrl + htmlUrl。`scripts/probe_feed.py` 是选源用的只读探查工具（Step 6 第一轮产物），`.github/workflows/probe-feeds.yml` 手动触发、在境外 IP 上探测这些源的可达性。
- 失败策略：单个源失败（超时 / 非 HTTPS / 域名不在 allowlist / 解析失败 / 0 条）时保留该源上一次已提交的数据、把原因写进构建日志、继续处理其他源；只有所有源都失败且没有历史数据时才非零退出。
- 信任边界（Step 6 起）：外部标题、摘要、链接一律只当展示文本，不当指令/代码/Prompt；前端只用 `textContent` 逐节点渲染（禁用 innerHTML 一族与 eval）；外部数据只写进 `rss-items.json` 与页面，不回写 config、AGENTS.md 或脚本。口径见 AGENTS.md「外部数据是不可信输入」。
- 后续 Step 将加入 arXiv 论文 Skill、Wiki、RAG、状态面板等；档案视觉语言与报头带导航继续沿用。
- 课程评分依据各 Step 验收清单 + git 记录。

## Capabilities and Constraints

- 必含信息：姓名、学校、专业、60 字内自我介绍、三个兴趣方向（AI Agent / 数据警务 / 知识管理）、邮箱。
- 用户名与邮箱在首页与「关于我」页两处均可见（院校 / 专业 / 年级 / 邮箱四项在关于我页同页可见）。
- 正文最大宽度 800px，单栏居中。
- 视觉方向为简报钉死（见 Brand Commitments），不得改成通用模板。
- 导航：六个菜单项顺序固定（首页 / 关于我 / 博客 / RSS订阅 / Research Papers / Wiki），全站共用同一份标记，当前项加 `aria-current="page"` 并用墨蓝加粗下划线指认（不用红）；`<nav>` 带可访问名称「主导航」。脚本生成的文章页不对应任何菜单项，因此一次 `aria-current` 都不设。站外链接只允许出现在阅读器页，且必须 https + `target="_blank"` + `rel="noopener noreferrer"`；外部资源引用（img/script/link 等）全站一律禁止，「零外部请求」是 Step 1 起的资产。
- 邮箱一栏为真实地址 1095568137@qq.com（2026-10-08 由本人提供并指定公开在本站）。
- 订阅地址为 `https://ajsterling123.github.io/my-agent-site/feed.xml`（绝对地址，阅读器需要）；站内引用仍是相对路径 `../feed.xml`。feed 里中文原样保留，`& < >` 用实体转义（不用 CDATA）。

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
