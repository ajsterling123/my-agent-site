/* reader.js —— 读取同域数据文件 ../data/rss-items.json，按订阅源分栏渲染条目。
 *
 * 三条刻意的约束（完整口径见 AGENTS.md「外部数据是不可信输入」）：
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
 * 3) 外链只是导航，不是资源。条目标题指向源站原文，用 https 绝对地址 + target="_blank" +
 *    rel="noopener noreferrer"；链接标签不会让浏览器去请求第三方资源（零外部资源承诺不受影响）。
 */
(function () {
  "use strict";

  var DATA_URL = "../data/rss-items.json";
  var DATE_RE = /^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})/;
  var HTTPS_RE = /^https:\/\/[^\s]+$/i;

  var container = document.getElementById("rss-reader");
  if (!container) {
    return;
  }

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

  function note(message) {
    var p = document.createElement("p");
    p.className = "intro";
    p.textContent = message;
    return p;
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
      var a = document.createElement("a");
      a.href = href;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.textContent = title;
      h3.appendChild(a);
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

  function buildGroup(group) {
    var section = document.createElement("section");
    section.className = "sec";

    var h2 = document.createElement("h2");
    h2.textContent = str(group.title) || str(group.id) || "未命名源";
    section.appendChild(h2);

    var items = Array.isArray(group.items) ? group.items : [];
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
    return section;
  }

  function render(doc) {
    var groups = doc && Array.isArray(doc.sources) ? doc.sources : [];
    container.replaceChildren();
    if (!groups.length) {
      container.appendChild(note("订阅数据是空的：先运行 python scripts/fetch_feeds.py 生成 data/rss-items.json。"));
      return;
    }
    for (var i = 0; i < groups.length; i += 1) {
      container.appendChild(buildGroup(groups[i]));
    }
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
    .then(render)
    .catch(showError);
}());
