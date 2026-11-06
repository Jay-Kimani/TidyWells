// Rasterise shop artwork with Chromium (Playwright). Usage: node shop/render.js MANIFEST.json
// Manifest: [{src:"x.svg"|"x.html", out:"x.png", w, h, scale, type:"png"|"jpeg"|"pdf", transparent:bool, quality:int}]
// Fonts (SIL OFL) come from @fontsource packages: FONT_DIR=/path/to/node_modules/@fontsource
const fs = require("fs"), path = require("path");
const { chromium } = require("playwright");
const FD = process.env.FONT_DIR || "/tmp/fonts/node_modules/@fontsource";
const faces = [];
function add(pkg, family, weights, styles) {
  for (const w of weights) for (const s of styles)
    faces.push(`@font-face{font-family:"${family}";font-weight:${w};font-style:${s};src:url("file://${FD}/${pkg}/files/${pkg}-latin-${w}-${s}.woff2") format("woff2")}`);
}
add("fraunces", "Fraunces", [400, 600, 700], ["normal", "italic"]);
add("inter", "Inter", [400, 500, 600, 700, 800], ["normal"]);
add("ibm-plex-mono", "IBM Plex Mono", [400, 500, 700], ["normal"]);
const CSS = faces.join("\n");
const SPECS = ['700 20px Fraunces', 'italic 400 20px Fraunces', 'italic 600 20px Fraunces', '400 20px Inter', '500 20px Inter', '600 20px Inter', '700 20px Inter', '800 20px Inter', '500 20px "IBM Plex Mono"', '700 20px "IBM Plex Mono"'];

(async () => {
  const jobs = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
  const base = path.dirname(path.resolve(process.argv[2]));
  const browser = await chromium.launch();
  const shell = path.join(base, "_shell.html");
  fs.writeFileSync(shell, `<!doctype html><meta charset="utf-8"><style>${CSS}html,body{margin:0;padding:0;background:transparent}svg{display:block}</style><div id="a"></div>`);
  const byScale = {};
  for (const j of jobs) (byScale[j.scale || 1] = byScale[j.scale || 1] || []).push(j);
  for (const [scale, list] of Object.entries(byScale)) {
    const ctx = await browser.newContext({ deviceScaleFactor: Number(scale), viewport: { width: 800, height: 600 } });
    const page = await ctx.newPage();
    await page.goto("file://" + shell);
    await page.evaluate(async (specs) => { await Promise.all(specs.map(s => document.fonts.load(s, "Aa≠³ᵢ0"))); }, SPECS);
    for (const j of list) {
      const src = fs.readFileSync(path.resolve(base, j.src), "utf8");
      if (j.type === "pdf") {
        await page.setContent(src.includes("<html") ? src : `<!doctype html><meta charset="utf-8"><style>${CSS}</style>${src}`, { waitUntil: "load" });
        await page.evaluate(async (specs) => { await Promise.all(specs.map(s => document.fonts.load(s, "Aa"))); await document.fonts.ready; }, SPECS);
        await page.pdf({ path: path.resolve(base, j.out), width: j.w, height: j.h, printBackground: true, margin: { top: 0, right: 0, bottom: 0, left: 0 } });
        console.log("pdf", j.out); continue;
      }
      await page.goto("file://" + shell);
      await page.setViewportSize({ width: j.w, height: j.h });
      await page.evaluate(async ([svg, w, h]) => {
        const a = document.getElementById("a"); a.innerHTML = svg;
        const s = a.querySelector("svg"); s.setAttribute("width", w); s.setAttribute("height", h);
        await document.fonts.ready;
      }, [src, j.w, j.h]);
      fs.mkdirSync(path.dirname(path.resolve(base, j.out)), { recursive: true });
      await page.screenshot({ path: path.resolve(base, j.out), type: j.type || "png", omitBackground: !!j.transparent, quality: j.type === "jpeg" ? (j.quality || 85) : undefined, clip: { x: 0, y: 0, width: j.w, height: j.h } });
      console.log(j.type || "png", j.out);
    }
    await ctx.close();
  }
  await browser.close();
})();
