# my-agent-site · 实验档案

张易孝（江苏警官学院 · 数据警务技术）的 AI Agent 课程实验记录站——一份持续更新的个人档案，由 AI Agent 按课程步骤逐步迭代交付。

## 目录结构

```
my-agent-site/
├── public/                  # 站点唯一发布目录（GitHub Pages 只部署它）
│   ├── index.html           # 首页
│   ├── about/index.html     # 关于我
│   ├── blog/index.html      # 博客（诚实占位，Step 4/5 填充）
│   ├── papers/index.html    # Research Papers（诚实占位，Step 7 填充）
│   ├── wiki/index.html      # Wiki（诚实占位，Step 8 填充）
│   └── styles.css           # 五个页面共用的样式（原生 CSS，无框架、无外部字体）
├── tools/
│   └── check_site.py        # 机械校验：导航一致性 / aria-current / 相对路径 / 链接可达
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

## 站点结构与链接规则（新增页面时必读）

- 每个页面 = **它自己目录下的 `index.html`**：首页在 `public/index.html`，子页在 `public/<栏目>/index.html`。
- **链接与资源引用一律用相对路径，并且写全文件名**（`about/index.html`、`../styles.css`、`../index.html`），
  不写 `/` 开头的根绝对路径——本站发布在 GitHub Pages 的项目子路径 `/my-agent-site/` 下，根绝对路径会 404。
- 子页相对 `public/` 的深度统一为 1，所以导航链接前缀统一是 `../`；将来若出现更深层的页面（如 `posts/<slug>/index.html`），
  只需把前缀改成 `../../`，导航块其余部分逐字节不动。
- 这么写是为了三种打开方式行为一致：本地 `http.server`、GitHub Pages 子路径、双击 `file://`
  （`about/` 这种目录写法在 `file://` 下会列出目录而不是打开页面）。

导航块在五个页面共用同一份标记，除链接前缀与 `aria-current="page"` 落在哪一项之外完全相同：

```html
<nav class="site-nav" aria-label="主导航">
  <ul>
    <li><a href="index.html" aria-current="page">首页</a></li>
    <li><a href="about/index.html">关于我</a></li>
    <li><a href="blog/index.html">博客</a></li>
    <li><a href="papers/index.html">Research Papers</a></li>
    <li><a href="wiki/index.html">Wiki</a></li>
  </ul>
</nav>
```

## 校验

```bash
python tools/check_site.py
```

检查五页导航是否一致、每页是否恰好一个 `aria-current="page"`（且指向本页）、
有无根绝对路径或外部资源引用、每个链接目标文件是否真实存在。退出码 0 为通过。

## 部署方式

推送到 `main` 分支即自动触发 GitHub Actions（`.github/workflows/deploy.yml`），
把 `public/` 发布到 GitHub Pages；也可在 Actions 页面手动触发（workflow_dispatch）。

首次使用需在仓库 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。
