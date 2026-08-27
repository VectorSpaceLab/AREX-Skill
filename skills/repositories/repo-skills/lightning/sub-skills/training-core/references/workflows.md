# Training Core Workflows

Use these workflows to implement or repair common Lightning training tasks without reopening the source repository.

## Convert Raw PyTorch to Lightning

Starting point in raw PyTorch usually contains model definition, dataloaders, optimizer, `loss.backward()`, `optimizer.step()`, device movement, and evaluation loops in one script.

Conversion checklist:

1. Keep the `torch.nn.Module` architecture intact inside a `LightningModule`.
2. Move forward inference into `forward`.
3. Move per-batch training logic into `training_step`; return the loss.
4. Move validation/test/predict logic into `validation_step`, `test_step`, and `predict_step`.
5. Move optimizer and scheduler creation into `configure_optimizers`.
6. Move dataset construction and dataloaders into a `LightningDataModule` if the data setup is more than a one-off loader.
7. Delete manual `.to(device)`, `.cuda()`, `loss.backward()`, `optimizer.step()`, and `optimizer.zero_grad()` in automatic optimization.
8. Delete manual `DistributedSampler` for normal `Trainer` workflows; Lightning handles it under distributed strategies.
9. Add `Trainer(max_steps=1, fast_dev_run=True)` or `limit_*_batches` for the first integration check.

Minimal module pattern:

```python
class LitModel(L.LightningModule):
    def __init__(self, in_dim: int, out_dim: int, lr: float = 1e-3):
        super().__init__()
        self.save_hyperparameters()
        self.net = torch.nn.Linear(in_dim, out_dim)

    def forward(self, x):
        return self.net(x)

    def training_step(self, batch, batch_idx):
        x, y = batch
        loss = torch.nn.functional.cross_entropy(self(x), y)
        self.log("train_loss", loss, on_step=True, on_epoch=True, prog_bar=True)
        return loss

    def validation_step(self, batch, batch_idx):
        x, y = batch
        loss = torch.nn.functional.cross_entropy(self(x), y)
        self.log("val_loss", loss, on_epoch=True, prog_bar=True)

    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=self.hparams.lr)
```

## Build a Datamodule

Use a datamodule when the user asks for reusable splits, configurable batch size, train/val/test/predict dataloaders, or distributed-safe data preparation.

Pattern:

```python
class MyDataModule(L.LightningDataModule):
    def __init__(self, batch_size: int = 32):
        super().__init__()
        self.batch_size = batch_size

    def prepare_data(self):
        # Download/tokenize once; do not assign required state here.
        pass

    def setup(self, stage: str | None = None):
        full = MyDataset(...)
        self.train_ds, self.val_ds = torch.utils.data.random_split(
            full, [train_len, val_len], generator=torch.Generator().manual_seed(42)
        )
        self.test_ds = MyDataset(...)

    def train_dataloader(self):
        return DataLoader(self.train_ds, batch_size=self.batch_size, shuffle=True)

    def val_dataloader(self):
        return DataLoader(self.val_ds, batch_size=self.batch_size)

    def test_dataloader(self):
        return DataLoader(self.test_ds, batch_size=self.batch_size)
```

Validation signals:

- `trainer.fit(model, datamodule=dm)` calls `prepare_data`, `setup("fit")`, train dataloader, and val dataloader.
- `trainer.test(model, datamodule=dm)` requires `test_dataloader` and usually `setup("test")` state.
- If a distributed run fails because attributes are missing, check that required dataset state is assigned in `setup`, not `prepare_data`.

## Standard Fit + Validation

Recommended baseline for new scripts:

```python
from lightning.pytorch.callbacks import EarlyStopping, ModelCheckpoint, LearningRateMonitor
from lightning.pytorch.loggers import CSVLogger

checkpoint = ModelCheckpoint(monitor="val_loss", mode="min", save_top_k=1, save_last=True)
early_stop = EarlyStopping(monitor="val_loss", mode="min", patience=5)
lr_monitor = LearningRateMonitor(logging_interval="epoch")
logger = CSVLogger("logs", name="baseline")

trainer = L.Trainer(
    accelerator="auto",
    devices="auto",
    max_epochs=20,
    callbacks=[checkpoint, early_stop, lr_monitor],
    logger=logger,
    deterministic=True,
)
trainer.fit(model, datamodule=dm)
```

Important details:

- `val_loss` must be logged from `validation_step` with the exact same name.
- Use `mode="min"` for losses and `mode="max"` for scores.
- `LearningRateMonitor` needs a logger.
- If using a logger, default checkpoints are saved under the logger directory unless `ModelCheckpoint(dirpath=...)` overrides it.

## Evaluation and Prediction

