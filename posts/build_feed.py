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
    pages = ["", "decline.html", "analysis.html", "methods.html", "guide.html", "pro.html", "about.html", "data.html", "corrections.html", "terms.html"]
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
