# Darts troubleshooting

## Install/import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'darts'` | package not installed in the active environment | Install `darts` in the environment that runs the code; then run `python -c "import darts; print(darts.__version__)"`. |
| Legacy install notes mention `u8darts` | Darts changed pip package naming in >=0.41.0 | Prefer `pip install darts`, `darts[torch]`, `darts[notorch]`, or `darts[all]`. |
| Optional model class import fails | missing extra such as torch, Prophet/GBM libraries, NeuralForecast, TiRex, ONNX, Ray, or Optuna | Install only the extra/package needed by that model family; see `installation-and-optional-dependencies.md`. |
| PyTorch import works but Darts neural training fails on GPU | CPU torch wheel or incompatible CUDA/driver/device | Verify `torch.cuda.is_available()`, the wheel CUDA version, and a tiny Darts trainer run before claiming GPU support. |
| Foundation wrapper starts downloading or fails due to cache | model weights/cache not present or network unavailable | Require explicit local cache path or network approval before constructing/downloading foundation models. |

## Data and frequency failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `TimeSeries` constructor cannot infer frequency | missing dates, duplicate timestamps, irregular index, or no `freq` | Use `fill_missing_dates=True` with explicit `freq`, or clean duplicates/irregularities before construction. |
| Unexpected `(time, component, sample)` shape | confused multivariate components with stochastic samples or multiple series | Route to `time-series-and-data`; inspect `series.n_components`, `series.n_samples`, and `series.is_stochastic`. |
| Static covariates do not align | component-specific static covariates have wrong row count/index | Use one row for global static covariates or one row per component for component-specific covariates. |
| Multiple entities collapsed incorrectly | group columns were encoded as components rather than multiple series | Use `TimeSeries.from_group_dataframe()` for entity-level multiple series. |

## Preprocessing and covariate failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Validation metrics look too good | scaler/filler was fit on validation/test data | Fit fittable transformers only on training data, then transform validation/test. |
| Forecast cannot be inverse-transformed | fitted invertible transformer not retained or applied to forecast scale incorrectly | Keep the fitted `Pipeline`/`Scaler` object and call `inverse_transform()` on forecasts with matching components. |
| `future_covariates` do not cover prediction range | covariate series ends before target end plus forecast horizon | Regenerate/append calendar covariates through the required horizon and validate frequency/index alignment. |
| Covariate argument rejected by a model | selected model does not support past/future covariates | Route to `forecasting-workflows` model-selection; switch to a compatible regression/global/torch model. |

## Forecasting failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `fit()`/`predict()` argument mismatch | using parameters from another model family | Check the owning sub-skill API reference; local/statistical, regression/global, and torch models differ. |
| Forecast length/start is wrong | wrong split point, horizon `n`, or covariate coverage | Assert `len(forecast) == n`, inspect `forecast.start_time()`, and compare to validation horizon. |
| Probabilistic forecast has one sample | model or call did not request/generate samples | Use a probabilistic-capable model and `predict(..., num_samples=...)` or configure a likelihood when required. |
| Historical forecast/backtest is slow | retraining or large horizon/window choices | Use bounded windows, avoid long retrain loops, and start with tiny examples. |

## Anomaly failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Score length is shorter than input | windowed scorer produces `len(series)-window+1` score points | Align labels/series to score time index before evaluating. |
| Binary detector output looks continuous or vice versa | confusing scorer outputs with detector outputs | Treat scorers as continuous scores; detectors produce binary anomaly flags. |
| Detector fails before detection | fittable detector such as `QuantileDetector` was not fit on normal scores | Fit the scorer on normal train data, score train data, fit detector on train scores, then detect validation scores. |

## Evaluation and plotting failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Metric output shape unexpected | reductions left time/component/series axes intact or collapsed them | Set `time_reduction`, `component_reduction`, and `series_reduction` intentionally; inspect shapes. |
| Interval metric rejects `q` | interval metrics use `q_interval`, not single quantiles | Use `q` for quantile metrics and `q_interval` for interval coverage/width metrics. |
| SHAP is slow or memory-heavy | background data too large or unsuitable | Use a small representative background and foreground; verify the fitted model is supported. |
| Plotting hangs in headless sessions | unconditional `plt.show()` or interactive notebooks | Save figures to files only when requested, or skip plotting in automated checks. |

## Safe diagnostics

Run these bundled scripts on tiny generated data before escalating:

```bash
python scripts/darts_doctor.py --json
python scripts/core_forecasting_smoke.py --json
python sub-skills/time-series-and-data/scripts/timeseries_doctor.py --json
python sub-skills/data-processing-and-covariates/scripts/transform_pipeline_smoke.py --quiet
python sub-skills/forecasting-workflows/scripts/forecasting_smoke.py --compact
python sub-skills/anomaly-detection/scripts/anomaly_smoke.py --json
python sub-skills/evaluation-and-explainability/scripts/evaluation_smoke.py --check-shap
```

For torch, run `python sub-skills/torch-and-foundation-models/scripts/torch_model_smoke.py --train` only when `darts[torch]` and PyTorch Lightning are installed and a short CPU smoke is acceptable.
