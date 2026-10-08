---
version: 1
slug: "about-html"
primary_target: "public/about/index.html"
related_targets: ["public/index.html"]
---

# Surface brief: public/about/index.html —— 关于我（档案附页）

## Scope & visitor mode

整站五个页面之一：无 JS、无外部资源、共用 `public/styles.css`。访客模式 Read——老师/同学想在不离开档案语法的情况下多了解这个人。

## Audience, job, action, proof, constraints

- 受众：课程任课老师/助教（核对身份四项是否在本页可见）、同学、本人回访。
- 任务：读完教育背景、技能工具链、在学课程、兴趣四栏；行动点仍是 mailto 邮箱。
- 证明：教育背景的登记行（院校 / 专业 / 年级 / 邮箱）就是核对面；技能栏每条附「证据：……」而不是熟练度自夸。
- 约束：院校/专业/年级/邮箱四项必须在本页可见；课程表与技能不加戏、不编造；与首页共用同一报头带与页脚，导航当前项为「关于我」。

## Chosen direction & memorable moment

沿用 index-html 钉死的「实验档案」世界（见 `.impeccable/surfaces/index-html.md`）：本页是同一份档案的附页，页名用 `.folio` 档（宋体 700，`clamp(1.75rem, 6vw, 2.5rem)`，0.14em），其下是同一套栏目题（1px 实线上）+ 登记行 + 条目账本。
难忘点：技能条目的「证据：……」尾句——技能不是形容词，是可核对的记录。

## Direction contract

THESIS: 这不是简历，是档案的附页——教育背景用登记行，技能用带证据的条目，没有的（课表）就诚实留「待补」。

OWN-WORLD: 与首页同一个世界：冷白纸面、墨蓝字与线、深蓝灰小字。本页不引入任何新颜色、新字族、新线档。

STORY: 访客从任意页点「关于我」进来，报头带不变（只有当前项换成墨蓝加粗 + 2px 下划线），先看到页名，再依次读到教育背景 → 技能工具链 → 在学课程（待补）→ 兴趣。

FIRST VIEWPORT: 报头带（3px 双线 → 元信息行 → 导航行 → 1px 实线）+ `.folio` 页名「关于我」+「教育背景」栏目题坐在 1px 墨蓝实线上，登记行四行（院校 / 专业 / 年级 / 邮箱）在 1440×900 内完整可见。

FORM: 沿用既有组件，只使用新增的 `.folio` 与 `.site-nav` 两个类；无图像生成。

FINISH: 与整站同批完成 finish review、DESIGN.md 与 design.json。

## Signature interaction

无。子页不新增任何动效——全站唯一动效仍是首页载入时的「盖章」一次。

## Unresolved decisions

- 「在学课程」栏暂无真实课表，按事实留「待补」占位；本人给出课程名后逐行登记。
- 邮箱已填入真实地址 1095568137@qq.com（2026-10-08 本人提供）。
