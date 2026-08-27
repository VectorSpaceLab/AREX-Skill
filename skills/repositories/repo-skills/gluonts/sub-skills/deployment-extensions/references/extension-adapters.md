# Extension adapters

`gluonts.ext` contains optional adapters for forecasting packages outside the selected base, PyTorch, and shell workflow. These adapters are useful when the user explicitly asks for Prophet, R forecast, Nixtla statsforecast/hierarchicalforecast, or Rotbaum tree models. They are not verified required backends in the base skill environment.

## Routing table

| Need | GluonTS adapter | Install boundary | Operating notes |
| --- | --- | --- | --- |
| Prophet wrapper | `gluonts.ext.prophet.ProphetPredictor` | `gluonts[prophet]` or direct `prophet` install | Produces `SampleForecast`; supports `prophet_params` and optional `init_model`. Dynamic real features must have length `len(target) + prediction_length`. Instantiation raises an actionable `ImportError` if Prophet is missing. |
| R univariate forecast | `gluonts.ext.r_forecast.RForecastPredictor` | `gluonts[R]` for `rpy2`, plus system R and R packages `forecast` and `nnfor` | Methods include `ets`, `arima`, `tbats`, `thetaf`, `stlar`, `fourier.arima`, `fourier.arima.xreg`, `croston`, and `mlp`. Requires an R executable and compatible R packages. |
| R hierarchical forecast | `gluonts.ext.r_forecast.RHierarchicalForecastPredictor` | `gluonts[R]` for `rpy2`, plus system R and R package `hts` | Requires hierarchy/grouping structure, bottom-series count, target dimension, and reconciliation method. Produces sample forecasts for hierarchical targets. |
| statsforecast models | `gluonts.ext.statsforecast.*Predictor` classes | `gluonts[statsforecast]` | Wraps Nixtla statsforecast models such as AutoARIMA, AutoETS, SeasonalNaive, Theta, Croston variants, MSTL, and others. Predictors return `QuantileForecast`; `quantile_levels` are mapped into statsforecast interval levels when supported. Missing dependency usually fails at module import. |
| hierarchicalforecast reconciliation | `gluonts.ext.hierarchicalforecast.HierarchicalForecastPredictor` | `gluonts[hierarchicalforecast]` | Requires `statsforecast` and `hierarchicalforecast`, a summation matrix `S`, optional `tags` and `ts_names`, a base model class, and a reconciler class. Targets are multivariate arrays arranged by hierarchy series. |
| Rotbaum tree models | `gluonts.ext.rotbaum.TreeEstimator` and `TreePredictor` | `gluonts[rotbaum]`; `gluonts[rotbaum-extra]` for LightGBM-backed quantile regression | Uses tree/quantile-regression style models. Default QRX path uses XGBoost. `QuantileRegression` uses LightGBM. QRF imports `skgarden`, which is not covered by the declared rotbaum extras and must be verified separately. Evaluation with `TreePredictor` should use `num_workers=0`. |
| SageMaker job submission | Python SDK around shell containers | `gluonts[sagemaker]` | Needed for client-side SageMaker APIs, not for the shell entrypoint itself. Requires AWS credentials and service access outside this skill's local verification. |

## Example adapter class paths

Use full class paths for `GLUONTS_FORECASTER`, shell `--forecaster`, or `forecaster_name`:

```text
gluonts.ext.prophet.ProphetPredictor
gluonts.ext.r_forecast.RForecastPredictor
gluonts.ext.r_forecast.RHierarchicalForecastPredictor
gluonts.ext.statsforecast.AutoARIMAPredictor
gluonts.ext.statsforecast.SeasonalNaivePredictor
gluonts.ext.hierarchicalforecast.HierarchicalForecastPredictor
gluonts.ext.rotbaum.TreePredictor
gluonts.ext.rotbaum.TreeEstimator
```

For simple local baselines, prefer core predictors from the forecasting-models sub-skill before adding optional adapters.

## Adapter-specific constraints

### Prophet

- Constructor: `ProphetPredictor(prediction_length, prophet_params=None, init_model=identity)`.
- Do not set `uncertainty_samples` in `prophet_params`; pass sample count through `predict(..., num_samples=...)`.
- Each dynamic real feature must cover both history and forecast horizon.
- Prophet needs at least two non-missing observations.

### R forecast adapters

- Import can expose `R_IS_INSTALLED` and `RPY2_IS_INSTALLED`; instantiation raises if R or rpy2 is missing.
- The Python extra is not enough: install the relevant R packages in the same runtime image.
- `RForecastPredictor` truncates history if `trunc_length` is set and computes a default seasonal period from `freq` when `period` is omitted.
- `RHierarchicalForecastPredictor` uses only bottom-level series during preprocessing and reconstructs hierarchy outputs using the supplied structure.

### statsforecast

- `StatsForecastPredictor` subclasses set a `ModelType` and pass remaining keyword arguments directly to that statsforecast model.
- `quantile_levels` can request quantile forecasts from models that support interval levels; otherwise expect mean-only behavior or a statsforecast-side limitation.
- Serialization/deserialization is supported by GluonTS predictor serialization when all optional packages are available.

### hierarchicalforecast

- Constructor arguments include `prediction_length`, `base_model`, `reconciler`, `S`, optional `tags`, optional `ts_names`, `intervals_method`, `quantile_levels`, `model_params`, and `reconciler_params`.
- Valid `intervals_method` values are `normality`, `bootstrap`, and `permbu`.
- `tags` and `ts_names`, when both supplied, must name the same set of series.

### Rotbaum

- `TreeEstimator` wraps `TreePredictor` and trains without a GluonTS Trainer.
- `TreePredictor` methods include `QRX`, `QuantileRegression`, and `QRF`.
- Dynamic/past/static feature flags require matching feature arrays in the dataset entries.
- For large datasets, tree fitting can be CPU and memory intensive; use bounded samples and explicit worker limits.

## Verification posture

Optional adapters should be treated as opt-in. Before using one in deployment, run a minimal import and one tiny prediction in the same environment that will run the shell. If an adapter requires system packages, R packages, AWS credentials, or Docker, record those as external prerequisites rather than assuming they are present.
