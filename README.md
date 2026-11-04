# Tidywells

Clean Canadian oil and gas regulator files into one layout and run simple decline curves. You use your own downloaded files; they stay on your machine.

Site, analysis and browser decline-curve tool: <https://jay-kimani.github.io/TidyWells/>

**Not affiliated with any regulator.** Outputs are illustrative only, not for reserves reporting or investment decisions.

## What it does
- **Loaders** for Petrinex public data (Alberta, Saskatchewan: Well Licence, Well Infrastructure, Conventional Volumetrics) and BC Energy Regulator files (`zone_prd*.csv`, `well_index.csv`). IDs stay as text so leading zeros survive; duplicates are resolved; masked (confidential) rows are dropped.
- **Decline curves:** bounded Arps hyperbolic fit (`fit_arps`), forecast with a terminal exponential switch (`forecast`), and a simple NPV (`npv`).
- **Analysis scripts** in `posts/` that reproduce the numbers in the write-ups.

## Install
Not on PyPI yet. From a clone of this repository:

```bash
pip install .
```

## Quick start
```python
import tidywells as tw

vol = tw.read_volumetrics("path/to/folder", province="AB")      # Vol_YYYY-MM-AB.csv.zip files
wells = tw.join_wells(vol,
        tw.read_well_infrastructure("Well Infrastructure-AB.csv.zip"),
        tw.read_well_licence("Well Licence-AB.csv.zip"))

well_id = vol["well_id"].iloc[0]
s = tw.monthly_series(vol, well_id, "OIL")                      # m3 per day, one value per month
t = [i / 12 for i in range(len(s))]                             # years
fit = tw.fit_arps(t, s.values * tw.loaders.M3_TO_BBL)           # qi, di, b, warnings
f = tw.forecast(fit['qi'], fit['di'], fit['b'], years=10)       # dict: t, rate, volume
print(fit, tw.npv(f['volume'], f['t'], price=70.0, opex_per_unit=20.0))
```
See `examples/quickstart.ipynb` for a longer walk-through.

## Data
This project does not host or redistribute any regulator data. Download the files yourself:
- Petrinex public data: <https://www.petrinex.ca/PD/Pages/default.aspx>
- BC Energy Regulator data centre: <https://www.bc-er.ca/data-reports/data-centre/>

Check each source's terms before reuse. Petrinex permits non-commercial use with Crown copyright acknowledged. Nothing here is legal advice.

## Reproduce the analysis
```bash
python posts/backtest.py ab FOLDER extra     # first post; also sk, bc
python posts/recovery.py ab FOLDER           # recovery post
python posts/monthly_agg.py ab FOLDER        # monthly totals for snapshots and seasonality
python posts/cache_matrix.py ab FOLDER      # well x month cache (also sk, bc), then:
python posts/wells_study.py ab FOLDER       # inventory, shut-ins, vintage, licensees, GOR
python posts/dq_study.py ab FOLDER          # data-quality counts
python posts/gen_posts2.py && python posts/build_feed.py
```

## Layout
- `src/tidywells/` package (decline math, loaders)
- `tests/` tests on synthetic data only
- `docs/` static site (GitHub Pages)
- `posts/` write-ups and the scripts behind them

## Publishing routine
About every two weeks: a monthly snapshot once new regulator files are out, with an analysis post in between. Add the new month's files, rerun `monthly_agg.py`, `gen_posts.py`, `build_feed.py`, then push.

## Releasing to PyPI (maintainer)
```bash
python -m pip install build twine
python -m build
python -m twine upload dist/*     # needs a PyPI account and API token
```

## Licence
MIT. See `LICENSE`.
