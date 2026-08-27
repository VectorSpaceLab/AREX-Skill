# Training, Checkpointing, Prediction, and Interpretation Workflows

This guide gives concrete PyTorch Forecasting 1.8.0 v1 recipes for models built from `TimeSeriesDataSet`. It assumes the data-pipeline sub-skill has already produced:

```python
training       # TimeSeriesDataSet for fitting
validation     # TimeSeriesDataSet for validation/prediction
train_loader   # training.to_dataloader(train=True, ...)
val_loader     # validation.to_dataloader(train=False, ...)
```

## Canonical imports

```python
import lightning.pytorch as pl
from lightning.pytorch.callbacks import EarlyStopping, LearningRateMonitor
from lightning.pytorch.tuner import Tuner

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
from pytorch_forecasting.metrics import (
    MAE,
    MASE,
    SMAPE,
    QuantileLoss,
    NormalDistributionLoss,
)
from pytorch_forecasting.models import TimeXer, xLSTMTime
```

Prefer `lightning.pytorch` imports for v1.8.0 workflows. Keep package/data-module v2 classes out of this v1 recipe.

## `.from_dataset()` construction pattern

Every stable v1 neural model should normally be created from the training dataset:

```python
model = ModelClass.from_dataset(training, **model_hyperparameters)
print(f"parameters: {model.size() / 1e3:.1f}k")
```

`.from_dataset()` copies feature-cardinality metadata, target scaling metadata, target names, categorical embeddings, continuous variable order, and output defaults from `TimeSeriesDataSet`. Manual construction is error-prone because the model must match encoded tensor positions.

### TemporalFusionTransformer for covariate-rich quantile forecasts

```python
tft = TemporalFusionTransformer.from_dataset(
    training,
    learning_rate=0.03,
    hidden_size=16,
    attention_head_size=1,
    dropout=0.1,
    hidden_continuous_size=8,
    output_size=7,
    loss=QuantileLoss(),
    log_interval=-1,
    log_val_interval=-1,
    reduce_on_plateau_patience=4,
)
```

Use this as the first rich-covariate model. Increase sizes only after a small run has stable loss and acceptable runtime.

### N-BEATS target-only fixed-window recipe

The dataset must be target-only, continuous, fixed-length, non-randomized, and without relative time index.

```python
nbeats = NBeats.from_dataset(
    training,
    learning_rate=3e-2,
    widths=[32, 256],
    num_blocks=[1, 1],
    num_block_layers=[2, 2],
    log_interval=-1,
    log_val_interval=-1,
    weight_decay=1e-2,
)
```

For `NBeatsKAN`, use the same dataset contract and optionally add a grid-update callback during training:

```python
from pytorch_forecasting.models.nbeats import GridUpdateCallback

nbeats_kan = NBeatsKAN.from_dataset(
    training,
    learning_rate=3e-2,
    widths=[32, 256],
    log_interval=-1,
    log_val_interval=-1,
)
callbacks = [GridUpdateCallback(update_interval=3)]
```

### N-HiTS for long horizon with covariates

```python
nhits = NHiTS.from_dataset(
    training,
    learning_rate=1e-2,
    hidden_size=64,
    n_layers=2,
    dropout=0.0,
    loss=MASE(),       # use QuantileLoss() only when uncertainty is required
    log_interval=-1,
)
```

`NHiTS` still requires fixed encoder/prediction lengths and continuous targets, but unlike `NBeats` it can use covariates.

### DeepAR probabilistic recipe

```python
deepar = DeepAR.from_dataset(
    training,
    learning_rate=0.05,
    hidden_size=16,
    rnn_layers=2,
    dropout=0.1,
    loss=NormalDistributionLoss(),
    log_interval=-1,
)
```

Use `DeepAR` when probabilistic samples matter. Inference cost scales with `n_samples`.

### Smaller covariate baselines

```python
rnn = RecurrentNetwork.from_dataset(
    training,
    learning_rate=0.03,
    hidden_size=16,
    rnn_layers=1,
    cell_type="LSTM",     # or "GRU"
    loss=MAE(),
    log_interval=-1,
)

mlp = DecoderMLP.from_dataset(
    training,
    learning_rate=0.03,
    hidden_size=64,
    n_hidden_layers=2,
    dropout=0.1,
    loss=QuantileLoss(),
    log_interval=-1,
)
```

`RecurrentNetwork` is a sequence baseline. `DecoderMLP` is a future/static-covariate baseline and should not be expected to recover complex encoder-history dynamics.

### TiDE and TimeXer long-horizon recipes

