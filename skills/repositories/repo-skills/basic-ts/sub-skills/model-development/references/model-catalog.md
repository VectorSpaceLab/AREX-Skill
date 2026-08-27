# BasicTS Model Catalog

## Purpose

Use this reference to choose a built-in BasicTS model family and to find the public import names that the installed package exposes.

## Multi-task families

These families expose task-specific wrappers for forecasting, classification, and/or reconstruction.

| Family | Public imports | Notes |
| --- | --- | --- |
| `iTransformer` | `iTransformerBackbone`, `iTransformerForForecasting`, `iTransformerForClassification`, `iTransformerForReconstruction`, `iTransformerConfig` | One of the most explicit multi-task families in the package. |
| `PatchTST` | `PatchTSTBackbone`, `PatchTSTForForecasting`, `PatchTSTForClassification`, `PatchTSTForReconstruction`, `PatchTSTConfig` | Patch-based transformer with wrappers for all three core tasks. |
| `TimesNet` | `TimesNetBackbone`, `TimesNetForForecasting`, `TimesNetConfig` | Forecasting wrapper is exported in the installed package; the backbone is shared internally. |
| `NonstationaryTransformer` | `NonstationaryTransformerBackbone`, `NonstationaryTransformerForForecasting`, `NonstationaryTransformerForClassification`, `NonstationaryTransformerForReconstruction`, `NonstationaryTransformerConfig` | Multi-task non-stationary transformer family. |

## Forecasting-first families

These families are primarily used for forecasting runs. Some may also be used in task-specific wrappers or specialized research settings.

| Family | Public imports | Notes |
| --- | --- | --- |
| `Autoformer` | `Autoformer`, `AutoformerConfig` | Decomposition transformer family. |
| `Crossformer` | `Crossformer`, `CrossformerConfig` | Cross-dimension dependency modeling. |
| `DLinear` | `DLinear`, `DLinearConfig` | Simple baseline, good for CPU smoke tests. |
| `DUET` | `DUET`, `DUETConfig` | Used in smoke tests and auxiliary-loss examples. |
| `FITS` | `FITS`, `FITSConfig` | Frequency/interpolation-oriented model family. |
| `FiLM` | `FiLM`, `FiLMConfig` | Frequency improved Legendre memory model family. |
| `FreTS` | `FreTS`, `FreTSConfig` | Frequency-domain forecasting family. |
| `HI` | `HI`, `HIConfig` | Historical inertia baseline. |
| `Informer` | `Informer`, `InformerConfig` | Classic long-sequence forecasting transformer. |
| `Koopa` | `Koopa`, `KoopaConfig` | Non-stationary dynamics family with callback support in the source tree. |
| `Leddam` | `Leddam`, `LeddamConfig` | Forecasting family with its own architecture/config subtree. |
| `LightTS` | `LightTS`, `LightTSConfig` | Lightweight forecasting family. |
| `MTSMixer` | `MTSMixer`, `MTSMixerConfig` | Mixer-style multivariate forecasting family. |
| `NLinear` | `NLinear`, `NLinearConfig` | Linear baseline family. |
| `SOFTS` | `SOFTS`, `SOFTSConfig` | Series-core fusion forecasting family. |
| `STID` | `STID`, `STIDConfig` | Strong smoke-test family for spatial-temporal forecasting. |
| `SegRNN` | `SegRNN`, `SegRNNConfig` | Segment-based recurrent forecasting family. |
| `SparseTSF` | `SparseTSF`, `SparseTSFConfig` | Sparse forecasting family. |
| `StemGNN` | `StemGNN`, `StemGNNConfig` | Graph-based multivariate forecasting family. |
| `TiDE` | `TiDE`, `TiDEConfig` | Dense encoder family for forecasting. |
| `TimeKAN` | `TimeKAN`, `TimeKANConfig` | KAN-style time-series family. |
| `TimeMixer` | `TimeMixerBackBone`, `TimeMixerForForecasting`, `TimeMixerConfig` | Exported backbone name is spelled `TimeMixerBackBone` in the package. |
| `TimeXer` | `TimeXer`, `TimeXerConfig` | Exogenous-variable forecasting family. |
| `Timer` | `Timer`, `TimerConfig` | Forecasting family with its own config package. |

## How to choose quickly

- **Need a safe CPU smoke baseline**: start with `DLinear`.
- **Need classification**: use a family that exports `*ForClassification` or a model tested in the classification smoke suite, such as `iTransformerForClassification` or `PatchTSTForClassification`.
- **Need imputation/reconstruction**: use a family that exports `*ForReconstruction`, such as `iTransformerForReconstruction` or `PatchTSTForReconstruction`.
- **Need timestamps or richer covariates**: prefer a family and config that explicitly exposes timestamp or auxiliary arguments, such as `TimesNetConfig` or `iTransformerConfig`.

## Verified source signals

- Public model exports were read from `src/basicts/models/*/__init__.py`.
- A CPU smoke suite exists under `tests/smoke_test/` for several of the families above.
- Installed-package inspection confirmed the public config signatures and the presence of the launcher/model imports used in the smoke tests.

## Notes for future agents

- Always match the family to the task wrapper instead of importing the raw backbone when a task-specific wrapper exists.
- When in doubt, inspect the model's public `__init__.py` and config class before writing a custom model contract.
- Keep model selection separate from data-layout questions; dataset file shapes are covered in `data-preparation`.
