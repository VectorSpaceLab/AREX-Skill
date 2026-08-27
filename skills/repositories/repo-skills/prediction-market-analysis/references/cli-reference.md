# CLI Reference

This repo is controlled by a small CLI and matching `make` targets.
Use this page when you need the command surface, not the deeper workflow guidance.

## Core commands

| Command | Purpose | Notes |
| --- | --- | --- |
| `uv run main.py analyze` | Open the analysis menu | Shows all discovered analysis classes and runs one selected analysis. |
| `uv run main.py analyze all` | Run every analysis | Saves each analysis output to `output/` using the analysis name. |
| `uv run main.py analyze <name>` | Run one analysis by name | Example names include `win_rate_by_price`, `polymarket_volume_over_time`, and `win_rate_by_price_animated`. |
| `uv run main.py index` | Open the indexer menu | Shows all discovered indexers and runs one selected indexer. |
| `uv run main.py package` | Package the data directory | Calls `src.common.util.package.package_data()` and writes `data.tar.zst`. |
| `uv run main.py` | Print CLI usage | Safe non-interactive usage check. |

## Make targets

| Target | Behavior | Notes |
| --- | --- | --- |
| `make analyze` | Delegates to `uv run main.py analyze` | Interactive menu. |
| `make run NAME` | Delegates to `uv run main.py analyze NAME` | Example: `make run win_rate_by_price`. |
| `make index` | Delegates to `uv run main.py index` | Interactive menu. |
| `make package` | Delegates to `uv run main.py package` | Packages `data/` into `data.tar.zst`. |
| `make setup` | Runs `scripts/install-tools.sh` then `scripts/download.sh` | Interactive and network/tooling dependent. |
| `make test` | Runs `uv run pytest tests/ -v` | Useful after adding or changing code. |
| `make lint` | Runs Ruff checks | Developer-only. |
| `make format` | Runs Ruff with `--fix` and formatter | Developer-only. |

## Analysis command behavior

- `analyze` discovers subclasses of `src.common.analysis.Analysis`.
- `analyze all` saves PNG, PDF, CSV, JSON, and GIF when available.
- Most analyses save into `output/<analysis-name>.*`.
- Animated analyses use GIF instead of PNG/PDF and may also emit CSV.
- The analysis menu is interactive and expects a terminal.

## Indexer command behavior

- `index` discovers subclasses of `src.common.indexer.Indexer`.
- The menu is interactive and expects a terminal.
- Each indexer writes Parquet chunks and may maintain a resume cursor file.

## Helper scripts

- `scripts/catalog.py --all` lists available analyses and indexers without opening the interactive menu when run through the repo environment.
- `scripts/run_analysis.sh [name|all]` is a thin wrapper around the analysis CLI.
- `scripts/run_index.sh` is a thin wrapper around the indexer CLI.
- `scripts/package_data.sh` is a thin wrapper around dataset packaging.

## Important caveats

- `make setup` is not a safe non-interactive helper; it can mutate the host by installing tools and downloading the dataset.
- The code path for `package` creates `data.tar.zst` but does not delete the source `data/` directory.
- `Analysis.load()` and `Indexer.load()` are cwd-sensitive unless you pass an explicit root path.
