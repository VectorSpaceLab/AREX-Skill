# Checkpointing, Resume, and Fine-Tune Reference

`ImagenTrainer.save` and `ImagenTrainer.load` are the supported persistence API. Prefer them over manual `state_dict` saves because the trainer moves EMA modules and handles optimizer, scheduler, scaler, and step state.

## What `trainer.save(path)` Writes

`save(path, overwrite=True, without_optim_and_sched=False, **kwargs)` waits for all processes, returns early on non-checkpointing processes, and writes through the trainer's fsspec filesystem.

The checkpoint dictionary includes:

- `model`: the Imagen / ElucidatedImagen state dict.
- `version`: package version string.
- `steps`: per-unet step tensor.
- `scaler{index}` and `optim{index}` for each unet unless `without_optim_and_sched=True`.
- `scheduler{index}` and `warmup{index}` only when those schedulers exist.
- `ema`: EMA unet state when `use_ema=True` on the main process.
- Extra keyword payload passed to `save`.
- `imagen_type` and `imagen_params` only when the model was created by `ImagenConfig` or `ElucidatedImagenConfig` and therefore has `_config`.

`overwrite=False` asserts if the target already exists. Use this to protect manual checkpoints from accidental replacement.

## Commandable Checkpoints

A checkpoint is commandable by CLI sampling and `load_imagen_from_checkpoint` only when it contains both `imagen_type` and `imagen_params`. Those fields are added by `trainer.save` only if the model was created through config classes, because direct `Unet(...)` / `Imagen(...)` construction does not attach `_config`.

Use this pattern when future `imagen sample --model ...` or portable fine-tuning is required:

```python
from imagen_pytorch import ImagenConfig, ImagenTrainer, load_imagen_from_checkpoint

imagen = ImagenConfig(unets=[...], image_sizes=[...]).create()
trainer = ImagenTrainer(imagen=imagen)
# train ...
trainer.save("checkpoint.pt")

imagen_for_reuse = load_imagen_from_checkpoint("checkpoint.pt", load_ema_if_available=True)
trainer_for_finetune = ImagenTrainer(imagen=imagen_for_reuse)
```

If the checkpoint was made from direct model construction, reconstruct the same architecture in code and call `trainer.load(path)`. Do not expect CLI sampling to infer the architecture.

## `trainer.load(path)` Behavior

`load(path, only_model=False, strict=True, noop_if_not_exist=False)`:

1. Uses the trainer filesystem and asserts the file exists unless `noop_if_not_exist=True`.
2. Loads the checkpoint on CPU to avoid extra GPU memory pressure.
3. Prints a version mismatch warning if checkpoint and package versions differ.
4. Tries `self.imagen.load_state_dict(loaded['model'], strict=strict)`. On shape/name mismatch it attempts partial same-shape restoration and prints skipped layers.
5. If `only_model=True`, returns after model weights are restored.
6. Restores `steps`, per-unet optimizer/scaler state, and schedulers/warmup schedulers when present.
7. If optimizer/scaler restoration fails, prints that mixed precision may have changed and continues with fresh optimizer/scaler state.
8. If `use_ema=True`, expects `ema` in the checkpoint and restores it, again falling back to same-shape partial restoration on mismatch.
9. Returns the loaded checkpoint dictionary.

For fine-tuning on new data, choose deliberately:

- Full resume: same architecture and optimizer settings, then `trainer.load(path)`.
- Weight-only fine-tune: same architecture, then `trainer.load(path, only_model=True)` and start with fresh steps/optimizer/EMA state, or load EMA weights with `load_imagen_from_checkpoint(..., load_ema_if_available=True)` and construct a fresh trainer.
- Architecture surgery: use `strict=False` only when partial same-shape loading is intentional and record which layers were skipped.

## Managed Checkpoint Folders

Constructor arguments `checkpoint_path` and `checkpoint_every` must be both set or both omitted.

When set:

- The trainer creates/uses an fsspec filesystem. Local paths are safest.
- On construction, the checkpointing process looks for `*.pt` under `checkpoint_path` and loads the newest `checkpoint.<total_steps>.pt` if present.
- Every `checkpoint_every` total unet updates, `update()` calls `save_to_checkpoint_folder()`.
- Files are named `checkpoint.<total_steps>.pt`.
- `max_checkpoints_keep` keeps the newest N by parsed step number; values `<= 0` disable pruning.
- Local filesystem checkpointing uses local-main process; non-local filesystems use main process.

Because folder loading happens in `__init__`, set `checkpoint_path` only when automatic resume is desired. Otherwise instantiate normally and call `load()` explicitly after any setup decisions.

## Fsspec Notes

`checkpoint_fs` can be supplied to control storage directly. Without it, the trainer calls `url_to_fs` on `checkpoint_path` or `./`.

Operational guidance:

- Use plain local paths for reproducible smoke checks and ordinary local training.
- Test any cloud or custom fsspec path with a tiny save/load before a long run.
- In 2.1.0, URL-style checkpoint folder support has a known limitation in the bucket-prefix helper; unsupported or untested prefixes may fail before training starts. Use local staging, an explicit `checkpoint_fs`, or a verified custom filesystem adapter when cloud storage is required.
- Ensure every process has the same filesystem credentials/configuration under Accelerate.

## Resume Second Unet Pattern

For cascade training, train and save one unet stage, then start a fresh process for the next stage.

```python
# first launch/process
trainer = ImagenTrainer(imagen=imagen, only_train_unet_number=1)
trainer.add_train_dataset(dataset_for_unet1, batch_size=...)
trainer.train_step(unet_number=1, max_batch_size=...)
trainer.save("cascade.pt")

# second launch/process with the same config-created or reconstructed model
trainer = ImagenTrainer(imagen=imagen, only_train_unet_number=2)
trainer.load("cascade.pt")
trainer.add_train_dataset(dataset_for_unet2, batch_size=...)
trainer.train_step(unet_number=2, max_batch_size=...)
trainer.save("cascade.pt")
```

If later CLI sampling is required, ensure `imagen` in both processes came from config classes so the saved checkpoint remains commandable.
