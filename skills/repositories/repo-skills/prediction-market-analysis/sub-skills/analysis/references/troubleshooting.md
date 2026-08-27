# Analysis Troubleshooting

## Empty result sets

Symptoms:
- The analysis runs but writes an empty CSV or a tiny figure.

Likely causes:
- No finalized Kalshi markets or no resolved Polymarket markets in the dataset.
- Missing trade files in the expected directory.
- Filters such as price ranges, volume thresholds, or category grouping removing all rows.

Fixes:
- Check the data-layout reference and confirm the required subdirectories exist.
- Verify that the markets used by the analysis actually resolve to `yes` or `no`.
- For Polymarket, confirm that the collateral lookup file exists when the analysis needs it.

## `Analysis.load()` cannot find modules

Symptoms:
- No analyses are discovered.
- The CLI says no analyses exist.

Likely causes:
- The current working directory is not the repo root.
- The scan path does not point at `src/analysis` in the checkout.

Fixes:
- Pass an explicit absolute source root.
- Run the command from the repo checkout root.
- Use the catalog helper to confirm the analysis list before debugging the loader.

## Missing chart output

Symptoms:
- The analysis writes CSV/JSON but not PNG/PDF, or vice versa.

Likely causes:
- The analysis returns only data or only an animation.
- The figure type does not match the requested output format.

Fixes:
- Check whether the analysis returns `Figure`, `FuncAnimation`, `chart`, or `None`.
- For animated analyses, expect GIF rather than PNG/PDF.

## Headless plotting

Symptoms:
- Matplotlib complains about display access or backend availability.

Fixes:
- Use a headless backend such as Agg in CI or terminal-only sessions.
- Close figures after saving to avoid leaking figure handles.
