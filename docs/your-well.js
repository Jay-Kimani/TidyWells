(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); }, svgText = "";
  function vis(on) { $("out").hidden = !on; $("ph").hidden = on; }
  function sel(el, vals, all) {
    el.innerHTML = (all ? '<option value="">' + all + "</option>" : "") + vals.map(function (v) { return '<option value="' + v.replace(/"/g, "&quot;") + '">' + v.replace(/</g, "&lt;") + "</option>"; }).join("");
  }
  var parsed = null;
  function read() {
    var r = WellPoster.parse($("paste").value);
    var msg = $("msg"); msg.textContent = "";
    if (r.error) { parsed = null; msg.textContent = r.error; vis(false); return; }
    parsed = r;
    $("wellrow").hidden = !r.wells.length; $("prodrow").hidden = !r.products.length;
    if (r.wells.length) { var cur = $("well").value; sel($("well"), r.wells, r.wells.length > 1 ? "Choose a well" : ""); if (r.wells.indexOf(cur) >= 0) $("well").value = cur; else if (r.wells.length === 1) $("well").value = r.wells[0]; }
    if (r.products.length) { var cp = $("prod").value; sel($("prod"), r.products, r.products.length > 1 ? "All products" : ""); if (r.products.indexOf(cp) >= 0) $("prod").value = cp; }
    if (r.bad) msg.textContent = r.bad + " line(s) skipped because they could not be read.";
    draw();
  }
  function draw() {
    if (!parsed) return;
    if (parsed.wells.length > 1 && !$("well").value) { $("msg").textContent = "This file has " + parsed.wells.length + " wells. Choose one."; vis(false); return; }
    var s = WellPoster.series(parsed.rows, {well: $("well").value, product: $("prod").value, rate: $("kind").value === "rate"});
    if (s.length < 3) { $("msg").textContent = "Need at least three months for a poster."; vis(false); return; }
    svgText = WellPoster.poster(s, {title: $("title").value.trim() || "My Well", unit: $("unit").value.trim() || "per day", theme: $("theme2").value});
    $("prev").innerHTML = svgText; vis(true);
  }
  function toPng() {
    var img = new Image(), blob = new Blob([svgText], {type: "image/svg+xml;charset=utf-8"}), url = URL.createObjectURL(blob);
    img.onload = function () {
      var c = document.createElement("canvas"); c.width = 3600; c.height = 4800;
      var x = c.getContext("2d"); x.drawImage(img, 0, 0, 3600, 4800); URL.revokeObjectURL(url);
      c.toBlob(function (b) { save(b, "my-well-poster.png"); }, "image/png");
    };
    img.src = url;
  }
  function save(b, name) { var a = document.createElement("a"); a.href = URL.createObjectURL(b); a.download = name; document.body.appendChild(a); a.click(); a.remove(); }
  ["paste"].forEach(function (i) { $(i).addEventListener("input", read); });
  ["well", "prod", "kind", "title", "unit", "theme2"].forEach(function (i) { $(i).addEventListener("input", draw); });
  $("file").addEventListener("change", function (e) { var f = e.target.files[0]; if (!f) return; var r = new FileReader(); r.onload = function () { $("paste").value = r.result; read(); }; r.readAsText(f); });
  $("ex").addEventListener("click", function () {
    var t = "month,volume\n", v = 900; for (var i = 0; i < 36; i++) { var y = 2023 + Math.floor(i / 12), m = (i % 12) + 1; t += y + "-" + (m < 10 ? "0" : "") + m + "," + Math.round(v) + "\n"; v = v * 0.955 + (i % 7 === 3 ? 25 : 0); }
    $("paste").value = t; $("title").value = "Example Well (synthetic)"; $("unit").value = "bbl per day"; $("kind").value = "vol"; read();
  });
  $("dl").addEventListener("click", toPng);
  $("dls").addEventListener("click", function () { save(new Blob([svgText], {type: "image/svg+xml"}), "my-well-poster.svg"); });
})();
