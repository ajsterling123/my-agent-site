# my-agent-site · 实验档案

张易孝（江苏警官学院 · 数据警务技术）的 AI Agent 课程实验记录站——一份持续更新的个人档案，由 AI Agent 按课程步骤逐步迭代交付。

## 目录结构

```
my-agent-site/
├── public/                  # 站点唯一发布目录（GitHub Pages 只部署它）
│   ├── index.html           # 首页
│   ├── about/index.html     # 关于我
│   ├── blog/index.html      # 博客列表（生成物：日期倒序，Step 5 再加 RSS）
│   ├── posts/<slug>.html    # 文章页（生成物，slug = content/posts/ 里的文件名）
│   ├── papers/index.html    # Research Papers（诚实占位，Step 7 填充）
│   ├── wiki/index.html      # Wiki（诚实占位，Step 8 填充）
│   └── styles.css           # 全站共用的样式（原生 CSS，无框架、无外部字体）
├── content/
│   └── posts/*.md           # 文章源文件（frontmatter：title / date / description）
├── scripts/
│   └── build_blog.py        # 构建脚本：Markdown → 博客列表页 + 文章页（幂等）
├── tools/
│   └── check_site.py        # 机械校验：页面骨架一致性 / 导航 / aria-current / 相对路径 / 链接可达
├── .github/workflows/
│   └── deploy.yml           # GitHub Actions 自动部署工作流（构建 → 校验 → 部署）
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
- 子页相对 `public/` 的深度统一为 1（`public/about/index.html`、`public/blog/index.html`、`public/posts/<slug>.html` 都一样），
  所以导航链接前缀统一是 `../`。生成页的前缀由 `scripts/build_blog.py` 按输出深度自动算：将来若出现更深层的页面
  （如 `public/posts/<slug>/index.html`），前缀会自己变成 `../../`，导航块其余部分逐字节不动。
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

## 如何新增一篇博客

1. 在 `content/posts/` 新建一个 `.md` 文件，文件名即 slug（同 URL），用 ASCII 小写字母、数字与 `-`，例如 `my-second-post.md`。
2. 文件开头写 frontmatter 三行，缺一不可：

   ```markdown
   ---
   title: 文章标题
   date: 2026-09-02
   description: 一句话摘要，会显示在列表页。
   ---
   ```

   日期必须是合法的 `YYYY-MM-DD`（`2026-9-2` 这种写法会被构建脚本拒绝）。
3. 正文用 Markdown 写。构建脚本目前支持：段落、`##` 二级标题、`###` 三级标题、无序列表（`- `）、
   有序列表（`1. `）、`**粗体**`、`` `行内代码` ``、`[链接](地址)`、`> 引用`。
   正文开头若重复写一次 `# 文章标题`，只要与 frontmatter 的 `title` 一致就会被忽略（页面的 `h1` 由标题提供）；
   别处再出现一级标题会直接构建失败——每页只能有一个 `h1`。
4. 在 `my-agent-site/` 下运行构建，再跑校验：

   ```bash
   python scripts/build_blog.py
   python tools/check_site.py
   ```

   构建会把列表页与所有文章页写好，并清掉源文件已删除的文章页。它只碰 `public/blog/index.html` 与
   `public/posts/*.html`，不动 `content/`，也不动手写页面。
5. 提交前重复跑一次构建：第二次应当报告「未变化」，`git status` 保持干净——这是幂等的证据。

文章里不要写站外链接（`http://` / `https://`）：本站零外部资源，校验脚本会把外部引用判为失败。

## 校验

```bash
python tools/check_site.py
```

扫描 `public/` 下的**全部**页面（手写五页 + 生成的文章页与列表页），检查：报头带的元信息行与页脚步数是否全站
逐字节一致、导航块除链接前缀与 `aria-current` 外是否与 `public/index.html` 一致、每页是否恰好一个 `h1`、
`aria-current` 是否恰好落在该页（文章页应当一次都没有）、有无根绝对路径或外部资源引用、
每个链接目标文件是否真实存在。链接前缀按页面相对 `public/` 的深度计算，所以手写页与生成页用同一套判据。
退出码 0 为通过。

## 部署方式

推送到 `main` 分支即自动触发 GitHub Actions（`.github/workflows/deploy.yml`），
把 `public/` 发布到 GitHub Pages；也可在 Actions 页面手动触发（workflow_dispatch）。

首次使用需在仓库 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。
