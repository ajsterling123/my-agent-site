/* reader.js —— 读取同域数据文件 ../data/rss-items.json，在页首生成一份「订阅目录」与一个筛选框，
 * 然后按订阅源分栏渲染条目。
 *
 * 四条刻意的约束（完整口径见 AGENTS.md「外部数据是不可信输入」）：
 *
 * 1) 数据只来自同域。抓取发生在构建期（scripts/fetch_feeds.py），这里只 fetch 同域这一份
 *    JSON，因此没有跨域请求、不碰 CORS，浏览器也不会因为本页去连任何一个第三方源。
 *
 * 2) 外部标题与摘要一律只当展示文本：全部用 document.createElement + textContent 逐节点创建。
 *    把字符串当标记解析的那几个 API、往文档流写内容的方法、以及动态求值的运行时入口，
 *    在本文件里一律不得出现 —— tools/check_feeds.py 会逐字扫描本文件，命中任何一个即校验失败，
 *    连注释里写都不行（本段因此特意不复述它们的名字）。数据侧的摘要也已在构建期剥成纯文本
 *    并删掉尖括号，这里再按纯文本渲染，双保险。
 *
 * 3) 链接分两类，出口只有一处。条目标题与栏目题下的「出处」指向源站，走 https 绝对地址
 *    + target="_blank" + rel="noopener noreferrer"；目录行与「回到目录」是页内锚点
 *    （"#" 加栏目 id），不出站。所有 href 都经由 buildLink 一处赋值，check_feeds.py 会数这个出口。
 *
 * 4) 目录、条数、出处、匹配说明、空状态全部从同一份数据算出来，页面骨架里不写死任何源名或条数
 *    —— 所以计数永远不会与 JSON 脱节。
 */
