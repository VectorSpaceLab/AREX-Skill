# Component Troubleshooting

Use this when component setup, exogenous data assembly, or multi-series configuration fails. Route base dataframe/frequency issues to `../core-forecasting/SKILL.md`, evaluation to `../evaluation-and-uncertainty/SKILL.md`, and plotting/save/load/runtime operations to `../operations-and-migration/SKILL.md`.

## Environment issues that can look like component failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Failure around `pandas.Series.view` | This package version expects pandas behavior removed in pandas 3. | Use pandas `<3`. |
| Lightning import fails around `pkg_resources` | Some Lightning dependency paths still rely on `pkg_resources`, removed from newer setuptools. | Use setuptools `<81`. |
| Plotly warning/error appears during non-plotting work | Optional `plotly-resampler` is not installed by the base package and logging can be misleading. | Ignore for component fit/predict; install plotting extras only for plotting tasks. |
| Tiny smoke run is slow or writes checkpoints/logs | Metrics/progress/checkpointing are enabled. | Use CPU, `collect_metrics=False`, and `fit(..., minimal=True, progress=None, checkpointing=False)`. |

## Duplicate or reserved names

Symptoms:

- `ValueError: Name '...' is reserved.`
- `ValueError: Name '...' already used for an event/seasonality/covariate/regressor.`
- A holiday name collides with a requested component name.

Recovery:

- Avoid reserved names: `trend`, `daily`, `weekly`, `yearly`, `events`, `holidays`, `yhat`, `ID`, `y_scaled`, `ds`, `t`, `y`, `index`, `cap`, `floor`, `cap_scaled`, and these names with `_lower` or `_upper` suffixes.
- Use unique names across all component types; a future regressor, event, seasonality, and holiday cannot share the same name.
- Use built-in seasonality constructor switches instead of `add_seasonality("weekly", ...)`.
- Create a new model and refit when component names or scope change after fitting.

## Missing future regressor columns

Symptoms:

- `Future values of all user specified regressors not provided`.
- `Future values of user specified regressor <name> not provided`.
- `Regressor <name> not found in regressors_df`.

Recovery:

1. Confirm the training dataframe contains every column registered by `add_future_regressor`.
2. Build `regressors_df` with every registered future regressor for exactly the requested horizon.
3. For multiple IDs, include `ID` when values differ by series and keep IDs identical to the prediction dataframe.
4. Sort `regressors_df` by `ID` and `ds` so row order matches future periods.
5. If the variable is not known in advance, do not use `add_future_regressor`; use a lagged regressor or forecast that variable separately.

## Event or holiday problems

Symptoms:

- Custom event effects do not appear.
- `create_df_with_events` fails.
- Country/subdivision is rejected.
- Event windows appear shifted or too wide.

Recovery:

- Call `add_events` before `create_df_with_events`.
- Event tables need `event` and `ds`, plus optional `ID` for per-series schedules.
- `events_df["event"]` values must match registered event names exactly.
- Pass known future events again to `make_future_dataframe(..., events_df=events_df)`.
- Keep `lower_window <= upper_window`; windows are inclusive frequency-step offsets around the event row.
- Add country holidays only once. Pass multiple countries as a list or subdivisions as one dictionary. If unsupported, use custom events.

## Autoregression or lagged regressor alignment

Symptoms:

- Insufficient input data for prediction.
- Initial rows are missing or `NaN` after adding lags.
- Forecasts look shifted after adding lagged covariates.

Recovery:

- Check the maximum lag across target AR and lagged regressors.
- Ensure every ID has at least that many historical rows before the forecast boundary.
- Compute rolling/lagged features within each ID group.
- Use lagged regressors for historical covariates only; use future regressors for known future covariates.
- Use `n_historic_predictions` deliberately when you need context rows in forecast output.

## Invalid global/local/glocal settings

Symptoms:

- Logs say an invalid `global_local` mode was set to `global`.
- Local trend settings are ignored with `growth="off"` or `growth="discontinuous"`.
- Multi-ID behavior looks global despite intended local/glocal modeling.

Recovery:

- Use `trend_global_local="global"` or `"local"`.
- Use `season_global_local="global"` or `"local"` and custom `add_seasonality(..., global_local="global"|"local"|"auto")`.
- For glocal/regularized-local behavior in this version, prefer `"local"` plus positive `trend_local_reg` or `seasonality_local_reg`.
- Use local components only with an `ID` dataframe and enough rows per ID.

## Multi-ID exogenous mismatches

Symptoms:

- `ID(s) [...] from regressors df is not valid - missing from original df ID column`.
- Similar invalid-ID errors for event frames.
- Forecast output has unexpected IDs or shared exogenous values.

Recovery:

1. Compare `set(df["ID"])` with IDs in `events_df` and `regressors_df`.
2. Include `ID` in exogenous frames only when values differ by series; omit it to broadcast shared values.
3. Do not introduce unseen IDs in future exogenous frames unless the base prediction dataframe contains those IDs and normalization settings are deliberate.
4. Route ID-specific plotting or parameter display to `../operations-and-migration/SKILL.md`.

## Conditional seasonality missing in future rows

Symptoms:

- `predict` fails after `make_future_dataframe`.
- Conditional seasonality has no effect in future periods.

Recovery:

- Recompute the condition column after creating the future dataframe.
- Ensure values are numeric 0/1 or fractional weights, not strings or missing values.
- For multi-ID conditions, compute values within each ID group when behavior differs by series.

## Multiplicative components are unstable

Recovery:

- Start with additive mode as a baseline.
- Confirm the target scale is suitable for multiplicative effects.
- Add regularization to flexible seasonalities, events, or regressors.
- Reduce Fourier order or event-window width.
- Evaluate with a holdout/CV workflow before accepting the component design.
