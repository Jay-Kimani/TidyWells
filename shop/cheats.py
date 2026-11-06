"""Three printable reference sheets (HTML for render.js -> PDF). Constants are standard published conversion factors."""
import json
import sys
from pathlib import Path

CSS = """
@page{size:11in 17in;margin:0}*{box-sizing:border-box}
html,body{margin:0;background:#0a1020;color:#eef3ff;font-family:Inter,Arial,sans-serif}
.pg{width:11in;height:17in;padding:.7in .75in;position:relative;overflow:hidden;background:#0a1020}
.k{font:600 11pt 'IBM Plex Mono',monospace;letter-spacing:.2em;text-transform:uppercase;color:#2f9bff}
h1{font:700 52pt/1.02 Fraunces,Georgia,serif;margin:.18in 0 .1in}
.sub{color:#8fa0c4;font-size:18pt;margin:0 0 .4in}
.g{display:grid;gap:.22in}.g2{grid-template-columns:1fr 1fr}
.b{background:#101a31;border:1px solid #26345a;border-radius:10px;padding:.2in .24in}
.b h2{font:700 24pt Fraunces,Georgia,serif;margin:0 0 .08in;color:#fff}
.b p,.b li{font-size:16pt;line-height:1.4;color:#c9d4ee;margin:.04in 0}.b ul{margin:.04in 0;padding-left:.22in}
.f{font:500 20pt 'IBM Plex Mono','DejaVu Sans Mono',monospace;color:#7fc0ff;margin:.08in 0}
table{border-collapse:collapse;width:100%;font-size:16pt}td,th{padding:.1in .08in;border-bottom:1px solid #26345a;text-align:left}
th{color:#8fa0c4;font-weight:600;font-size:12pt;letter-spacing:.1em;text-transform:uppercase}td:last-child{font-family:'IBM Plex Mono','DejaVu Sans Mono',monospace;color:#7fc0ff}
.ft{position:absolute;left:.75in;right:.75in;bottom:.5in;display:flex;justify-content:space-between;color:#8fa0c4;font-size:10pt;line-height:1.4}
.ft b{font:700 15pt Fraunces,Georgia,serif;color:#fff}
"""


def sheet(kicker, title, sub, body, note):
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body><div class="pg">'
            f'<div class="k">{kicker}</div><h1>{title}</h1><p class="sub">{sub}</p>{body}'
            f'<div class="ft"><span>{note}</span><b>tidywells.com</b></div></div></body></html>')


UNITS = sheet("Tidywells reference sheet", "Units &amp; Conversions", "The factors Canadian oil and gas data keeps tripping people on.", """<div style="zoom:.86">
<div class="g g2">
<div class="b"><h2>Oil</h2><table><tr><th>From</th><th>To</th></tr>
<tr><td>1 m³ oil</td><td>6.2898 bbl</td></tr><tr><td>1 bbl</td><td>0.158987 m³</td></tr>
<tr><td>1 m³/d</td><td>6.2898 bbl/d</td></tr><tr><td>1,000 m³ oil</td><td>6,289.8 bbl</td></tr></table></div>
<div class="b"><h2>Gas</h2><table><tr><th>From</th><th>To</th></tr>
<tr><td>1 m³ gas</td><td>35.3147 ft³</td></tr><tr><td>1 10³m³ (e3m3)</td><td>35.3147 Mcf</td></tr>
<tr><td>1 Mcf</td><td>1,000 ft³</td></tr><tr><td>1 MMcf</td><td>1,000 Mcf</td></tr><tr><td>1 Bcf</td><td>1,000 MMcf</td></tr></table></div>
<div class="b"><h2>Energy &amp; equivalents</h2><table><tr><th>From</th><th>To</th></tr>
<tr><td>1 GJ</td><td>0.947817 MMBtu</td></tr><tr><td>1 MMBtu</td><td>1.05506 GJ</td></tr>
<tr><td>6 Mcf gas</td><td>1 boe (6:1 rule of thumb)</td></tr></table>
<p>The 6:1 boe ratio is an energy convention, not a price or a physical law. Gas heating value varies by stream, so GJ per m³ is not constant.</p></div>
<div class="b"><h2>Pressure</h2><table><tr><th>From</th><th>To</th></tr><tr><td>1 kPa</td><td>0.145038 psi</td></tr><tr><td>1 psi</td><td>6.89476 kPa</td></tr><tr><td>1 MPa</td><td>1,000 kPa</td></tr></table></div>
</div>
<div class="b" style="margin-top:.22in"><h2>From monthly volume to a daily rate</h2>
<div class="f">rate = monthly volume ÷ days in that month</div>
<p>Regulators publish <b>monthly volumes</b>. Compare months by rate, not volume, or February will always look like a collapse. Alberta and Saskatchewan (Petrinex) report oil in m³ and gas in 10³m³; BC Energy Regulator files use their own units, so check the header before you add anything up.</p>
<div class="f">AB oil: m³ × 6.2898 ÷ 1000 = thousand bbl for the month<br>AB gas: 10³m³ × 35.3147 ÷ 1000 = MMcf for the month</div></div>
<div class="b" style="margin-top:.22in"><h2>Prefix traps</h2><ul><li><b>M</b> means thousand in field use (Mcf), but <b>MM</b> means million. In SI, M is mega (million). Always check which system you are reading.</li><li><b>k</b> is thousand: 1 kbbl/d = 1,000 bbl/d. <b>e3m3</b> and <b>10³m³</b> are the same unit.</li><li>Cumulative volumes are not rates. Never average them.</li></ul></div></div>
""", "Standard published conversion factors. Check units in the source file before relying on any result. Not engineering or investment advice.")

