"""Build docs/feed.xml (RSS 2.0) from posts/posts.json. Run after adding a post:
    python posts/build_feed.py
posts.json is a list of {title, slug, date (YYYY-MM-DD), summary}; the page is docs/posts/<slug>.html.
"""
import json
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://tidywells.com/"


def build(posts):
    items = []
    for p in sorted(posts, key=lambda p: p["date"], reverse=True):
        d = datetime.strptime(p["date"], "%Y-%m-%d").replace(hour=12, tzinfo=timezone.utc)
        url = f"{SITE}posts/{p['slug']}.html"
        items.append(f"<item><title>{escape(p['title'])}</title><link>{url}</link><guid>{url}</guid>"
                     f"<pubDate>{format_datetime(d)}</pubDate><description>{escape(p['summary'])}</description></item>")
    return ('<?xml version="1.0" encoding="UTF-8"?><?xml-stylesheet type="text/xsl" href="feed.xsl"?>'
            '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel><title>Tidywells</title>'
            f'<atom:link href="{SITE}feed.xml" rel="self" type="application/rss+xml"/>'
            f"<link>{SITE}</link><description>Canadian oil and gas data, decline curves and plain-language analysis.</description>"
            "<language>en-ca</language>" + "".join(items) + "</channel></rss>\n")


MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def card(p, root=""):
    y, m, _ = p["date"].split("-")
    svg = ""
    if p.get("thumb"):
        svg = '<div class="thumb">' + (ROOT / "posts" / f"thumb_{p['thumb']}.svg").read_text() + "</div>"
    return (f'<a class="card post" href="{root}posts/{p["slug"]}.html"><div><small class="date">{MONTHS[int(m) - 1]} {y}</small>'
            f'<b class="ptitle">{escape(p["title"])}</b><p>{escape(p["summary"])}</p></div>{svg}</a>')


def patch(path, html):
    s = path.read_text(encoding="utf-8")
    a, z = "<!--POSTS-->", "<!--/POSTS-->"
    i, j = s.index(a) + len(a), s.index(z)
    path.write_text(s[:i] + "\n" + html + "\n" + s[j:], encoding="utf-8")


def snaps_html(snaps):
    by = {}
    for p in sorted(snaps, key=lambda p: p["period"], reverse=True):
        by.setdefault(p["period"][:4], []).append(p)
    out = []
    for n, (y, ps) in enumerate(by.items()):
        links = "".join(f'<a class="snap" href="posts/{p["slug"]}.html"><b>{MONTHS[int(p["period"][5:]) - 1]}</b><span>{escape(p["summary"].split(";")[0])}</span></a>' for p in ps)
        out.append(f'<details{" open" if n == 0 else ""}><summary>{y} <small>({len(ps)} months)</small></summary><div class="snaps">{links}</div></details>')
    return "".join(out)


