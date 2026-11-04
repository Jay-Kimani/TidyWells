# How well does a simple decline curve forecast Canadian wells?

*Tidywells, November 2026*

We took public production data from Alberta, Saskatchewan and British Columbia and tested the most common decline curve (Arps, with a bounded b-factor) the hard way: fit it on a well's early months, predict the next 12 months, and compare to what was reported. Then we asked three follow-up questions: does the extra b-factor help, how much history do you need, and why does the curve run low?

## What we did

- **Data:** monthly well-level production, January 2022 to September 2026 (57 months). Alberta and Saskatchewan from Petrinex public data; BC from the BC Energy Regulator production file.
- **Wells:** up to 500 randomly chosen wells per group, restricted to wells that produced in at least 50 of the 57 months. Alberta and Saskatchewan use calendar-month averages; BC gas uses producing days.
- **Fit:** Arps decline fitted by least squares on log rate, starting at each well's peak month, b limited to 0 to 2.
- **Test:** forecast the cumulative volume over months 46 to 57 and compare to the reported volume. The main test trains on the first 45 months.

## 1. The headline result

| Group | Wells tested | Typical miss | Within ±25% | Within ±50% | Average bias |
|---|---|---|---|---|---|
| Alberta oil | 460 | 17% | 65% | 89% | −10% |
| Saskatchewan oil | 469 | 17% | 66% | 90% | −9% |
| Saskatchewan gas | 471 | 16% | 65% | 85% | −12% |
| BC gas | 483 | 13% | 75% | 92% | −8% |

*"Typical miss" is the median absolute error of the 12-month cumulative volume. Negative bias means the forecast was a bit low on average.*

About two thirds of wells landed within a quarter of the actual volume, and almost 90% within half. BC gas did best and Saskatchewan gas worst, but the groups are close. That is useful for a quick look, not for reserves.

## 2. Does the b-factor earn its keep?

The hyperbolic curve has an extra parameter (b) that lets the decline slow down over time. We compared it with a plain exponential curve (b fixed at 0) on the same wells.

| Group | Hyperbolic (b up to 2): typical miss | Exponential only: typical miss | Hyperbolic within ±25% | Exponential within ±25% |
|---|---|---|---|---|
| Alberta oil | 17% | 18% | 65% | 61% |
| Saskatchewan oil | 17% | 21% | 66% | 59% |
| Saskatchewan gas | 16% | 18% | 65% | 62% |
| BC gas | 13% | 16% | 75% | 68% |

The hyperbolic curve was better in every group, but not by a lot: one to four points on the typical miss. The bigger point is that b itself is not well determined. In every group the median fitted b sat at the upper limit of 2, and 83 to 90% of fits carried a warning (b at its bound, or many b values fitting about equally well). So the benefit comes from letting the curve flatten, not from any single well's b, and we would not read meaning into one well's b.

## 3. How much history do you need?

We refit each well on shorter training windows and predicted the same last 12 months.

| Group | 24 months of history | 36 months | 45 months |
|---|---|---|---|
| Alberta oil | 36% | 23% | 17% |
| Saskatchewan oil | 34% | 24% | 17% |
| Saskatchewan gas | 29% | 21% | 16% |
| BC gas | 24% | 19% | 13% |

This was the largest effect we measured. Going from 24 to 45 months of history roughly halved the typical miss. With two years of data the curve missed by 24 to 36% on a typical well, and fewer than half the wells landed within 25% in three of four groups. A forecast on a young well deserves much wider error bars than one on a well with four years behind it. Note that shorter windows also need the well to have a clear peak and decline within them, and some wells could not be fitted at all, so the tested counts are a little lower at 24 months.

## 4. Why does the curve run low?

Every group under-forecast on average, by 8 to 12%. A natural suspicion is wells whose rate recovers after the training window: a restart after a shut-in, a workover, a new completion, a pressure change, or seasonal operations. We cannot see the reasons in this data, but we can see whether the rate went back up. We flagged a well as "recovered" if its average rate in the 12 test months was higher than its average over the last three training months.

| Group | Share of wells whose rate recovered | Median error: recovered | Median error: kept declining |
|---|---|---|---|
| Alberta oil | 41% | −24% | 0% |
| Saskatchewan oil | 35% | −25% | −2% |
| Saskatchewan gas | 50% | −17% | 0% |
| BC gas | 39% | −21% | −2% |

Between 35 and 50% of wells recovered, and nearly all of the bias sits in that group, where the forecast ran 17 to 25% low on a typical well. Wells that simply kept declining had almost no bias (0 to −2%). In other words, the curve forecasts a declining well about right, and the miss comes from wells that do something a decline curve cannot know about. This is a description, not a proof: a rate increase is not always a restart, and this split uses information that was not available at forecast time.

## What this means in practice

- For a quick one-year volume on a well with about four years of history, a bounded hyperbolic fit is a reasonable screening number, wrong by under a fifth for a typical well.
- Treat young wells (two years or less) as about twice as uncertain.
- Do not trust a single well's b-factor. If you compare wells or portfolios, compare forecast volumes, not b.
- A forecast that ignores possible rate recoveries will tend to run low on a large share of wells. Any portfolio view should carry an allowance for that, or an explicit upside case.

## Limits

- The test only includes wells that kept producing across nearly all 57 months. Wells that shut in or stopped are excluded, so real accuracy across all wells would be worse.
- Forecasts here have no terminal-decline switch and no economics.
- One random sample of up to 500 wells per group, one time window, and no comparison against any industry forecast.
- Some volumes may be allocated rather than metered; we did not separate them.
- In a quick check on Alberta oil, the small group of fits with no warnings was not more accurate, so warnings flag uncertainty and are not a quality score.

## Reproduce it

Code: [github.com/Jay-Kimani/TidyWells](https://github.com/Jay-Kimani/TidyWells), `posts/backtest.py` (run it with `extra` for sections 2 to 4) and `src/tidywells/decline.py`. Download the files yourself from Petrinex and the BC Energy Regulator; we do not host the data.

Illustrative only. Not for reserves reporting or investment decisions.

*Contains information licensed from Petrinex public data (Alberta, Saskatchewan) and the BC Energy Regulator; Crown copyright of the provinces is acknowledged. Tidywells is not affiliated with any regulator.*
