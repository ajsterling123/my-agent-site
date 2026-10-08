# AGENTS.md —— 本仓库的长期约束

任何 Step、任何会话、任何 Agent 动手之前先读这份文件。视觉细节以 `DESIGN.md` 为准，产品事实以 `PRODUCT.md` 为准；本文件不复述它们，只固化那些不可协商的边界。

## 站点与目录

- 只用原生 HTML / CSS / JS；禁止框架、外部库、外部字体 CDN、图标库。当前站点零 `<script>`、零外部资源引用（唯一例外是内联 data-URI favicon）。
- 站点文件只放 `public/`（唯一发布目录，CI 只上传它）；构建脚本放 `scripts/`，校验脚本放 `tools/`；内容源放 `content/posts/`、`content/wiki/`。
- 生成的页面放 `public/` 下：文章页 `public/posts/`，列表页 `public/blog/`。
- 本站部署在 GitHub Pages 的项目子路径 `/my-agent-site/` 下，站内引用一律相对路径，禁止以 `/` 开头的根绝对路径；链接显式写全文件名（`about/index.html`、`../styles.css`），前缀按页面相对 `public/` 的深度取（1 层 `../`、2 层 `../../`）。

## 视觉（遵 DESIGN.md，不得擅改）

- 概念「实验档案」；冷白 `#F5F6F4`、墨蓝 `#1C2B3A`、蓝灰 `#6B7A89` / `#5F6E7D`（小号次级文字一律用 `#5F6E7D`）；红 `#B5322C` 在静止态只用于「当前·活跃」标记（「在册」章、「进行中」标）。
- 分隔语法：页首与页脚 3px 墨蓝双细线、导航行下 1px 实线、栏目 `h2` 压 1px 实线、条目间发丝线。
- 报头带（3px 双线 → 元信息行 → 导航行 → 1px 实线）五页同构，导航块除链接前缀与 `aria-current` 落在哪一项之外逐字节一致（`tools/check_site.py` 逐字节比对），页脚结构同构、左侧说明句按页改写；导航当前项用墨蓝加粗下划线 + `aria-current`，不用红。
- 字体：宋体标题、系统黑体正文、Consolas 等宽用于日期与编号；不引入第四个字族。
- 正文最大宽度 800px；不用卡片阵列、渐变、阴影、图标（唯一合法的 box-shadow 是「在册」章的内嵌双环纹样）。
- 全站唯一动效是首页载入「盖章」一次（子页零入场动效），且必须包在 `prefers-reduced-motion: no-preference` 内。

## 代码与生成物

- 不引入第三方依赖；Markdown 转换与模板拼接自己写。
- 构建脚本必须幂等：同一输入重复运行产出字节一致的输出，禁止追加模式（重复构建后 `git status` 必须干净）；脚本只清理自己生成的文件，不碰 `content/`。
- 日期一律 YYYY-MM-DD；生成的 HTML 必须对 `&` `<` `>` 转义。
- 改完页面必须先跑 `python tools/check_site.py`，不通过不得提交。

## 无障碍与响应式

- 语义化标签；每页恰好一个 `h1`；键盘焦点可见；`prefers-reduced-motion` 下无动画。
- 390px 与 320px 下不得出现横向滚动（`scrollWidth == clientWidth`）。

## 交付纪律

- 提交前展示 `git status`、`git diff` 与待提交文件清单。
- 不要替我执行 `git push`；不要修改我的全局 Git 配置。
- 提交信息用约定式前缀（`feat:` / `fix:` / `docs:` / `chore:` / `ci:`）。
