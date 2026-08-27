# Lightning Training Workflows

This guide adapts the repository U-Net and VarNet demos into source-independent workflows with explicit paths and CPU-safe debug options.

## Required Decisions

Before writing code or rendering a command, decide:

1. Model family: `unet` or `varnet`.
2. Challenge: `singlecoil` or `multicoil`.
3. Data root: a path containing challenge split directories such as `singlecoil_train` and `singlecoil_val` or `multicoil_train` and `multicoil_val`.
4. Output root: Lightning `default_root_dir` for logs, checkpoints, and test reconstructions.
5. Runtime mode: `train` for fitting or `test` for reconstruction generation.
6. Hardware path: CPU debug, single-device training, or DDP.
7. Sampling: `sample_rate` by slice or `volume_sample_rate` by volume, not both for the same split.

Do not depend on `fastmri_dirs.yaml` in generated user scripts. The demos call `fetch_dir` to discover `knee_path` and `log_path`, but robust generated workflows should require explicit `data_path` and `default_root_dir` inputs.

## U-Net Workflow

Use U-Net for baseline image-domain reconstruction.

Recommended wiring:

```python
mask = create_mask_for_mask_type("random", [0.08], [4])
train_transform = UnetDataTransform("singlecoil", mask_func=mask, use_seed=False)
val_transform = UnetDataTransform("singlecoil", mask_func=mask)
test_transform = UnetDataTransform("singlecoil")

data_module = FastMriDataModule(
    data_path=Path(data_path),
    challenge="singlecoil",
    train_transform=train_transform,
    val_transform=val_transform,
    test_transform=test_transform,
    test_split=test_split,
    test_path=Path(test_path) if test_path else None,
    batch_size=batch_size,
    num_workers=num_workers,
    distributed_sampler=use_ddp,
)

model = UnetModule(
    in_chans=1,
    out_chans=1,
    chans=32,
    num_pool_layers=4,
    drop_prob=0.0,
    lr=0.001,
    lr_step_size=40,
    lr_gamma=0.1,
    weight_decay=0.0,
)
```

Adaptations:

- Use `mask_type="random"` for the original knee U-Net demo.
- For brain or multicoil U-Net experiments, prefer `equispaced_fraction` only after confirming the data challenge and target preparation match the intended transform behavior.
- For fast CPU debug, shrink the model, set `num_workers=0`, set `batch_size=1`, and use Lightning `fast_dev_run=True` or `limit_train_batches=1`, `limit_val_batches=1`, `max_epochs=1`.

## VarNet Workflow

Use VarNet for multicoil end-to-end variational reconstruction.

Recommended wiring:

```python
mask = create_mask_for_mask_type("equispaced_fraction", [0.08], [4])
train_transform = VarNetDataTransform(mask_func=mask, use_seed=False)
val_transform = VarNetDataTransform(mask_func=mask)
test_transform = VarNetDataTransform()

data_module = FastMriDataModule(
    data_path=Path(data_path),
    challenge="multicoil",
    train_transform=train_transform,
    val_transform=val_transform,
    test_transform=test_transform,
    test_split=test_split,
    test_path=Path(test_path) if test_path else None,
    batch_size=batch_size,
    num_workers=num_workers,
    distributed_sampler=use_ddp,
)

model = VarNetModule(
    num_cascades=8,
    pools=4,
    chans=18,
    sens_pools=4,
    sens_chans=8,
    lr=0.001,
    lr_step_size=40,
    lr_gamma=0.1,
    weight_decay=0.0,
)
```

Adaptations:

- Keep `challenge="multicoil"` for normal VarNet use; the demo notes only multicoil is implemented there.
- Use `equispaced_fraction` for VarNet defaults. This maps to `EquispacedMaskFractionFunc`, which adjusts spacing to match the desired acceleration rate.
- For CPU smoke tests, reduce `num_cascades`, `pools`, `chans`, `sens_pools`, and `sens_chans`; do not copy the demo's two-GPU DDP defaults.

