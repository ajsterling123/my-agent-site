# content/wiki/README.md —— Wiki 规则（规则本身也是文件）

这里是「文件化 Memory」的规则文件：`scripts/build_wiki.py` 会跳过本文件（它不是词条，
不生成 `public/wiki/README.html`，也不需要 frontmatter）。改规则先改这里；
下面每一条都会由构建脚本或 `tools/check_site.py` 机械执行，写页面的人（或 Agent）照此执行。

## 目录与命名

1. 一个知识点一个文件，全部平铺在本目录（`content/wiki/`），文件名即 slug：
   ASCII 小写字母、数字与 `-`（如 `agent-experiment.md`）。slug 直接成为 URL，
   不用中文文件名；标题写在每页 frontmatter 的 `title` 里。
2. `index.md` 是索引页（栏目页）。它的正文写本 Wiki 的定位；正文之后的「页面清单」
   由构建脚本自动生成（每个 Wiki 页的标题、updated、tags），不手工维护，
   手工往输出里塞条目没有意义——下一个条目文件一落地，清单必然同步。

## 写入规则

3. **写入前先搜索**：先看本目录是否已有同义页面（按标题与内容找，不按文件名猜），
   已有页面存在时优先更新该页，不重复创建近义新页。
4. **三类内容三种写法**：
   - 「我的原话」：用 `>` 引用块，并注明出处（哪篇博客、站内附链接）；
   - 「Agent 总结」：直接写，不加标记；
   - 「外部来源」：必须附链接。链接按本站两级引用规则走站内路径——
     外部条目先登记进 RSS订阅 或 Research Papers 页（Step 6 / Step 7 的账本），
     Wiki 里指向那些页面；Wiki 页面文件里出现站外 `href` 会被 `check_site.py` 判失败。
   - 未经本人确认的 Agent 推断，一律不写入。
5. 每页（含 `index.md`）frontmatter 必填 `title` / `updated` / `tags`：
   `updated` 写成 YYYY-MM-DD 且必须是合法日期，改动内容就改更新日期；
   `tags` 用逗号分隔（如 `tags: agent, 协作, 验收`）。非法日期、缺字段、
   多余字段都会被构建拒绝。
6. 新建的页面至少用一个 `[[双向链接]]` 连接一个已有页面（仅当已有页面存在时适用）。
   写法：`[[slug]]` 显示文字默认取目标页标题；`[[slug|别名]]` 自定义显示文字。
   想在文字里提及这种语法本身，放进行内代码（`` `[[…]]` ``）即不参与解析。
7. **死链即构建失败**：`[[target]]` 必须对应本目录真实存在的 `<target>.md`，
   否则 `python scripts/build_wiki.py` 非零退出，并指出是哪个文件里的哪个链接。
8. **反向链接自动算**：每页底部「链接到此页的页面」由脚本从各页正文的 `[[链接]]`
   反查得出（不计自动生成的清单行，也不计本页指向自身的链接）；
   没有被任何页面引用的页面不显示该节。不许手写这节内容。

## 构建与修改流程

9. 改完任何 `content/wiki/*.md`，在仓库根运行：

   ```bash
   python scripts/build_wiki.py
   python tools/check_site.py
   ```

   生成物在 `public/wiki/`（带生成标记，`check_site.py` 校验）；
   生成页不许手改——改内容改 md，改呈现改脚本与 `public/styles.css`。
   Wiki 页面零 JavaScript：链接与反向链接都在构建期解决。
10. **Wiki 的任何修改都必须先以 `git diff` 呈现给本人确认，再提交。**
    包括新增页面、改规则、改 frontmatter——diff 是唯一的人工审查关口。
