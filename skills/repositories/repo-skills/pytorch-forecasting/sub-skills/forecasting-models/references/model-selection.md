# Model Selection Guide

This guide maps common forecasting tasks to PyTorch Forecasting 1.8.0 v1 model families. It assumes that data preparation is handled with `TimeSeriesDataSet` and the data-pipeline sub-skill.

## Import map

Stable v1 models exported from the package root:

```python
from pytorch_forecasting import (
    Baseline,
    TemporalFusionTransformer,
    NBeats,
    NBeatsKAN,
    NHiTS,
    DeepAR,
    RecurrentNetwork,
    DecoderMLP,
    TiDEModel,
)
```

Additional v1 model classes are available from the model package:

```python
from pytorch_forecasting.models import TimeXer, xLSTMTime
```

`pytorch_forecasting.models.SOFTS` exists in the distribution, but it is implemented on the experimental v2 base layer. Do not use it in a v1 `TimeSeriesDataSet` / `.from_dataset()` workflow; route SOFTS and v2 package/data-module questions to `../api-v2-workflows/SKILL.md`.

## Task-to-model table

| Task shape | Prefer | Why | Required cautions |
|---|---|---|---|
| Prove the dataloader and prediction path works before training | `Baseline` | No training; predicts from observed history and exercises `BaseModel.predict()` plumbing. | It is a sanity check, not a learned model. Use it before tuning neural architectures. |
| Covariate-rich business forecasting with static IDs, known future covariates, unknown observed covariates, short or mixed-length histories | `TemporalFusionTransformer` | Strong default for heterogeneous covariates, variable selection, attention, quantile loss, and interpretation. | Larger and slower than simple baselines; start with small `hidden_size`, `attention_head_size=1`, and `log_interval=-1`. |
| Target-only univariate regression benchmark with trend/seasonality decomposition | `NBeats` | Efficient target-only architecture with trend/seasonality/generic stacks. | Requires one continuous target, fixed encoder/prediction lengths, no random length, no relative time index, and no covariates. |
| Target-only N-BEATS variant with KAN layers | `NBeatsKAN` | Same target-only use case as `NBeats`, with KAN blocks and optional grid updates during training. | Same strict dataset requirements as `NBeats`; use `GridUpdateCallback` only when intentionally training KAN grids. |
| Long-horizon forecasting where interpolation/downsampling is attractive | `NHiTS` | Designed for long horizons; supports covariates and is often efficient versus attention-heavy models. | Requires continuous targets and fixed encoder/prediction lengths; backcast loss is only compatible with point forecasts. |
| Probabilistic autoregressive forecasting over many related continuous series | `DeepAR` | Distribution-loss model; can return mean/quantile-style summaries or raw samples via `mode="samples"`. | Continuous targets only; sampling can make inference slower; distribution choice matters. |
| Simple recurrent LSTM/GRU baseline with covariates and target lags | `RecurrentNetwork` | Smaller autoregressive model that uses covariates and supports `cell_type="LSTM"` or `"GRU"`. | Continuous targets only; source assertions reject `QuantileLoss`; use point losses such as `MAE()` unless you have verified a compatible `MultiLoss`. |
| Forecast mostly driven by decoder-known future covariates or static covariates | `DecoderMLP` | MLP consumes decoder/static features and can be a quick covariate baseline. | It does not model encoder history like recurrent/attention models; future covariates must be valid for the prediction window. |
| Efficient MLP-style long-term forecasting with future/static covariates | `TiDEModel` | Encoder-decoder MLP architecture for long-term forecasting without attention. | Requires continuous targets and fixed encoder/prediction lengths. `.from_dataset()` fills `input_chunk_length` and `output_chunk_length`. |
| Transformer-style exogenous-variable modeling with patching | `TimeXer` | Reconciles endogenous and exogenous variables; supports `features="S"`, `"MS"`, or `"M"`, quantile loss, and optional efficient attention. | Import from `pytorch_forecasting.models`; `context_length >= patch_length`; `hidden_size` must be divisible by `n_heads`. |
| Experimental long-horizon extended-LSTM target-history model | `xLSTMTime` | Uses sLSTM/mLSTM-style recurrent blocks and decomposition. | Import from `pytorch_forecasting.models`; provide explicit `input_size`, `hidden_size`, and `output_size` in `.from_dataset()`; use tiny fixed-window target-only checks before relying on it. |
| v2 package-layer experimentation | `SOFTS` or `*_pkg_v2` classes | New package/data-module API surface. | Out of scope here; route to `../api-v2-workflows/SKILL.md`. |

## Covariate and multivariate guidance