if __name__ == "__main__":
    raw = json.loads((ROOT / "posts" / "posts.json").read_text())
    # newest first; within one date, analysis posts come before snapshots, and later-added posts before earlier ones
    posts = [p for _, p in sorted(enumerate(raw), key=lambda t: (t[1]["date"], t[1].get("kind", "analysis") == "analysis", t[1].get("period", ""), t[0]), reverse=True)]
    analysis = [p for p in posts if p.get("kind", "analysis") == "analysis"]
    snaps = [p for p in posts if p.get("kind") == "snapshot"]
    (ROOT / "docs" / "feed.xml").write_text(build(posts[:40]), encoding="utf-8")
    patch(ROOT / "docs" / "index.html", card(analysis[0]))
    a = ROOT / "docs" / "analysis.html"
    patch(a, "".join(card(p) for p in analysis))
    t = a.read_text(encoding="utf-8")
    i, j = t.index("<!--SNAPS-->") + 12, t.index("<!--/SNAPS-->")
    a.write_text(t[:i] + "\n" + snaps_html(snaps) + "\n" + t[j:], encoding="utf-8")
    # sitemap + robots (search engines)
    base = "https://tidywells.com"
    pages = ["", "decline.html", "explore.html", "analysis.html", "glossary.html", "methods.html", "guide.html", "pro.html", "about.html", "data.html", "corrections.html", "terms.html"]
    urls = [(f"{base}/{pg}", None) for pg in pages] + [(f"{base}/posts/{p['slug']}.html", p["date"]) for p in posts]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u, d in urls:
        sm += f"<url><loc>{u}</loc>" + (f"<lastmod>{d}</lastmod>" if d else "") + "</url>\n"
    (ROOT / "docs" / "sitemap.xml").write_text(sm + "</urlset>\n", encoding="utf-8")
    (ROOT / "docs" / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n", encoding="utf-8")

    # open-data CSV, rebuilt from posts/monthly_agg.csv
    import csv
    src = ROOT / "posts" / "monthly_agg.csv"
    if src.exists():
        (ROOT / "docs" / "data").mkdir(exist_ok=True)
        with open(src, newline="") as fi, open(ROOT / "docs" / "data" / "tidywells-monthly-production.csv", "w", newline="") as fo:
            w = csv.writer(fo)
            w.writerow(["province", "product", "month", "volume", "unit", "wells_producing", "days_in_month"])
            for r in csv.DictReader(fi):
                w.writerow([r["province"], r["product"], r["month"], r["volume"], "m3" if r["product"] == "OIL" else "10^3 m3", r["wells"], r["days_in_month"]])
    # structured data (JSON-LD) so search engines understand posts and the site
    import re
    def ld_block(obj):
        return "<!--LD--><script type=\"application/ld+json\">" + json.dumps(obj) + "</script><!--/LD-->"
    def inject(path, block):
        t = path.read_text(encoding="utf-8")
        t = re.sub(r"<!--LD-->.*?<!--/LD-->", "", t, flags=re.S)
        path.write_text(t.replace("</head>", block + "</head>", 1), encoding="utf-8")
    pub = {"@type": "Organization", "name": "Tidywells", "url": "https://tidywells.com"}
    for p_ in posts:
        f = ROOT / "docs" / "posts" / f"{p_['slug']}.html"
        if f.exists():
            inject(f, ld_block({"@context": "https://schema.org", "@type": "Article", "headline": p_["title"], "description": p_["summary"], "datePublished": p_["date"], "dateModified": p_["date"], "author": pub, "publisher": pub, "mainEntityOfPage": f"https://tidywells.com/posts/{p_['slug']}.html"}))
    inject(ROOT / "docs" / "index.html", ld_block({"@context": "https://schema.org", "@type": "WebSite", "name": "Tidywells", "url": "https://tidywells.com/", "description": "Clean Canadian oil and gas regulator data, decline curves and plain-language analysis.", "publisher": pub}))

    # Medium call to action at the end of every post (before the comments), rebuilt on each run
    cta = ('<!--MEDCTA--><div class="promo blue"><div class="pt"><strong>Read it on Medium too, and follow along</strong>'
           '<span>We publish every analysis and monthly snapshot as a short article on Medium, with the key numbers up front. '
           'Follow Tidywells there to get each new one.</span></div>'
           '<a class="btn med" href="https://medium.com/@tidywells" target="_blank" rel="noopener">Follow on Medium</a></div><!--/MEDCTA-->')
    for p_ in posts:
        f = ROOT / "docs" / "posts" / f"{p_['slug']}.html"
        if not f.exists():
            continue
        t = re.sub(r"<!--MEDCTA-->.*?<!--/MEDCTA-->", "", f.read_text(encoding="utf-8"), flags=re.S)
        # comments box on analysis posts (generators do not emit its container)
        if p_.get("kind", "analysis") == "analysis" and 'id="comments"' not in t:
            t = t.replace("</article></main>", '<div id="comments"></div></article></main>', 1)
        if '<div id="comments">' in t:
            t = t.replace('<div id="comments">', cta + '<div id="comments">', 1)
        else:
            t = t.replace("</article></main>", cta + "</article></main>", 1)
        f.write_text(t, encoding="utf-8")

    # latest-data strip on the home page, from the monthly aggregate
    rows_ = list(csv.DictReader(open(ROOT / "posts" / "monthly_agg.csv")))
    conv_ = {"OIL": 6.2898 / 1000, "GAS": 35.3147 / 1000}
    ser_ = {}
    for r_ in rows_:
        ser_.setdefault((r_["province"], r_["product"]), {})[r_["month"]] = float(r_["volume"]) / float(r_["days_in_month"]) * conv_[r_["product"]]
    last_ = max(ser_[("AB", "OIL")])
    y_, m_ = int(last_[:4]), int(last_[5:])
    prev_ = f"{y_ - 1}-{m_:02d}"
    MON = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    def tile(label, key, unit):
        v = ser_[key][last_]
        g = (v / ser_[key][prev_] - 1) * 100
        cls = "up" if g >= 0 else "dn"
        return (f'<div><span>{label}</span><b>{v:,.0f} <small>{unit}</small></b>'
                f'<span class="{cls}">{"+" if g >= 0 else chr(8722)}{abs(g):.1f}% on a year earlier</span></div>')
    tiles_ = "".join([tile("Alberta oil", ("AB", "OIL"), "thousand bbl/d"), tile("Alberta gas", ("AB", "GAS"), "MMcf/d"),
                      tile("Saskatchewan oil", ("SK", "OIL"), "thousand bbl/d"), tile("BC gas", ("BC", "GAS"), "MMcf/d")])
    snap_slug = f"snapshot-{last_}"
    strip = (f'<!--LATEST--><section class="latest"><h2>Latest data: {MON[m_ - 1]} {y_}</h2><div class="lt">{tiles_}</div>'
             f'<p><a href="explore.html">Explore every month</a> · <a href="posts/{snap_slug}.html">Read the {MON[m_ - 1]} snapshot</a> · <a href="data.html">Download the data</a></p></section><!--/LATEST-->')
    ix = ROOT / "docs" / "index.html"
    t_ = re.sub(r"<!--LATEST-->.*?<!--/LATEST-->\n?", "", ix.read_text(encoding="utf-8"), flags=re.S)
    t_ = t_.replace("<main>\n", "<main>\n" + strip + "\n", 1)
    ix.write_text(t_, encoding="utf-8")
    # cite and share block at the end of every post
    for p_ in posts:
        f = ROOT / "docs" / "posts" / f"{p_['slug']}.html"
        if not f.exists():
            continue
        url = f"https://tidywells.com/posts/{p_['slug']}.html"
        yr = p_["date"][:4]
        tt_ = p_["title"]; sep_ = "" if tt_[-1] in ".?!" else "."
        cite = f"Tidywells ({yr}). {tt_}{sep_} {url}. Data: Petrinex and BC Energy Regulator public data."
        from urllib.parse import quote
        blk = ('<!--SHARE--><div class="share"><h3>Cite or share this</h3>'
               f'<p class="cite">{escape(cite)}</p><div class="sb">'
               f'<button data-copy="{escape(cite, {chr(34): "&quot;"})}">Copy citation</button>'
               f'<button data-copy="{url}">Copy link</button>'
               f'<a href="https://www.linkedin.com/sharing/share-offsite/?url={quote(url, safe="")}" target="_blank" rel="noopener">Share on LinkedIn</a>'
               f'<a href="https://twitter.com/intent/tweet?url={quote(url, safe="")}&text={quote(p_["title"], safe="")}" target="_blank" rel="noopener">Post on X</a></div>'
               '<script>document.querySelectorAll(".share [data-copy]").forEach(function(b){b.onclick=function(){var o=b.textContent,t=b.getAttribute("data-copy");'
               'var d=function(){b.textContent="Copied";setTimeout(function(){b.textContent=o},1400)};'
               'if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(d)}else{var x=document.createElement("textarea");x.value=t;document.body.appendChild(x);x.select();document.execCommand("copy");x.remove();d()}}});</script>'
               '</div><!--/SHARE-->')
        t_ = re.sub(r"<!--SHARE-->.*?<!--/SHARE-->", "", f.read_text(encoding="utf-8"), flags=re.S)
        if "<!--MEDCTA-->" in t_:
            t_ = t_.replace("<!--MEDCTA-->", blk + "<!--MEDCTA-->", 1)
        else:
            t_ = t_.replace("</article></main>", blk + "</article></main>", 1)
        f.write_text(t_, encoding="utf-8")
