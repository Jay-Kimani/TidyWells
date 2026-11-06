"""Analysis post: first-year decline of new wells (from posts/decline_study.json). Imports gen_posts2 (regenerates earlier posts).
    python posts/gen_posts3.py && python posts/build_feed.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_posts2 as g2  # noqa: E402

ROOT, PUB, CHIPS, PAL, n0, fig, add = g2.ROOT, g2.PUB, g2.CHIPS, g2.PAL, g2.n0, g2.fig, g2.add
D = json.loads((ROOT / "posts" / "decline_study.json").read_text())
AB, SK = D["AB"], D["SK"]
pc = lambda x: f"{100 * x:.0f}%"
rows = [("Alberta oil", AB["by_class"]["oil"]), ("Alberta bitumen", AB["by_class"]["bitumen"]),
        ("Alberta gas", AB["by_class"]["gas"]), ("Saskatchewan oil", SK["by_class"]["oil"])]
cats = [r[0] for r in rows]
f1 = g2.gbars(cats, [("25th percentile", [100 * r[1]["p25"] for r in rows], PAL[4]), ("Median", [100 * r[1]["median"] for r in rows], PAL[0]),
                     ("75th percentile", [100 * r[1]["p75"] for r in rows], PAL[2])],
              ylab="rate in months 10 to 12, % of early peak", yfmt=lambda v: f"{v:g}%", hi=120)
yrs = [2022, 2023, 2024, 2025]
vv = lambda prov, cls: {x["year"]: x for x in prov["by_vintage"] if x["cls"] == cls}
ao, ag, ab_, so = vv(AB, "oil"), vv(AB, "gas"), vv(AB, "bitumen"), vv(SK, "oil")
f2 = g2.chart([("Alberta oil", [100 * ao[y]["median"] for y in yrs], PAL[0]), ("Alberta gas", [100 * ag[y]["median"] for y in yrs], PAL[2]),
               ("Alberta bitumen", [100 * ab_[y]["median"] for y in yrs], PAL[3]), ("Saskatchewan oil", [100 * so[y]["median"] for y in yrs], PAL[1])],
              [str(y) for y in yrs], ylab="median, % of early peak", yfmt=lambda v: f"{v:g}%", lo=0, hi=100, right=160)
trs = "".join(f'<tr><td>{n}</td><td>{x["n"]:,}</td><td>{x["still_on"]:.0f}%</td><td>{pc(x["median"])}</td><td>{pc(x["p25"])} to {pc(x["p75"])}</td></tr>' for n, x in rows)
dr = AB["by_drill"]
vt = "".join(f'<tr><td>{n}</td>' + "".join(f'<td>{pc(d[y]["median"])} <small>(n {d[y]["n"]:,})</small></td>' for y in yrs) + "</tr>"
             for n, d in (("Alberta oil", ao), ("Alberta gas", ag), ("Alberta bitumen", ab_), ("Saskatchewan oil", so)))
AOR, SOR = AB["by_class"]["oil"]["median"], SK["by_class"]["oil"]["median"]
TK_F1 = f"A typical new Alberta oil well is at {pc(AOR)} of its early peak a year in; Saskatchewan oil {pc(SOR)}, Alberta gas {pc(AB['by_class']['gas']['median'])}."
TK_F2 = "Wells that started in 2025 declined about as much as those that started in 2022, in every group."
body = f'''<h1>How fast do new wells decline in their first year?</h1>{CHIPS}
<p>A decline curve starts with a big number and a steep fall. How steep is the first year in practice? We followed new wells in Alberta and Saskatchewan and compared each well's rate in months 10 to 12 with its early peak.</p>
<h2>What we did</h2>
<ul><li><b>New wells:</b> spud date in 2021 or later, first producing month between February 2022 and September 2025 (so each has at least a year of history in the data), and not already producing in January 2022.</li>
<li><b>Peak:</b> the highest daily rate in a well's first three producing months. Daily rate is the monthly volume divided by days in the month.</li>
<li><b>Measure:</b> the average daily rate in producing months 10 to 12 as a share of that peak. 100% means no decline.</li>
<li><b>Groups:</b> a well is "oil" if oil is at least half of its output on an energy basis (6 Mcf of gas counts as 1 bbl), otherwise "gas". Alberta wells licensed for crude bitumen are shown separately. Groups under 30 wells are not shown.</li>
<li><b>Survivors only:</b> the median covers wells that produced in all three of months 10 to 12; the table shows how many that was.</li></ul>
<h2>1. A typical new oil well is at about 40% of its early peak a year in</h2>
<div class="tw"><table><tr><th>Group</th><th>New wells</th><th>Producing in all of months 10 to 12</th><th>Median, % of early peak</th><th>Middle half of wells</th></tr>{trs}</table></div>
{fig(f1, "<b>Figure 1.</b> Rate in months 10 to 12 as a share of the early peak: median with the 25th and 75th percentiles. Real data, Alberta and Saskatchewan new wells.", take=TK_F1)}
<p>At the median, Alberta oil wells are producing {pc(AOR)} of their early peak a year in, Saskatchewan oil {pc(SOR)}, Alberta gas {pc(AB["by_class"]["gas"]["median"])} and Alberta bitumen wells {pc(AB["by_class"]["bitumen"]["median"])}. Bitumen wells hold up best, which may reflect a more gradual ramp-up, though we did not test that. The spread is wide: the middle half of Alberta bitumen wells runs from {pc(AB["by_class"]["bitumen"]["p25"])} to {pc(AB["by_class"]["bitumen"]["p75"])}, so more than a quarter of them are above their early peak a year in, while the middle half of Alberta gas wells runs from {pc(AB["by_class"]["gas"]["p25"])} to {pc(AB["by_class"]["gas"]["p75"])}.</p>
<h2>2. The shape has not changed, even where starting rates have</h2>
{fig(f2, "<b>Figure 2.</b> Median month 10 to 12 rate as a share of the early peak, by the year a well first produced. Real data.", take=TK_F2)}
<div class="tw"><table><tr><th>Group</th><th>2022</th><th>2023</th><th>2024</th><th>2025</th></tr>{vt}</table></div>
<p>Wells that started in 2025 declined about as much as those that started in 2022 in every group. Our <a href="new-wells-by-vintage.html">new-well vintage post</a> found Alberta oil wells (there including bitumen) starting stronger each year. That means newer wells start higher and still fall by a similar share, not that they hold their rate better.</p>
<h2>3. Horizontal versus other wells</h2>
<p>Almost all new Alberta wells are flagged horizontal. Horizontal oil wells were at {pc(dr["oil_horizontal"]["median"])} of their early peak a year in against {pc(dr["oil_other"]["median"])} for the {dr["oil_other"]["n"]} other oil wells; the other groups are too small to say much (Alberta gas: {pc(dr["gas_horizontal"]["median"])} against {pc(dr["gas_other"]["median"])} for {dr["gas_other"]["n"]} wells).</p>
<h2>What this means in practice</h2>
<ul><li>As a rough check on a forecast: a new oil well that is above 60% of its early peak at month 12 is in the top quarter of its peers; one below about 30% is in the bottom quarter.</li>
<li>Do not read a single well's year-one drop as a decline-curve parameter. The spread between wells is large, so fit curves to the well's own history and use these shares only as a sanity check.</li>
<li>Use the same definition of "peak" when comparing. Using the first month, a different window or a smoothed rate would give different percentages.</li></ul>
<h2>Limits</h2>
<ul><li>Taking the highest of three months as the peak pushes the ratio down; a well that ramps up over several months looks flatter under this measure.</li>
<li>Only wells that kept producing through months 10 to 12 are in the median, so wells that stopped before then are not counted as having declined. The table shows the share that survived.</li>
<li>Monthly volumes hide shut-ins within a month; the daily rate divides by calendar days, not producing days.</li>
<li>No adjustment for lateral length, completion size, location or fluid mix. Bitumen wells are identified by licence substance and are kept out of the Alberta oil group.</li>
<li>Wells that first produced in 2025 have the shortest history and can be revised as later months arrive.</li></ul>{g2.REPRO.replace("<code>posts/wells_study.py</code>", "<code>posts/decline_study.py</code>").replace("<code>posts/gen_posts2.py</code>", "<code>posts/gen_posts3.py</code>")}{g2.LICENCE}'''
add("first-year-decline", "How fast do new wells decline in their first year?",
    f"A typical new Alberta oil well is producing about {pc(AOR)} of its early peak rate a year in; Saskatchewan oil {pc(SOR)}, Alberta gas {pc(AB['by_class']['gas']['median'])}. The shape barely changed from 2022 to 2025.",
    body, g2.mini_bars(["AB oil", "AB bit.", "AB gas", "SK oil"], [("median", [100 * r[1]["median"] for r in rows], PAL[0])], "month 10-12 rate, % of early peak", hi=100))

pj = ROOT / "posts" / "posts.json"
posts = [p for p in json.loads(pj.read_text()) if p["slug"] not in {n["slug"] for n in g2.posts_new}]
posts += g2.posts_new
pj.write_text(json.dumps(posts, indent=2), encoding="utf-8")
print(len(posts), "posts total")