- If you have meaningful static covariates and known future covariates, start with `TemporalFusionTransformer`, `NHiTS`, `DeepAR`, `RecurrentNetwork`, `TiDEModel`, or `TimeXer`; do not choose `NBeats`/`NBeatsKAN` unless the dataset is target-only.
- If the series are many related entities, prefer a global model that can learn cross-series patterns from group IDs and covariates. `TemporalFusionTransformer`, `DeepAR`, `RecurrentNetwork`, `TiDEModel`, `NHiTS`, and `TimeXer` are better fits than target-only N-BEATS variants.
- If you have one or very few series, deep models need long histories and careful validation. Keep a `Baseline` and a small recurrent or MLP model as controls.
- For multi-target forecasting, verify the loss and output-size behavior. `TemporalFusionTransformer` has the broadest documented support, while `DeepAR`, `NHiTS`, `TiDEModel`, and `TimeXer` have native tests for multi-target-style paths. Keep the first pass small and assertion-backed.
- Categorical targets are not universally supported. `TemporalFusionTransformer` can be configured for categorical or heterogeneous targets with appropriate losses; `DeepAR`, `RecurrentNetwork`, `NHiTS`, `TiDEModel`, and N-BEATS variants assert continuous/regression targets.

## Uncertainty guidance

| Need | Recommended path | Notes |
|---|---|---|
| Non-parametric quantile forecasts | `TemporalFusionTransformer(loss=QuantileLoss(), output_size=len(quantiles))`, `NHiTS(loss=QuantileLoss())`, `DecoderMLP(loss=QuantileLoss())`, or `TimeXer(loss=QuantileLoss(...))` | Use `predict(..., mode="quantiles")` or standard predictions depending on downstream format. Quantile details belong in metrics-and-tuning. |
| Parametric probabilistic forecasts | `DeepAR(loss=NormalDistributionLoss())` or another compatible distribution loss | Use `predict(..., mode="samples", n_samples=...)` for raw sample tensors or `mode="prediction"` for averaged predictions. |
| Multivariate distribution loss | `DeepAR` or tested model/loss pairs with the correct multivariate loss | `MQF2DistributionLoss` requires the optional `cpflows` dependency. If it is absent, use `QuantileLoss`, `NormalDistributionLoss`, or another installed loss. |
| Point forecast only | `Baseline`, `NBeats`, `NHiTS`, `RecurrentNetwork`, `TiDEModel`, or constrained `TimeXer` | Point losses are faster and easier to debug. Keep quantiles/distributions for tasks that need calibrated intervals or samples. |

## Long-horizon and fixed-window guidance

- Long encoder and decoder lengths can freeze or slow training. The FAQ warns against unrealistically large windows; use shorter windows first, then scale only after a smoke run passes.
- `NBeats`, `NBeatsKAN`, `NHiTS`, and `TiDEModel` require fixed encoder and prediction lengths: `min_encoder_length == max_encoder_length`, `min_prediction_length == max_prediction_length`, `randomize_length=None`, and `add_relative_time_idx=False`.
- `NBeats`/`NBeatsKAN` additionally require that the only real input is the target listed in `time_varying_unknown_reals`. They should not receive static, known, or unknown covariates beyond the target.
- `NHiTS` is the first model to consider when the horizon is long and you still need covariates.
- `TimeXer` patching makes `patch_length` a model-selection parameter, not just a tuning parameter. If `context_length` is shorter than `patch_length`, construction fails.

## Interpretation and explainability guidance

- `TemporalFusionTransformer` has the richest built-in interpretation path: request raw predictions with `mode="raw", return_x=True`, call `interpret_output(...)`, then plot with `plot_interpretation(...)` if matplotlib is installed.
- `NBeats` and `NHiTS` expose decomposition/interpretation-style plots when raw outputs are available and matplotlib is installed.
- All v1 `BaseModel` descendants share `plot_prediction(x, out, idx=...)` for raw outputs, subject to optional plotting dependencies.
- Disable logging plots during debugging with `log_interval=-1` and `log_val_interval=-1`; plotting dependencies should not block training or prediction.

## Selection algorithm for future agents

1. Run `Baseline().predict(...)` or `scripts/tiny_forecasting_smoke.py` first when the environment or dataloader is untrusted.
2. If the task has covariates and needs interpretability, choose `TemporalFusionTransformer` unless runtime budget strongly favors a smaller architecture.
3. If the task is target-only with fixed windows, compare `NBeats`, `NBeatsKAN`, and `xLSTMTime`; keep `NBeats` as the stable first pass.
4. If the horizon is long, test `NHiTS`; test `TiDEModel` when future covariates and efficiency matter.
5. If the task needs probabilistic samples, choose `DeepAR` and an installed distribution loss.
6. If the task needs a simple covariate baseline, choose `RecurrentNetwork` or `DecoderMLP` before escalating to transformer-style models.
7. If a model triggers a dataset assertion, do not force it; either change the model or return to the data-pipeline sub-skill and construct a compatible dataset variant.