ARPS = sheet("Tidywells reference sheet", "Decline Curves, One Page", "The Arps family in the order you will meet it.", """
<div class="g g2">
<div class="b"><h2>Exponential &nbsp;(b = 0)</h2><div class="f">q = qᵢ · e<sup>−Dt</sup></div><p>A constant share of the rate is lost each period. Often used as a floor for late life.</p><div class="f">Nₚ = (qᵢ − q) / D</div><p>Cumulative production to rate q.</p></div>
<div class="b"><h2>Hyperbolic &nbsp;(0 &lt; b &lt; 2)</h2><div class="f">q = qᵢ / (1 + b·Dᵢ·t)<sup>1/b</sup></div><p>The decline rate itself falls as the well ages. Most unconventional wells need b above 0.</p></div>
<div class="b"><h2>Harmonic &nbsp;(b = 1)</h2><div class="f">q = qᵢ / (1 + Dᵢ·t)</div><p>A special case of the hyperbolic family. Cumulative grows without bound, so it needs a cutoff.</p></div>
<div class="b"><h2>Effective vs nominal</h2><div class="f">Dₑ = 1 − e<sup>−D</sup> &nbsp;(exponential)</div><p>Nominal D is the continuous rate; effective Dₑ is the share lost over a year. Mixing them up is the most common error.</p></div>
</div>
<div class="b" style="margin-top:.22in"><h2>What the symbols mean</h2><table><tr><th>Symbol</th><th>Meaning</th></tr>
<tr><td>q</td><td>rate at time t</td></tr><tr><td>qᵢ</td><td>initial rate at the start of the decline</td></tr><tr><td>Dᵢ</td><td>initial nominal decline rate (per unit time)</td></tr><tr><td>b</td><td>decline exponent (curvature)</td></tr><tr><td>t</td><td>time since the start of the decline</td></tr></table></div>
<div class="b" style="margin-top:.22in"><h2>Habits that keep a fit honest</h2><ul><li>Fit from the peak rate, not from first production.</li><li>Convert monthly volumes to daily rates first.</li><li>Bound b (Tidywells uses 0 to 2) so a noisy tail cannot produce nonsense.</li><li>Report the range, not one number. A fit is a description of the past, not a promise.</li><li>Shut-ins, workovers and curtailments break the curve. Mark them and refit.</li></ul></div>
""", "Reference: Arps, J.J. (1945), Analysis of Decline Curves, Transactions of the AIME. Illustrative only; not for reserves reporting or investment decisions.")

GOTCHA = sheet("Tidywells reference sheet", "Regulator Data Gotchas", "Seven things that quietly break an analysis of public Canadian well data.", """
<div class="g">
<div class="b"><h2>1. Leading zeros in IDs matter</h2><p>A well or facility ID is text, not a number. Open a file in a spreadsheet and 0001234 becomes 1234, then joins fail or match the wrong record.</p></div>
<div class="b"><h2>2. Licensed ≠ producing</h2><p>A licence says a well may exist. Only a production report says it produced. Count producing wells from production rows, not from licence lists.</p></div>
<div class="b"><h2>3. Monthly volume is not a rate</h2><p>Divide by days in the month before comparing months. February is short, not broken.</p></div>
<div class="b"><h2>4. Check the unit on every file</h2><p>m³, 10³m³, bbl, Mcf: the header tells you, the filename may not. Alberta and Saskatchewan (Petrinex) and BC (BCER) do not share a layout.</p></div>
<div class="b"><h2>5. Prorated and estimated rows</h2><p>Some volumes are allocated across wells rather than metered one by one. Treat single-well precision with care.</p></div>
<div class="b"><h2>6. Regulators restate months</h2><p>The first number published for a month can change later. Keep dated copies of what you downloaded so you can see what moved.</p></div>
<div class="b"><h2>7. Totals differ between sources</h2><p>A product definition (for example conventional volumetrics only) changes the total. When two sources disagree, compare definitions before assuming an error.</p></div>
</div>
""", "General cautions drawn from the public file layouts. Tidywells is not affiliated with any regulator; this is not legal or investment advice.")


def main(out):
    out = Path(out)
    (out / "svg").mkdir(parents=True, exist_ok=True)
    jobs = []
    for slug, html in (("units-and-conversions", UNITS), ("decline-curves-one-page", ARPS), ("regulator-data-gotchas", GOTCHA)):
        (out / "svg" / f"sheet-{slug}.html").write_text(html, encoding="utf-8")
        jobs.append({"src": f"svg/sheet-{slug}.html", "out": f"print/digital/tidywells-{slug}-11x17.pdf", "w": "11in", "h": "17in", "type": "pdf"})
    json.dump(jobs, open(out / "manifest-sheets.json", "w"))


if __name__ == "__main__":
    main(sys.argv[1])
