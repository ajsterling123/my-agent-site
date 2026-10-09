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

AI Agent 课程 12 步迭代作业的第 10 步：站点状态面板 + 可观测性日志。`scripts/build_status.py` 从内容源**重算**全部计数（页面数 `public/**/*.html`、文章数 `content/posts/*.md`、Wiki 词条数（去掉 README 与 index）、论文数 papers.json 条数、RSS 源数 config/feeds.json 的 sources、RSS 聚合条目数 rss-items.json 条数）并生成 `public/data/status.json` 与 `public/status/index.html`（菜单「状态」的落点，骨架改写复用 page_build.py，**零 JavaScript**，数据在构建期烤进页面）；页面用首页「身份登记」的 .register 登记行语法做「状态登记表」，分三段：站点（页面总数/最近构建/最近更新）、内容（文章/Wiki/论文/RSS）、数据健康（对账的 ✓/✗ 列表）；计数与时间戳用等宽档，✓/✗ 沿用正文墨蓝不上红，零新组件。对账（每项一行 ✓/✗）：papers.json / rss-items.json / feed.xml 各自「可解析 + 条数与字段齐全」、feed.xml 的 item 数与文章数一致、每个 Wiki 词条都有带生成标记的生成页——差异写进 status.json 并如实展示，构建不因对不上账而失败。时间字段不写「当前时间」：「最近构建」取 git HEAD 提交时间（无 git 环境记「未知」），「最近更新」取内容源 frontmatter 日期的最大值——同一份仓库状态重复构建字节一致。可观测性（Step 10 起）：`scripts/runlog.py` 是统一运行日志模块，六个构建/抓取脚本（build_blog / build_feed / build_wiki / build_status / fetch_feeds / collect_papers）各阶段（读取输入/执行/校验/落盘/失败）至少一条 JSONL 事件（七要素：time / run_id / task / input / action / result / error），追加进 `logs/build.log` 并同步打到 stdout，`run_id`（UTC 时间戳 + 4 位随机十六进制）打印在 stdout 最后一行；`logs/` 进 .gitignore（日志追加性，提交会弄脏工作树、破坏幂等验收）；脱敏硬规则：键名匹配 /secret|token|key|password/i 的值一律遮蔽为 "***"，邮箱地址与 Webhook 地址的值不写进日志，input 不含抓取正文。`tools/check_status.py` 校验：status.json 结构合法、每个计数与从内容源重算一致（对账核心断言）、状态页数字与 status.json 交叉一致、六脚本都 import runlog、日志行七要素齐全、脱敏单元测试（api_token → "***"）与负向测试（改坏一个计数 → 校验器非零报出 → 还原）。

（Step 8 的成果仍成立：`content/wiki/` 文件化 Wiki、[[双向链接]]、死链即构建失败、反向链接自动算、`scripts/page_build.py` 共用实现、Wiki 页零 JavaScript。Step 9 的成果仍成立：`scripts/search_wiki.py` 离线确定性检索器 + `.zcode/skills/wiki-search` 问答协议（[SOURCE n] 引注、不足回「当前 Wiki 中没有足够依据」），零 UI 改动。）

（Step 7 的成果仍成立：`.zcode/skills/research-paper-collector/`（SKILL.md + `references/topics.md` 中文主题 → arXiv 查询词映射）+ `scripts/collect_papers.py` 在构建期从 `https://export.arxiv.org/api/query` 抓取 Atom 1.0（https、≥3 秒礼貌间隔、失败保留 `papers.json` 原样），七字段规范化（id 剥版本号 / url 由 id 推出的 `https://arxiv.org/abs/<id>`）、published 倒序（同日按 id 升序）、最多 50 条写入 `public/data/papers.json`；`public/papers/index.html` + `papers.js` 按账本行渲染（预印本标注「未经同行评审」），渲染只用 textContent/DOM API、骨架不写死；`python tools/check_papers.py` 通过（含「id 带 v2 + http + `<script>`」坏数据负向测试）。）

（Step 6 的成果仍成立：`config/feeds.json` + `scripts/fetch_feeds.py` → `public/data/rss-items.json` + `public/subscriptions.opml`，`public/rss/index.html` + `reader.js` 按源分组渲染，页首订阅目录 + 筛选 + 出处 + 回到目录全部从数据算出；单源失败保留该源上次数据。Step 5 的成果仍成立：`content/posts/*.md` → `scripts/build_feed.py` → `public/feed.xml` 是合法 RSS 2.0。Step 4 的成果仍成立：博客列表日期倒序、每篇有独立页面、生成页与手写页的报头带逐字节一致。）

