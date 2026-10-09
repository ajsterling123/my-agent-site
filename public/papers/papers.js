/* papers.js —— 读取同域数据文件 ../data/papers.json，把 arXiv 检索结果按档案账本的
 * 语法登记成论文条目（等宽日期 / 宋体标题外链 / 作者 / 可展开摘要 / 来源标记）。
 *
 * 与 rss/reader.js 同一套约束（完整口径见 AGENTS.md「外部数据是不可信输入」）：
 *
 * 1) 数据只来自同域。检索发生在构建期（scripts/collect_papers.py，由
 *    .zcode/skills/research-paper-collector 技能调用），这里只 fetch 同域这一份
 *    JSON，浏览器不会因为本页去连 arXiv。
 *
 * 2) arXiv 的标题与摘要一律只当展示文本：全部用 document.createElement +
 *    textContent 逐节点创建。把字符串当标记解析的那几个 API、往文档流写内容的
 *    方法、以及动态求值的运行时入口，在本文件里一律不得出现——
 *    tools/check_papers.py 会逐字扫描本文件，命中任何一个即校验失败，连注释里
 *    写都不行（本段因此特意不复述它们的名字）。数据侧的摘要已在构建期剥成纯文本
 *    并删掉尖括号，这里再按纯文本渲染，双保险。
 *
 * 3) 外链只有一个出口。条目标题指向 arXiv 原文，走数据里的 https 绝对地址，
 *    外加 target="_blank" 与 rel="noopener noreferrer"；本页面内没有别的链接出口。
 *    所有 href 都经由 buildLink 一处赋值，check_papers.py 会数这个出口。
 *
 * 4) 条目、计数、空状态全部从同一份数据算出来，页面骨架里不写死任何论文——
 *    所以页面内容永远跟着 papers.json 走。arXiv 是预印本平台：来源标记写明
 *    「预印本」，不把任何条目说成已同行评审。
 */
(function () {
  "use strict";

  var DATA_URL = "../data/papers.json";
  var HTTPS_RE = /^https:\/\/[^\s]+$/i;
  var MAX_LISTED_AUTHORS = 3;

  var container = document.getElementById("papers-list");
  if (!container) {
    return;
  }

  function str(value) {
    return typeof value === "string" ? value : "";
  }

  /* 数据侧已保证 https，这里再挡一次：不是 https 就退化成纯文本标题 */
  function safeHref(url) {
    var value = str(url);
    return HTTPS_RE.test(value) ? value : null;
  }

  /* 链接的唯一出口：站外一律 https 且带 rel/target（外链只是导航，显式声明） */
  function buildLink(text, href) {
    var a = document.createElement("a");
    a.textContent = text;
    a.href = href;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    return a;
  }

  function note(message) {
    var p = document.createElement("p");
    p.className = "intro";
    p.textContent = message;
    return p;
  }

  /* 作者多于 MAX_LISTED_AUTHORS 位时列前三位 + 「等 N 人」，N 是总人数 */
  function authorLine(authors) {
    var names = Array.isArray(authors) ? authors.filter(function (a) {
      return typeof a === "string" && a.trim();
    }).map(function (a) { return a.trim(); }) : [];
    if (!names.length) {
      return "";
    }
    if (names.length <= MAX_LISTED_AUTHORS) {
      return names.join(", ");
    }
    return names.slice(0, MAX_LISTED_AUTHORS).join(", ") + " 等 " + names.length + " 人";
  }

  function buildPaper(item) {
    var li = document.createElement("li");
    li.className = "post-row";

    var time = document.createElement("time");
    time.className = "post-date";
    var published = str(item.published);
    if (published) {
      time.setAttribute("datetime", published);
    }
    time.textContent = published || "日期未知";
    li.appendChild(time);

    var box = document.createElement("div");
    box.className = "post-item";

    var title = str(item.title) || "（无标题）";
    var h3 = document.createElement("h3");
    var href = safeHref(item.url);
    if (href) {
      h3.appendChild(buildLink(title, href));
    } else {
      h3.textContent = title;
    }
    box.appendChild(h3);

    var authors = authorLine(item.authors);
    if (authors) {
      var byline = document.createElement("p");
      byline.textContent = authors;
      box.appendChild(byline);
    }

    var summary = str(item.summary);
    if (summary) {
      var details = document.createElement("details");
      details.className = "paper-summary";
      var label = document.createElement("summary");
      label.textContent = "摘要";
      details.appendChild(label);
      var body = document.createElement("p");
      body.textContent = summary;
      details.appendChild(body);
      box.appendChild(details);
    }

    var source = document.createElement("p");
    source.className = "paper-source";
    source.textContent = (str(item.source) || "arXiv") + " · 预印本，未经同行评审";
    box.appendChild(source);

    li.appendChild(box);
    return li;
  }

  function render(papers) {
    var section = document.createElement("section");
    section.className = "sec";

    var h2 = document.createElement("h2");
    h2.textContent = "论文登记";
    section.appendChild(h2);

    if (!papers.length) {
      section.appendChild(note(
        "本页还没有论文记录：运行 python scripts/collect_papers.py --query \"<arXiv 查询词>\" "
        + "（或请 Agent 执行 research-paper-collector 技能）后刷新。"));
      container.replaceChildren(section);
      return;
    }

    var list = document.createElement("ul");
    list.className = "post-list";
    for (var i = 0; i < papers.length; i += 1) {
      if (papers[i] && typeof papers[i] === "object") {
        list.appendChild(buildPaper(papers[i]));
      }
    }
    section.appendChild(list);

    var count = document.createElement("p");
    count.className = "paper-note";
    count.textContent = "共 " + list.children.length + " 条，按提交日期倒序，最多保留 50 条。";
    section.appendChild(count);

    container.replaceChildren(section);
  }

  function prepare(doc) {
    var papers = doc && Array.isArray(doc.papers) ? doc.papers : [];
    render(papers);
  }

  function showError(err) {
    container.replaceChildren(note(
      "读不到论文数据（" + err.message + "）。若这是本地双击打开的页面（file://），"
      + "浏览器会拦截同域 fetch —— 请用 python -m http.server 8080 --directory public 预览；"
      + "机读数据在 data/papers.json。"));
  }

  if (typeof fetch !== "function") {
    showError(new Error("浏览器不支持 fetch"));
    return;
  }

  fetch(DATA_URL, { cache: "no-cache" })
    .then(function (response) {
      if (!response.ok) {
        throw new Error("HTTP " + response.status);
      }
      return response.json();
    })
    .then(prepare)
    .catch(showError);
}());
