---
name: ultra-fast-lane-detection
description: "Routes Ultra-Fast-Lane-Detection workflows for data preparation,
  training, evaluation, export, and speed/deployment tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Ultra-Fast-Lane-Detection

Use this skill when the task is about the Ultra-Fast-Lane-Detection lane detection repo: preparing CULane or TuSimple data, training a model, evaluating checkpoints, visualizing outputs, exporting TorchScript, or benchmarking speed.

## Start here

- Read `references/repo-provenance.md` if you want to confirm this skill matches the current checkout or to decide whether `refresh-repo-skill` is needed.
- Run `scripts/check_environment.py` when you need a quick local smoke of imports, config parsing, and CUDA availability.
- Use the sub-skill that matches the task family; this root file is only a router.

## Install and runtime notes

- This repo is not packaged as an installable distribution.
- Use a Python environment with PyTorch and torchvision compatible with your backend, then install the runtime requirements listed by the repo (`requirements.txt` plus the small optional helpers used by the scripts here).
- The documented workflows assume the repository root is on `PYTHONPATH` when you run the scripts from a checkout or copied tree.
- CUDA is required for the native training, evaluation, demo, and speed scripts because the source code calls `.cuda()` directly.
- The CULane evaluator also needs a C++ toolchain and OpenCV C++ development files.

## Route map

### `sub-skills/data-and-config/`
Read this when the task is about dataset layout, TuSimple conversion, config overrides, row anchors, or any `data_root`/`log_path` problem.

### `sub-skills/training/`
Read this for single-GPU or distributed training, checkpoints, resume/finetune behavior, losses, schedulers, and TensorBoard logging.

### `sub-skills/evaluation-and-visualization/`
Read this for `test.py`, CULane/TuSimple scoring, demo AVI generation, and evaluator build/run questions.

### `sub-skills/export-and-speed/`
Read this for TorchScript export, synthetic speed checks, camera/video speed notes, and LibTorch/OpenCV deployment caveats.

## Common entry points

- `data-and-config` owns the data preparation path and the configuration defaults.
- `training` owns the optimization loop and checkpoint lifecycle.
- `evaluation-and-visualization` owns benchmark outputs and visual inspection.
- `export-and-speed` owns deployment-oriented export and throughput checks.

## When to read references

- `references/workflow-map.md` for a compact overview of the repo workflows and where each sub-skill routes them.
- `references/troubleshooting.md` for cross-cutting failures such as missing dependencies, CUDA runtime issues, checkpoint mismatches, and dataset path mistakes.
- `references/repo-provenance.md` for staleness checks and repo snapshot details.

## Safe smoke check

If you only need to confirm the repo knowledge is usable, run the bundled smoke helper before deeper work:

```bash
python scripts/check_environment.py --repo-root . --device cuda
```

If CUDA is not available, rerun with `--device cpu` to verify the non-GPU import path and record the missing backend separately.

## Sub-skill reminders

- Do not expect the original repo docs to stay open in a later session; the sub-skills and bundled references should carry the needed details.
- Do not use this root file for long API tables, detailed command catalogs, or troubleshooting matrices; those belong in the sub-skills' references.
- Do not mix evaluation, export, and training advice in one route when a dedicated sub-skill exists.
