---
name: analysis
description: "Guide Kalshi, Polymarket, and cross-venue analysis workflows for
  prediction-market-analysis."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# analysis

Use this sub-skill for anything that runs, interprets, or extends the repo's analysis classes.
It covers both the menu-driven CLI and the Python `Analysis` framework.

## Use this route when

- The user wants to run a named analysis or all analyses.
- The user wants calibration, return, volume, category, or statistical-study guidance.
- The user wants a new analysis class or a fix to an existing one.
- The user wants help understanding `Analysis`, `AnalysisOutput`, or `ChartConfig`.

## Scope

### Included

- Kalshi calibration and pricing analyses.
- Kalshi maker/taker, category, hour-of-day, and volume analyses.
- Kalshi meta statistics and paper-style statistical tests.
- Polymarket calibration, volume, and trade-time analyses.
- The cross-venue animated calibration comparison.
- `Analysis.save()` output formats and `ChartConfig` JSON export.

### Excluded

- Market/trade/block backfills and cursor recovery, which belong to `sub-skills/indexing/`.
- Dataset download, archive creation, and host-tool installation, which belong to `sub-skills/data-ops/`.

## Read first

- `../../references/analysis-catalog.md` for the full analysis list.
- `../../references/api-reference.md` for the `Analysis` and `ChartConfig` APIs.
- `../../references/data-layout.md` for the required Parquet inputs.
- `../../references/troubleshooting.md` for cross-cutting failures.

## Core workflow

1. Identify the analysis name from the catalog or from `scripts/catalog.py`.
2. Confirm the required input directories exist.
3. Run the analysis with `uv run main.py analyze <name>` or the equivalent wrapper.
4. Read the saved outputs under `output/<analysis-name>.*`.
5. If the analysis is missing, thin, or failing, inspect the relevant source module and the family-specific troubleshooting notes.

## Analysis families

### Kalshi calibration and pricing

Use these when the task is about price calibration, mispricing, or expected value:

- `win_rate_by_price`
- `mispricing_by_price`
- `win_rate_by_trade_size`
- `ev_yes_vs_no`

Typical inputs:
`data/kalshi/trades/`, `data/kalshi/markets/`.

### Kalshi time and volume

Use these when the task is about temporal trends or notional volume:

- `returns_by_hour`
- `vwap_by_hour`
- `volume_over_time`
- `longshot_volume_share_over_time`
- `kalshi_calibration_deviation_over_time`
- `maker_taker_gap_over_time`

Typical inputs:
`data/kalshi/trades/`, sometimes `data/kalshi/markets/`.

### Kalshi maker/taker and category studies

Use these when the task compares makers and takers, direction, or category grouping:

- `trade_size_by_role`
- `maker_returns_by_direction`
- `maker_win_rate_by_direction`
- `maker_vs_taker_returns`
- `maker_taker_returns_by_category`
- `market_types`
- `yes_vs_no_by_price`
- `meta_stats`
- `statistical_tests`

Typical inputs:
`data/kalshi/trades/`, `data/kalshi/markets/`, and `src.analysis.kalshi.util.categories`.

### Polymarket analyses

Use these when the task is about Polymarket calibration, volume, or block-level trade history:

- `polymarket_win_rate_by_price`
- `polymarket_calibration_by_bucket`
- `polymarket_volume_over_time`
- `polymarket_trades_over_time`

Typical inputs:
`data/polymarket/trades/`, `data/polymarket/legacy_trades/`, `data/polymarket/markets/`, `data/polymarket/blocks/`, and `data/polymarket/fpmm_collateral_lookup.json`.

### Cross-venue comparison

Use `win_rate_by_price_animated` when the user wants a single workflow that compares Kalshi and Polymarket in one animated calibration plot.

Typical inputs:
Both platforms' data directories plus `data/polymarket/blocks/` and the collateral lookup file.

## Adding or fixing an analysis

- Subclass `Analysis`.
- Set a stable `name` and a human-readable `description` in `__init__`.
- Keep data selection, transformations, figure creation, and chart serialization inside `run()` or helper methods.
- Return `AnalysisOutput`.
- Use `self.progress()` for longer SQL or dataframe steps.
- Prefer `ChartConfig` helpers when the analysis should also emit JSON chart output.
- Use the category helpers from `src.analysis.kalshi.util.categories` when grouping Kalshi markets.

## Common failure patterns

- Missing or empty `data/` subtrees.
- No finalized or resolved markets, leading to empty dataframes.
- Missing Polymarket helper files, especially the collateral lookup or block timestamps.
- `Analysis.load()` returning no classes because the command was run from the wrong directory.
- Matplotlib backend issues on headless hosts.

## Helpful helper

- `../../scripts/catalog.py` lists the analysis names without opening the interactive menu when run through the repo environment.
