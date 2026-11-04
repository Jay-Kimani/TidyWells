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
