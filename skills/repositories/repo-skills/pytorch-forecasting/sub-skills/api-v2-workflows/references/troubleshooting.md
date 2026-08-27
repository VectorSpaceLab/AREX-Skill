# API-v2 Troubleshooting

API-v2 is beta in PyTorch Forecasting 1.8.0. Treat failures as likely API instability or metadata/config mismatch first. For stable production workflows, use the v1 data and model sub-skills instead.

## First triage

1. Confirm the user really wants API-v2. If they did not ask for beta/v2, route to v1.
2. Confirm the D1 dataset metadata with `dataset.get_metadata()`.
3. Confirm the D2 datamodule metadata before model construction.
4. Confirm the model/package is paired with the correct datamodule family.
5. Reduce to CPU, small batch size, short epochs, and no checkpointing until wiring works.

## Common symptoms and fixes

| Symptom or signal | Likely cause | Concrete fix |
|---|---|---|
| User asks for stable production forecasting but mentions `TimeSeries` or v2 snippets. | API-v2 is beta and not the production path. | Explain the stability difference; route stable work to v1 `TimeSeriesDataSet` and v1 model workflows. Use API-v2 only if explicitly requested for experimentation. |
| `KeyError: 'max_encoder_length'`, `'encoder_cont'`, `'decoder_cont'`, or static-feature metadata keys when constructing `TFT`, `Samformer`, `TIDE`, `DecoderMLP_v2`, or `SOFTS`. | Model expects `EncoderDecoderTimeSeriesDataModule.metadata`, but metadata is missing or came from `TslibDataModule`. | Build `EncoderDecoderTimeSeriesDataModule`, validate `dm.metadata`, then pass `metadata=dm.metadata`. Do not pass D1 `dataset.get_metadata()` directly to M-layer models. |
| `context_length`/`prediction_length` are zero or Tslib model shapes are invalid. | `DLinear` or `TimeXer` did not receive `TslibDataModule.metadata`, or Tslib config used encoder/decoder key names. | Use `TslibDataModule` with `context_length` and `prediction_length`; pass `metadata=tslib_dm.metadata`. For package wrappers use `DLinear_pkg_v2` or `TimeXer_pkg_v2` with Tslib config keys. |
| Datamodule builds but train/val/predict windows are empty. | Series are shorter than the requested history+horizon, or the split leaves too few series for the stage. | Ensure each series has at least `max_encoder_length + max_prediction_length` or `context_length + prediction_length` rows. Increase number of groups or adjust `train_val_test_split`, window lengths, and `window_stride`. |
| `TypeError` from `TimeSeries` tensor conversion, often with object/string categories. | The D1 layer converts raw DataFrame feature arrays to tensors before mature categorical preprocessing. | Numeric-code categorical columns for beta experiments and list them in `cat=[...]`. Keep target numeric for the covered v2 models. |
| Known-future variables are missing from decoder/future inputs. | The column was not included in D1 `known=[...]`, or its name differs between DataFrame and config. | Check `dataset.get_metadata()["col_known"]`; use exact column names. Encoder/decoder `decoder_cont`/`decoder_cat` and Tslib `future_*` inputs only include known features. |
| Static features are counted incorrectly. | Static columns were omitted from `static=[...]`, or categorical/static type lists are inconsistent. | Include static numeric columns in `static=[...]` and `num=[...]`; include static categorical columns in `static=[...]` and `cat=[...]`. Then recheck `static_categorical_features` and `static_continuous_features` in metadata. |
| `pkg.predict()` raises `RuntimeError: Model is not initialized`. | Package was created without `ckpt_path` and prediction was called before `fit()` built the model from datamodule metadata. | Call `pkg.fit(..., save_ckpt=False)` first, or instantiate the package with a valid checkpoint path and sidecar metadata artifacts. |
| `datamodule_cfg must be provided to build a datamodule`. | A P-layer package received D1 data but no `datamodule_cfg`. | Supply the correct `datamodule_cfg` for the package's internal D2 datamodule. For D1 input the package cannot infer lengths/batch settings safely. |
| `TypeError: __init__() got an unexpected keyword argument ...` for a model. | Config key belongs to another model/datamodule family or to a tutorial typo. | Check model-specific keys. Examples: `TimeXer` uses `n_heads`, not `nhead`; `TIDE` uses `optim`, `optim_config`, `scheduler_config`, not the standard optimizer key names; Tslib uses `context_length`, not `max_encoder_length`. |
| `return_info` warning for an unknown key. | The prediction callback recognizes only selected keys. | Use `return_info=["x"]`, `return_info=["decoder_lengths"]`, or the documented experimental keys `"y"` and `"index"` only after confirming batch structure. |
| `return_info=["index", "y"]` fails with a custom dataloader. | API-v2 prediction callback expects specific batch tuple structure, and custom or current beta dataloaders may not provide the expected index/y payload. | Retry with `return_info=["x"]`; inspect one prediction batch; adapt the dataloader or collect index columns externally from the D1 DataFrame. |
| `mode="quantiles"` fails or returns unexpected shape. | Loss does not implement quantile conversion, or model output/loss pairing is not quantile-aware. | Use `QuantileLoss` in `model_cfg` for quantile experiments, validate `mode="raw"` first, then retry `mode="quantiles"`. |
| Package checkpoint reload cannot find configs/metadata. | Reload expects sidecar artifacts saved next to the best checkpoint. | Use package `fit(save_ckpt=True)` so `model_cfg.pkl`, `datamodule_cfg.pkl`, and `metadata.pkl` are saved alongside the checkpoint; keep the same package class for reload. |
| Import error for `lightning`, `pandas`, `scikit-learn`, or torch. | Core package dependencies are absent from the current Python environment. | Install/activate an environment with `pytorch-forecasting` core dependencies. API-v2 smoke checks do not require CUDA/GPU. |
| Optuna or matplotlib import errors during an API-v2 experiment. | Optional packages are not part of a minimal core install. | Do not add tuning/plotting unless the task needs them. API-v2 data/model wiring can be validated without Optuna or matplotlib. |

