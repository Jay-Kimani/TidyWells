// Shop page behaviour: colourway swatches; store links appear only when config.js sets them.
(function () {
  "use strict";
  // product page: colourway switch between the pictures
  document.querySelectorAll(".pview").forEach(function (v) {
    v.querySelectorAll(".sw button").forEach(function (b) {
      b.addEventListener("click", function () {
        v.querySelectorAll("img[data-pi]").forEach(function (im) { im.hidden = im.getAttribute("data-pi") !== b.getAttribute("data-pi"); });
        v.querySelectorAll(".sw button").forEach(function (o) { o.setAttribute("aria-pressed", o === b ? "true" : "false"); });
      });
    });
  });
  document.querySelectorAll(".prod").forEach(function (card) {
    var img = card.querySelector("img[data-base]");
    if (img) {
      card.querySelectorAll(".sw button").forEach(function (b) {
        b.addEventListener("click", function () {
          img.src = img.getAttribute("data-base") + b.getAttribute("data-cw") + ".jpg";
          card.querySelectorAll(".sw button").forEach(function (o) { o.setAttribute("aria-pressed", o === b ? "true" : "false"); });
        });
      });
    }
  });
  document.addEventListener("DOMContentLoaded", function () {
  var action = window.TIDYWELLS_NEWSLETTER_ACTION || "";
  document.querySelectorAll(".waitlist").forEach(function (wl) {
  if (action) {
    wl.innerHTML = '<form action="' + action.replace(/"/g, "") + '" method="post" target="_blank"><input type="hidden" value="1" name="embed"><input type="hidden" name="tag" value="shop-launch">' +
      '<input type="email" name="email" required placeholder="you@example.com" aria-label="Email address"><button type="submit" class="btn primary">Tell me when it opens</button></form>' +
      '<p class="shop-note">You will be added to the Tidywells email list with a shop-launch tag. Unsubscribe any time from any email.</p>';
  } else {
    wl.innerHTML = '<p class="shop-note">Follow on <a href="https://tidywells.substack.com/" target="_blank" rel="noopener">Substack</a> to hear when the shop opens.</p>';
  }
  });
  // Store links: shown only once config.js sets TIDYWELLS_SHOP_OPEN = true (the Shopify store is password-protected until then).
  var links = window.TIDYWELLS_SHOP_LINKS || {}, open = window.TIDYWELLS_SHOP_OPEN === true;
  function ok(u) { return typeof u === "string" && /^https:\/\//.test(u); }
  if (open) {
    document.querySelectorAll(".badge").forEach(function (b) { b.textContent = "Now open"; });
    document.querySelectorAll("[data-slug]").forEach(function (el) {
      var u = links[el.getAttribute("data-slug")], go = el.classList.contains("go") ? el : el.querySelector(".go");
      if (!go || !u) return;
      var one = function (url, label) { return '<a class="btn primary" href="' + url + '" target="_blank" rel="noopener">' + label + '</a>'; };
      var html = "";
      if (typeof u === "object") { if (ok(u.night)) html += one(u.night, "Night edition in the store "); if (ok(u.paper)) html += " " + one(u.paper, "Paper edition in the store"); }
      else if (ok(u)) html = one(u, "Buy in the store");
      if (html) { go.className = "go"; go.innerHTML = html; }
    });
  }
  });
})();

// product page: click the picture for a larger preview; click again to zoom in, Esc or the x to close
(function () {
  "use strict";
  var view = document.querySelector(".pview");
  if (!view) return;
  var box, img, zoomed = false;
  function build() {
    box = document.createElement("div");
    box.className = "lb"; box.hidden = true; box.setAttribute("role", "dialog"); box.setAttribute("aria-modal", "true"); box.setAttribute("aria-label", "Larger picture");
    box.innerHTML = '<button type="button" class="lb-x" aria-label="Close">&times;</button><div class="lb-s"><img alt=""></div><p class="lb-h">Click the picture to zoom, Esc to close</p>';
    document.body.appendChild(box);
    img = box.querySelector("img");
    box.addEventListener("click", function (e) { if (e.target === img) { zoomed = !zoomed; box.classList.toggle("zoom", zoomed); } else close(); });
    document.addEventListener("keydown", function (e) { if (!box.hidden && e.key === "Escape") close(); });
  }
  function open(src, alt) {
    if (!box) build();
    img.src = src; img.alt = alt || ""; zoomed = false; box.classList.remove("zoom"); box.hidden = false;
    document.documentElement.style.overflow = "hidden"; box.querySelector(".lb-x").focus();
  }
  function close() { box.hidden = true; document.documentElement.style.overflow = ""; }
  view.querySelectorAll("img").forEach(function (im) {
    im.tabIndex = 0; im.setAttribute("role", "button"); im.style.cursor = "zoom-in";
    function go() { open(im.getAttribute("data-full") || im.currentSrc || im.src, im.alt); }
    im.addEventListener("click", go);
    im.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); go(); } });
  });
})();
