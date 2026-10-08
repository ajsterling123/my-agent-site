# my-agent-site · 实验档案

张易孝（江苏警官学院 · 数据警务技术）的 AI Agent 课程实验记录站——一份持续更新的个人档案，由 AI Agent 按课程步骤逐步迭代交付。

## 目录结构

```
my-agent-site/
├── public/                  # 站点唯一发布目录（GitHub Pages 只部署它）
│   ├── index.html           # 首页
│   ├── about/index.html     # 关于我
│   ├── blog/index.html      # 博客列表（生成物：日期倒序 + 订阅入口）
│   ├── posts/<slug>.html    # 文章页（生成物，slug = content/posts/ 里的文件名）
│   ├── feed.xml             # RSS 2.0 订阅源（生成物，Step 5）
│   ├── papers/index.html    # Research Papers（诚实占位，Step 7 填充）
│   ├── wiki/index.html      # Wiki（诚实占位，Step 8 填充）
│   └── styles.css           # 全站共用的样式（原生 CSS，无框架、无外部字体）
├── content/
│   └── posts/*.md           # 文章源文件（frontmatter：title / date / description）
├── scripts/
│   ├── site_data.py         # slug / 文章页路径 / 站点绝对地址 / 排序的唯一来源（两个构建脚本共用）
│   ├── build_blog.py        # 构建脚本：Markdown → 博客列表页 + 文章页（幂等）
│   └── build_feed.py        # 构建脚本：Markdown frontmatter → public/feed.xml（幂等）
├── tools/
│   ├── check_site.py        # 机械校验：页面骨架一致性 / 导航 / aria-current / 相对路径 / 链接可达
│   └── check_feed.py        # 机械校验：feed.xml 的 schema / 绝对地址 / RFC 822 日期 / 排序 / 转义
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
   python scripts/build_feed.py
   python tools/check_site.py
   python tools/check_feed.py
   ```

   构建会把列表页、所有文章页与 `public/feed.xml` 写好，并清掉源文件已删除的文章页。它只碰
   `public/blog/index.html`、`public/posts/*.html` 与 `public/feed.xml`，不动 `content/`，也不动手写页面。
   新增一篇文章就是「列表页多一行 + feed 多一个 `<item>`」，不需要改脚本或手写任何页面。
5. 提交前重复跑一次构建：第二次应当报告「未变化」，`git status` 保持干净——这是幂等的证据。

文章里不要写站外链接（`http://` / `https://`）：本站零外部资源，校验脚本会把外部引用判为失败。

## RSS 订阅源（feed.xml）

- 生成物在 `public/feed.xml`，部署后订阅地址是 <https://ajsterling123.github.io/my-agent-site/feed.xml>；站内入口是博客列表页页尾那一行「订阅：feed.xml」，以及列表页 `<head>` 里的 `rel="alternate"`。
- 内容源与博客页完全相同：`content/posts/*.md` 的 frontmatter（`title` / `date` / `description`）。加一篇文章 → 列表页多一行、feed 多一个 `<item>`，日期顺序按 `date` 倒序、同一天按 slug 升序（稳定，重复构建字节一致）。
- `lastBuildDate` 取**最新一篇文章的日期**，不取「此刻」——否则每次构建都会产生 diff。没有文章时退回 `1970-01-01`。
- 日期用 `email.utils.format_datetime` 写成 RFC 822 的 `+0800`（东八区固定），**不用 `strftime('%a')`**：中文 locale 下它会输出「周三」，阅读器解析不了。中文正文原样保留，`&`、`<`、`>` 用 XML 实体转义（不用 CDATA）。
- 所有 URL（站点根、文章页、feed 自身）都从 `scripts/site_data.py` 的 `SITE_BASE_URL` 一个常量派生，slug 与文章页路径的规则也只写在那一个文件里——改站址只改一处。

## 校验

```bash
python tools/check_site.py
python tools/check_feed.py
```

`check_site.py` 扫描 `public/` 下的**全部**页面（手写五页 + 生成的文章页与列表页），检查：报头带的元信息行与
页脚步数是否全站逐字节一致、导航块除链接前缀与 `aria-current` 外是否与 `public/index.html` 一致、每页是否
恰好一个 `h1`、`aria-current` 是否恰好落在该页（文章页应当一次都没有）、有无根绝对路径或外部资源引用、
每个链接目标文件是否真实存在。链接前缀按页面相对 `public/` 的深度计算，所以手写页与生成页用同一套判据。

`check_feed.py` 真的用 `xml.etree.ElementTree` 解析 `public/feed.xml`：根必须是 `rss` 且 `version="2.0"`、
文件无 BOM、无 CDATA、channel 五个字段齐全且 `language` 为 `zh-CN`、`link` 是站点首页绝对地址；item 数与
`content/posts/` 篇数相等，每个 item 五字段齐全、`link`/`guid` 是 `https://` 绝对地址且与生成的文章页一致、
`guid` 指向文章自身页面、页面对应的 `.html` 真实存在、标题与摘要能无损还原；`pubDate` 用
`email.utils.parsedate_to_datetime` 解析并核对时区为 `+0800`；条目顺序真的是日期倒序、同日期下稳定。
最后做一次**负向测试**：临时写一篇标题含 `& < >` 的文章，重新构建后 feed 仍能被解析（证明转义有效），
随后删掉临时文件并重建，确认 feed 字节与测试前完全一致——临时文件不会留在仓库里。

两个脚本退出码 0 为通过。

## 部署方式

推送到 `main` 分支即自动触发 GitHub Actions（`.github/workflows/deploy.yml`），
把 `public/` 发布到 GitHub Pages；也可在 Actions 页面手动触发（workflow_dispatch）。

首次使用需在仓库 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。