## Metadata mismatch checklist

When model construction fails, print these before changing model code:

```python
print(dataset.get_metadata())
print(type(data_module).__name__)
print(data_module.metadata)
```

Expected metadata family:

- Encoder/decoder models need keys such as `encoder_cat`, `encoder_cont`, `decoder_cat`, `decoder_cont`, `target`, `max_encoder_length`, and `max_prediction_length`.
- Tslib models need keys such as `feature_names`, `feature_indices`, `n_features`, `context_length`, `prediction_length`, and `features`.

If the keys are from the other family, rebuild the datamodule rather than patching the model.

## Config key sanity checks

Use these rules when converting a user's v1 or pseudocode request:

- D1 `TimeSeries`: `time`, `target`, `group`, `num`, `cat`, `known`, `unknown`, `static`.
- `EncoderDecoderTimeSeriesDataModule`: `max_encoder_length`, `max_prediction_length`, optional min lengths, normalizers/scalers, `batch_size`, `train_val_test_split`.
- `TslibDataModule`: `context_length`, `prediction_length`, `freq`, `window_stride`, normalizers/scalers, `batch_size`, `train_val_test_split`.
- P-layer package: `datamodule_cfg`, `model_cfg`, `trainer_cfg`, optional `ckpt_path`.
- `trainer_cfg` is for `lightning.pytorch.Trainer`; do not put model constructor keys there.
- `model_cfg` is for the M-layer constructor; do not put D2 length keys there unless the model source actually accepts them.

## Safer `return_info` workflow

1. Start with no `return_info` and `mode="raw"`.
2. If raw output contains `"prediction"`, try `mode="prediction"`.
3. Add `return_info=["x"]` for batch inspection.
4. Add `return_info=["decoder_lengths"]` only for encoder/decoder batches.
5. Treat `"index"` and `"y"` as experimental; if they fail, collect those values from your original DataFrame or dataloader wrapper.

## When to stop using API-v2

Stop and route to v1 if:

- The user requires a production-stable pipeline.
- The model/datamodule pair needs unsupported categorical target handling.
- The task depends on undocumented or changing beta internals.
- The requested failure fix would require modifying v2 source code rather than adjusting configs, metadata, or datamodule pairing.
