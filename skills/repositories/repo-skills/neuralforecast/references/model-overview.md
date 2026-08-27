# Model Overview

## Purpose

Read this when the user asks which NeuralForecast model family to use, how a
constructor differs from nearby models, or whether a model needs extra runtime
packages.

## The public model catalog

The package exports a broad mix of recurrent, decomposition, linear, transformer,
mixer, probabilistic, and multivariate architectures:

- Recurrent / recursive: `RNN`, `GRU`, `LSTM`, `DilatedRNN`, `DeepAR`.
- Classical / basis-style and decomposition: `NHITS`, `NBEATS`, `NBEATSx`,
  `DLinear`, `NLinear`, `DeepNPTS`, `TiDE`, `KAN`, `RMoK`.
- Transformer / attention family: `TFT`, `VanillaTransformer`, `Informer`,
  `Autoformer`, `FEDformer`, `PatchTST`, `iTransformer`, `TimeLLM`, `TimeXer`.
- Mixer / multivariate family: `MLPMultivariate`, `TSMixer`, `TSMixerx`,
  `SOFTS`, `SOFTSSharp`, `TimeMixer`, `XLinear`, `StemGNN`, `TimesNet`, `BiTCN`.
- Simple baseline: `MLP`.
- Hierarchical wrapper: `HINT`.
- Optional-dependency models: `TimeLLM`, `xLSTM`.

## Quick selection heuristics

| User need | Good family | Notes |
| --- | --- | --- |
| Fast baseline forecasting | `MLP`, `NLinear`, `DLinear` | Small, simple, and easy to debug. |
| Long-horizon decomposition-style forecasting | `NHITS`, `NBEATS`, `NBEATSx` | Common quickstart families. |
| Multivariate series with strong cross-series interaction | `MLPMultivariate`, `TSMixer`, `TSMixerx`, `StemGNN`, `TimeMixer`, `XLinear`, `SOFTS`, `SOFTSSharp`, `iTransformer`, `TimeXer` | Check `n_series` and exogenous support first. |
| Probabilistic or quantile forecasting | `DeepAR`, `NHITS`, `NBEATSx`, `TFT`, loss-based wrappers | Route to `probabilistic-losses` for the loss choice. |
| Exogenous variables matter | `RNN`, `GRU`, `LSTM`, `DilatedRNN`, `DeepAR`, `MLP`, `NHITS`, `NBEATSx`, `TFT`, `VanillaTransformer`, `Informer`, `Autoformer`, `FEDformer`, `BiTCN`, `TiDE`, `TSMixer`, `TSMixerx`, `xLSTM` | Some families do not accept exogenous covariates; verify before routing. |
| Hierarchical reconciliation | `HINT` | Requires a summing matrix `S` and a base model. |
| Optional LLM or xLSTM experimentation | `TimeLLM`, `xLSTM` | Need their extra dependencies; otherwise the module flags are off. |

## Signature patterns worth remembering

- Recurrent models often accept `input_size=-1`, `inference_input_size`, and
  `h_train` knobs that only make sense for recursive forecasting.
- Multivariate-first models usually require `n_series` at construction.
- `HINT(h, S, model, reconciliation, alias=None)` wraps another model instead of
  defining its own time-series backbone.
- Many families accept `futr_exog_list`, `hist_exog_list`, `stat_exog_list`, and
  categorical exogenous options, but not all do.

## Capability flags from source

The package source uses flags such as `EXOGENOUS_FUTR`, `EXOGENOUS_HIST`,
`EXOGENOUS_STAT`, `EXOGENOUS_CAT`, `MULTIVARIATE`, and `RECURRENT` to guard
unsupported combinations. The key routeing idea is simple: a model that lacks a
flag should not be recommended for that workflow.

Representative examples from source inspection:

- `DeepAR`, `RNN`, `GRU`, `LSTM`, `DilatedRNN`, `MLP`, `NHITS`, `NBEATSx`,
  `TFT`, `VanillaTransformer`, `Informer`, `Autoformer`, `FEDformer`, `BiTCN`,
  `TiDE`, `TSMixer`, `TSMixerx`, and `xLSTM` accept exogenous features.
- `DLinear`, `NLinear`, `NBEATS`, `PatchTST`, `iTransformer`, `SOFTS`,
  `SOFTSSharp`, `StemGNN`, `RMoK`, and `TimeLLM` are source-flagged as not
  taking some exogenous inputs; route users away from exogenous-heavy tasks.
- `RNN`, `GRU`, `LSTM`, `DilatedRNN`, and `DeepAR` are recurrent-oriented.
- `iTransformer`, `MLPMultivariate`, `SOFTS`, `SOFTSSharp`, `StemGNN`,
  `TimeMixer`, `TSMixer`, `TSMixerx`, `TimeXer`, and `XLinear` are multivariate
  or multivariate-first.

## Read next

- `api-reference.md` for constructor signatures.
- `workflows.md` for end-to-end model usage.
- `troubleshooting.md` for `n_series`, optional dependency, and exogenous errors.
