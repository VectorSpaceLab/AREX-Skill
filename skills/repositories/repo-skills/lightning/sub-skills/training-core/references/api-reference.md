# Training Core API Reference

This reference covers the public Lightning training API surfaces most agents need for day-to-day model work. Version facts used for this skill: the source repository is Lightning `2.6.2`; the installed inspection package available during generation verified `2.6.1` signatures where `2.6.2` was not yet published on the package index. CPU Torch was used for inspection, so this sub-skill does not claim GPU runtime validation.

## Imports and Compatibility

Prefer these imports for new code:

```python
import lightning as L
from lightning.pytorch import Trainer, LightningModule, LightningDataModule, seed_everything
```

Equivalent explicit imports are common in existing projects:

```python
import lightning.pytorch as pl
from lightning.pytorch.callbacks import EarlyStopping, LearningRateMonitor, ModelCheckpoint
from lightning.pytorch.loggers import CSVLogger, TensorBoardLogger
```

Legacy `pytorch_lightning` compatibility may exist in user projects. For new or refreshed code, prefer `lightning` / `lightning.pytorch` unless the task is explicitly maintaining a legacy import style.

## LightningModule Essentials

A `LightningModule` is a `torch.nn.Module` plus training loop hooks. Keep plain model code in `__init__`/`forward`, and loop-specific logic in the step hooks.

Core hooks:

- `__init__`: define submodules and hyperparameters; call `self.save_hyperparameters()` for constructor values that should be saved in checkpoints.
- `forward(...)`: inference-only tensor path; `trainer.predict` uses `predict_step`, while direct `model(x)` uses `forward`.
- `training_step(batch, batch_idx)`: compute and return the training loss in automatic optimization.
- `validation_step(batch, batch_idx)`: compute validation metrics and log monitor values such as `val_loss`.
- `test_step(batch, batch_idx)`: compute final held-out metrics.
- `predict_step(batch, batch_idx, dataloader_idx=None)`: return predictions for `trainer.predict`.
- `configure_optimizers()`: return an optimizer, optimizer/scheduler tuple, or dictionary describing optimizers and LR schedulers.

High-value methods and properties:

- `self.log(name, value, on_step=..., on_epoch=..., prog_bar=..., logger=...)`: logs scalar metrics for callbacks, progress bar, and loggers. Values monitored by `ModelCheckpoint` or `EarlyStopping` must be logged under the exact `monitor` name.
- `self.save_hyperparameters(ignore=[...])`: stores constructor arguments in `self.hparams` and checkpoint `hyper_parameters`; ignore large modules or objects that should not be serialized.
- `self.trainer`: available after attachment to a `Trainer`, useful for properties such as `estimated_stepping_batches` in scheduler setup.
- `self.device`: use for creating tensors compatible with current placement when needed; avoid hard-coded `.cuda()` or `.to('cuda')` in module code.

Lightning handles device placement and distributed samplers for standard `Trainer` workflows. Do not add `.cuda()`, `.to(device)`, or a manual `DistributedSampler` unless the task is explicitly a lower-level Fabric or custom strategy workflow.

## LightningDataModule Essentials

Use a `LightningDataModule` when data splits, preparation, or dataloaders should be reusable or configurable.

Core hooks:

- `prepare_data()`: one-time CPU work such as download/tokenization. Do not assign state here that all ranks need, because it may run only on one process.
- `setup(stage)`: create datasets and splits for `"fit"`, `"validate"`, `"test"`, or `"predict"`; assign instance attributes here.
- `train_dataloader()`, `val_dataloader()`, `test_dataloader()`, `predict_dataloader()`: return PyTorch dataloaders.
- `teardown(stage)`: optional cleanup.

Common fit call:

```python
trainer.fit(model, datamodule=data_module)
```

Use `random_split(..., generator=torch.Generator().manual_seed(seed))` or `seed_everything(..., workers=True)` when deterministic splits or dataloader-worker randomness matter.

## Trainer Essentials

`Trainer` orchestrates the training, validation, test, and prediction loops. Verified signature facts include defaults for `accelerator='auto'`, `strategy='auto'`, `devices='auto'`, `precision`, `callbacks`, `fast_dev_run`, `barebones`, `model_registry`, and `suggest_integrations`.

Common options:

- `accelerator`: `"auto"`, `"cpu"`, `"gpu"`, `"tpu"`, `"hpu"`, or accelerator instance. Route hardware depth to `../distributed-accelerators/SKILL.md`.
- `strategy`: `"auto"`, `"ddp"`, strategy instances, and other strategy names. Keep standard usage here; route deep strategy work elsewhere.
- `devices`: `"auto"`, integer count, list of device ids, or device selector depending on accelerator.
- `max_epochs`, `min_epochs`, `max_steps`, `min_steps`: stopping bounds.
- `fast_dev_run`: run one or a small number of batches through train/val/test to catch integration errors quickly.
- `limit_train_batches`, `limit_val_batches`, `limit_test_batches`, `limit_predict_batches`: shrink loops for smoke tests or debugging.
- `overfit_batches`: debug whether the model can memorize a tiny subset.
- `callbacks`: list of callback instances such as `ModelCheckpoint`, `EarlyStopping`, and `LearningRateMonitor`.
- `logger`: `True`, `False`, logger instance, or list of logger instances.
- `default_root_dir`: default output directory for logs/checkpoints when not overridden by logger/callback paths.
- `enable_checkpointing`, `enable_progress_bar`, `enable_model_summary`: enable or disable standard Trainer behavior.
- `deterministic`: request deterministic algorithms for reproducibility.
- `barebones`: disable overhead features for raw loop speed investigation; avoid using it when callbacks/loggers/checkpointing are required.

