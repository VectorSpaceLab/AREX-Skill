---
name: training-evaluation
description: "Construct and troubleshoot MMDetection3D training, testing,
  evaluation, visualization-hook, TTA, distributed, and Slurm commands."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MMDetection3D training-evaluation sub-skill

Use this sub-skill when the user needs to train, test, evaluate, visualize evaluation outputs, enable test-time augmentation, or launch distributed/Slurm MMDetection3D jobs from an already chosen config and prepared dataset.

## Best-fit tasks

- Build safe single-process, distributed, or Slurm training commands for `tools/train.py` semantics.
- Build safe single-process, distributed, or Slurm test/evaluation commands for `tools/test.py` semantics.
- Decide how to pass `--work-dir`, `--amp`, `--sync_bn`, `--auto-scale-lr`, `--resume`, and nested `--cfg-options` overrides.
- Add evaluation output prefixes for validation artifacts or benchmark submissions.
- Add visualization-hook flags (`--show`, `--show-dir`, `--task`, score threshold, wait time) without assuming a GUI is available.
- Add `--tta` only when the selected segmentation config contains the required TTA sections.
- Diagnose launch, evaluator, visualization, TTA, CPU/GPU, port, and Slurm failures.

## Route elsewhere

- Dataset download, info-file generation, dataset layout validation, and stale annotation migrations belong in `data-preparation`.
- Choosing model families, editing config inheritance, changing dataset roots/classes, and validating config syntax belong in `configuration-model-zoo`.
- Standalone inference demos, inferencer APIs, and prediction serialization without evaluation belong in `inference`.
- Geometry API use and offline interpretation of saved OBJ/visualizer artifacts belong in `structures-visualization`.
- TorchServe, model publishing/conversion, log plotting, FLOPs, and benchmark helper boundaries belong in `serving-tools`.

## Operating procedure

1. Confirm the caller has a config path, dataset prepared for that config, and for testing a checkpoint path. If these are missing, route before generating commands.
2. Choose the launcher pattern in [references/workflows.md](references/workflows.md): single process, distributed shell launcher, or Slurm launcher.
3. Generate command strings with the bundled dry-run helper:

   ```bash
   python scripts/build_train_test_command.py --help
   ```

   The helper prints shell commands only; it never starts training, testing, distributed workers, or Slurm jobs.
4. For training, decide whether the job needs `--work-dir`, `--amp`, `--sync_bn`, `--auto-scale-lr`, `--resume`, and config overrides before adding launch resources.
5. For testing/evaluation, decide whether the task is ordinary metric evaluation, benchmark formatting, saved visualization, or segmentation TTA. Use [references/evaluation.md](references/evaluation.md) for evaluator-specific output keys.
6. For distributed or Slurm jobs, set GPU count and ports explicitly when multiple jobs may share a host. Avoid the default port collision described in [references/troubleshooting.md](references/troubleshooting.md).
7. Before recommending an expensive run, check the high-signal guardrails below and the failure patterns in [references/troubleshooting.md](references/troubleshooting.md).

## High-signal guardrails

- Do not run long training/evaluation as a verification step. Prefer parser/help checks, config checks, and command rendering unless the user explicitly authorizes the expensive job.
- `--work-dir` overrides config `work_dir`; if neither is set, MMEngine uses `./work_dirs/<config-basename>`.
- `--amp` only converts a config whose optimizer wrapper type is `OptimWrapper`; configs already using AMP warn, and unrelated wrappers fail.
- `--auto-scale-lr` requires the config to define `auto_scale_lr.enable` and `auto_scale_lr.base_batch_size`.
- `--resume` with no value means auto-resume from the latest checkpoint in the work directory; `--resume path/to/checkpoint.pth` resumes from that checkpoint.
- `--sync_bn` accepts `none`, `torch`, or `mmcv`; it is mainly useful for multi-GPU training and should not be used as a generic CPU fix.
- Evaluation output prefixes are usually nested under `test_evaluator.*`; do not pass a top-level `submission_prefix` unless the active config explicitly consumes it.
- `--show`/`--show-dir` activate the visualization hook and require a valid `--task` choice. Saved visualization works headlessly through output files, but documented use is for single-GPU debugging.
- `--tta` in this release is for 3D segmentation configs that include both `tta_model` and `tta_pipeline`; do not enable it for ordinary 3D detection configs.
- CPU train/test is experimental and narrow. Most point-cloud models depend on CUDA 3D ops; CPU testing is documented only for SMOKE-style debugging.
