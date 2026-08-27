---
name: eda-visualization
description: "Use AutoViz to profile tabular data and generate static or
  interactive EDA charts."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# EDA Visualization

Use this sub-skill when the user wants AutoViz to visualize a CSV, TXT, Excel file, JSON-like file, or pandas DataFrame. This is the primary route for `AutoViz_Class`, `AutoViz`, chart formats, plot directories, sampling limits, target variables, and static or interactive plots.

## Use this when

- The user asks for one-line EDA, automated visualization, or quick dataset profiling.
- The task names `AutoViz_Class`, `AV.AutoViz`, `AutoViz_Main`, `AutoViz_Holo`, `chart_format`, `verbose`, `depVar`, or `dfte`.
- The user needs to choose between `png`, `svg`, `jpg`, `bokeh`, `server`, or `html` outputs.
- The user is debugging missing plots, empty plots, file-loading issues, or output-directory behavior.
- The user wants to know how AutoViz chooses plot families from supervised or unsupervised data.

## Core flow

1. Identify whether the input is a filename or a DataFrame.
2. If using a filename, pass the path as `filename`; if using a DataFrame, pass `filename=""` and `dfte=df`.
3. Set `depVar` to the target column for supervised EDA or `""` / `None` for unsupervised exploration.
4. Pick a `chart_format`:
   - `svg`, `png`, or `jpg` for matplotlib/static plots.
   - `bokeh`, `server`, or `html` for the HoloViews/Bokeh path.
5. Use `max_rows_analyzed` and `max_cols_analyzed` to bound large datasets.
6. Use `verbose=2` and `save_plot_dir` when the user wants files written instead of displayed.
7. After the run, summarize the most useful plot families rather than every internal helper.

## Read these references

- [`references/workflows.md`](references/workflows.md): end-to-end file and DataFrame recipes.
- [`references/interactive-backends.md`](references/interactive-backends.md): Bokeh/HoloViews/html/server behavior and dependency notes.
- [`references/troubleshooting.md`](references/troubleshooting.md): common EDA failures and how to recover.
- [`../../references/chart-formats.md`](../../references/chart-formats.md): compact chart-format matrix.
- [`../../references/api-reference.md`](../../references/api-reference.md): exact signatures and helper notes.
- [`../../references/install-and-compatibility.md`](../../references/install-and-compatibility.md): when the chart path fails because the environment is incomplete.

## Use these scripts

- Run [`scripts/autoviz_smoke.py`](scripts/autoviz_smoke.py) to verify the static AutoViz path on a safe in-memory DataFrame.
- Run [`scripts/autoviz_interactive_smoke.py`](scripts/autoviz_interactive_smoke.py) to check that interactive backend imports and the `html` route are usable.
- Run [`../../scripts/inspect_install.py`](../../scripts/inspect_install.py) if the environment itself is the problem.

## Decision points

- Prefer static `svg` or `png` when running headless or inside automated tests.
- Prefer `html` when the user wants a saved interactive artifact without keeping a server process alive.
- Treat `server` as a browser/server workflow; do not start a long-running server unless the user asked for it.
- Use a nonempty `save_plot_dir` for reproducible outputs; otherwise AutoViz creates `AutoViz_Plots` under the current working directory when saving.
- Explain that AutoViz classifies variables before plotting, so tiny toy data can be classified as IDs, booleans, or categorical columns in surprising ways.
- If a supervised run has many columns, mention that AutoViz may use feature selection to limit the plots.

## Typical plot families

- scatter plots for numeric predictors against the target
- pairwise scatter plots for numeric-variable relationships
- distribution plots for target or feature distributions
- violin plots for class or regression comparisons
- heatmaps for numeric correlation inspection
- bar and pivot plots for categorical or mixed data
- date/time plots when date variables are present
- catscatter plots when there are mostly categorical variables
- wordcloud plots when string-like variables are detected

## Cross-routing

- If an AutoViz run fails inside `pandas_dq` or the user asks how to fix dataset issues, switch to [`../data-quality-fixes/SKILL.md`](../data-quality-fixes/SKILL.md).
- If string columns trigger wordclouds, NLTK downloads, or text-cleaning questions, switch to [`../text-wordclouds/SKILL.md`](../text-wordclouds/SKILL.md).
- Do not tell future users to open the original repository notebooks. Use this skill's references and bundled scripts instead.
- Keep the response focused on the chosen `chart_format` and data shape; do not restate every helper function in the package.

## Troubleshooting reminders

- If no plots appear, check whether the target column exists and whether AutoViz removed many columns as IDs or low-information features.
- If the run is interactive but nothing renders, try `html` first and confirm the required dependencies are installed.
- If plots are saved but hard to find, inspect the `save_plot_dir` argument and the target-named output subdirectory.
- If a tiny fixture gives odd plot families, make the test data more varied before treating the behavior as a bug.