Loop methods:

```python
trainer.fit(model, train_dataloaders=None, val_dataloaders=None, datamodule=None, ckpt_path=None)
trainer.validate(model=None, dataloaders=None, ckpt_path=None, datamodule=None)
trainer.test(model=None, dataloaders=None, ckpt_path=None, datamodule=None)
trainer.predict(model=None, dataloaders=None, ckpt_path=None, datamodule=None)
```

Use `ckpt_path="best"` after a checkpointing fit when you want the best checkpoint selected by the active `ModelCheckpoint` callback. Use an explicit `.ckpt` path to resume or evaluate a specific saved run.

## Optimization API

Automatic optimization is the default and should be used for most tasks. In automatic optimization:

- Return a loss tensor from `training_step`.
- Return optimizer/scheduler configuration from `configure_optimizers`.
- Do not call `optimizer.zero_grad()`, `loss.backward()`, or `optimizer.step()` yourself.
- Lightning handles scheduler stepping for native PyTorch schedulers when declared in `configure_optimizers`.

Common return forms:

```python
def configure_optimizers(self):
    return torch.optim.Adam(self.parameters(), lr=1e-3)
```

```python
def configure_optimizers(self):
    optimizer = torch.optim.Adam(self.parameters(), lr=1e-3)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=1)
    return {
        "optimizer": optimizer,
        "lr_scheduler": {"scheduler": scheduler, "interval": "epoch", "frequency": 1},
    }
```

Use manual optimization only when the user needs multiple optimizers or non-standard stepping. Set `self.automatic_optimization = False`, use `self.optimizers()`, call `self.manual_backward(loss)`, and step optimizers explicitly. If the user wants full manual loop ownership outside `Trainer`, route to Fabric.

## Callbacks

Verified callback signatures include `ModelCheckpoint`, `EarlyStopping`, and `LearningRateMonitor`.

### ModelCheckpoint

Use for automatic checkpoint saving and best-model selection.

High-value options:

- `dirpath`: output directory. Without this, checkpoints normally go under the logger directory or `default_root_dir`-based checkpoint directory.
- `filename`: pattern such as `"{epoch:02d}-{val_loss:.3f}"`.
- `monitor`: logged metric name to rank checkpoints, for example `"val_loss"`.
- `mode`: `"min"` for losses, `"max"` for scores.
- `save_top_k`: number of best checkpoints; `-1` saves all, `0` saves none.
- `save_last`: `True` or supported link behavior when a latest checkpoint is needed.
- `every_n_train_steps`, `every_n_epochs`, `train_time_interval`: checkpoint frequency.
- `save_weights_only`: save only model weights when optimizer/scheduler resume state is not needed.

Access paths after fit:

```python
checkpoint = ModelCheckpoint(monitor="val_loss", mode="min", save_top_k=1)
trainer = Trainer(callbacks=[checkpoint])
trainer.fit(model, datamodule=dm)
print(checkpoint.best_model_path)
print(checkpoint.last_model_path)
```

### EarlyStopping

Use to stop training when a monitored metric stops improving.

High-value options:

- `monitor`: exact metric name logged with `self.log`.
- `mode`: `"min"` or `"max"`.
- `patience`: number of validation checks without improvement before stopping.
- `min_delta`: minimum improvement threshold.
- `check_on_train_epoch_end`: set when monitoring a training metric and no validation loop should drive checks.
- `strict`: when true, missing monitor metrics are errors; when false, missing metrics warn/skip depending on behavior.

### LearningRateMonitor

Use with a logger to record optimizer LR schedules.

High-value options:

- `logging_interval`: `"step"`, `"epoch"`, or `None` for scheduler-driven default.
- `log_momentum`: include momentum when available.
- `log_weight_decay`: include weight decay when available.

Requires a logger. If `logger=False`, there is nowhere to write LR metrics.

## Loggers

Verified logger signatures include `CSVLogger` and `TensorBoardLogger`.

### CSVLogger

Useful for dependency-light local metrics.

Typical usage:

```python
logger = CSVLogger(save_dir="logs", name="experiment")
trainer = Trainer(logger=logger)
```

Outputs metrics under a versioned experiment directory, often including `metrics.csv` and hyperparameter metadata.

### TensorBoardLogger

Useful when TensorBoard is installed and interactive metric visualization is desired.

Typical usage:

```python
logger = TensorBoardLogger(save_dir="tb_logs", name="experiment")
trainer = Trainer(logger=logger)
```

If TensorBoard dependencies are missing, fall back to `CSVLogger` or install the optional logger dependency.

## Checkpoint Loading and Resuming

Load weights and hyperparameters into a module:

```python
model = MyModule.load_from_checkpoint("path/to/model.ckpt")
model.eval()
y = model(x)
```

Resume full training state:

```python
trainer.fit(model, datamodule=dm, ckpt_path="path/to/model.ckpt")
```

Evaluate or predict from best checkpoint:

```python
trainer.test(model, datamodule=dm, ckpt_path="best")
predictions = trainer.predict(model, datamodule=dm, ckpt_path="best")
```

For manual saves use `trainer.save_checkpoint("example.ckpt")` instead of `torch.save` so strategy-specific checkpoint behavior is honored.

## Reproducibility

Use both seeding and Trainer settings:

```python
from lightning.pytorch import seed_everything

seed_everything(42, workers=True)
trainer = Trainer(deterministic=True)
```

Also seed dataset splits explicitly and keep preprocessing randomness inside dataloader workers compatible with `workers=True`.
