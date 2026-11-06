"""Writes docs/didnt-work.html. Edit the ENTRIES below when something new fails; each must be true and link to evidence."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pagetpl import page, hero, stats as stats_strip, bubble, layout  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ENTRIES = [
    ("4 November 2026", "We got a headline wrong",
     "Our new-wells-by-vintage post said Alberta gas wells were starting 19% stronger. That was an artefact of how we sorted wells into oil and gas: the rule put many oil wells that also produce gas into the gas group. We replaced it with a rule based on which product is at least half of a well's output, reran the study and rewrote the post.",
     [("Corrected post", "posts/new-wells-by-vintage.html"), ("Corrections log", "corrections.html")]),
    ("3 to 4 November 2026", "Our first explanation for low forecasts only went part of the way",
     "Our decline-curve backtest on about 1,900 wells found that the fitted curve runs low. We then checked whether wells that recover after the training window explain it: about 35 to 50% of wells do recover, and a low month just before the forecast multiplies the typical miss by two to five. That does not account for all of the gap, and we have not found the rest.",
     [("The backtest", "posts/decline-backtest.html"), ("The recovery study", "posts/recovery-low-forecasts.html")]),
    ("4 November 2026", "Our seasonal forecast does not beat repeating last month",
     "We built a forecast that takes the same month last year and scales it by recent year-on-year growth. In the first backtest of the scorecard it was beaten, on average across the six series, by simply repeating last month: roughly 4.7% mean error against 5.1%. Our method won on some series and horizons, not overall. We publish it anyway, and the live log will show whether that holds on data we have not seen yet.",
     [("Forecast scorecard", "scorecard.html")]),
]


TAGS = ["Wrong headline", "Partial explanation", "Lost to baseline"]


def build():
    cards = "".join(
        f'<div class="ecard"><div class="meta"><span class="pill {"bad" if k == 0 else ""}">{TAGS[k]}</span><span>{d}</span></div><h2>{t}</h2><p>{body}</p>'
        '<div class="lk">' + " ".join(f'<a href="{u}">{n} &rarr;</a>' for n, u in links) + "</div></div>"
        for k, (d, t, body, links) in enumerate(ENTRIES))
    side = (bubble("How to read this page", "<p>Each entry says what we expected, what happened and where the evidence is. Newest first.</p>") +
            bubble("Spotted something?", '<p>If a mistake is missing here, <a href="https://github.com/Jay-Kimani/TidyWells/issues">tell us</a>. Fixed errors are also listed on <a href="corrections.html">Corrections</a>.</p>'))
    h = [hero("Research · Negative results", "What didn't work",
              "Most sites show only the analyses that worked. This page lists the ones that did not: the mistakes we made and the methods that lost."),
         stats_strip([(str(len(ENTRIES)), "entries so far"), (ENTRIES[0][0].split(" to ")[-1], "most recent entry")]),
         layout(cards, side),
         '<p class="muted" style="margin-top:28px;font-size:14px">Informational only, not investment, legal or engineering advice. Entries are written by hand in <code>posts/gen_didnt_work.py</code>.</p>']
    return "\n".join(h)


if __name__ == "__main__":
    (ROOT / "docs" / "didnt-work.html").write_text(
        page("didnt-work.html", "What didn't work", "Mistakes we made and methods that lost, with links to the evidence: corrected headlines, partial explanations and forecasts that did not beat the baseline.",
             build(), cls="rp"), encoding="utf-8")
