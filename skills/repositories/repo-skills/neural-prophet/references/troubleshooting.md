# NeuralProphet Cross-Cutting Troubleshooting

## Quick diagnostic order

1. Run `python scripts/check_neuralprophet_install.py` from the root of this generated skill or by script path.
2. If imports pass but fitting fails, run `sub-skills/core-forecasting/scripts/smoke_forecast.py`.
3. If user data is involved, run `sub-skills/core-forecasting/scripts/validate_neuralprophet_dataframe.py --input-file data.csv`.
4. If a component, uncertainty, plotting, save/load, or wrapper workflow fails, route to the owning sub-skill troubleshooting file.

## Known compatibility pins for this version

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'pkg_resources'` | Lightning stack imports `pkg_resources`; very new setuptools may not ship it | `python -m pip install 'setuptools<81'` |
| `AttributeError: 'Series' object has no attribute 'view'` in frequency inference | Current code path expects pandas 2.x behavior | `python -m pip install 'pandas<3'` |
| Misleading `Importing plotly failed` log | Optional `plotly-resampler` is missing, not necessarily base Plotly | Use matplotlib/plotly-static or install `plotly-resampler` only when needed |
| CUDA expectations fail | Core workflows do not require CUDA; PyTorch backend may not match hardware | Use `accelerator='cpu'` for diagnostics; verify torch CUDA separately before GPU training |

## Data and API misuse

- Basic training data must have `ds` and `y`; multi-series data uses `ID`.
- Pass explicit `freq` when data are sparse, irregular, monthly, sub-daily, or too short for reliable inference.
- Configure regressors/events/seasonalities before fitting, and keep required columns available during prediction.
- A model with future regressors needs future regressor values for the prediction horizon.
- A model with events needs event occurrences supplied through event dataframes where the API expects them.

## Optional dependencies

- Base install covers normal core forecasting, plotting packages, and PyTorch training.
- `plotly-resampler` is optional and skipped unless interactive resampling is required.
- `livelossplot` comes from the `live` extra and is only needed for live loss plotting.
- Documentation, metrics, linters, and dev dependencies are not required for Researcher package use.

## When to stop and ask for external resources

Stop instead of improvising when the task requires:

- Large benchmark-scale training or long notebooks.
- Network downloads for tutorial datasets.
- GPU/accelerator claims that must be verified on specific hardware.
- Private data, credentials, MLflow services, or external dashboards.
