# Lightning Training API Reference

This reference captures the fastMRI Lightning APIs needed to build training and test workflows without opening the original repository examples.

## Imports

```python
from pathlib import Path

import pytorch_lightning as pl
from fastmri.data.subsample import create_mask_for_mask_type
from fastmri.data.transforms import UnetDataTransform, VarNetDataTransform
from fastmri.pl_modules import FastMriDataModule, UnetModule, VarNetModule
```

If importing `fastmri.data` fails with `ModuleNotFoundError: requests`, install `requests` in the runtime environment; this checkout imports it from data utilities even though it is not declared in `setup.cfg`.

## FastMriDataModule

Exact signature:

```python
FastMriDataModule(
    data_path: Path,
    challenge: str,
    train_transform: Callable,
    val_transform: Callable,
    test_transform: Callable,
    combine_train_val: bool = False,
    test_split: str = "test",
    test_path: Optional[Path] = None,
    sample_rate: Optional[float] = None,
    val_sample_rate: Optional[float] = None,
    test_sample_rate: Optional[float] = None,
    volume_sample_rate: Optional[float] = None,
    val_volume_sample_rate: Optional[float] = None,
    test_volume_sample_rate: Optional[float] = None,
    train_filter: Optional[Callable] = None,
    val_filter: Optional[Callable] = None,
    test_filter: Optional[Callable] = None,
    use_dataset_cache_file: bool = True,
    batch_size: int = 1,
    num_workers: int = 4,
    distributed_sampler: bool = False,
)
```

Key behavior:

- `data_path` is the root containing split directories such as `singlecoil_train`, `singlecoil_val`, `singlecoil_test`, `multicoil_train`, `multicoil_val`, or `multicoil_test`.
- `challenge` is `singlecoil` or `multicoil`; it controls split directory prefixes and transform behavior.
- `test_split` selects `val`, `test`, or `challenge`; `test_path` overrides `data_path / f"{challenge}_{test_split}"` for test dataloaders.
- `combine_train_val=True` builds a combined training dataset from train and val split directories for leaderboard-style training.
- Use either `sample_rate` or `volume_sample_rate` per split, never both; the same rule applies to `val_sample_rate`/`val_volume_sample_rate` and `test_sample_rate`/`test_volume_sample_rate`.
- `train_filter`, `val_filter`, and `test_filter` receive raw sample metadata and can include/exclude samples before dataloader creation.
- `use_dataset_cache_file=True` caches dataset metadata and calls split datasets in `prepare_data`; set it false for tiny synthetic tests or cache-related debugging.
- `distributed_sampler=True` uses `DistributedSampler` for training and `fastmri.data.VolumeSampler` for validation/test volume dispatch; set it true for DDP.
- Worker initialization reseeds any transform `mask_func`; under DDP it includes the distributed rank so each worker/rank gets deterministic but distinct mask RNG state.

## Masks and Transforms

Create masks with:

```python
mask = create_mask_for_mask_type(mask_type, center_fractions, accelerations)
```

Supported CLI-style `mask_type` values include `random`, `equispaced`, `equispaced_fraction`, `magic`, and `magic_fraction`. Exact class names include `EquiSpacedMaskFunc` for `equispaced` and `EquispacedMaskFractionFunc` for `equispaced_fraction`.

Use U-Net transforms:

```python
train_transform = UnetDataTransform(challenge, mask_func=mask, use_seed=False)
val_transform = UnetDataTransform(challenge, mask_func=mask)
test_transform = UnetDataTransform(challenge)
```

Use VarNet transforms:

```python
train_transform = VarNetDataTransform(mask_func=mask, use_seed=False)
val_transform = VarNetDataTransform(mask_func=mask)
test_transform = VarNetDataTransform()
```

The training transform sets `use_seed=False` to vary random masks across epochs. Validation uses the default fixed seeding, and test normally omits the mask because held-out data may already be masked according to the challenge.

## UnetModule

Exact signature:

```python
UnetModule(
    in_chans=1,
    out_chans=1,
    chans=32,
    num_pool_layers=4,
    drop_prob=0.0,
    lr=0.001,
    lr_step_size=40,
    lr_gamma=0.1,
    weight_decay=0.0,
    **kwargs,
)
```

`UnetModule` subclasses `MriModule`, so `num_log_images` can be passed through `**kwargs`. It trains with L1 loss on normalized images, validates with image metrics, and test outputs reconstruction arrays keyed by filename/slice.