Validation before or after fit:

```python
trainer.validate(model=model, datamodule=dm)
```

Test after fit:

```python
trainer.test(model=model, datamodule=dm, ckpt_path="best")
```

Prediction:

```python
predictions = trainer.predict(model=model, datamodule=dm, ckpt_path="best")
```

Use `forward` for direct inference and `predict_step` for `Trainer.predict` behavior such as unpacking batches or returning postprocessed outputs.

## Checkpoint Workflows

### Save Best and Last

```python
checkpoint = ModelCheckpoint(
    dirpath="checkpoints",
    filename="{epoch:02d}-{val_loss:.4f}",
    monitor="val_loss",
    mode="min",
    save_top_k=1,
    save_last=True,
)
trainer = L.Trainer(callbacks=[checkpoint])
trainer.fit(model, datamodule=dm)
print(checkpoint.best_model_path)
```

### Resume Training

```python
model = LitModel(...)
trainer = L.Trainer(max_epochs=100)
trainer.fit(model, datamodule=dm, ckpt_path="checkpoints/last.ckpt")
```

Use `ckpt_path` in `fit`; do not use old `resume_from_checkpoint` patterns.

### Load for Inference

```python
model = LitModel.load_from_checkpoint("checkpoints/best.ckpt")
model.eval()
with torch.no_grad():
    y = model(x)
```

If constructor arguments were not saved with `save_hyperparameters`, pass them to `load_from_checkpoint`.

### Extract Plain PyTorch Weights

Lightning checkpoints contain `state_dict` keys for module attributes. For a nested encoder:

```python
checkpoint = torch.load("model.ckpt", map_location="cpu")
encoder_weights = {k.removeprefix("encoder."): v for k, v in checkpoint["state_dict"].items() if k.startswith("encoder.")}
encoder.load_state_dict(encoder_weights)
```

Route production export or serving decisions to `../deployment-serving/SKILL.md`.

## Learning Rate Scheduling

Automatic optimization example:

```python
def configure_optimizers(self):
    optimizer = torch.optim.AdamW(self.parameters(), lr=1e-3)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=10)
    return {
        "optimizer": optimizer,
        "lr_scheduler": {"scheduler": scheduler, "interval": "epoch", "frequency": 1},
    }
```

For step-level schedules:

```python
"lr_scheduler": {"scheduler": scheduler, "interval": "step"}
```

For `OneCycleLR`, use Trainer's estimated step count:

```python
def configure_optimizers(self):
    optimizer = torch.optim.AdamW(self.parameters(), lr=1e-3)
    scheduler = torch.optim.lr_scheduler.OneCycleLR(
        optimizer, max_lr=1e-3, total_steps=self.trainer.estimated_stepping_batches
    )
    return {"optimizer": optimizer, "lr_scheduler": {"scheduler": scheduler, "interval": "step"}}
```

## Tuning and Debug Runs

Use these before long jobs:

- `fast_dev_run=True`: one train/val/test/predict batch path where applicable; disables or alters some normal long-run behavior, so use it only as a smoke test.
- `max_steps=1` with `limit_val_batches=1`: quick fit that still behaves more like a real Trainer run than `fast_dev_run`.
- `overfit_batches=1` or a small fraction: check whether the model can memorize a tiny subset.
- `detect_anomaly=True`: investigate autograd NaNs/in-place errors, but expect slowdown.
- `num_sanity_val_steps=0`: skip validation sanity checks only when debugging data or speed; do not hide real validation failures in production scripts.
- `barebones=True`: profile core loop overhead only; do not combine with callbacks, checkpointing, logging, or progress features expected by the task.

## Reproducible Training

Baseline:

```python
L.seed_everything(42, workers=True)
trainer = L.Trainer(deterministic=True)
```

Also:

- Seed `random_split` with a `torch.Generator`.
- Keep random transforms compatible with dataloader worker seeding.
- Record package versions and Trainer options in logs or hyperparameters.
- Avoid claiming bitwise reproducibility across different hardware/backend combinations unless the environment has been validated.

## Validation Procedure for Generated Code

1. Run import/help smoke: `python sub-skills/training-core/scripts/lightning_smoke.py --help`.
2. Run one CPU step: `python sub-skills/training-core/scripts/lightning_smoke.py --max-steps 1 --fast-dev-run`.
3. Inspect output for `LIGHTNING_SMOKE_OK` and a checkpoint/log directory under the supplied `--default-root-dir`.
4. For user code, add `fast_dev_run=True` first; then a tiny real run with `max_steps=2`, `limit_val_batches=1`, and the intended callbacks/loggers.
5. Verify monitored metrics appear in logger output or `trainer.callback_metrics` under the exact names used by callbacks.