```python
tide = TiDEModel.from_dataset(
    training,
    hidden_size=64,
    num_encoder_layers=2,
    num_decoder_layers=2,
    temporal_width_future=4,
    dropout=0.1,
)

timexer = TimeXer.from_dataset(
    training,
    hidden_size=64,
    n_heads=4,
    e_layers=1,
    d_ff=128,
    patch_length=min(16, training.max_encoder_length),
    features="MS",       # "S" univariate, "MS" multivariate-single-target, "M" multi-target
    loss=MAE(),
)
```

For `TimeXer`, ensure `training.max_encoder_length >= patch_length` and `hidden_size % n_heads == 0` before construction.

### xLSTMTime cautious recipe

```python
xlstm = xLSTMTime.from_dataset(
    training,
    input_size=1,
    hidden_size=32,
    output_size=1,
    xlstm_type="slstm",   # or "mlstm"
    num_layers=1,
    learning_rate=1e-2,
    loss=SMAPE(),
)
```

Use this only after a target-only fixed-window smoke test passes. Provide `input_size`, `hidden_size`, and `output_size` explicitly.

## Lightning Trainer setup

### Debug trainer: one or two batches on CPU

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
```

Use this when a model, loss, or dataset is new. If this fails, fix the failure before increasing model size or GPU usage.

### Normal trainer with early stopping and LR logging

```python
early_stop = EarlyStopping(
    monitor="val_loss",
    min_delta=1e-4,
    patience=5,
    verbose=False,
    mode="min",
)
lr_logger = LearningRateMonitor()

trainer = pl.Trainer(
    max_epochs=30,
    accelerator="auto",
    devices="auto",
    gradient_clip_val=0.1,
    callbacks=[lr_logger, early_stop],
    enable_checkpointing=True,
    limit_train_batches=1.0,
    limit_val_batches=1.0,
)
```

If logging packages are not installed or a logger is disabled, omit `LearningRateMonitor()`.

## Learning-rate finder handoff

Learning-rate finder details belong to `../metrics-and-tuning/SKILL.md`, but this is the safe model-side invocation pattern:

```python
# Avoid plot spam and artificial fast-dev limits during lr_find.
model.hparams.log_interval = -1
if hasattr(model.hparams, "log_val_interval"):
    model.hparams.log_val_interval = -1

lr_trainer = pl.Trainer(
    accelerator="auto",
    devices="auto",
    gradient_clip_val=0.1,
    limit_train_batches=1.0,
    limit_val_batches=1.0,
    enable_checkpointing=False,
)

result = Tuner(lr_trainer).lr_find(
    model,
    train_dataloaders=train_loader,
    val_dataloaders=val_loader,
    early_stop_threshold=1000.0,
    max_lr=0.3,
)
suggested_lr = result.suggestion()
if suggested_lr is not None:
    model.hparams.learning_rate = suggested_lr
```

Do not set `fast_dev_run=True` on the trainer used by `lr_find()`. If matplotlib is absent, skip `result.plot(...)` and rely on `result.suggestion()`.

## Fit, test, checkpoint, and reload

```python
trainer.fit(model, train_dataloaders=train_loader, val_dataloaders=val_loader)

# Optional, if a test dataloader exists:
# test_outputs = trainer.test(model, dataloaders=test_loader)

best_path = trainer.checkpoint_callback.best_model_path
if not best_path:
    raise RuntimeError("No best checkpoint path; enable checkpointing and run fit first.")

loaded = type(model).load_from_checkpoint(best_path)
```

Use the concrete class when you need static readability:

```python
loaded_tft = TemporalFusionTransformer.load_from_checkpoint(best_path)
```

A loaded model stores dataset parameters from training, so it can also build prediction datasets from compatible DataFrames through `predict(dataframe, ...)`. For new raw DataFrames, confirm schema and future-known covariates with the data-pipeline sub-skill first.

## Prediction workflows

### Baseline sanity prediction

```python
baseline_result = Baseline().predict(
    val_loader,
    fast_dev_run=True,
    return_index=True,
    return_decoder_lengths=True,
)
print(baseline_result.output.shape)
print(baseline_result.index.head())
```

Use this before neural training to validate dataloader and prediction plumbing.

### Standard model prediction

```python
prediction = loaded.predict(
    val_loader,
    mode="prediction",
    batch_size=64,
    num_workers=0,
    return_index=True,
    return_decoder_lengths=True,
    return_x=True,
    return_y=True,
    trainer_kwargs={
        "accelerator": "cpu",
        "devices": 1,
        "enable_progress_bar": False,
    },
)
```

When any `return_*` flag is true, the return value is a `Prediction` tuple-like object with fields:

- `prediction.output`: tensor, list/tuple of tensors, or nested output depending on target/loss/model.
- `prediction.index`: pandas DataFrame with the decoded prediction index when `return_index=True`.
- `prediction.decoder_lengths`: tensor of decoder lengths when `return_decoder_lengths=True`.
- `prediction.x`: concatenated model input tensors when `return_x=True`.
- `prediction.y`: target tuple `(y, weight)` when `return_y=True`.

If no return flags are set, `predict()` usually returns the prediction tensor/list directly rather than a full `Prediction` object.

### Prediction modes

```python
# Point prediction or distribution/quantile mean-like default
point = loaded.predict(val_loader, mode="prediction")