Demo-aligned U-Net defaults:

- `challenge="singlecoil"` unless training a multicoil U-Net with intentionally prepared image targets.
- `mask_type="random"`, `center_fractions=[0.08]`, `accelerations=[4]` for the classic knee-style baseline.
- `chans=32`, `num_pool_layers=4`, `drop_prob=0.0`, `lr=0.001`, `lr_step_size=40`, `lr_gamma=0.1`, `weight_decay=0.0` for normal training.
- For CPU or synthetic smoke tests, reduce `chans` and `num_pool_layers` and enable `fast_dev_run` or one-batch trainer limits.

## VarNetModule

Exact signature:

```python
VarNetModule(
    num_cascades: int = 12,
    pools: int = 4,
    chans: int = 18,
    sens_pools: int = 4,
    sens_chans: int = 8,
    lr: float = 0.0003,
    lr_step_size: int = 40,
    lr_gamma: float = 0.1,
    weight_decay: float = 0.0,
    **kwargs,
)
```

`VarNetModule` subclasses `MriModule`, so `num_log_images` can be passed through `**kwargs`. It trains an end-to-end variational network with `SSIMLoss`, center-crops validation output/target to the smallest shape, and test crops output to `batch.crop_size` with a special smaller-output guard.

Demo-aligned VarNet defaults:

- `challenge="multicoil"`; the repository demo says only multicoil is implemented for VarNet.
- `mask_type="equispaced_fraction"`, `center_fractions=[0.08]`, `accelerations=[4]` for the default VarNet demo.
- Demo script uses `num_cascades=8`, `pools=4`, `chans=18`, `sens_pools=4`, `sens_chans=8`, `lr=0.001`, `lr_step_size=40`, `lr_gamma=0.1`, `weight_decay=0.0`.
- Live module defaults use `num_cascades=12` and `lr=0.0003`; choose deliberately rather than mixing defaults accidentally.

## Trainer, Checkpoints, and Test Outputs

The repository demos use older Lightning helpers:

```python
parser = pl.Trainer.add_argparse_args(parser)
trainer = pl.Trainer.from_argparse_args(args)
```

Modern Lightning may require direct `pl.Trainer(...)` construction and renamed accelerator/device arguments. Preserve the semantics rather than the old helper calls.

Checkpoint behavior from the demos:

- Create `default_root_dir / "checkpoints"` before training.
- Add `pl.callbacks.ModelCheckpoint(dirpath=..., save_top_k=True, verbose=True, monitor="validation_loss", mode="min")`.
- If no explicit checkpoint is set and checkpoint files exist, resume from the newest `*.ckpt` in that checkpoint directory.

Test output behavior from `MriModule`:

- `trainer.test(model, datamodule=data_module)` calls the module test epoch hook.
- Reconstructions are saved to `Path(trainer.default_root_dir) / "reconstructions"`.
- Without an attached trainer, the fallback is `Path.cwd() / "reconstructions"`; avoid relying on that in scripts.

## Minimal Program Skeleton

```python
mask = create_mask_for_mask_type(mask_type, center_fractions, accelerations)
if model_kind == "unet":
    train_transform = UnetDataTransform(challenge, mask_func=mask, use_seed=False)
    val_transform = UnetDataTransform(challenge, mask_func=mask)
    test_transform = UnetDataTransform(challenge)
    model = UnetModule(chans=chans, num_pool_layers=num_pool_layers)
else:
    train_transform = VarNetDataTransform(mask_func=mask, use_seed=False)
    val_transform = VarNetDataTransform(mask_func=mask)
    test_transform = VarNetDataTransform()
    model = VarNetModule(num_cascades=num_cascades, chans=chans)

data_module = FastMriDataModule(
    data_path=Path(data_path),
    challenge=challenge,
    train_transform=train_transform,
    val_transform=val_transform,
    test_transform=test_transform,
    combine_train_val=combine_train_val,
    test_split=test_split,
    test_path=Path(test_path) if test_path else None,
    sample_rate=sample_rate,
    volume_sample_rate=volume_sample_rate,
    batch_size=batch_size,
    num_workers=num_workers,
    distributed_sampler=distributed_sampler,
)

trainer = pl.Trainer(default_root_dir=default_root_dir, fast_dev_run=fast_dev_run)
if mode == "train":
    trainer.fit(model, datamodule=data_module)
else:
    trainer.test(model, datamodule=data_module)
```
