# AutoViz troubleshooting

## Import and environment failures

| Symptom | Diagnosis | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: pandas_dq` | AutoViz imports `pandas_dq` at module load. | Install AutoViz runtime dependencies or `pandas-dq>=1.29`. |
| `ModuleNotFoundError: IPython` from `pandas_dq` | `pandas_dq` imports `IPython.display`. | Install `ipython` even in headless environments. |
| `AttributeError: 'DataFrame' object has no attribute 'applymap'` | pandas 3.x removed `applymap`; `pandas_dq` 1.29 still uses it. | Use pandas 2.x for AutoViz 0.1.905 workflows. |
| `xgboost 1.6.2 is not supported on this platform` | Pip's XGBoost wheel metadata or platform tags are incompatible. | Use a compatible conda-forge CPU build or another supported XGBoost version `<1.7`. |
| `pkg_resources` errors during XGBoost import | Older XGBoost code expects `pkg_resources`. | Install `setuptools<81` or use a conda-forge XGBoost build. |
| HoloViews/Bokeh import error | Interactive stack missing. | Install `hvplot`, `holoviews`, `panel`, `bokeh`, and `IPython`. |

## Plotting surprises

- Tiny toy datasets can make numeric columns look like IDs, booleans, or categorical variables. Use more varied values in smoke data when checking plot branches.
- A missing or misspelled `depVar` can make AutoViz return early or treat the dataset as unsupervised.
- `max_rows_analyzed` samples large datasets; do not treat sampled plot output as a full-data statistical report.
- `max_cols_analyzed` can trigger feature selection through XGBoost for supervised problems.
- `verbose=2` saves plots instead of displaying them; choose a writable `save_plot_dir`.
- `chart_format='server'` may start a live Panel/Bokeh server. Use `html` when a saved interactive artifact is enough.

## Data-quality failures

- AutoViz calls `data_cleaning_suggestions` before plotting. If an AutoViz run fails before plots appear, check the data-quality sub-skill and package versions.
- Duplicate rows, mixed object types, infinity values, rare categories, and high correlation/leakage are expected warnings, not necessarily fatal errors.
- For reusable train/test cleaning, use `FixDQ` rather than only reading the report.

## Text and wordcloud failures

- The wordcloud branch can call `nltk.download('popular')`; in offline environments, prepare NLTK data or avoid triggering the wordcloud branch.
- Missing `wordcloud` or `nltk` dependencies break wordcloud generation.
- Short low-cardinality string columns may be classified as categorical or boolean rather than text; use longer, higher-cardinality strings to test wordcloud behavior.

## Import banner

`import autoviz` prints a banner showing a suggested call sequence. This is normal for version `0.1.905` and is not an error.
