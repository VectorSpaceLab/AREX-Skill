# Cross-cutting StatsForecast troubleshooting

Read this before diving into sub-skill-specific troubleshooting when a task fails during import, installation, data preparation, forecasting, model choice, or distributed execution.

## Triage flow

1. Run the root import check:
   ```bash
   python scripts/check_statsforecast_env.py --json
   ```
2. Run the root quick smoke:
   ```bash
   python scripts/statsforecast_quick_smoke.py --json
   ```
3. If installation/import fails, use [installation-and-environment.md](installation-and-environment.md).
4. If dataframe schema or `X_df` alignment fails, use `sub-skills/core-forecasting/references/data-formats.md` and `sub-skills/core-forecasting/references/troubleshooting.md`.
5. If a model is unsuitable or missing optional dependencies, use `sub-skills/model-selection/references/troubleshooting.md`.
6. If feature creation fails, use `sub-skills/feature-engineering/references/troubleshooting.md`.
7. If Dask/Ray/Spark/Fugue execution fails, use `sub-skills/distributed-execution/references/troubleshooting.md`.

## Common symptoms

| Symptom | Likely cause | Next action |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'statsforecast'` | Package is not installed in the active Python. | Install `statsforecast`, then run `scripts/check_statsforecast_env.py`. |
| Build fails with `Eigen/Dense` or `Eigen/Core` missing | Source checkout install lacks Eigen headers/submodule. | Use a wheel or initialize/provide Eigen headers before editable install. |
| Forecast fails asking for exogenous columns through `X_df` | Training data included future-varying regressor columns for an exogenous-aware model. | Build one future row per `unique_id` and horizon with the same regressor columns; see `core-forecasting`. |
| Duplicate output columns or model name collision | Two model instances have the same alias/repr. | Set a distinct `alias` on repeated model classes; see `model-selection`. |
| Conformal interval request fails with minimum-sample message | Not enough history for requested `h` and `n_windows`. | Reduce horizon/windows or provide more history; see `core-forecasting` troubleshooting. |
| `AutoMFLES requires scikit-learn` | Optional dependency missing. | Install scikit-learn or choose a different model. |
| Dask/Ray/Spark DataFrame errors | Optional distributed dependencies or runtime services are missing, or output was not materialized. | Install the needed backend and use `.compute()`, `.show()`, or `.collect()` as appropriate; see `distributed-execution`. |

## Keep outputs deterministic

- Sort forecasts by id/time before comparing pandas, polars, and distributed outputs.
- Use small generated fixtures for debugging before scaling to many series.
- Keep model aliases explicit when comparing variants.
- Prefer `forecast(df=..., h=...)` for memory-efficient one-shot forecasts; use `fit`/`predict` only when later reuse of fitted state is needed.
