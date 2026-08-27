# Model Configuration Notes

## Use The Root Model Catalog First

`references/model-overview.md` lists the supported registry keys. Use this file for the extra shape and contract details that are easy to miss when building configs.

## NARX

NARX is one of the few Flow Forecast models whose config is intentionally explicit about lag structure.

Required / common keys:

- `n_time_series`: total input channels.
- `forecast_history`: encoder window length.
- `output_seq_len`: prediction length.
- `n_targets`: number of autoregressive targets.
- `n_target_lags`: past target steps to feed into the MLP.
- `n_exog_lags`: past exogenous steps to feed into the MLP.
- `hidden_size`, `num_hidden_layers`, `dropout`, `activation`.
- `probabilistic`: optional probabilistic output mode.

Rules:

- `n_target_lags` and `n_exog_lags` must be less than or equal to `forecast_history`.
- The first `n_targets` columns of `relevant_cols` are treated as the target block.
- Use `simple_decode` for the closed-loop inference path.

## Temporal Models

Informer-style and other temporal-feature models use `TemporalLoader`.

Common keys:

- `temporal_feats`: the explicit time-feature columns.
- `label_len`: decoder warm-up length.
- `forecast_history` / `forecast_length`.
- `relevant_cols` and `target_col`.

Notes:

- The loader splits temporal features from the main feature matrix.
- The validation path fills the decoder prefix using `label_len` when present.
- These models are much easier to debug when the time columns are already cleaned and sorted.

## Transformer Variants And Mixers

For `SimpleTransformer`, `CustomTransformerDecoder`, `TransformerXL`, `Informer`, `Crossformer`, `DLinear`, `NLinear`, `ITransformer`, `TSMixer`, and `TSMixerExt`, the exact constructor keys vary by family, but these rules hold broadly:

- Keep `forecast_history` aligned with the training loader.
- Keep `forecast_length` aligned with the evaluator and inference config.
- Make sure `n_time_series` or the equivalent input-dimension key matches the number of selected feature columns.
- When a decoder is involved, the target window and decoder prefix must match the config's `label_len`, `out_len`, or similar horizon key.

## DA-RNN

DA-RNN follows a separate Python-level path.

Use:

- `flood_forecast.preprocessing.preprocess_da_rnn.make_data()` to build the `TrainData` container.
- `flood_forecast.da_rnn.train_da.da_rnn()` to create the encoder/decoder pair and training config.
- `flood_forecast.da_rnn.train_da.train()` to fit the network.

Notes:

- There is no dedicated package CLI for DA-RNN in this repo.
- TensorBoard logging is optional but may require a compatible `tensorboard` install.
- Current snapshot caveat: `preprocess_da_rnn.make_data()` returns a `TrainData` object with `features` and `targets` fields, while `train_da.da_rnn()` expects the older `da_rnn.custom_types.TrainData` fields `feats` and `targs`. Use an adapter before training:

```python
from flood_forecast.da_rnn.custom_types import TrainData as DaTrainData
from flood_forecast.preprocessing.preprocess_da_rnn import make_data
from flood_forecast.da_rnn.train_da import da_rnn, train

raw = make_data("data.csv", target_col=["height"], test_length=3, relevant_cols=["temp", "precip"])
train_data = DaTrainData(raw.features, raw.targets)
config, model = da_rnn(train_data, n_targs=train_data.targs.shape[1])
train(model, train_data, config, n_epochs=1)
```

## Meta / Autoencoder Training

`meta_train.py` forces `forecast_length = 1` and uses `forward_params = {}`.

Use this path when:

- The model is `BasicAE` or another meta/autoencoding workflow.
- You want a representation-learning stage before downstream use.

## ODE And Physics Models

`ODEForecast` and the hydrology models need additional structure beyond a plain sequence model.

Important keys:

- `dynamics_params`: selects the dynamics class and constructor kwargs.
- `solver_params`: integration settings for `NeuralODE`.
- `encoder_hidden_dim` and `encoder_layers`.
- `time_step`: physical spacing between forecast steps.

For `HybridGR4Model`, the catchment embedding and the meteorological sequence are separate inputs.

## Classification And Variable-Length Training

- `GeneralClassificationLoader` rewrites `forecast_history` from `sequence_length` and uses `forecast_length = 1`.
- `VariableSequenceLength` uses `series_marker_column` and `task` to decide how to turn grouped examples into batches.
- These loaders do not follow the same evaluation shape as forecasting loaders.

## Transfer Learning And Resume

- `weight_path` loads a state dict before training.
- `weight_path_add["excluded_layers"]` drops layers from the checkpoint before load.
- `weight_path_add["frozen_layers"]` freezes the named modules after load.

## Validation Hint

If a model config is structurally correct but instantiation fails, compare the exact constructor in the source or the root model catalog. The easiest mismatch to miss is a loader/model pair that expects different horizon semantics.
