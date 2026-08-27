---
name: training-evaluation-configs
description: "Route MMOCR config-driven training, testing, evaluation, model-zoo
  selection, distributed/Slurm launch, AMP, resume, and TTA preflights."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# training-evaluation-configs

Use this router when the task is to inspect, edit, preflight, or launch MMOCR config-driven training/testing/evaluation. It covers Python config inheritance, `--cfg-options`, model-zoo family selection, checkpoint matching, `train.py`/`test.py`, distributed scripts, Slurm scripts, AMP, resume/load behavior, prediction dumping, and test-time augmentation.

## Route first

- Config syntax, `_base_` inheritance, default scope, dataloaders, evaluators, `work_dir`, `resume`, `load_from`, or one-off override checks: read [config reference](references/config-reference.md) and run the safe [config smoke helper](scripts/mmocr_config_smoke.py).
- Single-device training/testing, distributed launch, Slurm launch, offline evaluation, visualization, `--amp`, `--auto-scale-lr`, `--resume`, `--save-preds`, or `--tta`: read [training and evaluation workflows](references/training-evaluation-workflows.md).
- Model-family choice, model-index aliases, config/checkpoint matching, evaluator family, or AMP support by algorithm: read [model zoo reference](references/model-zoo.md).
- Broken `_base_` paths, shell quoting, missing data paths, missing checkpoints, checkpoint/config mismatch, CPU/CUDA fallback, unsupported AMP, port conflicts, Slurm variables, or `work_dir`/checkpoint/resume confusion: read [troubleshooting](references/troubleshooting.md).

## Boundaries

Route elsewhere when the task is not an end-to-end training/evaluation/config problem:

- Dataset download, conversion, annotation format, dataset-zoo authoring, LMDB preparation, or generated dataset bases: `../data-preparation/`.
- OCR/KIE inferencer APIs, prediction-only inference, model-name inference smoke tests, or high-level OCR chains: `../ocr-inference/`.
- Model internals, custom components, registries, data samples, metrics as classes, transforms, visualizers, or project extension code: `../model-api-components/`.

## Safe operating pattern

1. Load the target config with the smoke helper before any real train/test command.
2. Confirm `default_scope`, `model.type`, dataloader dataset types/batch sizes, evaluator types, `work_dir`, `resume`, `load_from`, TTA fields, and distributed backend.
3. Match the config family to the checkpoint and evaluator before enabling expensive launch options.
4. Choose the smallest launcher that fits the hardware: single-device first, then distributed, then Slurm.
5. Enable `--amp`, `--auto-scale-lr`, `--resume`, `--save-preds`, or `--tta` only after the workflow and model-zoo references say the route is valid.

## Source-script policy

- The bundled smoke helper only calls `mmengine.Config.fromfile` and `cfg.merge_from_dict`; it never builds a runner, dataset, model, evaluator, or training loop.
- Official `train.py`, `test.py`, distributed, and Slurm scripts are real execution routes. Document and use them only when the user intends to start training or evaluation.
- Offline evaluation and visualization tools are reference-only in this sub-skill because they build evaluators, datasets, visualizers, or simulated runners.
