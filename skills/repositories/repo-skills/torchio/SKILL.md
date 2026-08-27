---
name: torchio
description: "Use TorchIO 2.0 for medical image loading, preprocessing,
  augmentation, patch-based training/inference, CLI conversion, and I/O
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TorchIO

Use this skill when working with TorchIO, a PyTorch-oriented library for 3D medical image loading, preprocessing, augmentation, patch sampling, dense inference, and command-line image utilities.

## Start Here

1. Confirm the package imports:
   ```python
   import torchio as tio
   print(tio.__version__)
   ```
2. Use TorchIO 2.0 names in generated code: `Flip`, `Affine`, `Noise`, `Motion`, `BiasField`, `Spike`, and `Ghosting` instead of old `Random*` class names.
3. Build in-memory images with `tio.ScalarImage(tensor)` or `tio.LabelMap(tensor)` using 4D `(C, I, J, K)` tensors.
4. Keep runtime examples self-contained with synthetic tensors or user-provided image paths; do not depend on TorchIO repository examples or tests.

## Route by Task

- **Data containers and validation**: use [data-model](sub-skills/data-model/SKILL.md) for `Image`, `ScalarImage`, `LabelMap`, `Subject`/`Study`, affines, points, bounding boxes, lazy/eager source handling, saving, and source-shape errors.
- **Preprocessing and augmentation**: use [transforms](sub-skills/transforms/SKILL.md) for transform families, `Compose`, `OneOf`, `SomeOf`, include/exclude routing, per-instance batches, history/inverse behavior, and MONAI/Cornucopia adapters.
- **Patch training and dense inference**: use [patch-workflows](sub-skills/patch-workflows/SKILL.md) for `GridSampler`, `UniformSampler`, `WeightedSampler`, `LabelSampler`, `Queue`, `SubjectsLoader`, `PatchLocation`, and `PatchAggregator`.
- **CLI, conversion, visualization, and remote I/O**: use [cli-and-io](sub-skills/cli-and-io/SKILL.md) for the `torchio` console entry point, `info`, `convert`, `transform`, `cache`, plotting/animation, NIfTI-Zarr, cloud/remote extras, and cache/download caveats.

## Shared References

- Read [API quick map](references/api-quick-map.md) when choosing which TorchIO class or sub-skill owns a task.
- Read [troubleshooting](references/troubleshooting.md) for install/import, optional dependency, API drift, tensor shape, CLI, and workflow-routing failures.
- Read [repo provenance](references/repo-provenance.md) before refreshing this skill against a newer TorchIO checkout.

## Safe Smoke Checks

Run the nearest bundled script after installing TorchIO and its base dependencies:

```bash
python sub-skills/data-model/scripts/data_model_smoke.py
python sub-skills/transforms/scripts/transform_history_smoke.py
python sub-skills/transforms/scripts/include_exclude_smoke.py
python sub-skills/patch-workflows/scripts/patch_workflow_smoke.py
python sub-skills/cli-and-io/scripts/torchio_cli_smoke.py --print-only
```

Use full CLI smoke only when local temporary file creation and NIfTI conversion are acceptable:

```bash
python sub-skills/cli-and-io/scripts/torchio_cli_smoke.py
```

## Install and Extras Guidance

- Base install should provide `torch`, `nibabel`, `SimpleITK`, `numpy`, `tyro`, `fsspec[http]`, and TorchIO core APIs.
- Optional extras are task-specific: `plot` for Matplotlib visualization, `video` for GIF/MP4 animation, `monai` and `cornucopia` for transform adapters, `zarr` for NIfTI-Zarr, and cloud extras for `s3`, `azure`, or `gcs` remote storage.
- CPU is sufficient for the skill workflows unless the user's own model or pipeline requires CUDA.

## Common Decisions

- Use `ScalarImage` for continuous intensity data and `LabelMap` for masks/segmentations so spatial transforms use correct interpolation.
- Use `Subject` to keep multiple images and metadata aligned through transforms and patch sampling.
- Use `include`/`exclude` transform arguments when only some image keys should change.
- Use `GridSampler` plus `PatchAggregator` for dense inference; use `Queue` plus random samplers for stochastic patch training.
- Use the CLI for one-off inspection/conversion and the Python API for pipelines that need precise parameter control, batching, or model integration.
