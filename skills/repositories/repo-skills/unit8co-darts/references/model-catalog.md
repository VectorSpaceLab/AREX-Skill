# Darts model catalog and routing

Use this catalog to choose the owning sub-skill and dependency boundary before writing code.

## Core/base forecasting routes

| Family | Examples | Typical use | Owner |
| --- | --- | --- | --- |
| Naive baselines | `NaiveMean`, `NaiveSeasonal`, `NaiveDrift`, `NaiveMovingAverage` | sanity checks, seasonal baseline, fast comparisons | `forecasting-workflows` |
| Statistical/local models | `ExponentialSmoothing`, `ARIMA`, `AutoARIMA`, `Theta`, `FourTheta`, `FFT`, `KalmanForecaster`, `Croston` | single-series forecasting with low setup | `forecasting-workflows` |
| Regression/global models | `LinearRegressionModel`, `RegressionModel`, `RandomForest`, `LightGBMModel`, `XGBModel`, `CatBoostModel` | lagged target/covariate forecasting, multiple series, tabular regressors | `forecasting-workflows`; optional GBM libraries require `darts[notorch]` |
| Ensemble/conformal | `RegressionEnsembleModel`, `NaiveEnsembleModel`, conformal wrappers | combine/calibrate existing forecasts | `forecasting-workflows`, then metrics in `evaluation-and-explainability` |

## PyTorch neural routes

| Family | Examples | Typical use | Owner |
| --- | --- | --- | --- |
| Sequence neural models | `RNNModel`, `BlockRNNModel`, `TCNModel`, `TransformerModel` | neural forecasting with chunk lengths and trainer kwargs | `torch-and-foundation-models` |
| Deep architectures | `NBEATSModel`, `NHiTSModel`, `TFTModel`, `TiDEModel`, `DLinearModel`, `NLinearModel`, `TSMixerModel`, `PatchTSTModel` | global models over one or more series; many accept past/future covariates depending on class | `torch-and-foundation-models` |
| Torch explainers | TFT/torch-specific explainability helpers | explain fitted neural models when dependencies and model support exist | start with `torch-and-foundation-models`, then `evaluation-and-explainability` |

## Foundation and wrapper routes

| Family | Examples | Extra conditions | Owner |
| --- | --- | --- | --- |
| Foundation wrappers | Chronos2, TimesFM2.5, PatchTST foundation variants | local cache or approved network download, memory, wrapper-specific packages | `torch-and-foundation-models` |
| NeuralForecast/TiRex wrappers | `NeuralForecastModel`, `TiRexModel` | install `neuralforecast` or `tirex-ts` separately | `torch-and-foundation-models` |

## Anomaly routes

| Family | Examples | Typical use | Owner |
| --- | --- | --- | --- |
| Scorers | `KMeansScorer`, `PyODScorer`, difference/norm scorers | continuous anomaly scores from raw values or residuals | `anomaly-detection` |
| Detectors | `QuantileDetector`, `ThresholdDetector`, `IQRDetector` | convert continuous scores to binary anomaly flags | `anomaly-detection` |
| Anomaly models | `ForecastingAnomalyModel`, filtering anomaly wrappers | score residuals from Darts models | `anomaly-detection`, with model training routed to forecasting/torch |

## Metrics and explainability routes

- Deterministic point forecasts: `mae`, `mse`, `rmse`, `mape`, `r2_score`, etc. → `evaluation-and-explainability`.
- Stochastic forecasts: quantile loss, interval coverage/width, CRPS-like metrics → `evaluation-and-explainability`.
- SHAP for fitted sklearn-like Darts forecasting models → `evaluation-and-explainability`.

## Selection rules

1. Start with install constraints: if the user forbids torch, avoid torch models. If optional GBM/Prophet packages are absent, choose core/base models or ask/plan an install.
2. Validate data representation and covariate spans before selecting complex models.
3. Use naive/core baselines before neural/foundation models.
4. Do not treat `num_samples` as universally supported. Check the model family and likelihood/probabilistic support.
5. Do not claim GPU or foundation execution unless that exact backend/cache was verified in the user's environment.
