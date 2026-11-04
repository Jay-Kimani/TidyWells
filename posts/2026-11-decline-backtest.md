# How well does a simple decline curve forecast Canadian wells?

*Tidywells, November 2026*

We took public production data from Alberta, Saskatchewan and British Columbia and tested the most common decline curve (Arps, with a bounded b-factor) the hard way: fit it on the first 45 months of a well's life, predict the next 12, and compare to what was reported.

## What we did

- **Data:** monthly well-level production, January 2022 to September 2026 (57 months). Alberta and Saskatchewan from Petrinex public data; BC from the BC Energy Regulator production file.
- **Wells:** up to 500 randomly chosen wells per group, restricted to wells that produced in at least 50 of the 57 months. Alberta and Saskatchewan oil and Saskatchewan gas use calendar-month averages; BC gas uses producing days.
- **Fit:** Arps decline fitted by least squares on log rate, starting at each well's peak month, b limited to 0 to 2.
- **Test:** forecast the cumulative volume over months 46 to 57 and compare to the reported volume.

## Results

| Group | Wells tested | Typical miss | Within ±25% | Within ±50% | Average bias |
|---|---|---|---|---|---|
| Alberta oil | 460 | 17% | 65% | 89% | −10% |
| Saskatchewan oil | 469 | 17% | 66% | 90% | −9% |
| Saskatchewan gas | 471 | 16% | 65% | 85% | −12% |
| BC gas | 483 | 13% | 75% | 92% | −8% |

"Typical miss" is the median absolute error of the 12-month cumulative volume. Negative bias means the forecast was a bit low on average.

## What stands out

1. **A simple curve is decent at one-year screening.** About two thirds of wells landed within a quarter of the actual volume, and almost 90% within half. That is useful for a quick look, not for reserves.
2. **The curve is consistently a little pessimistic.** All four groups under-forecast, by 8 to 12% on average. A likely reason is wells that were shut in, then restarted or re-completed, but we have not tested that.
3. **b is not well determined.** In every group the median fitted b sat at the upper limit of 2, and 83 to 90% of fits carried a warning (b at its bound, or many b values fitting about equally well). Treat any single well's b with suspicion.
4. **Warnings are not a quality score.** In a quick check on Alberta oil, the small group of fits with no warnings was not more accurate.

## Limits

- The test only includes wells that kept producing across nearly all 57 months. Wells that shut in or stopped are excluded, so real accuracy across all wells would be worse.
- Forecasts here have no terminal-decline switch and no economics.
- One sample per group, one time window, not compared against any industry forecast.
- Some volumes may be allocated rather than metered; we did not separate them.

Illustrative only. Not for reserves reporting or investment decisions.

## Reproduce it

Code: [github.com/Jay-Kimani/TidyWells](https://github.com/Jay-Kimani/TidyWells), `posts/backtest.py` and `src/tidywells/decline.py`. Download the files yourself from Petrinex and the BC Energy Regulator; we do not host the data.

*Contains information licensed from Petrinex public data (Alberta, Saskatchewan) and the BC Energy Regulator; Crown copyright of the provinces is acknowledged. Tidywells is not affiliated with any regulator.*
