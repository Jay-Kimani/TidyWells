// Comments for analysis posts. Uses Cusdis (name + comment, no account, moderated) when TIDYWELLS_CUSDIS_APP_ID is set;
// otherwise falls back to giscus (GitHub sign-in) if configured. Shows nothing if neither is configured.
(function () {
  var box = document.getElementById("comments");
  if (!box) return;
  var id = window.TIDYWELLS_CUSDIS_APP_ID, g = window.TIDYWELLS_GISCUS;
  function dark() { return document.documentElement.dataset.theme !== "light"; }
  if (id) {
    box.innerHTML = '<h2>Comments</h2><p class="muted" style="margin-top:-6px">Questions, corrections and ideas are welcome. Leave a name and a comment; no account needed. Comments appear after approval. Please be civil, and no investment tips or promotion.</p>' +
      '<div id="cusdis_thread" data-host="https://cusdis.com" data-app-id="' + String(id).replace(/[^A-Za-z0-9-]/g, "") +
      '" data-page-id="' + location.pathname.replace(/"/g, "") + '" data-page-url="' + location.origin + location.pathname +
      '" data-page-title="' + document.title.replace(/"/g, "&quot;") + '" data-theme="' + (dark() ? "dark" : "light") + '"></div>';
    var s = document.createElement("script");
    s.src = "https://cusdis.com/js/cusdis.es.js"; s.async = true; s.defer = true;
    document.body.appendChild(s);
    var t = document.getElementById("theme");
    if (t) t.addEventListener("click", function () {
      setTimeout(function () {
        var th = document.getElementById("cusdis_thread");
        if (th && window.CUSDIS) { th.setAttribute("data-theme", dark() ? "dark" : "light"); window.CUSDIS.setTheme(dark() ? "dark" : "light"); }
      }, 50);
    });
    return;
  }
  if (!g || !g.repoId || !g.categoryId) return;
  box.innerHTML = '<h2>Comments</h2><p class="muted" style="margin-top:-6px">Sign in with GitHub to comment; comments are public. Be civil, and no investment tips or promotion.</p>';
  var gs = document.createElement("script");
  gs.src = "https://giscus.app/client.js"; gs.async = true; gs.crossOrigin = "anonymous";
  var a = { repo: g.repo, "repo-id": g.repoId, category: g.category, "category-id": g.categoryId, mapping: "pathname",
    strict: "1", "reactions-enabled": "1", "emit-metadata": "0", "input-position": "top", theme: dark() ? "dark_dimmed" : "light", lang: "en", loading: "lazy" };
  for (var k in a) gs.setAttribute("data-" + k, a[k]);
  box.appendChild(gs);
})();
