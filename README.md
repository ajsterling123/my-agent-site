# my-agent-site · 实验档案

张易孝（江苏警官学院 · 数据警务技术）的 AI Agent 课程实验记录站——一份持续更新的个人档案，由 AI Agent 按课程步骤逐步迭代交付。

## 目录结构

```
my-agent-site/
├── public/                  # 站点唯一发布目录（GitHub Pages 只部署它）
│   ├── index.html           # 首页
│   └── styles.css           # 样式（原生 CSS，无框架、无外部字体）
├── .github/workflows/
│   └── deploy.yml           # GitHub Actions 自动部署工作流
├── .impeccable/             # 设计档案（设计系统 sidecar、surface brief、评审截图）
├── DESIGN.md                # 设计系统记录
├── PRODUCT.md               # 产品事实档案
└── README.md
```

## 本地预览

在本目录（`my-agent-site/`）运行：

```bash
python -m http.server 8080 --directory public
```

浏览器访问 <http://localhost:8080>。也可以直接双击 `public/index.html` 打开。

## 部署方式

推送到 `main` 分支即自动触发 GitHub Actions（`.github/workflows/deploy.yml`），
把 `public/` 发布到 GitHub Pages；也可在 Actions 页面手动触发（workflow_dispatch）。

首次使用需在仓库 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。
