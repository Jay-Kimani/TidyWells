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
SITE = "https://jay-kimani.github.io/TidyWells/"


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
    posts = sorted(json.loads((ROOT / "posts" / "posts.json").read_text()), key=lambda p: (p["date"], p.get("period", "")), reverse=True)
    analysis = [p for p in posts if p.get("kind", "analysis") == "analysis"]
    snaps = [p for p in posts if p.get("kind") == "snapshot"]
    (ROOT / "docs" / "feed.xml").write_text(build(posts[:40]), encoding="utf-8")
    patch(ROOT / "docs" / "index.html", card(analysis[0]))
    a = ROOT / "docs" / "analysis.html"
    patch(a, "".join(card(p) for p in analysis))
    t = a.read_text(encoding="utf-8")
    i, j = t.index("<!--SNAPS-->") + 12, t.index("<!--/SNAPS-->")
    a.write_text(t[:i] + "\n" + snaps_html(snaps) + "\n" + t[j:], encoding="utf-8")