## CPU Fast-Dev Path

When the goal is only to verify code, transforms, and Lightning wiring:

- Set `accelerator="cpu"` or omit accelerator in older Lightning versions.
- Set `devices=1` in modern Lightning, or `gpus=0` in older Lightning.
- Use `fast_dev_run=True` for a full train/val/test sanity path, or set `max_epochs=1`, `limit_train_batches=1`, and `limit_val_batches=1` for a less intrusive debug run.
- Use `num_workers=0` to avoid multiprocessing surprises on small fixtures.
- Set `use_dataset_cache_file=False` for synthetic or temporary datasets.
- Use explicit `data_path` and `default_root_dir` placeholders; do not create or require a directory YAML file.

The bundled command renderer can produce CPU-safe command guidance from this sub-skill directory:

```bash
python scripts/build_training_command.py \
  --model unet \
  --mode train \
  --data-path DATA_ROOT \
  --default-root-dir RUN_ROOT \
  --cpu-fast-dev
```

If the skill has been imported into a central skills directory, first locate `fastmri/sub-skills/lightning-training/`, then run the script from that directory or pass the script path explicitly. The renderer outputs command scaffolding for a user-owned training entrypoint; it is not itself a complete trainer.

## DDP and Volume Dispatch

The data module has two DDP-specific behaviors that generated workflows should preserve:

- `distributed_sampler=True` uses a regular `DistributedSampler` for training and `fastmri.data.VolumeSampler` for validation/test so slices from the same volume are dispatched coherently.
- `worker_init_fn` reseeds transform `mask_func` objects. Under DDP it incorporates the distributed rank, worker id, and combined dataset index so mask randomness does not collapse across ranks.

For older Lightning demo style, DDP was represented by `strategy="ddp"` in the demos and checked with `args.accelerator in ("ddp", "ddp_cpu")` before constructing the data module. Modern Lightning separates `accelerator`, `devices`, and `strategy`; generated code should compute `distributed_sampler` from the chosen strategy, not blindly from a stale `accelerator` string.

## Checkpoint and Resume Pattern

Use a stable output root:

```python
run_root = Path(default_root_dir)
checkpoint_dir = run_root / "checkpoints"
checkpoint_dir.mkdir(parents=True, exist_ok=True)
checkpoint_callback = pl.callbacks.ModelCheckpoint(
    dirpath=checkpoint_dir,
    save_top_k=True,
    verbose=True,
    monitor="validation_loss",
    mode="min",
)
```

For old Lightning, resume may be `resume_from_checkpoint`. For modern Lightning, pass `ckpt_path` to `trainer.fit(...)` or `trainer.test(...)` if required by the installed version. Preserve these intent-level rules:

- Prefer an explicit checkpoint path supplied by the user.
- If implementing auto-resume, select the newest `*.ckpt` from `default_root_dir / "checkpoints"`.
- Keep checkpoint paths under the explicit output root.
- During `test`, expect reconstructions under `default_root_dir / "reconstructions"`.

## Leaderboard-Style Training

Use `combine_train_val=True` when training a final model after validation choices are already settled. It combines `challenge_train` and `challenge_val` directories into one training dataset.

Recommended safeguards:

- Keep `test_split="challenge"` or provide `test_path` explicitly for final inference.
- Record the held-out validation policy outside the runtime code; after combining train and val, validation metrics no longer estimate generalization in the same way.
- Preserve `distributed_sampler=True` for DDP so volume dispatch still works in validation/test.
- Do not set `sample_rate` and `volume_sample_rate` simultaneously while combining splits.

## Advanced VarNet Examples

The adaptive VarNet and feature VarNet example directories are reference-only for this sub-skill. Their READMEs recommend separate pinned environments because their PyTorch Lightning requirements differ from the base fastMRI installation. Do not merge their arguments into the baseline `VarNetModule` workflow unless the user explicitly asks for those examples and accepts a separate environment.
