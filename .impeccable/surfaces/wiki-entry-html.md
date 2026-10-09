---
version: 1
slug: "wiki-entry-html"
primary_target: "public/wiki/agent-experiment.html"
related_targets: ["public/wiki/index.html", "public/posts/hello-agent.html"]
---

# Surface brief: public/wiki/agent-experiment.html —— Wiki 词条页（已实现）

## Scope & visitor mode

Wiki 的词条页之一（`public/wiki/<slug>.html`），由 `scripts/build_wiki.py` 从 `content/wiki/agent-experiment.md` 生成（无 JS、无外部资源、共用 `public/styles.css`）。访客模式 Read：老师/同学核对「一个知识点一页」的整理质量，以及双向链接是否真的可点。

## Audience, job, action, proof, constraints

- 受众：课程任课老师/助教、同学、本人回访。
- 任务：读懂这一个知识点的概念与决策（不是复述博客全文），顺着「链接到此页的页面」走回索引；行动点是正文 [[index]] 链接与引用块里的博客原文链接。
- 证明：「我的原话」用引用块注明出处（本档案博客文章[《我的第一次 Agent 实验》](../posts/hello-agent.html)）；「链接到此页的页面」由构建期反查生成；页脚注明源文件位置 `content/wiki/agent-experiment.md`。
- 约束：三类内容三种写法（原话用引用块 / Agent 总结不加标记 / 外部来源必须附链接）；不写入未经确认的推断；480px 收成单列；320px 无横向滚动；零 JavaScript。

## Chosen direction & memorable moment

沿用「实验档案」世界：词条页就是档案里的单页记录——头部复用 `.post-head`（h1 + 「更新于」等宽日期 + `.wiki-meta` 等宽标签行），正文复用 `.post-body`（引用块用双发丝线夹摘录，与文章页同一语法），底部反向链接账本复用 `.post-list`。
难忘点：词条底部「链接到此页的页面」——每页都带着「谁引用了我」的账，双向不是口号。

## Direction contract

THESIS: 词条是提炼后的知识点——概念、决策与验收，不复述全文；出处用公文式引注压在引用块里。

OWN-WORLD: 与整站同一个世界；本页样式全部复用（`.post-head` / `.post-body` / `.post-list` / `.sec`），`.wiki-meta` 与栏目页共用，零新色、零新字体、零动效。

STORY: 访客从栏目页页面清单点进来 → 读 h1、更新日期与标签 → 读核心认识（引用原话）、三问、验收 → 顺着反向链接回到索引。

FIRST VIEWPORT: 报头带 → `.post-head`（页名 + 更新于 + 标签行）→ 正文首段与「核心认识」栏目题，一屏读完。

FORM: 骨架从 `public/index.html` 改写（`scripts/page_build.py` 共用实现），内容由构建脚本生成；不手写这一页。

FINISH: 与整站同批通过 `tools/check_site.py`（wiki/ 内容页 0 个 aria-current、生成页标记、链接目标存在）与四个校验器。

## Signature interaction

无。全站唯一动效仍是首页的盖章，本页没有任何动效。

## Unresolved decisions

- 同一知识点被多篇博客支撑时的多出处格式未定（当前单出处）。
- 词条数变多后「页面清单」是否按标签分组的策略未定。
