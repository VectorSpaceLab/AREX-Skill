# Model Troubleshooting Guide

Use this guide when PyTorch Forecasting v1 model construction, Lightning training, prediction, checkpointing, plotting, or interpretation fails. First prove the data path with `Baseline().predict(...)` or the bundled `scripts/tiny_forecasting_smoke.py`; then isolate model-specific issues.

## Fast triage sequence

1. **Environment**: can Python import `torch`, `lightning.pytorch`, `pandas`, and `pytorch_forecasting`?
2. **Dataloader**: can `Baseline().predict(val_loader, fast_dev_run=True)` return output?
3. **Dataset/model compatibility**: does `.from_dataset(training, ...)` fail before training? If yes, read the assertion and choose a compatible model or rebuild the dataset.
4. **One-batch CPU fit**: can a tiny model train with `accelerator="cpu"`, `limit_train_batches=1`, `limit_val_batches=1`, and `num_workers=0`?
5. **Prediction flags**: can the fitted or loaded model run `predict(..., fast_dev_run=True, return_index=True, return_decoder_lengths=True)`?
6. **Scale up slowly**: only after the above pass should you raise model size, batch size, epochs, dataloader workers, GPU usage, or hyperparameter tuning.

## Symptom-to-fix table

| Symptom | Likely cause | Concrete fixes |
|---|---|---|
| Training appears frozen while CPU/GPU is busy | Model too large, encoder/decoder windows too long, dataloader workers bottleneck, index construction from missing timesteps, or heavy logging/plotting | Print `model.size()`; reduce `hidden_size`, layers, encoder length, prediction length, and batch size; set `num_workers=0`; disable plots with `log_interval=-1`; debug with `limit_train_batches=1`; avoid `allow_missing_timesteps=True` unless needed. |
| `.from_dataset()` raises an assertion for `NBeats` or `NBeatsKAN` | Dataset is not target-only or fixed-window | Rebuild dataset with one continuous target, `time_varying_unknown_reals=[target]`, no covariates, `min_encoder_length=max_encoder_length`, `min_prediction_length=max_prediction_length`, `randomize_length=None`, `add_relative_time_idx=False`, and `add_target_scales=False`; otherwise choose `NHiTS` or `TemporalFusionTransformer`. |
| `.from_dataset()` raises fixed-length assertions for `NHiTS` or `TiDEModel` | Variable encoder/prediction lengths or randomized lengths | Use a fixed-window dataset variant or choose a model that accepts variable lengths such as `TemporalFusionTransformer`, `DeepAR`, or `RecurrentNetwork`. |
| `RecurrentNetwork` rejects `QuantileLoss` | Source assertions disallow quantile loss for recurrent network output | Use `MAE()`, `SMAPE()`, or another verified point loss; choose `TemporalFusionTransformer`, `NHiTS`, `DecoderMLP`, or `TimeXer` for quantile forecasts. |
| `DeepAR` rejects target normalizer / categorical target | DeepAR expects continuous targets and distribution losses | Use continuous target columns and a numeric target normalizer; for categorical or heterogeneous targets, evaluate `TemporalFusionTransformer` with compatible losses. |
| `TimeXer` construction fails with patch or attention errors | `context_length < patch_length` or `hidden_size` not divisible by `n_heads` | Set `patch_length <= training.max_encoder_length`; choose `hidden_size` as a multiple of `n_heads`; start with `hidden_size=64`, `n_heads=4`, `e_layers=1`. |
| `xLSTMTime.from_dataset()` errors on missing sizes | The class expects explicit shape hyperparameters | Pass `input_size`, `hidden_size`, and `output_size` explicitly; use target-only fixed-window smoke tests before using it in production. |
| Lightning says no best checkpoint path exists | Checkpointing disabled or `fit()` did not complete validation | Set `enable_checkpointing=True`, provide `val_dataloaders`, and run `trainer.fit()` successfully before reading `trainer.checkpoint_callback.best_model_path`. |
| `predict()` returns a tensor when code expects `.output` | No `return_*` flag was set | Set at least one of `return_index=True`, `return_decoder_lengths=True`, `return_x=True`, or `return_y=True` to get a `Prediction` tuple-like object. |
| `predict()` writes files but returns no useful object | `output_dir` was set | Treat prediction files as the output and do not access `.output`; remove `output_dir` for in-memory predictions. |
| `mode="raw"` output shape is nested or not a tensor | Raw network output is a model-specific dictionary/tuple | Inspect `raw.output` keys/fields; use `mode=("raw", "prediction")` only if the model's raw output has a `prediction` field. |
| `DeepAR` prediction is slow | Probabilistic sampling multiplies inference work | Lower `n_samples` for debugging; use `mode="prediction"` when raw samples are not required. |
| Loss diverges or becomes NaN | Learning rate too high, target scale unsuitable, distribution/loss mismatched to target, invalid target values, or no gradient clipping | Lower `learning_rate` by 10x; add or revise `target_normalizer`; use `gradient_clip_val=0.1`; check target NaNs/infinities; switch to a simpler point loss; run one-batch CPU fit. |
| LR finder never finishes | `fast_dev_run=True`, artificial batch limits, poor target normalization, or early stop threshold too low | Do not use `fast_dev_run` for LR finder; set `limit_train_batches=1.0`; use a target normalizer; set `early_stop_threshold=1000.0`; set model `log_interval=-1`. |
| Matplotlib warnings during LR finder or training | Plot logging without a plotting backend/logger | Set `log_interval=-1` and `log_val_interval=-1`; install matplotlib only if plots are required; skip `result.plot(...)` and use `result.suggestion()`. |
| `LearningRateMonitor` errors about logger | Trainer logger disabled or unavailable | Remove `LearningRateMonitor()` or enable a Lightning logger. Keep `logger=False` only for minimal smoke/debug runs. |
| TensorBoard logger import/setup fails | Optional logging dependency absent | Use Lightning's default logger, a simple CSV logger, or `logger=False`; do not let TensorBoard block model verification. |
| `MQF2DistributionLoss` import or training fails | Optional `cpflows` extra absent or incompatible | Use `QuantileLoss()` or another installed loss; install the optional dependency only when the task explicitly requires MQF2. |
| CUDA/GPU behavior differs from CPU | Device-specific kernel, memory, or attention backend issue | Reproduce with `trainer_kwargs={"accelerator": "cpu"}`; lower batch/model size; for `TimeXer`, disable `use_efficient_attention` while isolating; CPU is sufficient for selected skill smoke checks. |

