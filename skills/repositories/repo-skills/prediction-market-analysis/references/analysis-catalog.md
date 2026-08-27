# Analysis Catalog

This repo exposes 24 analysis classes discoverable through `src.common.analysis.Analysis.load()`.
Use this catalog when deciding which analysis to run or when adding a new one.

## Kalshi analyses

### Calibration and price

- `win_rate_by_price` — calibration scatter and chart for taker/maker positions by price.
- `mispricing_by_price` — compares taker, maker, and combined mispricing at each price.
- `win_rate_by_trade_size` — price-adjusted win rate by trade-size bucket.
- `ev_yes_vs_no` — expected value of YES vs NO at each price level.

### Time and volume

- `returns_by_hour` — excess return by hour of day.
- `vwap_by_hour` — VWAP by hour of day.
- `volume_over_time` — quarterly notional volume.
- `longshot_volume_share_over_time` — quarterly taker share in longshot buckets.
- `kalshi_calibration_deviation_over_time` — rolling calibration deviation over time.
- `maker_taker_gap_over_time` — quarterly maker vs taker excess-return gap.

### Direction, role, and category

- `trade_size_by_role` — maker vs taker trade-size distribution.
- `maker_returns_by_direction` — maker excess returns when buying YES vs NO.
- `maker_win_rate_by_direction` — maker win rates when buying YES vs NO.
- `maker_vs_taker_returns` — maker vs taker excess returns by price.
- `maker_taker_returns_by_category` — maker vs taker excess returns by market category.
- `market_types` — category/group treemap of market volume.
- `yes_vs_no_by_price` — YES vs NO share of volume by price.
- `meta_stats` — dataset counts and summary statistics.
- `statistical_tests` — paper-style hypothesis tests over size, asymmetry, category, and direction.

## Polymarket analyses

- `polymarket_win_rate_by_price` — calibration scatter for CTF and legacy trades.
- `polymarket_calibration_by_bucket` — decile calibration bars and metrics.
- `polymarket_volume_over_time` — quarterly notional volume using CTF plus USDC legacy trades.
- `polymarket_trades_over_time` — block-level trade counts over time.

## Cross-venue comparison

- `win_rate_by_price_animated` — animated side-by-side Kalshi vs Polymarket calibration.

## What these analyses share

- Most analyses read Parquet data from `data/kalshi/...` or `data/polymarket/...`.
- Most return an `AnalysisOutput` with a figure, a dataframe, and sometimes a chart config.
- `Analysis.save()` writes the outputs to `output/<analysis-name>.*`.
- The `chart` field is JSON-serializable through `ChartConfig.to_json()`.

## Common inputs by family

| Family | Required inputs | Typical output |
| --- | --- | --- |
| Kalshi calibration/price | trades + markets | scatter or line chart plus CSV |
| Kalshi time/volume | trades, sometimes markets | line or bar chart plus CSV |
| Kalshi category/role | trades + markets, sometimes category helpers | bars, treemaps, or tables |
| Polymarket | trades, legacy trades, markets, sometimes blocks and collateral lookup | calibration or volume chart plus CSV/JSON |
| Comparison | both Kalshi and Polymarket datasets plus blocks | animated GIF plus CSV |

## Edge-case notes

- `meta_stats` and `statistical_tests` are data-first analyses and may return no figure.
- `win_rate_by_price_animated` requires the broadest input set and is the first place to check for missing blocks or missing collateral lookup data.
- Category-aware Kalshi analyses depend on `src.analysis.kalshi.util.categories`.
- Some analyses skip malformed rows or unresolved markets rather than failing hard.
