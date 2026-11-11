// Comments for analysis posts. If TIDYWELLS_COMMENTS_API is set, uses the Tidywells comment service
// (name + comment, no account, published straight away, Turnstile spam check). Otherwise falls back to giscus
// (GitHub sign-in) if configured. Shows nothing if neither is configured.
(function () {
  var box = document.getElementById("comments");
  if (!box) return;
  var api = (window.TIDYWELLS_COMMENTS_API || "").replace(/\/$/, ""), site = window.TIDYWELLS_TURNSTILE_SITEKEY || "";
  var g = window.TIDYWELLS_GISCUS;
  function dark() { return document.documentElement.dataset.theme !== "light"; }
  function el(tag, props, kids) {
    var e = document.createElement(tag);
    for (var k in props || {}) { if (k === "text") e.textContent = props[k]; else e.setAttribute(k, props[k]); }
    (kids || []).forEach(function (c) { e.appendChild(c); });
    return e;
  }
  if (api && site) {
    var page = location.pathname, list = el("div", { id: "cm-list" }), msg = el("p", { class: "muted", role: "status" });
    var name = el("input", { type: "text", maxlength: "60", placeholder: "Your name", required: "required", "aria-label": "Your name" });
    var body = el("textarea", { maxlength: "2000", rows: "4", placeholder: "Your comment", required: "required", "aria-label": "Your comment" });
    var hp = el("input", { type: "text", name: "website", tabindex: "-1", autocomplete: "off", "aria-hidden": "true", style: "position:absolute;left:-9999px" });
    var ts = el("div", { class: "cf-turnstile", "data-sitekey": site, "data-theme": dark() ? "dark" : "light" });
    var btn = el("button", { type: "submit", class: "btn primary", text: "Post comment" });
    var form = el("form", { class: "panel", style: "display:grid;gap:10px;margin:14px 0" }, [name, body, hp, ts, btn, msg]);
    [name, body].forEach(function (i) { i.style.cssText = "width:100%;box-sizing:border-box;padding:9px 11px;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--fg);font:inherit"; });
    box.appendChild(el("h2", { text: "Comments" }));
    box.appendChild(el("p", { class: "muted", style: "margin-top:-6px", text: "Questions, corrections and ideas are welcome. Leave a name and a comment; no account needed. Please be civil, and no investment tips or promotion." }));
    box.appendChild(list); box.appendChild(form);
    var loadTs = document.createElement("script");
    loadTs.src = "https://challenges.cloudflare.com/turnstile/v0/api.js"; loadTs.async = true; loadTs.defer = true;
    document.body.appendChild(loadTs);
    var load = function () {
      fetch(api + "/comments?page=" + encodeURIComponent(page)).then(function (r) { return r.json(); }).then(function (d) {
        list.textContent = "";
        if (!(d.comments || []).length) list.appendChild(el("p", { class: "muted", text: "No comments yet. Be the first." }));
        (d.comments || []).forEach(function (c) {
          list.appendChild(el("div", { class: "card", style: "margin:10px 0;padding:12px 16px" }, [
            el("strong", { text: c.name }), el("small", { class: "muted", text: "  " + new Date(c.created).toLocaleDateString() }),
            el("p", { style: "margin:6px 0 0;white-space:pre-wrap", text: c.body })]));
        });
      }).catch(function () {});
    };
    load();
    form.addEventListener("submit", function (ev) {
      ev.preventDefault(); btn.disabled = true; msg.textContent = "Posting...";
      var tokEl = form.querySelector("[name=cf-turnstile-response]");
      fetch(api + "/comments", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ page: page, name: name.value, body: body.value, website: hp.value, token: tokEl ? tokEl.value : "" }) })
        .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); })
        .then(function (x) {
          if (x.ok) { msg.textContent = "Thanks! Your comment is posted."; body.value = ""; load(); if (window.turnstile) window.turnstile.reset(); }
          else msg.textContent = x.d.error || "Something went wrong. Please try again.";
        }).catch(function () { msg.textContent = "Could not reach the comment service. Please try again."; })
        .then(function () { btn.disabled = false; });
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
