# Training Core Troubleshooting

Use this when standard Lightning training code fails to import, configure, fit, validate, checkpoint, log, or resume.

## Install and Import Failures

Symptoms:

- `ModuleNotFoundError: No module named 'lightning'`
- `ModuleNotFoundError: No module named 'pytorch_lightning'`
- Code imports `pytorch_lightning` but new examples use `lightning.pytorch`

Checks:

```bash
python - <<'PY'
import lightning
import lightning.pytorch as pl
print(lightning.__version__)
print(pl.Trainer)
PY
```

Fixes:

- Install the public package that contains `lightning.pytorch` in the active environment.
- Prefer `import lightning as L` or `import lightning.pytorch as pl` for new code.
- Preserve `pytorch_lightning` imports only when maintaining legacy user code that already depends on that namespace.
- Do not mix classes from different namespaces in one script if avoidable; use one import style consistently.

## Optional Dependency Failures

Symptoms:

- TensorBoard logger import or runtime failure.
- TorchVision unavailable in example-derived code.
- CLI extras errors mentioning `jsonargparse`.

Fixes:

- Replace `TensorBoardLogger` with `CSVLogger` for a dependency-light local run.
- Remove TorchVision-dependent image saving or dataset downloads from smoke tests; use synthetic tensors when validating training mechanics.
- Route `LightningCLI` / `jsonargparse` issues to `../cli-configuration/SKILL.md`.

## Missing `configure_optimizers`

Symptom:

- Misconfiguration error saying no `configure_optimizers()` method is defined.

Fix:

```python
def configure_optimizers(self):
    return torch.optim.Adam(self.parameters(), lr=1e-3)
```

If the model intentionally has no optimizer, the task may be prediction/evaluation-only; use `trainer.validate`, `trainer.test`, or `trainer.predict` without `fit`, or implement a no-op-free evaluation script.

## Manual PyTorch Loop Code Still Present

Symptoms:

- Code calls `loss.backward()` or `optimizer.step()` inside `training_step` with default automatic optimization.
- Code calls `.cuda()` or `.to(device)` inside `LightningModule` hooks.
- Dataloader uses a manual `DistributedSampler` and later fails under a Lightning distributed strategy.

Fixes:

- In automatic optimization, return the loss and let Lightning run zero-grad, backward, optimizer step, scheduler step, precision, and strategy hooks.
- Remove hard-coded device movement; create new tensors with `new_tensor = old_tensor.new_zeros(...)` or `tensor.to(reference_tensor)` only when necessary.
- Remove manual distributed samplers for normal `Trainer` workflows. Route custom distributed data behavior to `../distributed-accelerators/SKILL.md`.
- If the user truly needs manual optimizer stepping, set `self.automatic_optimization = False` and use Lightning manual optimization APIs, or route full manual-loop ownership to Fabric.

## Checkpoint Monitor Missing

Symptoms:

- `ModelCheckpoint(monitor='val_loss')` or `EarlyStopping(monitor='val_loss')` fails or never saves/stops as expected.
- Error or warning says the monitored key is not available.

Root cause:

The metric named in `monitor` must be logged with exactly the same string before the callback checks it.

Fix:

```python
def validation_step(self, batch, batch_idx):
    loss = ...
    self.log("val_loss", loss, on_epoch=True, prog_bar=True, logger=True)
```

Checklist:

- Match spelling exactly: `val_loss` is different from `valid_loss`.
- For validation monitors, ensure `validation_step` and `val_dataloader` exist and validation is not disabled by `limit_val_batches=0`.
- For train-only monitoring, use `self.log("train_loss", ..., on_epoch=True)` and configure `EarlyStopping(check_on_train_epoch_end=True)` when appropriate.
- Set `mode="min"` for losses and `mode="max"` for scores.
- For checkpoint filenames using metrics, include metrics that are logged at the checkpoint interval.

## Checkpoints Saved in Unexpected Location

Symptoms:

- `default_root_dir` is set, but checkpoints appear under a logger directory.
- No checkpoint appears after `fit`.

Rules:

- Without a logger, checkpoints default under `default_root_dir`.
- With a logger, checkpoints usually go under the logger's experiment/version directory.
- `ModelCheckpoint(dirpath=...)` explicitly controls checkpoint location.
- `enable_checkpointing=False` disables checkpoint callbacks.
- `fast_dev_run` is for debugging and can alter normal checkpoint/logger behavior.

Fix:

