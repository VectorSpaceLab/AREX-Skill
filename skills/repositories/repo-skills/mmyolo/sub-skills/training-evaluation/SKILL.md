---
name: training-evaluation
description: "Route safe MMYOLO training, testing, prediction output, launchers,
  logging, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# MMYOLO training-evaluation

Use this sub-skill when the user needs to construct or review MMYOLO training, resume, AMP, distributed launch, testing/evaluation, prediction dump, training-log, scheduler-plot, or confusion-matrix workflows.

## Safety boundary

This sub-skill is for **safe command construction and preflight review**. Training and evaluation can be long-running, GPU-heavy, write checkpoints/logs, and touch datasets. Do not launch a real training/evaluation job unless the caller explicitly asks for execution after the preflight decisions are clear.

For safe command builders that print commands without running MMYOLO, use:

- [scripts/mmyolo_train_help.py](scripts/mmyolo_train_help.py) for package-level `mim train mmyolo` command construction.
- [scripts/mmyolo_test_help.py](scripts/mmyolo_test_help.py) for package-level `mim test mmyolo` command construction and `.pkl`/`.pickle` output validation.

## Start here

1. Identify the workflow: train, resume, AMP train, test/evaluate, dump predictions, visualize evaluation outputs, distributed, Slurm, log analysis, scheduler visualization, or confusion matrix.
2. Verify inputs before launch planning:
   - training: config path, dataset availability, work directory, requested backend/GPU count, resume checkpoint if not auto-resume;
   - testing: config path, checkpoint path, output format request, visualization/output directory, TTA/deploy flags, backend/GPU count;
   - distributed: launcher type, visible devices, GPU count, unique port, node rank/address, or Slurm partition/job resources.
3. Build a command with one of the bundled helpers or the recipes in [references/training-evaluation.md](references/training-evaluation.md).
4. Check exact CLI behavior in [references/cli-reference.md](references/cli-reference.md).
5. If anything fails preflight, use [references/troubleshooting.md](references/troubleshooting.md) before suggesting expensive reruns.

## Route away

- Config editing, model family selection, `metainfo`, class counts, evaluator paths, optimizer-wrapper changes, TTA config definitions, visualization-backend config edits, or `--cfg-options` design belong in `config-customization`.
- Dataset conversion, COCO/YOLO/LabelMe layout checks, annotation browsing, or anchor optimization belongs in `data-tools`.
- Image/video inference demos, feature-map visualization, BoxAM/Grad-CAM, LabelMe prediction export, or SAHI large-image inference belongs in `inference-visualization`.
- ONNX, TensorRT, RKNN, MMDeploy, EasyDeploy export/build/inference, and checkpoint-format conversion belongs in `deployment-conversion`.

## Core decisions

- Prefer `mim train mmyolo ...` / `mim test mmyolo ...` when MMYOLO is installed as a package and OpenMIM exposes package train/test commands.
- Treat the original source shell wrappers as evidence for distributed/Slurm option mapping only. Use MIM launcher options in runtime guidance instead of depending on checkout-local script paths.
- Use `--resume` alone for auto-resume from the work directory, or `--resume PATH` for a specific checkpoint.
- Use `--amp` only when the config optimizer wrapper is compatible; see the AMP assertions in troubleshooting.
- For prediction dumps, use `--out result.pkl` or `--out result.pickle` for rich pickle outputs; use `--json-prefix path/prefix` for COCO-style JSON prefix output.
- Prefer `--show-dir DIR` over `--show` on headless machines.

## Usability cases this sub-skill must handle

- Generate a resume+AMP training command, then explain why AMP may warn or assert based on `optim_wrapper.type`.
- Translate a request such as “evaluate this checkpoint and save both JSON and PKL predictions” into valid `mim test mmyolo` options, including `.pkl`/`.pickle` suffix validation and the `--json-prefix` prefix rule.
