# API Overview

This reference summarizes the public HyperTools surface and the shared
contracts that cut across the sub-skills. Use the focused sub-skill references
for detailed recipes, edge cases, and troubleshooting.

## Package identity

- Distribution name: `hypertools`
- Import module: `hypertools`
- Package version in this snapshot: `1.0.0`
- Python floor: `>=3.10`

## Public exports

| Name | Typical use | Primary router |
| --- | --- | --- |
| `plot` | Figure creation, styling, animation, export, and overlays | `sub-skills/visualization/` |
| `analyze` | Canonical stage dispatcher and pipeline replay | `sub-skills/pipeline/` |
| `reduce` | Dimensionality reduction and reuse | `sub-skills/pipeline/` |
| `align` | Cross-dataset alignment and reuse | `sub-skills/pipeline/` |
| `normalize` | Z-scoring and normalization stages | `sub-skills/pipeline/` |
| `describe` | Data description and summary | `sub-skills/pipeline/` |
| `cluster` | Hard labels or mixture memberships | `sub-skills/pipeline/` |
| `manip` | Manipulation dispatch and chaining | `sub-skills/pipeline/` |
| `predict` | Forecast future rows | `sub-skills/forecasting/` |
| `impute` | Fill missing values | `sub-skills/forecasting/` |
| `load` | Resolve and load data sources | `sub-skills/io/` |
| `save` | Persist arrays, frames, models, and plots | `sub-skills/io/` or `sub-skills/visualization/` |
| `apply_model` | Stack-once / fit-once / unstack core | `sub-skills/pipeline/` |
| `Pipeline` | Reusable fitted stage chain | `sub-skills/pipeline/` |
| `set_interactive_backend` | Session-level renderer preference | `sub-skills/visualization/` |
| `HyperAnimation` | Return type for animated matplotlib plots | `sub-skills/visualization/` |
| `io` | LSL and streaming helpers | `sub-skills/io/` |
| `supported_models` | Reduce/cluster registry discovery | `sub-skills/pipeline/` |
| `HypertoolsError` | Base error | cross-cutting |
| `HypertoolsBackendError` | Backend selection or renderer failure | cross-cutting |
| `HypertoolsIOError` | Load/save/source failure | cross-cutting |

## Shared contracts

- `plot` returns a matplotlib `Figure`, a plotly `Figure`, or a
  `HyperAnimation` depending on backend and animation settings.
- `plot(..., return_model=True)` returns a bundle, not a raw label array.
- `analyze(..., cluster=...)` returns transformed data; recover labels from the
  fitted cluster step when `return_model=True`.
- `load` returns raw data, a DataFrame/array/list/dict, or a streaming object;
  it does not return a legacy `DataGeometry` shell in 1.0.
- `save` chooses the output format from the filename extension.
- `predict` and `impute` accept fitted forecasters/imputers back as `model=`
  on new data when the shape is compatible.
- Tuples behave like lists for dispatcher-style multi-dataset inputs.
- 1-D arrays, flat lists, and `pandas.Series` are treated as univariate
  timeseries for forecasting and imputation.
- Model specs may be strings, dicts, classes, instances, or lists of specs,
  depending on the dispatcher.
- The canonical analysis order is `manip -> normalize -> reduce -> align ->
  cluster`.
- `Pipeline.fit_transform` refits every step; `Pipeline.transform` reuses the
  fitted steps when the step supports out-of-sample application.

## When to look deeper

- Plot styling, animation, streaming, `save_path`, and overlays belong in
  `sub-skills/visualization/`.
- Source precedence, trust rules, built-in datasets, and LSL belong in
  `sub-skills/io/`.
- Stage grammar, `ndims`, `random_state`, and model reuse belong in
  `sub-skills/pipeline/`.
- Text vectorizers, corpus handling, and Hugging Face fallback belong in
  `sub-skills/text/`.
- Forecast horizons, model families, and imputation behavior belong in
  `sub-skills/forecasting/`.
