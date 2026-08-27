---
name: data-loading
description: "Load and inspect fastMRI HDF5 data, datasets, masks, transforms,
  and data sampling controls."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# fastMRI Data Loading

Use this sub-skill when the task is about reading fastMRI HDF5 files, validating split/key layout, constructing `SliceDataset`, `CombinedSliceDataset`, or `AnnotatedSliceDataset`, choosing mask functions, applying `UnetDataTransform` or `VarNetDataTransform`, or debugging dataset sampling/cache behavior.

## Route Here

- The user has knee or brain fastMRI `.h5` data and needs to identify whether it is `singlecoil` or `multicoil`, train/val/test/challenge, or missing target reconstructions.
- The user needs Python objects such as `SliceDataset`, `CombinedSliceDataset`, `AnnotatedSliceDataset`, `RandomMaskFunc`, `EquiSpacedMaskFunc`, `EquispacedMaskFractionFunc`, `UnetDataTransform`, or `VarNetDataTransform`.
- The user sees loader errors involving `challenge`, `sample_rate`, `volume_sample_rate`, `dataset_cache.pkl`, HDF5 keys, or `ismrmrd_header` metadata.
- The user wants safe inspection or tiny synthetic fastMRI-like HDF5 fixtures before training, inference, or submission work.

## Use These Files

- [references/data-formats.md](references/data-formats.md) explains fastMRI HDF5 split layouts, required keys, target reconstruction expectations, metadata, and practical directory checks.
- [references/api-reference.md](references/api-reference.md) summarizes the dataset, mask, transform, sampling, cache, and annotation APIs with exact constructor signatures.
- [references/troubleshooting.md](references/troubleshooting.md) maps common loader, mask, transform, cache, and optional dependency failures to fixes.
- [scripts/inspect_fastmri_h5.py](scripts/inspect_fastmri_h5.py) safely summarizes `.h5` keys, k-space shapes, reconstruction keys, attrs, masks, and ISMRMRD crop metadata.
- [scripts/create_tiny_fastmri_h5.py](scripts/create_tiny_fastmri_h5.py) creates deterministic lightweight fastMRI-like HDF5 files for loader/schema validation.

## Boundary Routing

- For FFT, complex tensor conventions, `rss`, crop math, or operator shape debugging, route to [mri-operators](../mri-operators/).
- For `FastMriDataModule`, dataloaders, Lightning trainers, DDP samplers, and full training loops, route to [lightning-training](../lightning-training/).
- For saved reconstructions, file metrics, leaderboard-style outputs, or submission HDF5 files, route to [evaluation-submission](../evaluation-submission/).

## Quick Decision Path

1. Inspect one or more `.h5` files with `scripts/inspect_fastmri_h5.py` and confirm `kspace`, optional `mask`, optional reconstruction target, attrs, and `ismrmrd_header` crop metadata.
2. Choose `challenge="singlecoil"` for single-coil knee data or `challenge="multicoil"` for multicoil knee/brain data; invalid challenge names raise a `ValueError`.
3. Use `SliceDataset` for one split, `CombinedSliceDataset` for multiple roots, or `AnnotatedSliceDataset` when fastMRI+ annotations are needed.
4. Use either slice sampling (`sample_rate`) or volume sampling (`volume_sample_rate`), never both; use `raw_sample_filter` and `num_cols` for metadata/shape filtering.
5. Choose a mask with `create_mask_for_mask_type`, then pass it to `UnetDataTransform` or `VarNetDataTransform` only when synthetic undersampling is needed.
