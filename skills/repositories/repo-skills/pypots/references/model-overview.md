# Model Overview

Read this file when you need to choose a PyPOTS model family before diving
into a task-specific route. The full, current model catalog is also available
from the bundled CLI command `pypots-cli model list`.

## High-Level Choice Guide

- **Fast, no-training baselines**: `Mean`, `Median`, `LOCF`, `Lerp`.
- **General neural imputation**: `SAITS`, `BRITS`, `MRNN`, `USGAN`, `TEFN`,
  `TimesNet`, `Transformer`, `iTransformer`, `PatchTST`, `Autoformer`, and
  the other deep imputation families.
- **Forecasting**: `BTTF`, `TEFN`, `TimeMixer`, `TimeLLM`, `FITS`, `CSDI`,
  `DLinear`, `GPT4TS`, `MOMENT`, `TimeMixerPP`, `MixLinear`, and related
  forecasting families.
- **Classification**: `Raindrop`, `TS2Vec`, `TimesNet`, `BRITS`, `CSAI`,
  `GRUD`, `SAITS`, `iTransformer`, `TEFN`, `PatchTST`, `Autoformer`, and
  `SeFT`.
- **Anomaly detection**: `TimesNet`, `TEFN`, `TimeMixer`, `Transformer`,
  `FiLM`, `SegRNN`, `ImputeFormer`, `PatchTST`, `DLinear`, `SAITS`, `iTransformer`,
  `Crossformer`, `Pyraformer`, `FEDformer`, `Informer`, `ETSformer`,
  `NonstationaryTransformer`, and `TimeMixerPP`.
- **Clustering**: `CRLI`, `VaDER`.
- **Representation**: `TS2Vec`.

The task subskills own the actual workflow details. Use this file to pick the
right route, then read the matching API, data-format, and troubleshooting
references.

## Task Families

### Imputation

Use imputation when the output should replace missing values in a partially
observed series.

Typical model families:

| Family | Examples | Notes |
| --- | --- | --- |
| Naive | `Mean`, `Median`, `LOCF`, `Lerp` | No training; good first smoke checks and quick baselines. |
| Standard neural nets | `SAITS`, `BRITS`, `MRNN`, `USGAN`, `CSAI`, `TEFN` | Train on `X`; often save checkpoints and TensorBoard logs. |
| Transformer/time-series backbones | `TimesNet`, `Transformer`, `iTransformer`, `PatchTST`, `Autoformer`, `FiLM`, `DLinear`, `SCINet`, `Reformer`, `Pyraformer`, `FEDformer`, `Informer`, `ETSformer`, `Crossformer`, `NonstationaryTransformer` | Use when you want a paper-backed backbone adapted for missing values. |
| Forecast/LLM-derived or foundation-style models | `TimeMixer`, `TimeLLM`, `GPT4TS`, `MOMENT`, `TimeMixerPP`, `TOTEM`, `TSLANet`, `TKAN`, `HELIX`, `FITS`, `FreTS`, `Koopa`, `MICN`, `TiDE`, `ImputeFormer`, `StemGNN`, `TRMF`, `GRUD`, `RevIN_SCINet`, `SegRNN` | Often need more parameter tuning or optional dependencies. |

Common output key: `imputation`.
Common helper: `impute()`.

### Forecasting

Use forecasting when the model predicts future timesteps and returns a series
for `X_pred`.

Typical model families:

| Family | Examples | Notes |
| --- | --- | --- |
| Probabilistic / matrix factorization | `BTTF` | Lightweight classical baseline; no training loop like the neural models. |
| Neural forecasters | `TEFN`, `TimeMixer`, `TimeMixerPP`, `TimesNet`, `Transformer`, `FITS`, `DLinear`, `MICN`, `SegRNN`, `FiLM`, `MixLinear`, `CSDI`, `GPT4TS`, `MOMENT`, `TimeLLM` | Use `X` plus `X_pred` inputs and evaluate against future targets. |

Common output key: `forecasting`.
Common helper: `forecast()`.

### Classification

Use classification when the output is a class or class probability for each
sample.

Typical model families:

| Family | Examples | Notes |
| --- | --- | --- |
| Specialized classifiers | `Raindrop`, `TS2Vec`, `CSAI`, `BRITS`, `GRUD`, `SAITS`, `TEFN` | Good default starting points for partially observed series classification. |
| Backbone-adapted models | `TimesNet`, `iTransformer`, `PatchTST`, `Autoformer` | Often reuse a time-series backbone plus the classification head. |

Common output keys: `classification_proba` and `classification`.
Common helpers: `predict_proba()` and `classify()`.

### Anomaly Detection

Use anomaly detection when the output marks anomalous timesteps or samples.

Typical model families:

| Family | Examples | Notes |
| --- | --- | --- |
| Backbone-adapted detectors | `TimesNet`, `TEFN`, `TimeMixer`, `Transformer`, `FiLM`, `SegRNN`, `DLinear`, `SAITS`, `iTransformer`, `PatchTST`, `Autoformer`, `Crossformer`, `Pyraformer`, `FEDformer`, `Informer`, `ETSformer`, `NonstationaryTransformer`, `TimeMixerPP` | Train with anomaly-rate-aware settings and evaluate with binary metrics. |

Common output key: `anomaly_detection`.
Common helper: `detect()`.

### Clustering

Use clustering when the output assigns each sample to an unsupervised cluster.

Typical model families:

| Family | Examples | Notes |
| --- | --- | --- |
| Clustering-specific models | `CRLI`, `VaDER` | `CRLI` can expose latent variables and uses two optimizers. |

Common output key: `clustering`.
Common helper: `cluster()`.

### Representation

Use representation learning when you need embeddings rather than labels.

Typical model families:

| Family | Examples | Notes |
| --- | --- | --- |
| Representation models | `TS2Vec` | Useful for downstream classifiers, anomaly detectors, and visual inspection. |

Common output key: `representation`.
Common helper: `represent()`.

## Optional Backend and Service Notes

- `Raindrop` relies on the `torch-geometric` stack. If those packages are
  missing, the model can be present in the package catalog but fail when you try
  to instantiate or train it.
- LLM-oriented paths such as `TimeLLM` may need extra tokenizer/model packages
  and model downloads in addition to the base PyPOTS install.
- `TimeSeriesAI` is exposed as a separate umbrella client in `pypots` but is
  not part of the local, fully verified task workflows in this skill.

## Use the CLI Catalog for Drift Checks

If you suspect the catalog has changed in a newer checkout, run:

```bash
pypots-cli model list
```

That command reflects the installed package and is a quick way to see current
model names per task.
