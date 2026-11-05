// Site-wide extras, all optional via config.js: cookieless analytics (Cloudflare Web Analytics) and a labelled sponsor strip.
(function () {
  var t = window.TIDYWELLS_CF_ANALYTICS_TOKEN;
  if (t && /^[A-Za-z0-9]{16,64}$/.test(t)) {
    var s = document.createElement("script");
    s.defer = true; s.src = "https://static.cloudflareinsights.com/beacon.min.js";
    s.setAttribute("data-cf-beacon", JSON.stringify({ token: t }));
    document.head.appendChild(s);
  }
  var sp = window.TIDYWELLS_SPONSOR, main = document.querySelector("main");
  if (sp && sp.name && sp.url && /^https:\/\//.test(sp.url) && main) {
    var d = document.createElement("div");
    d.className = "sponsor";
    var l = document.createElement("small"); l.textContent = "Sponsor";
    var a = document.createElement("a");
    a.href = sp.url; a.rel = "sponsored noopener"; a.target = "_blank";
    a.textContent = sp.name + (sp.text ? " — " + sp.text : "");
    d.appendChild(l); d.appendChild(a);
    main.insertBefore(d, main.firstChild);
  }
})();

// Navigation dropdowns: one open at a time; close on outside click, Escape or choosing a link.
(function () {
  function all() { return document.querySelectorAll("nav details.dd"); }
  document.addEventListener("toggle", function (e) {
    if (e.target.matches && e.target.matches("nav details.dd") && e.target.open) {
      all().forEach(function (d) { if (d !== e.target) d.open = false; });
    }
  }, true);
  document.addEventListener("click", function (e) {
    all().forEach(function (d) { if (!d.contains(e.target)) d.open = false; });
    if (e.target.closest && e.target.closest("nav details.dd .menu a")) all().forEach(function (d) { d.open = false; });
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") all().forEach(function (d) { if (d.open) { d.open = false; d.querySelector("summary").focus(); } });
  });
})();
