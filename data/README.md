# Data folder (15 funds, all verified 25-Sep-2026)

Subfolder per fund inside `data/`:

```
data/
  README.md
  tata-<slug>-direct-growth/  x15
    nav_daily.csv        # full daily history, ISO dates, sorted, deduped
    yearly_returns.csv   # year-end NAV + annual_return_pct + observations
    metadata.json        # fund facts + download stats + sources
    summary.txt          # human-readable factsheet
    holdings.csv         # top holdings 31-Aug-2026 (or note if not disclosed)
    factsheet_snapshot.json  # AUM/YTM/duration/expense/returns snapshot
    peers.csv            # only money_market + gilt (Tata pages show no category-peer table for others)
  combined/
    comparison_summary.csv  # 15-row side-by-side stats
    download_manifest.json
```

Notes:
- Tata site "Fund Age" = Regular plan age. Direct-Growth files cover FULL Direct history
  (earliest dates: money 2013-01-01, gilt 2013-01-07, short/value/large_mid 2013-01-02,
  retirement 2013-01-04, consumer/banking/resources 2015-12-29, flexi 2018-09-10,
  ultra_short 2019-01-23, focused 2019-12-06, dividend 2021-05-27, business 2021-08-11,
  housing 2022-09-09; all end 2026-09-25).
- Old dividend code 119234 ended 01-Jun-2018; current Dividend Yield Direct-Growth is 148947.
- Re-runs refresh only the 4 core files; holdings/factsheet/peers are preserved.
