# Model Overview

## Purpose

Read this before choosing a `model_name`, loss, optimizer, scaler, decoder, or model family in Flow Forecast. The package is a registry-driven time-series framework: a few config strings determine which model class, criterion, optimizer, scaler, and decoding path are constructed at runtime.

## Core Registry Facts

- The primary registry lives in `flood_forecast.model_dict_function`.
- The high-level wrapper `flood_forecast.time_model.PyTorchForecast` looks up `params["model_name"]` in `pytorch_model_dict` and builds the matching class.
- The trainer uses `params["model_type"]` to choose the PyTorch path versus the DA-RNN path.
- `params["wandb"]` is expected to be `False` or a mapping; a bare `True` is not a valid config shape for this package.

## Supported `model_name` Values

The table below summarizes the keys observed in `pytorch_model_dict` and the major shape/config notes that matter most to users.

| Model name | Class | Family / use | Important config notes |
|---|---|---|---|
| `MultiAttnHeadSimple` | `flood_forecast.transformer_xl.multi_head_base.MultiAttnHeadSimple` | Lightweight attention baseline | Uses `number_time_series` / `n_time_series`; common starting point for training tests. |
| `SimpleTransformer` | `flood_forecast.transformer_xl.transformer_basic.SimpleTransformer` | Classic transformer encoder-decoder | Often uses `seq_length`, `n_heads`, `d_model`, `number_time_series`. |
| `TransformerXL` | `flood_forecast.transformer_xl.transformer_xl.TransformerXL` | Transformer-XL style sequence model | Expect transformer-style sequence inputs and larger memory/attention config. |
| `DummyTorchModel` | `flood_forecast.transformer_xl.dummy_torch.DummyTorchModel` | Smoke / minimal harness | Useful for environment checks and loader plumbing, not a real forecasting baseline. |
| `LSTM` | `flood_forecast.basic.lstm_vanilla.LSTMForecast` | Vanilla recurrent baseline | Shape-driven model; common in basic training configs. |
| `SimpleLinearModel` | `flood_forecast.basic.linear_regression.SimpleLinearModel` | Small linear baseline | Often paired with `simple_decode` for closed-loop rollout. |
| `CustomTransformerDecoder` | `flood_forecast.transformer_xl.transformer_basic.CustomTransformerDecoder` | Transformer decoder variant | Typical config uses `seq_length`, `n_time_series`, decoder length controls, and optional target forcing. |
| `DARNN` | `flood_forecast.da_rnn.model.DARNN` | Dual-stage attention RNN | Requires DA-RNN preprocessing via `preprocess_da_rnn.make_data` and `da_rnn/train_da.py` for the native training path. |
| `DecoderTransformer` | `flood_forecast.transformer_xl.transformer_bottleneck.DecoderTransformer` | Bottleneck / decoder-centric transformer | Often appears in series-id and multi-step configs. |
| `BasicAE` | `flood_forecast.meta_models.basic_ae.AE` | Autoencoder / meta representation | Used by `meta_train.py`; `forecast_length` is forced to 1 in the meta-training path. |
| `Informer` | `flood_forecast.transformer_xl.informer.Informer` | Efficient long-sequence transformer | Usually needs `TemporalLoader`, temporal features, and `label_len` / `out_len` / `factor` settings. |
| `DSANet` | `flood_forecast.transformer_xl.dsanet.DSANet` | Dual self-attention network | Often used with long sequences and attention-specific configs. |
| `VanillaGRU` | `flood_forecast.basic.gru_vanilla.VanillaGRU` | GRU baseline | Simpler recurrent alternative to LSTM. |
| `DLinear` | `flood_forecast.basic.d_n_linear.DLinear` | Linear decomposition model | Common in short smoke configs with simple loader shapes. |
| `Crossformer` | `flood_forecast.transformer_xl.cross_former.Crossformer` | Cross-dimension transformer | Strongly shape-sensitive; segment-length and dimensional config matter. |
| `NLinear` | `flood_forecast.basic.d_n_linear.NLinear` | Linear baseline | Similar workflow to DLinear. |
| `TSMixer` | `torchtsmixer.TSMixer` | Mixer family | Requires the external `pytorch-tsmixer` distribution. |
| `TSMixerExt` | `torchtsmixer.TSMixerExt` | Extended mixer family | Also requires `pytorch-tsmixer`. |
| `ITransformer` | `flood_forecast.transformer_xl.itransformer.ITransformer` | Inverted transformer | Sequence/feature ordering matters. |
| `CrossVIVIT` | `flood_forecast.multi_models.crossvivit.RoCrossViViT` | Multimodal video/vision transformer | Needs `einops` and `jaxtyping`; used in multimodal workflows. |
| `NARX` | `flood_forecast.basic.narx.NARX` | Nonlinear autoregressive model | Uses `n_target_lags`, `n_exog_lags`, `output_seq_len`, `probabilistic`; good fit for the bundled smoke helper. |
| `NeuralODE` | `flood_forecast.ode.neural_ode.ODEForecast` | Encoder-ODE-decoder model | Uses `dynamics_params`, `solver_params`, and `forecast_length`; `torchdiffeq` required. |

## Common Config Keys

### Top-level keys

