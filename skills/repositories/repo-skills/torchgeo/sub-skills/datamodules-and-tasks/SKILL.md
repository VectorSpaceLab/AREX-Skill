---
name: datamodules-and-tasks
description: "Use for TorchGeo Lightning DataModules, CLI/config runs, task
  classes, losses, metrics, prediction/plot hooks, and training workflow
  wiring."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# TorchGeo datamodules and tasks

Use this sub-skill when wiring TorchGeo into Lightning training, validation, testing, prediction, CLI configs, or task modules.

## DataModule operating facts

- `BaseDataModule` wraps a dataset class, `batch_size`, `num_workers`, split datasets, split dataloaders, and Kornia augmentation hooks.
- `prepare_data()` may download data when `download=True`; it must not create split state. `setup(stage)` creates datasets/samplers and is called on every process.
- `GeoDataModule` is for `GeoDataset` classes and sets `collate_fn = stack_samples`. It manages `RandomPatchSampler`, `GriddedPatchSampler`, and batch samplers for split-specific patch extraction.
- `NonGeoDataModule` is for integer-indexed datasets and ordinary PyTorch dataloader shuffle/split semantics.
- `on_after_batch_transfer()` applies the split-specific augmentation after the batch reaches the device. This is where Kornia GPU augmentations belong.

## Task classes

TorchGeo task modules are Lightning modules for common geospatial ML problems:

- `Classification`: timm-backed image classification with `weights`, `in_channels`, task type, class/label counts, losses, and optional frozen backbone.
- `SemanticSegmentation`: SMP or TorchGeo FCN segmentation with `model`, `backbone`, `weights`, `in_channels`, multiclass/multilabel/binary settings, losses, and freeze options.
- Other task modules cover change detection, detection, instance segmentation, regression, temporal/spatiotemporal tasks, MAE, MoCo, BYOL, SimCLR, and IO benchmark workflows.

Before changing a task, inspect its corresponding `tests/tasks/test_<task>.py` for constructor matrix, batch schema, metric expectations, and trainer smoke coverage.

## CLI/config workflow

- The `torchgeo` console script is declared as `torchgeo.main:main`.
- Prefer JSONArgParse/Lightning config files for reproducible training. Explicitly name the datamodule, task/model, trainer, optimizer/scheduler parameters, and paths.
- For smoke checks, use small fake fixtures and `max_epochs=1`, small batch sizes, and no checkpoint downloads.

## Batch and mask handling

- Images are typically tensors shaped `(B, C, H, W)`; some spatiotemporal paths use `(B, T, C, H, W)` and may flatten or route to spatiotemporal tasks.
- Segmentation masks may require dtype conversion for Kornia and restoration before loss/metrics.
- Detection and instance segmentation batches can contain variable-length boxes/masks; use the datamodule utility collate function used by the tests.

## Read next

- [reference](references/datamodules-and-tasks.md) for task-specific examples and verification candidates.
- Root [troubleshooting](../../references/troubleshooting.md) for Lightning, Kornia, and optional dependency failures.
