---
version: 2
slug: "papers-html"
primary_target: "public/papers/index.html"
related_targets: ["public/papers/papers.js", "public/data/papers.json", "public/index.html", "public/blog/index.html"]
---

# Surface brief: public/papers/index.html —— Research Papers（已实现）

## Scope & visitor mode

整站页面之一：无外部资源、共用 `public/styles.css`。与 RSS订阅 页同一模式——条目由 `public/papers/papers.js` 读同域 `../data/papers.json` 后逐节点渲染（构建期由 `scripts/collect_papers.py` 经 `.zcode/skills/research-paper-collector` 技能抓取并规范化）。访客模式 **Read**：读者（课程验收的老师/助教、本人）要一眼看清「最近检索到了哪些 arXiv 论文、每条是谁写的、原文在哪」，并知道这些是预印本、不是已同行评审。

## Audience, job, action, proof, constraints

- 受众：课程任课老师/助教（核对论文数据链路：Skill → 抓取脚本 → JSON → 页面）、同学、本人回访。
- 任务：按提交日期倒序浏览最近的论文，点标题去 arXiv 原文读摘要；条目多时靠折叠的摘要收住行高。
- 行动点：论文标题是站外跳转（新窗口，`target="_blank"` + `rel="noopener noreferrer"`）；摘要是展开（原生 `<details>`/`<summary>`，无 JS 逻辑）；页尾给出换主题的入口（技能里的映射表）。
- 证明：页面本身就是证明——10 条真实条目（2026-10-09 抓取，默认主题 AI Agent），每条的 `url` 都是由 id 推出的 `https://arxiv.org/abs/<id>`；条目与计数全部由脚本从同一份 JSON 算出，骨架里不写死任何论文（`tools/check_papers.py` 会核对）；同一个校验器还会跑一条「id 带 v2 + http + `<script>`」的坏数据负向测试。
- 约束：外部内容只当纯文本（`textContent` 逐节点渲染）；不加卡片、图标、阴影、徽章；预印本不是「活动」，静止态不用红；禁 JS 时不白屏（`<noscript>` 回退说明含机读数据入口）；480px 单列、390/320px 无横向滚动（已实测）。

## Chosen direction & memorable moment

沿用「实验档案」世界，本页是档案里的**论文引文登记册**：与博客列表同一张账本（`.post-list` / `.post-row` / `.post-date` / `.post-item`），一行一条论文——左列等宽日期，右列宋体标题（外链）、次级色作者行、可展开的摘要与一行等宽来源标记，行间发丝线。它不给论文任何特殊待遇：别人的论文和本站文章在同一张账本上、用同一套字与线。
难忘点：**每条末尾那行等宽小字「arXiv · 预印本，未经同行评审」**——诚实声明被写进每一条登记，与占位页时代「宁可留空也不编造」一脉相承。

## Direction contract

THESIS: 论文登记的价值在出处可核对与诚实标注——id 剥版本号、url 由 id 推出、预印本写明未经同行评审。

OWN-WORLD: 与首页同一个世界。本页复用博客列表的账本类（`.post-list` / `.post-row` / `.post-date` / `.post-item`）与 `.sec`（栏目题压 1px 墨蓝实线）；自己的 CSS 全收在 `styles.css` 的「Research Papers」注释块里，仅四条小规则：`details.paper-summary`（summary 是页脚说明句那一档小字）、`p.paper-source`（等宽小字的来源标记）、`.paper-note`（尾注）；作者行与摘要正文直接落 `.post-item p` 的次级档。零新色、零新字体、零新圆角、零阴影、零动效。

STORY: 访客点「Research Papers」进来 → 读一段说明（数据从哪来、预印本声明）→ 逐条浏览账本行，点标题去 arXiv 原文（新窗口），想知道细节就展开摘要 → 页尾知道想换主题改的是技能里的映射表。骨架里没有条目，全部由 papers.js 从同域 JSON 生成。

FIRST VIEWPORT: 报头带（导航当前项「Research Papers」墨蓝加粗下划线）→ `.folio` 页名「Research Papers」→ 一段 `.intro` 说明（检索发生在构建期、arXiv 是预印本平台）→「论文登记」栏目题与首屏内的前几条账本行。

FORM: 页面骨架手工写成（与其它五个手写页同构，导航块逐字节一致）；条目、计数、空状态全部由脚本从同域 JSON 生成；数据由抓取脚本生成，不手改。

FINISH: 与整站同批通过 `tools/check_site.py`（本页在 `public/papers/` 下，是 Step 7 起允许站外导航链接的两个外部内容页之一）与 `tools/check_papers.py`（七字段 / id 无版本后缀 / url 可由 id 推出 / 排序可复现 / 零禁用 API / 外链单出口 / 骨架不写死条目 / 坏数据负向测试）；`deploy.yml` 的 Check 步含 `check_papers.py`（校验进 CI、抓取留本地，Step 6 口径）。DESIGN.md 已补「论文账本 Papers」组件规格。

## Signature interaction

摘要展开：本页唯一的交互动作，用的是原生 `<details>`/`<summary>`——浏览器自带的展开/收起与三角标记，零 JS、零新组件。摘要长（arXiv 摘要常见上千字符），默认折叠让账本行保持紧凑，展开才是完整摘要。
其余动作：论文标题的站外跳转（新窗口，沿用全局链接响应，hover 变红）。全站唯一动效仍是首页的盖章。

## Unresolved decisions

- 数据新鲜度：`papers.json` 是提交进仓库的生成物，抓取按 Step 6 口径留本地（校验进 CI），线上是「最后一次本地抓取」的快照。要刷新就再跑一遍技能工作流。
- 条目上限 50 条、默认 10 条由抓取脚本的 `--limit` 控制；本页不分页、不设筛选——10 条一屏读完，等某个主题的登记长起来再谈（到时可沿用 The Index Rule 加目录）。
- 换主题只改 `references/topics.md` 的映射或 `--query`；页面骨架与渲染脚本不需要动。