# Quantile representation for compatible losses/models
quantiles = loaded.predict(val_loader, mode="quantiles")

# Raw network output dictionary; needed for plotting and interpretation
raw = loaded.predict(val_loader, mode="raw", return_x=True)

# A named field from raw output, if the model's forward output contains it
raw_prediction = loaded.predict(val_loader, mode=("raw", "prediction"))
```

`mode="raw"` is the right mode for `plot_prediction(...)`, `interpret_output(...)`, and model-specific output debugging.

### DeepAR sample prediction

`DeepAR.predict()` adds `n_samples` and maps `mode="samples"` to the raw sampled prediction field:

```python
mean_pred = deepar.predict(val_loader, mode="prediction", n_samples=100)
samples = deepar.predict(val_loader, mode="samples", n_samples=100)
```

Expect `samples` to include a sample dimension; runtime increases with `n_samples`.

### Writing predictions to disk

```python
loaded.predict(
    val_loader,
    mode="prediction",
    output_dir="predictions_out",
    write_interval="batch",
)
```

When `output_dir` is set, predictions are written as PyTorch files and the in-memory return is not useful. Do not combine this with code that expects `prediction.output`.

## Interpretation and plotting

Plotting requires matplotlib. Logging figures during training additionally requires a logger that supports `add_figure`; otherwise plotting hooks are skipped or warnings appear. For headless or minimal environments, keep `log_interval=-1` and produce plots only in explicit analysis steps.

### Base prediction plot

```python
raw = loaded.predict(val_loader, mode="raw", return_x=True, fast_dev_run=True)
fig = loaded.plot_prediction(raw.x, raw.output, idx=0, add_loss_to_title=True)
```

This works for many `BaseModel` descendants when raw output and input are returned.

### TemporalFusionTransformer interpretation

```python
raw = tft.predict(val_loader, mode="raw", return_x=True, fast_dev_run=True)
interpretation = tft.interpret_output(raw.output, reduction="sum")
fig = tft.plot_interpretation(interpretation)
fig2 = tft.plot_prediction(raw.x, raw.output, idx=0, plot_attention=True)
```

Use `reduction="sum"` or `"mean"` for aggregate variable/attention summaries; use `"none"` for per-item analysis.

### N-BEATS / N-HiTS style decomposition plots

```python
raw = model.predict(val_loader, mode="raw", return_x=True, fast_dev_run=True)
fig = model.plot_prediction(raw.x, raw.output, idx=0, add_loss_to_title=True)
if hasattr(model, "plot_interpretation"):
    fig2 = model.plot_interpretation(raw.x, raw.output, idx=0)
```

Use these plots only after a training or debug fit; untrained decomposition plots prove API shape, not model quality.

## End-to-end small CPU template

```python
# 1. Instantiate a small model.
model = TemporalFusionTransformer.from_dataset(
    training,
    hidden_size=4,
    hidden_continuous_size=2,
    attention_head_size=1,
    dropout=0.1,
    learning_rate=0.03,
    output_size=7,
    loss=QuantileLoss(),
    log_interval=-1,
)

# 2. Fit one batch to check all hooks.
trainer = pl.Trainer(
    max_epochs=1,
    accelerator="cpu",
    devices=1,
    limit_train_batches=1,
    limit_val_batches=1,
    num_sanity_val_steps=0,
    gradient_clip_val=0.1,
    enable_checkpointing=True,
)
trainer.fit(model, train_loader, val_loader)

# 3. Reload and predict one batch with metadata.
best_path = trainer.checkpoint_callback.best_model_path
loaded = type(model).load_from_checkpoint(best_path)
result = loaded.predict(
    val_loader,
    fast_dev_run=True,
    return_index=True,
    return_decoder_lengths=True,
    return_x=True,
    trainer_kwargs={"accelerator": "cpu", "devices": 1},
)
assert len(result.index) == result.output.shape[0]
```

Run this template before launching expensive epochs, Optuna, multi-GPU, or full-dataset predictions.
