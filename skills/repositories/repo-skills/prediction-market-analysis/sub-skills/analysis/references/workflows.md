# Analysis Workflows

## Running an analysis

1. Use `scripts/catalog.py --analyses` or the analysis catalog to pick a name.
2. Confirm the required input directories exist under `data/`.
3. Run `uv run main.py analyze <analysis-name>`.
4. Read the saved files in `output/`.

## Running everything

`uv run main.py analyze all` runs every discovered analysis and saves each output under `output/<analysis-name>.*`.
Use this when you want a bulk refresh or when you are checking how multiple analyses interact with the same dataset.

## Interpreting outputs

- Figures are usually written as PNG and PDF.
- Dataframes are written as CSV when the analysis returns `AnalysisOutput.data`.
- Chart configs are written as JSON when the analysis returns `AnalysisOutput.chart`.
- Animated analyses may write GIF instead of PNG/PDF.
- `meta_stats` and `statistical_tests` are data-first analyses and may not produce a figure.

## Extending an analysis

- Keep the SQL or dataframe logic near the `run()` method.
- Use `self.progress()` around longer reads or aggregations.
- Prefer small helper methods for figure creation and chart serialization.
- Reuse `src.analysis.kalshi.util.categories` for category-aware Kalshi logic rather than duplicating category extraction.

## Special cases

- `win_rate_by_price_animated` needs both Kalshi and Polymarket inputs plus the blocks and collateral lookup files.
- `polymarket_volume_over_time` and `polymarket_calibration_by_bucket` also need the collateral lookup file.
- `market_types` uses a treemap and depends on the hierarchical category helper.
