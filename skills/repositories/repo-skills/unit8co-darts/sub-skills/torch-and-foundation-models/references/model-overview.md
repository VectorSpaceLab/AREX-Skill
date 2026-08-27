# Torch and foundation model overview

## Darts torch model families

| Family | Examples | Notes |
| --- | --- | --- |
| Recurrent/sequence | `RNNModel`, `BlockRNNModel` | Require chunk/sequence configuration and `darts[torch]`. |
| Convolution/transformer | `TCNModel`, `TransformerModel` | Good for tiny CPU smoke with short chunks. |
| Deep forecasting architectures | `NBEATSModel`, `NHiTSModel`, `TFTModel`, `TiDEModel`, `DLinearModel`, `NLinearModel`, `TSMixerModel`, `PatchTSTModel` | Often global models; covariate support differs by class. |
| Classification torch models | Darts classifier model families | Route metric selection carefully; classification metrics differ from forecast metrics. |

Use core `forecasting-workflows` when the user asks for non-neural baselines or forbids torch.

## Foundation and external wrappers

| Wrapper/family | Extra requirements | Safety notes |
| --- | --- | --- |
| Chronos/Chronos2-style wrappers | torch stack, Hugging Face/model weights/cache | May download weights; require local cache or approved network. |
| TimesFM/TimesFM2.5-style wrappers | wrapper-specific packages and weights | Treat memory/cache as required evidence before construction. |
| `NeuralForecastModel` | `neuralforecast>=3.0.0` | Not included in the baseline verified environment. |
| `TiRexModel` | `tirex-ts>=1.4.0` | Not included in the baseline verified environment. |

Do not silently instantiate foundation wrappers in a no-network environment. First check whether the user provided local model/cache paths and whether optional packages are installed.

## Model choice handoff

- Need a quick sanity forecast: use core baselines in `forecasting-workflows`.
- Need neural training with custom covariates: validate data/covariate spans first, then select a torch model here.
- Need foundation inference: confirm cache/download and memory, then use the wrapper-specific API after import inspection in the target environment.
- Need metrics/reporting: route to `evaluation-and-explainability`.

## What was verified

Baseline verification covered `TCNModel` construction and one tiny CPU training run. It did not verify every torch architecture, every covariate combination, GPU execution, foundation wrappers, or external wrapper packages.