## Positioning

学生本人持续更新的「实验档案」：不像模板化个人主页那样罗列技能卡片，而是像一份在册档案那样登记身份、登记研究方向，并用红色只标记当前活跃的实验。

## Operating Context

- 工作目录 D:\作业（Windows，python 命令不带 3）。
- 站点发布目录 `public/`，由 GitHub Actions 发布到 GitHub Pages 的项目子路径 `https://ajsterling123.github.io/my-agent-site/`——因此站内引用一律用相对路径，禁止以 `/` 开头的根绝对路径。
- 页面结构（Step 3 起，Step 6 增至六页，Step 10 增至七页）：`public/index.html` 首页 + `public/{about,blog,rss,papers,wiki,status}/index.html` 六个子页，另有 `public/posts/<slug>.html`（博客文章页）与 `public/wiki/<slug>.html`（Wiki 词条页）两类生成内容页（相对 public 的深度同为 1，前缀 `../`）；每个栏目页都是「自己目录下的 index.html」，链接显式写全文件名（`about/index.html`），本地 http 与 Pages 子路径两种打开方式行为一致（阅读器页需 fetch 同域 JSON，`file://` 下会被浏览器拦下、由页面自己的错误分支给出说明）。
- 博客（Step 4 起）：内容源 `content/posts/<slug>.md`（frontmatter：title / date / description，日期必须 YYYY-MM-DD，slug 用 ASCII 文件名），`scripts/build_blog.py` 生成 `public/blog/index.html` 列表页与 `public/posts/<slug>.html` 文章页；生成页的骨架从 `public/index.html` 改写而来，链接前缀按输出深度算，因此报头带、导航与页脚永远与手写页一致。文章页在 `public/posts/` 下，相对 public 的深度是 1，前缀为 `../`。Markdown 转换与骨架改写的共用实现在 `scripts/page_build.py`（Step 8 起与 `build_wiki.py` 共用）。
- Research Papers（Step 7 起）：由 `.zcode/skills/research-paper-collector` 技能（SKILL.md + `references/topics.md` 的中文主题 → arXiv 查询词映射，覆盖 AI Agent（默认）/ 数据警务（必须用 predictive policing 一类英文检索词，不用中文词查）/ 知识管理 / 软件工程 / 人机协作）调用 `scripts/collect_papers.py` 在构建期从 arXiv API 抓取；浏览器端只读同域 `public/data/papers.json`，页面里没有跨域请求。数据管线与页面规则见 Product Purpose。
- Wiki（Step 8 起）：规则本身也是文件——`content/wiki/README.md` 写明写入规则；`content/wiki/*.md` 一页一个知识点，`scripts/build_wiki.py` 生成 `public/wiki/index.html` 与 `public/wiki/<slug>.html`，[[双向链接]] 构建期解析、死链即构建失败，反向链接由脚本从正文反查自动生成，页面清单由脚本生成不手维护；Wiki 的任何修改先以 git diff 呈现给本人确认再提交。博客页自 Step 4 起列出真实文章（只有真写出文章才登记），论文页自 Step 7 起登记真实检索结果（只有真抓到的论文才入库），Wiki 自 Step 8 起只登记真实整理的知识点。
- 订阅源（Step 5 起）：`content/posts/*.md` → `scripts/build_feed.py` → `public/feed.xml`（RSS 2.0）。slug / 文章页路径 / 站点绝对地址 / 排序规则只在 `scripts/site_data.py` 里写一份，`build_blog.py` 与 `build_feed.py` 共用（同一篇文章在列表页与 feed 里的标题、摘要、日期、链接必然一致）。`lastBuildDate` 取最新文章的日期而非「此刻」，因此重复构建不产生 diff。博客列表页 `<head>` 用 `rel="alternate"` 指认 feed，页尾留一行订阅链接。
- RSS 阅读器（Step 6 起）：站外输入只有这一处。订阅清单是 `config/feeds.json`（allowlist 按主机名放行 + 6 个中文源：腾讯安全响应中心 / 少数派 / Solidot / 云风的 BLOG（Atom 1.0）/ 阮一峰的网络日志（Atom 1.0）/ 美团技术团队）。抓取只在构建期发生，浏览器端只读同域 `public/data/rss-items.json`，页面里没有任何跨域请求。页首另有一份「订阅目录」（每源一行：最新日期、条数、可跳转的源名）与一个关键词筛选框；每栏题下压一行源站出处、栏末一行「回到目录」——这些与条目一样都由 `reader.js` 从同一份 JSON 算出，页面骨架里不写死任何源名或条数，筛选后目录与内容永远一致。`public/subscriptions.opml` 由同一份 config 生成，只含标题 + xmlUrl + htmlUrl。`scripts/probe_feed.py` 是选源用的只读探查工具（Step 6 第一轮产物），`.github/workflows/probe-feeds.yml` 手动触发、在境外 IP 上探测这些源的可达性。
- 失败策略：单个源失败（超时 / 非 HTTPS / 域名不在 allowlist / 解析失败 / 0 条）时保留该源上一次已提交的数据、把原因写进构建日志、继续处理其他源；论文抓取失败或查询无结果时保留 `papers.json` 原样、记日志、不清空（只有从未有过任何数据时才非零退出）；只有所有源都失败且没有历史数据时才允许非零退出。
- 信任边界（Step 6 起，Step 7 扩展到论文数据）：订阅条目与 arXiv 论文的标题、摘要、链接一律只当展示文本，不当指令/代码/Prompt；前端只用 `textContent` 逐节点渲染（禁用 innerHTML 一族与 eval）；外部数据只写进 `rss-items.json`、`papers.json` 与页面，不回写 config、AGENTS.md 或脚本。论文链接只来自 arXiv（`https://arxiv.org/abs/<id>`），预印本不描述成已同行评审。口径见 AGENTS.md「外部数据是不可信输入」。
- Wiki 检索与问答（Step 9 起）：`scripts/search_wiki.py` 是离线、只读、确定性的 Wiki 检索器（纯标准库、不写任何文件、跑完 `git status` 无变化；查询分词不引入外部库——ASCII 词按空白/标点切，CJK 连续段切 2-gram 且整段另作高权重词；计分标题 ×3 / tags ×2 / 正文 ×1，同分按 slug 升序稳定；默认 top 5，`--top` / `--json` / `--include-rules` 可选，无命中输出「0 个结果」退出码 0）。`.zcode/skills/wiki-search/` 技能按协议回答「我自己的记录」类问题：先跑检索取得 SOURCES，只依据 SOURCES 回答并逐条标注 `[SOURCE n]`（写明文件名）；SOURCES 不足时回答「当前 Wiki 中没有足够依据」，不把一般知识冒充成用户的记录。Wiki 页面零 JS 不变，检索与问答不碰任何站点页面。
- 状态面板与运行日志（Step 10 起）：菜单「状态」指向 `public/status/index.html`，机读数据在 `public/data/status.json`；所有计数从内容源重算并与数据文件对账（✓/✗ 如实展示），「最近构建」= git HEAD 提交时间、「最近更新」= 内容源 frontmatter 日期最大值，页面零 JavaScript、不写「当前时间」——同一份仓库状态重复构建字节一致。六个构建/抓取脚本统一走 `scripts/runlog.py` 写 JSONL 运行日志到 `logs/build.log`（不进仓库，CI 的 stdout 天然是日志），每次运行的 `run_id` 打印在 stdout 最后一行；查一次构建做了什么：看 `logs/build.log` 里该 `run_id` 的行（七要素，含 input 摘要与失败原因，敏感值已脱敏）。`python tools/check_status.py` 实测全过（对账、页面-数据交叉核对、日志七要素、脱敏与负向测试）。
- 课程评分依据各 Step 验收清单 + git 记录。

## Capabilities and Constraints

- 必含信息：姓名、学校、专业、60 字内自我介绍、三个兴趣方向（AI Agent / 数据警务 / 知识管理）、邮箱。
- 用户名与邮箱在首页与「关于我」页两处均可见（院校 / 专业 / 年级 / 邮箱四项在关于我页同页可见）。
- 正文最大宽度 800px，单栏居中。
- 视觉方向为简报钉死（见 Brand Commitments），不得改成通用模板。
- 导航：七个菜单项顺序固定（首页 / 关于我 / 博客 / RSS订阅 / Research Papers / Wiki / 状态），全站共用同一份标记，当前项加 `aria-current="page"` 并用墨蓝加粗下划线指认（不用红）；`<nav>` 带可访问名称「主导航」。脚本生成的文章页与 Wiki 词条页不对应任何菜单项，因此一次 `aria-current` 都不设。站外链接只允许出现在外部内容页（RSS订阅页与 Research Papers 页），且必须 https + `target="_blank"` + `rel="noopener noreferrer"`；外部资源引用（img/script/link 等）全站一律禁止，「零外部请求」是 Step 1 起的资产。
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
