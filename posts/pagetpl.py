"""Shared page shell for generated pages (same head, nav placeholder and footer as the rest of the site).
build_feed.py fills the navigation on every page, so the shell leaves it empty."""
from html import escape

HEAD = '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">\n<title>{title} · Tidywells</title><meta name="description" content="{desc}"><link rel="stylesheet" href="style.css"><link rel="alternate" type="application/rss+xml" title="Tidywells" href="feed.xml"><style>article{max-width:720px}main a,footer a{color:var(--accent)}table{border-collapse:collapse;width:100%;font-size:14px}th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}.tw{overflow-x:auto}code{font-size:13px}</style><link rel="canonical" href="https://tidywells.com/{page}"><link rel="icon" type="image/png" href="img/favicon.png"><meta property="og:image" content="https://tidywells.com/img/og.png"><meta property="og:site_name" content="Tidywells"><meta name="twitter:card" content="summary_large_image"><style>{css}</style></head>\n'
FOOT = '<footer><div id="subscribe"></div><small>Not affiliated with any regulator. Provided as is, no warranty. <a href="feed.xml">RSS</a> · <a href="https://medium.com/@tidywells" target="_blank" rel="noopener">Medium</a> · <a href="https://tidywells.substack.com/" target="_blank" rel="noopener">Substack</a> · <a href="terms.html">Terms and privacy</a> · <a href="shop.html">Shop</a> · <a href="sponsor.html">Sponsor</a> · <a href="data.html">Open data</a> · <a href="glossary.html">Glossary</a> · <a href="corrections.html">Corrections</a> · <a href="https://github.com/Jay-Kimani/TidyWells">Code</a></small></footer>\n<script src="config.js"></script><script src="subscribe.js"></script><script src="site.js"></script>\n<script>document.getElementById("theme").onclick=()=>{const r=document.documentElement;r.dataset.theme=r.dataset.theme==="light"?"dark":"light"}</script>\n</body></html>\n'


def page(name, title, desc, body, css=""):
    head = (HEAD.replace("{title}", escape(title)).replace("{desc}", escape(desc, quote=True))
            .replace("{css}", css).replace("{page}", name))
    return head + "<body>\n<header><nav></nav></header>\n<main><article>\n" + body + "\n</article></main>\n\n" + FOOT
