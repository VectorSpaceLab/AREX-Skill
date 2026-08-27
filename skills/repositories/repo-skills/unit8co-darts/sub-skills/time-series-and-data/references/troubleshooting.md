# TimeSeries troubleshooting

## Missing or irregular timestamps

**Symptom:** Darts cannot infer frequency, a date is missing after construction, or split/forecast boundaries are off.

**Fix:**

1. Sort by time and remove duplicate timestamps.
2. Decide whether missing points should be explicit.
3. Use `fill_missing_dates=True` with explicit `freq`, e.g. `freq="D"` for daily data.
4. Inspect inserted values; fill them later with `MissingValuesFiller` if needed.

Do not pad the target with fake future values just to satisfy a forecast horizon. Future horizon coverage belongs in covariates, not target construction.

## Components vs multiple series

**Symptom:** A user has stores/items/entities and accidentally makes one wide multivariate series.

**Fix:**

- If columns are variables for the same entity and share the same timestamps, keep one multivariate series.
- If columns identify entities, use `from_group_dataframe()` to get a list of series.
- For global models, maintain parallel lists for target series and covariates.

## Static covariate shape errors

**Symptom:** static covariates raise shape/index errors or appear attached incorrectly.

**Fix:**

- Use one row for global covariates, or one row per component for component-specific covariates.
- For component-specific covariates, index rows by component names such as `sales`, `returns`.
- After construction, inspect `series.static_covariates` before fitting models.

## Stochastic sample confusion

**Symptom:** stochastic forecasts or probabilistic data look like extra components.

**Fix:**

- Components are named variables; samples are probabilistic draws.
- Deterministic values usually appear as `(time, component)` through `values()`.
- Use `all_values()` to inspect the sample axis.
- Route probabilistic metric handling to `evaluation-and-explainability`.

## Export surprises

**Symptom:** a pandas export loses entity/group context or static metadata.

**Fix:**

- For one series, use `pd_dataframe()` and add entity/static columns explicitly if needed.
- For multiple series, rebuild a group table intentionally or verify `to_group_dataframe()` behavior in the installed Darts version.
- Do not assume the original source repository dataset layout exists in the user's project.
