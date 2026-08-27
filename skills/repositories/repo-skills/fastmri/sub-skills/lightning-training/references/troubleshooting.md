# Lightning Training Troubleshooting

Use this reference when a fastMRI Lightning train/test workflow fails during argument parsing, data module setup, transform construction, distributed training, checkpoint resume, or reconstruction writing.

## Lightning API Version Drift

Symptoms:

- `AttributeError: type object 'Trainer' has no attribute 'add_argparse_args'`
- `AttributeError: type object 'Trainer' has no attribute 'from_argparse_args'`
- `TypeError` for `gpus`, `accelerator`, `strategy`, `resume_from_checkpoint`, or `replace_sampler_ddp`

Cause:

The repository demos use an older PyTorch Lightning API. Modern Lightning versions often prefer direct `pl.Trainer(...)`, `accelerator="cpu"`/`"gpu"`, `devices=...`, `strategy="ddp"`, and explicit `ckpt_path` in `fit`/`test` calls.

Fix:

- Keep the fastMRI module/data APIs, but rewrite trainer construction for the installed Lightning version.
- Replace demo `gpus=0` with `accelerator="cpu", devices=1` when required.
- Replace demo DDP settings with `accelerator="gpu", devices=N, strategy="ddp"` when required.
- Compute `distributed_sampler=True` whenever the chosen strategy is DDP, even if the installed Lightning argument names changed.
- Replace `resume_from_checkpoint` with `ckpt_path=...` in `trainer.fit(...)` or `trainer.test(...)` if the installed Lightning requires it.

## Missing fastmri_dirs.yaml

Symptoms:

- A demo script asks for `fastmri_dirs.yaml` or fails while calling `fetch_dir`.
- Data and log paths resolve to missing placeholders.

Cause:

Repository demos use `fetch_dir` with a relative YAML file for local convenience.

Fix:

- Prefer generated scripts that require explicit `--data_path` and `--default_root_dir`.
- If maintaining a demo-compatible script, create a local directory config from a template only as a user convenience, not as a hard dependency.
- Keep logs/checkpoints under `default_root_dir` and test reconstructions under `default_root_dir / "reconstructions"`.

## CPU-Only Machine Uses GPU/DDP Defaults

Symptoms:

- CUDA device errors.
- DDP process launch failures.
- Training hangs during distributed initialization.

Cause:

The repository U-Net and VarNet demos default to two GPUs and DDP-style settings.

Fix:

- Use a CPU debug path: `fast_dev_run=True`, `num_workers=0`, `batch_size=1`, and one device.
- Reduce model size for smoke tests: smaller U-Net `chans`/`num_pool_layers`, or smaller VarNet `num_cascades`/`chans`/`pools`/`sens_*`.
- Disable DDP-only sampler behavior when not actually using DDP by setting `distributed_sampler=False`.

## Challenge and Mask Mismatch

Symptoms:

- Transform errors or unexpected tensor shapes.
- VarNet training fails on singlecoil data.
- Metrics or reconstructions are nonsensical after a seemingly valid run.

Cause:

Transforms, data challenge, and mask policy must match the intended model family.

Fix:

- U-Net knee baseline: start with `challenge="singlecoil"`, `UnetDataTransform`, and `mask_type="random"`.
- Brain or multicoil-style U-Net experiments: consider `equispaced_fraction` only after checking the data and target preparation.
- VarNet baseline: use `challenge="multicoil"`, `VarNetDataTransform`, and `mask_type="equispaced_fraction"`.
- Use exact mask names carefully: CLI value `equispaced` maps to `EquiSpacedMaskFunc`; CLI value `equispaced_fraction` maps to `EquispacedMaskFractionFunc`.

## sample_rate and volume_sample_rate Conflict

Symptoms:

- `ValueError: Can set sample_rate or volume_sample_rate, but not both.`
- Similar errors for validation or test sample rates.

Cause:

`FastMriDataModule` allows either slice-level or volume-level sampling for a split, not both.

Fix:

