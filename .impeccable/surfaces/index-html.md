---
version: 1
slug: "index-html"
primary_target: "public/index.html"
related_targets: []
---

# Surface brief: public/index.html —— 课程实验档案首页

## Scope & visitor mode

单页静态首页（无 JS）。访客模式 Read：老师/同学要在几秒内读到「这是谁、在读什么、正在做什么实验」。

## Audience, job, action, proof, constraints

- 受众：课程任课老师/助教（按验收清单核对）、同学、本人回访。
- 任务：核对身份登记与研究方向；唯一行动点是 mailto 邮箱链接。
- 证明：身份登记行（姓名/院校/专业/年级/邮箱）即核对面。
- 约束：原生 HTML+CSS 双文件；800px 单栏；无外部资源；390px 不破版。

## Chosen direction & memorable moment

简报钉死方向：「实验档案」——页面即一份在册档案（登记表 + 条目 + 状态标记）。
难忘点：巨幅宋体姓名旁一枚旋转的红色「在册」章；页面唯一动效是载入时「盖章」一次。
红色纪律：#B5322C 只出现在「在册」章与「进行中」标记两处。

## Direction contract

THESIS: 这不是个人主页，是一份正在更新的在册档案——用登记表与条目组织身份，拒绝模板主页的卡片阵列与技能罗列。

OWN-WORLD: 冷白 #F5F6F4 纸面；墨蓝 #1C2B3A 文字与分隔线（页首/页尾 3px 双细线、栏目 1px 实线、条目间发丝线）；蓝灰 #6B7A89 次级（小字加深至达标变体 ≈#5F6E7D）；红 #B5322C 仅两处活跃标记。宋体系加粗做姓名与栏目题，系统黑体做正文，Consolas 等宽做日期与文件元数据。

STORY: 访客先读到一行等宽的「最后更新」，随即看到在册的巨幅姓名与登记表，明白这是谁的档案；三行研究方向里，带红标的那条就是本学期正在进行的实验；页脚给出进度（STEP 1/12）。

FIRST VIEWPORT: 顶部一行等宽小字，左「个人实验档案」右「最后更新：2026-10-07」，行外上下各一道墨蓝双细线/单细线；其下档案头：姓名「张易孝」宋体加粗 clamp(2.75rem,9vw,3.75rem)、字距放宽，右上角旋转 -6° 的红框「在册」章；姓名块之下「身份登记」栏目开始：h2 压 1px 墨蓝实线，登记表 dl 四行（院校/专业/年级/邮箱），行间发丝线，邮箱为 mailto 等宽链接（页面唯一行动点），在 1440×900 内完整可见。

FORM: 方向由用户简报钉死（brief-pinned beats the roll），未运行 concept-seed，无 seed key；构建路径 code-first（本机无图像生成）。

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance.

## Signature interaction

载入时「盖章」一次：红章从 scale(1.7) 落定至 scale(1) 并显影，ease-out，约 0.5s，仅此一处动效；prefers-reduced-motion 下静止常显。

## Unresolved decisions

- 自我介绍与三条方向的描述文字为可替换草稿（身份四项已由用户确认）。
- 邮箱 you@example.com 待用户替换为真实邮箱。
