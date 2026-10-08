---
version: 1
slug: "post-html"
primary_target: "public/posts/hello-agent.html"
related_targets: ["public/blog/index.html", "public/index.html"]
---

# Surface brief: public/posts/&lt;slug&gt;.html —— 文章页（已实现）

## Scope & visitor mode

由 `scripts/build_blog.py` 从 `content/posts/*.md` 生成的每篇文章页（无 JS、无外部资源、共用 `public/styles.css`）。访客模式 Read：把一篇读完，读完仍能沿导航继续走。`primary_target` 指向当前唯一一篇，模板对每篇相同。

## Audience, job, action, proof, constraints

- 受众：课程任课老师/助教（核对文章是否真的成文、能不能顺畅读完）、同学、本人回访。
- 任务：读到标题、登记日期与正文；行动点是顶部导航（回首页/关于我/博客/Research Papers/Wiki）。
- 证明：正文与 `content/posts/<slug>.md` 一一对应；页面骨架与手写页逐字节一致，由 `tools/check_site.py` 校验。
- 约束：每页恰好一个 `h1`（由 frontmatter 的 `title` 提供）；**不设 `aria-current`**（文章页不对应任何菜单项）；不要「在册」章、不要入场动效；320px 无横向滚动。

## Chosen direction & memorable moment

沿用「实验档案」世界：一篇文章就是一页档案——页名档（与子页 `.folio` 同字号）+ 一行等宽「登记于 YYYY-MM-DD」，正文按档案自述的行距（17px / 2.05）排，小节题压在 1px 墨蓝实线上。
难忘点：标题下那行等宽登记日期——文章是「归档」进来的，不是发布出去的。

## Direction contract

THESIS: 文章是档案里的一页：页名、登记日期、正文；层级仍靠字号、字距与三档线，不靠装饰。

OWN-WORLD: 与首页同一个世界；新增样式只有 `.post-head` / `.post-body` 及其正文元素（h2/h3、列表、行内代码、引用、粗体），零新色、零新字体、零动效。

STORY: 访客从列表点进来 → 读到宋体大标题与其下的等宽登记日期 → 正文（段落、小节、列表）→ 页脚的进度印记。

FIRST VIEWPORT: 报头带（无当前项）→ `.post-head`（宋体大标题 + 等宽登记日期）→ 正文首段，一屏内读完开头。

FORM: 骨架从 `public/index.html` 改写、链接前缀按输出深度算；正文由脚本内自写的极简 Markdown 转换产出，不引第三方依赖。

FINISH: 与整站同批通过 `tools/check_site.py`（已覆盖生成页）与 impeccable detect；DESIGN.md 已补「文章页」组件规格。

## Signature interaction

无。全站唯一动效仍是首页的盖章；文章页没有章，也没有任何入场动效。

## Unresolved decisions

- 代码块、图片、表格等 Markdown 语法暂不支持（只做支持的那几类）；将来加语法时必须同时补样式规格。
- 「上一篇/下一篇」与按日期/标签的索引未做；文章页目前只从博客列表页进入。