- For train, choose one of `sample_rate` or `volume_sample_rate`.
- For val, choose one of `val_sample_rate` or `val_volume_sample_rate`.
- For test, choose one of `test_sample_rate` or `test_volume_sample_rate`.
- Prefer `volume_sample_rate` when debugging volume-level validation/test behavior.

## DDP Validation or Test Volume Dispatch Is Wrong

Symptoms:

- Duplicate or missing slices in validation/test aggregation.
- Per-volume metrics behave inconsistently under DDP.
- Reconstructions have incomplete volumes.

Cause:

DDP needs volume-aware validation/test sampling. The fastMRI data module only enables that when `distributed_sampler=True`.

Fix:

- Set `distributed_sampler=True` for DDP.
- In older Lightning demo semantics, also use `replace_sampler_ddp=False` so Lightning does not replace the data module sampler.
- In modern Lightning, verify equivalent sampler replacement behavior for the installed version.

## Mask Randomness Collapses Across Workers

Symptoms:

- Training masks look identical across ranks/workers when DDP should diversify them.
- Reproducibility changes unexpectedly after increasing workers.

Cause:

The data module reseeds transform `mask_func` objects in `worker_init_fn`. Under DDP, the seed includes distributed rank and worker identity.

Fix:

- Pass mask functions through `UnetDataTransform` or `VarNetDataTransform`; do not reimplement worker seeding outside the data module unless necessary.
- Use `use_seed=False` for training transforms and default fixed seeding for validation transforms.
- Keep `distributed_sampler=True` for DDP workflows.

## combine_train_val Changes Validation Meaning

Symptoms:

- Validation no longer measures a held-out split as expected.
- Final leaderboard training accidentally uses validation data before model selection is complete.

Cause:

`combine_train_val=True` creates one training dataset from train and val split directories.

Fix:

- Use `combine_train_val=True` only for final leaderboard-style training after hyperparameters and checkpoint policy are selected.
- Use explicit `test_split="challenge"` or `test_path` for final inference.
- Avoid combining train and val during exploratory model selection.

## Checkpoint Resume Fails

Symptoms:

- `resume_from_checkpoint` is ignored or rejected.
- Training starts from scratch despite existing checkpoints.
- Test cannot load the intended model.

Cause:

Checkpoint resume APIs changed across Lightning versions, and demos only auto-select the newest checkpoint if `resume_from_checkpoint` is unset.

Fix:

- Prefer explicit checkpoint paths from the user.
- For old Lightning, set `args.resume_from_checkpoint` before `Trainer.from_argparse_args(args)` or pass the equivalent supported argument.
- For modern Lightning, pass `ckpt_path` to `trainer.fit(model, datamodule=..., ckpt_path=...)` or `trainer.test(model, datamodule=..., ckpt_path=...)`.
- Keep auto-discovery limited to `default_root_dir / "checkpoints"`.

## Test Output Location Is Surprising

Symptoms:

- Test completes, but no reconstructions appear where expected.
- Reconstructions appear in the current working directory.

Cause:

`MriModule.test_epoch_end` saves to `trainer.default_root_dir / "reconstructions"` when a trainer is attached; otherwise it falls back to the current working directory.

Fix:

- Always set an explicit `default_root_dir`.
- Run test through `trainer.test(model, datamodule=data_module)`.
- Look for `.h5` reconstruction files under `default_root_dir / "reconstructions"`.

## ModuleNotFoundError: requests

Symptoms:

- `import fastmri.data` or data utility import fails with `ModuleNotFoundError: requests`.

Cause:

This checkout imports `requests` from fastMRI data utilities, but `setup.cfg` does not declare it.

Fix:

- Install `requests` in the runtime environment.
- Re-run a small import smoke check before launching long training jobs.

## Advanced Adaptive or Feature VarNet Dependency Drift

Symptoms:

- Adaptive VarNet or feature VarNet examples fail with Lightning or PyTorch version conflicts.

Cause:

Their READMEs recommend separate pinned environments because their Lightning requirements differ from the base fastMRI installation.

Fix:

- Treat those examples as separate workflows, not as drop-in arguments for baseline `VarNetModule`.
- Create a separate environment if the user explicitly asks to reproduce those examples.