## Dataset/model compatibility checks

Before constructing the model, write down these facts from the `TimeSeriesDataSet`:

```python
print(training.target)
print(training.max_encoder_length, training.min_encoder_length)
print(training.max_prediction_length, training.min_prediction_length)
print(training.reals)
print(training.flat_categoricals)
print(training.randomize_length)
print(training.add_relative_time_idx)
```

Interpret them as follows:

- If `flat_categoricals` or extra real covariates are present, do not use `NBeats`/`NBeatsKAN`.
- If min/max lengths differ, do not use `NBeats`, `NBeatsKAN`, `NHiTS`, or `TiDEModel` without rebuilding a fixed-window dataset.
- If the target is categorical, avoid `DeepAR`, `RecurrentNetwork`, `NHiTS`, `TiDEModel`, and N-BEATS variants.
- If future-known covariates are missing for the decoder window, covariate-heavy models may construct but learn misleading relationships; fix the data-pipeline first.
- If multi-target is used, ensure the chosen loss is a `MultiLoss` or another model-compatible multi-target loss and that `output_size` matches the loss output contract.

## Debug trainer snippets

### CPU one-batch fit

```python
trainer = pl.Trainer(
    max_epochs=1,
    accelerator="cpu",
    devices=1,
    gradient_clip_val=0.1,
    limit_train_batches=1,
    limit_val_batches=1,
    num_sanity_val_steps=0,
    enable_checkpointing=True,
    enable_model_summary=False,
    enable_progress_bar=True,
)
trainer.fit(model, train_dataloaders=train_loader, val_dataloaders=val_loader)
```

### Prediction-only isolation

```python
result = model.predict(
    val_loader,
    fast_dev_run=True,
    return_index=True,
    return_decoder_lengths=True,
    trainer_kwargs={"accelerator": "cpu", "devices": 1, "enable_progress_bar": False},
)
```

### Disable expensive plotting/logging

```python
if hasattr(model, "hparams"):
    model.hparams.log_interval = -1
    if hasattr(model.hparams, "log_val_interval"):
        model.hparams.log_val_interval = -1
```

## Checkpoint and reload failures

- `load_from_checkpoint(path)` should be called on the same model class that created the checkpoint, for example `TemporalFusionTransformer.load_from_checkpoint(path)` or `type(model).load_from_checkpoint(path)`.
- A checkpoint path is only meaningful after a successful `fit()` with checkpointing enabled.
- If the checkpoint loads but prediction on a raw DataFrame fails, rebuild the prediction data with the same training dataset parameters. The model stores dataset parameters, but the DataFrame must still contain required future-known covariates and group/time columns.
- If code needs a portable inference bundle, save both the model checkpoint and enough data-pipeline metadata to recreate compatible prediction frames. Do not rely on the original training DataFrame being available.

## Plotting and interpretation caveats

- `plot_prediction(...)`, `plot_interpretation(...)`, and LR finder plots require matplotlib. If it is absent, training and prediction can still be valid.
- Many training-time interpretation hooks only log when `log_interval > 0` and the logger supports `add_figure`. Missing figure logging is not a model failure.
- Use `mode="raw", return_x=True` for interpretation. Standard `mode="prediction"` output is usually insufficient for attention, decomposition, or raw component plots.
- Untrained model plots validate tensor shapes only. Use them for API debugging, not for quality claims.

## When to switch models instead of debugging longer

- Switch from `NBeats`/`NBeatsKAN` to `NHiTS` or `TemporalFusionTransformer` when covariates matter.
- Switch from `TemporalFusionTransformer` to `RecurrentNetwork`, `DecoderMLP`, `TiDEModel`, or `NHiTS` when runtime budget is too tight for attention.
- Switch from point-loss models to `DeepAR` or quantile-capable models only when uncertainty is an explicit deliverable.
- Switch from v1 models to the api-v2 sub-skill only when the task specifically requires v2 package/data-module APIs or SOFTS.
