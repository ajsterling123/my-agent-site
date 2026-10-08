---
title: 我的第一次 Agent 实验
date: 2026-09-02
description: 从一句模糊需求到一个可以验收的个人主页。
---

# 我的第一次 Agent 实验

我发现，和 Agent 协作的关键不是把句子写得很长，而是给出清晰的目标、约束和验收标准。

## 今天的收获

- 先说明用户是谁；
- 再说明页面应该包含什么；
- 最后说明如何判断完成。

验证必须实际执行：
- 连续运行两次构建脚本，第二次之后 git status 应干净（证明幂等）；
- 跑 python tools/check_site.py；
- 在 my-agent-site/ 下起 python -m http.server 8080 --directory public，浏览器打开
  /blog/ 与生成的文章页，确认样式加载（文章页的 ../../styles.css 生效）、导航能跳转；
- 390px 与 320px 下检查无横向滚动。
