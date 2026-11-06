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
    pages = ["", "decline.html", "explore.html", "analysis.html", "glossary.html", "methods.html", "guide.html", "pro.html", "about.html", "data.html", "clean.html", "scorecard.html", "revisions.html", "didnt-work.html", "corrections.html", "terms.html", "shop.html", "your-well.html"]
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
    cta = ('<!--MEDCTA--><div class="promo blue"><div class="pt"><strong>Get every new analysis by email or on Medium</strong>'
           '<span>We publish each analysis and monthly snapshot as a short article on Substack and Medium, with the key numbers up front. '
           'Follow Tidywells on either to get each new one.</span></div>'
           '<div class="btns"><a class="btn sub" href="https://tidywells.substack.com/" target="_blank" rel="noopener">Subscribe on Substack</a>'
           '<a class="btn med" href="https://medium.com/@tidywells" target="_blank" rel="noopener">Follow on Medium</a></div></div><!--/MEDCTA-->')
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
    # reproduce-this-number block on monthly snapshots (placed before the share box)
    for p_ in posts:
        f = ROOT / "docs" / "posts" / f"{p_['slug']}.html"
        if p_.get("kind") != "snapshot" or not f.exists():
            continue
        mon = p_["period"]
        code = ('import csv, io, urllib.request\n'
                'url = "https://tidywells.com/data/tidywells-monthly-production.csv"\n'
                'conv = {"OIL": 6.2898 / 1000, "GAS": 35.3147 / 1000}   # m3 -> thousand bbl, 10^3 m3 -> MMcf\n'
                'for r in csv.DictReader(io.StringIO(urllib.request.urlopen(url).read().decode())):\n'
                f'    if r["month"] == "{mon}":\n'
                '        rate = float(r["volume"]) / float(r["days_in_month"]) * conv[r["product"]]   # per day\n'
                '        print(r["province"], r["product"], f"{rate:,.0f}" if (r["product"] == "GAS" or rate >= 100) else f"{rate:,.1f}")\n')
        blk = ('<!--REPRO--><details class="repro"><summary>Reproduce these numbers</summary>'
               '<p>Every figure above comes from the <a href="../data.html">open dataset</a> (province-level monthly totals built from the regulators’ public files). '
               'Divide the month’s volume by the days in the month, then convert units. This short Python script prints the same daily rates shown in the table; it needs no libraries.</p>'
               f'<pre><code>{escape(code)}</code></pre>'
               '<p>The same checks run automatically on every change, see <a href="../data.html">How we check this</a>. '
               'To go back to the raw regulator files, use the <a href="../clean.html">file cleaner</a> or the <a href="https://github.com/Jay-Kimani/TidyWells">Python package</a>.</p></details><!--/REPRO-->')
        t_ = re.sub(r"<!--REPRO-->.*?<!--/REPRO-->", "", f.read_text(encoding="utf-8"), flags=re.S)
        t_ = t_.replace("</article></main>", blk + "</article></main>", 1) if "<!--SHARE-->" not in t_ else t_.replace("<!--SHARE-->", blk + "<!--SHARE-->", 1)
        f.write_text(t_, encoding="utf-8")
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

    # grouped site navigation, rebuilt on every page (header block is replaced wholesale)
    NAV = [
        ("link", "Home", "index.html", None),
        ("menu", "Tools", "tools", [
            ("decline.html", "Decline curve", "Fit a curve to one well"),
            ("explore.html", "Production explorer", "Charts for AB, SK and BC"),
            ("clean.html", "File cleaner", "Clean a regulator file in your browser")]),
        ("menu", "Research", "research", [
            ("analysis.html", "Analysis", "Studies and monthly snapshots"),
            ("data.html", "Open data", "Download the data and see the checks"),
            ("scorecard.html", "Forecast scorecard", "Our forecasts, graded against what happened"),
            ("revisions.html", "Data revisions", "What the regulators changed after publishing"),
            ("didnt-work.html", "What didn't work", "Negative results and mistakes we found")]),
        ("menu", "Learn", "learn", [
            ("methods.html", "Methods", "Sources, rules and limits"),
            ("guide.html", "Data guide", "How the regulator files work"),
            ("glossary.html", "Glossary", "Oil and gas terms in plain words")]),
        ("link", "Shop", "shop.html", "shopbtn"),
        ("menu", "About", "about", [
            ("about.html", "About Tidywells", "Who builds it and why"),
            ("about.html#how-this-is-made", "How this is made", "Where AI is used, and how it is checked"),
            ("corrections.html", "Corrections", "Mistakes we found and fixed"),
            ("terms.html", "Terms and privacy", "Disclaimer and data use")]),
    ]
    GROUP_OF = {"index.html": "index.html", "decline.html": "tools", "explore.html": "tools", "clean.html": "tools", "scorecard.html": "research", "revisions.html": "research", "didnt-work.html": "research", "analysis.html": "research",
                "data.html": "research", "methods.html": "learn", "guide.html": "learn", "glossary.html": "learn",
                "about.html": "about", "corrections.html": "about", "terms.html": "about",
                "sponsor.html": "about", "shop.html": "shop.html", "your-well.html": "shop.html"}
    def nav_html(prefix, cur):
        grp = GROUP_OF.get(cur)
        out = [f'<div class="util"><div><a href="{prefix}data.html">Open data</a><a href="{prefix}pro.html">Pro data pack</a><a href="{prefix}corrections.html">Corrections</a>'
               f'<a href="https://github.com/Jay-Kimani/TidyWells" target="_blank" rel="noopener">GitHub</a>'
               f'<a href="https://tidywells.substack.com/" target="_blank" rel="noopener">Substack</a></div></div>'
               f'<header><nav><a class="brand" href="{prefix}index.html" aria-label="Tidywells home">'
               f'<img class="logo-l" src="{prefix}img/logo.png" alt="Tidywells" height="44">'
               f'<img class="logo-d" src="{prefix}img/logo-dark.png" alt="" height="44"></a>']
        for kind, label, key, extra in NAV:
            if kind == "link":
                cls = " ".join(c for c in [extra, "on" if grp == key else ""] if c)
                out.append('<a' + (' class="%s"' % cls if cls else '') + f' href="{prefix}{key}">{label}</a>')
            else:
                ON = ' class="on"'
                items = "".join(
                    f'<a{ON if href == cur else ""} href="{prefix}{href}"><b>{t}</b><small>{d}</small></a>'
                    for href, t, d in extra)
                out.append(f'<details class="dd{" on" if grp == key else ""}"><summary>{label}</summary><div class="menu">{items}</div></details>')
        out.append('<button id="theme">Theme</button></nav></header>')
        return "".join(out)
    docs_ = ROOT / "docs"
    for f in sorted(docs_.glob("*.html")) + sorted((docs_ / "posts").glob("*.html")):
        t = f.read_text(encoding="utf-8")
        if f.parent.name == "posts":
            prefix, cur = "../", "analysis.html"
        else:
            prefix, cur = ("/" if f.name == "404.html" else ""), f.name
        t2 = re.sub(r'(?:<div class="util">.*?</div></div>)?<header><nav>.*?</nav></header>', lambda m: nav_html(prefix, cur), t, count=1, flags=re.S)
        t2 = re.sub(r"<!--PROMO-->.*?<!--/PROMO-->\n?", "", t2, flags=re.S)
        t2 = t2.replace('r.dataset.theme==="light"?"dark":"light"', 'r.dataset.theme==="dark"?"light":"dark"')
        if t2 != t:
            f.write_text(t2, encoding="utf-8")

    # Substack alongside Medium: home/analysis promo, About buttons, footer link on every page
    SUB = "https://tidywells.substack.com/"
    promo = ('<!--MEDIUM--><div class="promo blue"><div class="pt"><strong>New: our monthly analysis articles are on Substack and Medium</strong>'
             '<span>Plain-language write-ups of every monthly snapshot and analysis, with the key numbers up front. Subscribe on Substack for email, or follow on Medium.</span></div>'
             f'<div class="btns"><a class="btn sub" href="{SUB}" target="_blank" rel="noopener">Subscribe on Substack</a>'
             '<a class="btn med" href="https://medium.com/@tidywells" target="_blank" rel="noopener">Read on Medium</a></div></div><!--/MEDIUM-->')
    follow = ('<!--FOLLOW--><h2>Follow Tidywells</h2><p>Updates, new analyses and the code are in these places.</p>'
              '<p style="display:flex;flex-wrap:wrap;gap:10px"><a class="btn med" href="https://www.linkedin.com/company/tidywells" target="_blank" rel="noopener">Follow on LinkedIn</a>'
              '<a class="btn med" href="https://github.com/Jay-Kimani/TidyWells" target="_blank" rel="noopener">View the code on GitHub</a>'
              '<a class="btn med" href="https://medium.com/@tidywells" target="_blank" rel="noopener">Read on Medium</a>'
              f'<a class="btn sub" href="{SUB}" target="_blank" rel="noopener">Subscribe on Substack</a></p><!--/FOLLOW-->')
    med_a = '<a href="https://medium.com/@tidywells" target="_blank" rel="noopener">Medium</a>'
    sub_a = f'<a href="{SUB}" target="_blank" rel="noopener">Substack</a>'
    for f in sorted(docs_.glob("*.html")) + sorted((docs_ / "posts").glob("*.html")):
        t = f.read_text(encoding="utf-8"); t0 = t
        t = re.sub(r"<!--MEDIUM-->.*?<!--/MEDIUM-->", lambda m: promo, t, flags=re.S)
        t = re.sub(r"<!--FOLLOW-->.*?<!--/FOLLOW-->", lambda m: follow, t, flags=re.S)
        if sub_a not in t:
            t = t.replace(med_a, med_a + " · " + sub_a)
        pref = "../" if f.parent.name == "posts" else ("/" if f.name == "404.html" else "")
        # secondary Pro mention: a slim strip at the end of the main content, plus a footer link
        if f.name not in ("pro.html", "404.html", "sponsor.html", "shop.html", "your-well.html"):
            strip = (f'<!--PRO--><p class="pro-strip"><b>Tidywells Pro</b> &middot; tidy monthly data packs as CSV files, CAD $4.99 a month with a 3-day free trial. '
                     f'<a href="{pref}pro.html">Learn more</a></p><!--/PRO-->')
            t = re.sub(r"<!--PRO-->.*?<!--/PRO-->", lambda m: strip, t, flags=re.S) if "<!--PRO-->" in t else t.replace("</main>", "</main>\n" + strip, 1)
        if "<footer" in t and 'pro.html">Pro' not in t.rsplit("<footer", 1)[1]:
            head_, foot_ = t.rsplit("<footer", 1)
            t = head_ + "<footer" + foot_.replace(">Shop</a>", f'>Shop</a> · <a href="{pref}pro.html">Pro data pack</a>', 1)
        if "<footer" in t and f'>Shop</a>' not in t.rsplit("<footer", 1)[1]:
            head_, foot_ = t.rsplit("<footer", 1)
            t = head_ + "<footer" + foot_.replace(sub_a, sub_a + f' · <a href="{pref}shop.html">Shop</a>', 1)
        if t != t0:
            f.write_text(t, encoding="utf-8")
