// Comments for analysis posts, powered by giscus (GitHub Discussions). Shows nothing until configured in config.js.
(function () {
  var c = window.TIDYWELLS_GISCUS, box = document.getElementById("comments");
  if (!box || !c || !c.repoId || !c.categoryId) return;
  function theme() { return document.documentElement.dataset.theme === "light" ? "light" : "dark_dimmed"; }
  box.innerHTML = '<h2>Comments</h2><p class="muted" style="margin-top:-6px">Questions, corrections and ideas are welcome. Sign in with GitHub to comment; comments are public and stored in GitHub Discussions. Be civil, and no investment tips or promotion.</p>';
  var s = document.createElement("script");
  s.src = "https://giscus.app/client.js";
  s.async = true; s.crossOrigin = "anonymous";
  var a = { repo: c.repo, "repo-id": c.repoId, category: c.category, "category-id": c.categoryId, mapping: "pathname",
    strict: "1", "reactions-enabled": "1", "emit-metadata": "0", "input-position": "top", theme: theme(), lang: "en", loading: "lazy" };
  for (var k in a) s.setAttribute("data-" + k, a[k]);
  box.appendChild(s);
  var t = document.getElementById("theme");
  if (t) t.addEventListener("click", function () {
    setTimeout(function () {
      var f = document.querySelector("iframe.giscus-frame");
      if (f) f.contentWindow.postMessage({ giscus: { setConfig: { theme: theme() } } }, "https://giscus.app");
    }, 50);
  });
})();