```python
checkpoint = ModelCheckpoint(dirpath="checkpoints", monitor="val_loss", mode="min", save_top_k=1)
trainer = L.Trainer(callbacks=[checkpoint], logger=CSVLogger("logs", name="run"))
```

## Resume and Load Confusion

Use the right path for the goal:

- Resume full training state: `trainer.fit(model, datamodule=dm, ckpt_path="last.ckpt")`.
- Load module weights/hyperparameters for inference: `model = LitModel.load_from_checkpoint("best.ckpt")`.
- Test/predict the best checkpoint after fitting: `trainer.test(model, datamodule=dm, ckpt_path="best")`.
- Manually save strategy-aware checkpoints: `trainer.save_checkpoint("file.ckpt")`.

Do not use deprecated `resume_from_checkpoint` patterns in new code.

## Strict Checkpoint Loading Fails

Symptoms:

- Missing or unexpected key errors from `load_from_checkpoint`.
- Constructor argument errors while loading.

Fixes:

- If constructor args were not saved, pass them to `load_from_checkpoint`.
- If architecture intentionally changed, set `self.strict_loading = False` in the module or load a filtered `state_dict` manually.
- If large objects were passed to `__init__`, use `self.save_hyperparameters(ignore=[...])` and pass those objects again during load.

## DataModule State Missing

Symptoms:

- Attribute errors for datasets on worker/rank processes.
- `train_dataloader` cannot find `self.train_ds`.
- Test/predict dataloaders fail after fit-only setup.

Fixes:

- Assign required dataset state in `setup(stage)`, not `prepare_data`.
- Handle `stage in (None, "fit")`, `"validate"`, `"test"`, and `"predict"` as needed.
- Keep downloads/tokenization-only work in `prepare_data`.
- Call `trainer.fit(model, datamodule=dm)`, `trainer.test(model, datamodule=dm)`, and `trainer.predict(model, datamodule=dm)` so Lightning manages hooks.

## Logger Problems

Symptoms:

- `LearningRateMonitor` complains because no logger is configured.
- TensorBoard files are not created.
- Metrics are not visible in CSV/TensorBoard.

Fixes:

- Set `logger=CSVLogger("logs", name="debug")` for a simple local logger.
- Do not set `logger=False` when using `LearningRateMonitor` or expecting metric files.
- Ensure `self.log(..., logger=True)` or the default logger behavior is not disabled.
- For TensorBoard, install the TensorBoard optional dependency or use `CSVLogger`.

## `fast_dev_run` Misuse

Symptoms:

- A smoke run succeeds but no normal checkpoint/log artifacts appear.
- User expects early stopping or long-run callbacks to behave normally during `fast_dev_run`.

Guidance:

- Use `fast_dev_run=True` only to test wiring and catch import/shape/hook errors.
- Follow with a tiny real run:

```python
trainer = L.Trainer(max_steps=2, limit_val_batches=1, callbacks=[checkpoint], logger=logger)
```

## Backend or Hardware Limitations

Symptoms:

- Requested GPU/TPU/MPS/DeepSpeed/FSDP but local environment only has CPU.
- Device count mismatch.
- Precision mode unsupported on the selected accelerator.

Fixes:

- For core training smoke tests, force CPU: `Trainer(accelerator="cpu", devices=1, max_steps=1)`.
- Do not claim GPU validation from a CPU-only smoke run.
- Route accelerator, strategy, precision, and distributed-launch depth to `../distributed-accelerators/SKILL.md`.

## API Boundary Misroutes

Route elsewhere when the failure is not training-core-owned:

- `LightningCLI`, config files, parser subclassing, `--trainer.*` flags: `../cli-configuration/SKILL.md`.
- Fabric `setup`, `launch`, `backward`, manual loop wrapping: `../fabric-expert-loops/SKILL.md`.
- FSDP, DeepSpeed, DDP spawn, GPU visibility, TPU, MPS, precision plugins: `../distributed-accelerators/SKILL.md`.
- Serving, export, endpoint validation, TorchScript/ONNX/TensorRT: `../deployment-serving/SKILL.md`.

## Smoke Script Fails

Run:

```bash
python sub-skills/training-core/scripts/lightning_smoke.py --max-steps 1 --fast-dev-run
```

Expected output contains `LIGHTNING_SMOKE_OK`. If it fails:

- Import error: fix package installation in the active environment.
- Shape error: compare user model batch shapes with the script's simple `(features, target)` convention.
- Monitor error: confirm `val_loss` is logged before checkpoint/early stopping checks.
- Logger/checkpoint path issue: rerun with `--default-root-dir` pointing to a writable directory.