(function () {
  "use strict";

  var DATA_URL = "../data/rss-items.json";
  var DATE_RE = /^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})/;
  var HTTPS_RE = /^https:\/\/[^\s]+$/i;
  var TOC_ID = "toc";
  var FILTER_ID = "rss-filter";

  var container = document.getElementById("rss-reader");
  if (!container) {
    return;
  }

  var entries = [];       /* [{ group, id, items }]：id 是栏目锚点，items 是未筛选的原始条目 */
  var total = 0;          /* 全部条目数，只给空状态的说明句用 */
  var needle = "";        /* 筛选框里的原文（回显） */
  var query = "";         /* needle 的小写形式（比对） */
  var content = null;     /* 目录与各栏的容器，每次筛选整体重画 */
  var resultNote = null;  /* 匹配说明 / 空状态，aria-live 区 */

  function str(value) {
    return typeof value === "string" ? value : "";
  }

  /* published 是 "2026-10-08T14:42:14+08:00"；取不出来就显示「日期未知」。 */
  function dateParts(published) {
    var m = DATE_RE.exec(str(published));
    return m ? { day: m[1], time: m[2] } : null;
  }

  /* 数据侧已保证 https，这里再挡一次：不是 https 就退化成纯文本标题 */
  function safeHref(link) {
    var value = str(link);
    return HTTPS_RE.test(value) ? value : null;
  }

  /* 出处一行显示主机名就够认源了；拿不到就退回原样，绝不编造地址 */
  function hostOf(url) {
    try {
      return new URL(url).hostname || str(url);
    } catch (err) {
      return str(url);
    }
  }

  function note(message, className) {
    var p = document.createElement("p");
    p.className = className || "intro";
    p.textContent = message;
    return p;
  }

  /* 栏目锚点：只由 config 的源 id 派生（[A-Za-z0-9_-]），空值时退回序号，保证 id 稳定且可跳 */
  function sectionId(group, index) {
    var clean = str(group.id).replace(/[^A-Za-z0-9_-]/g, "");
    return "source-" + (clean || String(index));
  }

  /* 链接的唯一出口：站内锚点只给 "#" 开头的目标，站外一律 https 且带 rel/target */
  function buildLink(text, href, external) {
    var a = document.createElement("a");
    a.textContent = text;
    a.href = href;
    if (external) {
      a.target = "_blank";
      a.rel = "noopener noreferrer";
    }
    return a;
  }

  function buildTime(item, withClock) {
    var el = document.createElement("time");
    el.className = "post-date";
    var parts = dateParts(item.published);
    if (!parts) {
      el.textContent = "日期未知";
      return el;
    }
    el.setAttribute("datetime", str(item.published));
    var day = document.createElement("span");
    day.textContent = parts.day;
    el.appendChild(day);
    if (withClock) {
      var clock = document.createElement("span");
      clock.textContent = parts.time;
      el.appendChild(clock);
    }
    return el;
  }

  function buildItem(item, withClock) {
    var li = document.createElement("li");
    li.className = "post-row";
    li.appendChild(buildTime(item, withClock));

    var box = document.createElement("div");
    box.className = "post-item";

    var title = str(item.title) || "（无标题）";
    var h3 = document.createElement("h3");
    var href = safeHref(item.link);
    if (href) {
      h3.appendChild(buildLink(title, href, true));
    } else {
      h3.textContent = title;
    }
    box.appendChild(h3);

    var summary = str(item.summary);
    if (summary) {
      var p = document.createElement("p");
      p.textContent = summary;
      box.appendChild(p);
    }

    li.appendChild(box);
    return li;
  }

  /* 同一栏同一天有多条时，日期补一行时刻，免得看起来像没排序 */
  function hasSameDay(items) {
    var seen = {};
    for (var i = 0; i < items.length; i += 1) {
      var parts = dateParts(items[i].published);
      if (!parts) {
        continue;
      }
      if (seen[parts.day]) {
        return true;
      }
      seen[parts.day] = true;
    }
    return false;
  }

  /* 该栏最新一条的日期（条目已按时间倒序，第一个有日期的就是它） */
  function newestDate(items) {
    for (var i = 0; i < items.length; i += 1) {
      var parts = dateParts(items[i].published);
      if (parts) {
        return { day: parts.day, raw: str(items[i].published) };
      }
    }
    return null;
  }

  /* 筛选比对：标题 + 摘要，大小写不敏感 */
  function filterItems(items) {
    if (!query) {
      return items;
    }
    var kept = [];
    for (var i = 0; i < items.length; i += 1) {
      var hay = (str(items[i].title) + " " + str(items[i].summary)).toLowerCase();
      if (hay.indexOf(query) !== -1) {
        kept.push(items[i]);
      }
    }
    return kept;
  }

  /* 目录行：左列等宽最新日期，右列源名（站内锚点）与推到行尾的条数。
     索引行只给「机读数据 + 一个可跳转的名字」——不给摘要、不给外链，与内容行区分开。 */
  function buildTocRow(entry, count) {
    var li = document.createElement("li");
    li.className = "post-row";

    var latest = newestDate(entry.items);
    var time = document.createElement("time");
    time.className = "post-date";
    if (latest) {
      time.setAttribute("datetime", latest.raw);
      time.textContent = latest.day;
    } else {
      time.textContent = count ? "日期未知" : "无条目";
    }
    li.appendChild(time);

    var box = document.createElement("div");
    box.className = "post-item";
    var h3 = document.createElement("h3");
    h3.appendChild(buildLink(str(entry.group.title) || str(entry.group.id) || "未命名源",
                            "#" + entry.id, false));
    box.appendChild(h3);
    if (count) {
      var size = document.createElement("span");
      size.className = "rss-toc-count";
      size.textContent = count + " 条";
      box.appendChild(size);
    }
    li.appendChild(box);
    return li;
  }

  function buildToc(shown) {
    var nav = document.createElement("nav");
    nav.className = "sec rss-toc";
    nav.setAttribute("aria-label", "订阅目录");

    var h2 = document.createElement("h2");
    h2.id = TOC_ID;
    h2.textContent = "订阅目录";
    nav.appendChild(h2);

    var list = document.createElement("ul");
    list.className = "post-list";
    for (var i = 0; i < shown.length; i += 1) {
      list.appendChild(buildTocRow(shown[i].entry, shown[i].items.length));
    }
    nav.appendChild(list);
    return nav;
  }

  function buildGroup(entry, items) {
    var section = document.createElement("section");
    section.className = "sec";
    section.id = entry.id;

    var h2 = document.createElement("h2");
    h2.textContent = str(entry.group.title) || str(entry.group.id) || "未命名源";
    section.appendChild(h2);

    /* 出处：栏目题下的一行源站地址（外链，不是资源请求） */
    var site = safeHref(entry.group.html_url);
    if (site) {
      var source = document.createElement("p");
      source.className = "rss-source";
      source.appendChild(buildLink(hostOf(site), site, true));
      section.appendChild(source);
    }

    if (!items.length) {
      section.appendChild(note("本栏暂无条目。"));
      return section;
    }

    var withClock = hasSameDay(items);
    var list = document.createElement("ul");
    list.className = "post-list";
    for (var i = 0; i < items.length; i += 1) {
      list.appendChild(buildItem(items[i], withClock && !!dateParts(items[i].published)));
    }
    section.appendChild(list);

    var back = document.createElement("p");
    back.className = "rss-back";
    var link = buildLink("回到目录", "#" + TOC_ID, false);
    link.setAttribute("aria-label", "回到订阅目录（" + (str(entry.group.title) || "本栏") + "栏读完了）");
    back.appendChild(link);
    section.appendChild(back);
    return section;
  }

  function buildFilter() {
    var row = document.createElement("div");
    row.className = "rss-filter";

    var label = document.createElement("label");
    label.setAttribute("for", FILTER_ID);
    label.textContent = "筛选条目";
    row.appendChild(label);

    var input = document.createElement("input");
    input.id = FILTER_ID;
    input.type = "search";
    input.autocomplete = "off";
    input.placeholder = "标题或摘要里的关键词";
    input.value = needle;
    input.addEventListener("input", function () {
      needle = input.value.trim();
      query = needle.toLowerCase();
      draw(false);
    });
    row.appendChild(input);
    return row;
  }

  function updateNote(matched, sources) {
    if (!query) {
      resultNote.hidden = true;
      resultNote.textContent = "";
      return;
    }
    resultNote.hidden = false;
    resultNote.textContent = matched
      ? "匹配 " + matched + " 条，来自 " + sources + " 个源。"
      : "没有匹配「" + needle + "」的条目；清空筛选框可看全部 " + total + " 条。";
  }

  function draw(restore) {
    var shown = [];
    var matched = 0;
    for (var i = 0; i < entries.length; i += 1) {
      var kept = filterItems(entries[i].items);
      if (kept.length || !query) {
        shown.push({ entry: entries[i], items: kept });
        matched += kept.length;
      }
    }

    content.replaceChildren();
    if (shown.length) {
      content.appendChild(buildToc(shown));
      for (var j = 0; j < shown.length; j += 1) {
        content.appendChild(buildGroup(shown[j].entry, shown[j].items));
      }
    }
    updateNote(matched, shown.length);

    if (restore) {
      restoreHash();
    }
  }

  /* 栏目标是载入后才生成的，浏览器自己不会补跳，所以首次渲染完自己跳一次（瞬间定位，不做缓动） */
  function restoreHash() {
    var id = str(location.hash).slice(1);
    if (!id) {
      return;
    }
    var target = document.getElementById(id);
    if (target) {
      target.scrollIntoView();
    }
  }

  function prepare(doc) {
    var list = doc && Array.isArray(doc.sources) ? doc.sources : [];
    if (!list.length) {
      container.replaceChildren(note(
        "订阅数据是空的：先运行 python scripts/fetch_feeds.py 生成 data/rss-items.json。"));
      return false;
    }
    for (var i = 0; i < list.length; i += 1) {
      var items = Array.isArray(list[i].items) ? list[i].items : [];
      total += items.length;
      entries.push({ group: list[i], id: sectionId(list[i], i), items: items });
    }

    content = document.createElement("div");
    resultNote = document.createElement("p");
    resultNote.className = "rss-note";
    resultNote.setAttribute("aria-live", "polite");
    resultNote.hidden = true;
    container.replaceChildren(buildFilter(), resultNote, content);
    return true;
  }

  function showError(err) {
    container.replaceChildren(note(
      "读不到订阅数据（" + err.message + "）。若这是本地双击打开的页面（file://），"
      + "浏览器会拦截同域 fetch —— 请用 python -m http.server 8080 --directory public 预览；"
      + "订阅清单在 subscriptions.opml。"));
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
    .then(function (doc) {
      if (prepare(doc)) {
        draw(true);
      }
    })
    .catch(showError);
}());