- `model_name`: registry key above.
- `model_type`: usually `"PyTorch"`; `trainer.py` also handles `"da_rnn"`.
- `model_params`: constructor kwargs for the chosen model.
- `dataset_params`: loader and split settings.
- `training_params`: optimizer, criterion, epochs, batch size, and optimizer kwargs.
- `inference_params`: forecast window, test path, decoder settings, and evaluation-specific options.
- `metrics`: list of metric names passed through `make_criterion_functions`.
- `wandb`: `False` or a mapping with `project`, `name`, and `tags`.
- `weight_path`: optional checkpoint path for loading pretrained weights.
- `weight_path_add`: optional freeze / excluded-layer settings for transfer learning.

### Common `model_params` patterns

| Pattern | Typical keys | Notes |
|---|---|---|
| Generic sequence models | `n_time_series`, `seq_len`, `forecast_history`, `forecast_length`, `number_time_series` | Most baseline and transformer-family models use some combination of these keys. |
| Decoder-based models | `output_seq_len`, `out_len`, `label_len`, `dec_in`, `c_out` | Ensure the decoder horizon matches the forecast length expected by the loader and evaluator. |
| Temporal-feature models | `factor`, `d_model`, `n_heads`, `e_layers`, `d_layers` | Informer/Crossformer/transformer variants need feature- and attention-specific dimensions. |
| NARX | `n_targets`, `n_target_lags`, `n_exog_lags`, `hidden_size`, `num_hidden_layers`, `dropout`, `activation`, `probabilistic` | `n_target_lags` and `n_exog_lags` must not exceed `forecast_history`. |
| ODE / physics models | `dynamics_params`, `solver_params`, `encoder_hidden_dim`, `time_step` | `dynamics_params["type"]` selects a registered ODE right-hand side. |
| Multimodal models | `image_size`, `image_channels`, `static_features`, `history_features`, `history_len`, `patch_size`, `embedding_dim`, `fusion` | See the multimodal-physics sub-skill for catchment and GR4 workflows. |

## Criterion / Optimizer / Scaler Registries

### Criteria

`pytorch_criterion_dict` includes the most common names used in configs:

- `MSE`, `SmoothL1Loss`, `PoissonNLLLoss`, `RMSE`, `MAPE`, `DilateLoss`, `L1`, `PenalizedMSELoss`, `CrossEntropyLoss`, `NegativeLogLikelihood`, `BCELossLogits`, `FocalLoss`, `QuantileLoss`, `BinaryCrossEntropy`, `GaussianLoss`, `MASELoss`.

### Optimizers

`pytorch_opt_dict` supports:

- `Adam`, `SGD`, `BertAdam`.

### Scalers

`scaler_dict` includes:

- `StandardScaler`, `RobustScaler`, `MinMaxScaler`, `MaxAbsScaler`.

### Decoders

`decoding_functions` includes:

- `simple_decode`, `greedy_decode`.

### Interpolation helpers

`interpolate_dict` includes:

- `back_forward`, `back_forward_generic`, `forward_back_generic`.

## Optional Dependency Notes

| Dependency | Used by | What fails without it |
|---|---|---|
| `einops` | CrossViViT, catchment encoders, some transformer utilities | Import failures for multimodal and some transformer modules. |
| `pytorch-tsmixer` | `TSMixer`, `TSMixerExt` | `model_dict_function` import or TSMixer model construction fails. |
| `torchdiffeq` | `NeuralODE`, `ODEForecast`, GR4/hybrid physics models | ODE import and integration fail. |
| `jaxtyping` | CrossViViT annotations and some tensor-shape helpers | Multimodal model import may fail. |
| `wandb` | Training/inference logging | `PyTorchForecast`/`InferenceMode` import or runtime logging may fail if the package is missing or incompatible. |
| `google-cloud-storage` | GCS download/upload helpers | GCS paths and uploads fail. |
| `shap` / `plotly` | Explainability and plots | SHAP summaries or confidence-interval figures fail. |
| `tensorboard` | DA-RNN tensorboard logging path | `SummaryWriter` imports or tensorboard logging fail. |
| `numba` | DILATE loss | `DilateLoss` import/runtime fails. |

## Shape And Workflow Caveats

- `CSVDataLoader` uses `forecast_history` for the input window and `forecast_length` for the target window.
- `TemporalLoader` depends on `feature_param["datetime_params"]` and usually needs `sort_column` to be a real datetime column.
- `CSVSeriesIDLoader` expects a series-id column and returns dictionaries keyed by series index.
- `GeneralClassificationLoader` and `VariableSequenceLength` are not forecasting loaders; their configs differ from the default CSV loader.
- `PyTorchForecast` sets up the device before loading the model, so device-related failures often happen early.
- `load_model` and `InferenceMode` expect saved weights and config structures to match the runtime registry names exactly.
- `ODEForecast` and the GR4/hybrid models are sensitive to forcing shape, parameter shape, and time-grid consistency.

## Where To Read Next

- [training](../sub-skills/training/SKILL.md) for config-driven fit/resume/eval workflows.
- [inference](../sub-skills/inference/SKILL.md) for saved-model prediction and plotting.
- [multimodal-physics](../sub-skills/multimodal-physics/SKILL.md) for catchment embeddings and hydrology models.
- [data-preparation](../sub-skills/data-preparation/SKILL.md) for loader and preprocessing details.
