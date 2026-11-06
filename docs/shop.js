// Shop page behaviour: colourway swatches; store links appear only when config.js sets them.
(function () {
  "use strict";
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
  var store = window.TIDYWELLS_SHOP_URL, links = window.TIDYWELLS_SHOP_LINKS || {};
  function ok(u) { return typeof u === "string" && /^https:\/\//.test(u); }
  if (ok(store) || Object.keys(links).length) {
    document.querySelectorAll(".badge").forEach(function (b) { b.textContent = "Now open"; });
    document.querySelectorAll(".prod").forEach(function (card) {
      var u = links[card.getAttribute("data-slug")] || store, go = card.querySelector(".go");
      if (go && ok(u)) { go.className = "go"; go.innerHTML = '<a href="' + u + '" target="_blank" rel="noopener">View in store</a>'; }
    });
  }
  });
})();
