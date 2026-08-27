---
name: prediction-market-analysis
description: "Route analysis, indexing, and data-ops guidance for the
  prediction-market-analysis repo."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# prediction-market-analysis

This skill covers the repo that analyzes and collects Kalshi and Polymarket market data.
The repo is centered on three user-facing workflows:

- `analyze` for calibration, returns, volume, category, and comparison studies.
- `index` for Kalshi and Polymarket market/trade/block backfills.
- `setup` / `package` for dataset download, archive management, and local data packaging.

## Environment

- Preferred setup: `uv sync --frozen --group dev` from the repo root.
- Minimal import smoke: `uv run python -c "import src; print(src.__file__)"`.
- The bundled helper scripts assume the repo runtime dependencies are available.

## First stop

- Read `references/cli-reference.md` for command names and command-line behavior.
- Read `references/data-layout.md` for directory layout, parquet inputs, and env vars.
- Read `references/api-reference.md` for the public Python classes and helper functions.
- Read `references/troubleshooting.md` when a workflow fails, returns empty data, or cannot find files.

## When to use each sub-skill

### `sub-skills/analysis/`
Use when the task is about:

- Running or interpreting an existing analysis.
- Comparing Kalshi vs Polymarket calibration, returns, or volume.
- Understanding `Analysis`, `AnalysisOutput`, `ChartConfig`, or `Analysis.load()` behavior.
- Adding a new analysis class under `src/analysis/`.

Typical signals:
`win_rate_by_price`, `mispricing`, `maker_taker`, `volume_over_time`, `meta_stats`, `polymarket`, `calibration`, `chart`, `output/`.

### `sub-skills/indexing/`
Use when the task is about:

- Backfilling Kalshi or Polymarket markets or trades.
- Resuming interrupted cursor-based collection jobs.
- Fetching Polygon block timestamps or legacy FPMM trades.
- Understanding `KalshiClient`, `PolymarketClient`, `PolygonClient`, or `Indexer.load()` behavior.
- Adding a new indexer class under `src/indexers/`.

Typical signals:
`kalshi_markets`, `kalshi_trades`, `polymarket_markets`, `polymarket_trades`, `polymarket_blocks`, `polymarket_fpmm_trades`, `cursor`, `backfill`, `POLYGON_RPC`, `resume`.

### `sub-skills/data-ops/`
Use when the task is about:

- Downloading the prebuilt dataset or restoring the `data/` directory.
- Packaging the dataset into `data.tar.zst`.
- Installing or diagnosing local host tools such as `zstd`, `aria2c`, `curl`, or `wget`.
- Understanding the repo's `make setup` and `make package` workflows.

Typical signals:
`make setup`, `make package`, `data.tar.zst`, `download.sh`, `install-tools.sh`, `zstd`, `aria2c`, `curl`, `wget`.

## Shared facts

- The package distribution is `prediction-market-data`; the source package tree is rooted at `src/`.
- `Analysis.load()` and `Indexer.load()` default to `src/analysis` and `src/indexers` relative to the current working directory.
- The repo uses Parquet data under `data/kalshi/` and `data/polymarket/`, plus CSV/JSON/PNG/PDF/GIF outputs under `output/`.
- `main.py` dispatches `analyze`, `index`, and `package`.
- `make setup` is a convenience wrapper for host-tool installation plus dataset download.
- `main.py package` / `make package` create `data.tar.zst`; the code does not delete the source `data/` directory.

## Bundled helpers

- `scripts/catalog.py` lists available analyses and indexers from the repo checkout when run through the repo environment.
- `scripts/run_analysis.sh` runs the analysis CLI from the repo root.
- `scripts/run_index.sh` runs the indexing CLI from the repo root.
- `scripts/package_data.sh` runs dataset packaging from the repo root.

## Shared references

- `references/analysis-catalog.md` for the full analysis catalog.
- `references/indexing-catalog.md` for the full indexer catalog and cursor files.
- `references/data-ops.md` for download, extraction, and packaging details.
- `references/troubleshooting.md` for cross-cutting failures.

If a request names missing data, a cursor problem, a Polygon RPC issue, a download failure, or a headless plotting problem, read the matching troubleshooting section before guessing.
