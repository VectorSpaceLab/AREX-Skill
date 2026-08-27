---
name: lightning-training
description: "Build fastMRI PyTorch Lightning training and test workflows with
  FastMriDataModule, UnetModule, VarNetModule, masks, transforms, checkpoints,
  and CPU-safe debug commands."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# fastMRI Lightning Training

Use this sub-skill when an agent needs to train, debug, resume, or test fastMRI `UnetModule` or `VarNetModule` workflows with PyTorch Lightning. Keep raw HDF5 layout and split details in [data-loading](../data-loading/SKILL.md), raw model constructor details in [model-architectures](../model-architectures/SKILL.md), and final metric/submission packaging in [evaluation-submission](../evaluation-submission/SKILL.md).

## Start Here

- Use [references/training-workflows.md](references/training-workflows.md) when writing an end-to-end train/test script, adapting a U-Net or VarNet demo, choosing CPU fast-dev settings, or preserving DDP volume dispatch.
- Use [references/api-reference.md](references/api-reference.md) when wiring exact `FastMriDataModule`, `UnetModule`, `VarNetModule`, mask, transform, checkpoint, or test-output APIs.
- Use [references/troubleshooting.md](references/troubleshooting.md) when diagnosing Lightning version drift, missing directory config, CPU-only runs, mask/challenge mismatches, sample-rate conflicts, cache/import failures, checkpoint resume, or reconstruction paths.
- Use [scripts/build_training_command.py](scripts/build_training_command.py) to render explicit, source-independent command guidance for U-Net or VarNet training, test, CPU debug, DDP, and leaderboard-style `combine_train_val` runs.

## Routing Rules

- Prefer `UnetModule` with `UnetDataTransform` for baseline image-domain training on singlecoil or multicoil challenge data.
- Prefer `VarNetModule` with `VarNetDataTransform` for multicoil end-to-end variational network training; keep VarNet challenge as `multicoil` unless the surrounding code has explicitly implemented a different path.
- Use `create_mask_for_mask_type` with `random` for the classic knee U-Net demo and `equispaced_fraction` for brain/multicoil-style and VarNet workflows; exact mask classes include `EquiSpacedMaskFunc` and `EquispacedMaskFractionFunc`.
- For DDP, set the data module `distributed_sampler=True` so validation/test volumes dispatch coherently, and let worker seeding handle `mask_func` randomness per worker/rank.
- For CPU-only or quick verification, render a one-device `fast_dev_run` or one-batch debug path instead of copying demo GPU/DDP defaults.
- For leaderboard-style training, use `combine_train_val=True` only after validation choices are intentional, then test with explicit `test_path` or `test_split` and save reconstructions under the Lightning `default_root_dir`.
