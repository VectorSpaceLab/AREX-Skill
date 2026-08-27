---
name: training-and-evaluation
description: "Operate FastReID training and evaluation launch commands,
  DefaultTrainer APIs, distributed options, checkpoints, solver schedules,
  metrics, logs, and custom training loops."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# FastReID training and evaluation

Use this sub-skill when the task is about running or adapting FastReID training,
evaluation-only runs, distributed launch flags, resume/checkpoint behavior,
solver/scheduler settings, trainer hooks, evaluation metrics, logs, or custom
training-loop extensions.

## Route elsewhere first

- Dataset download, directory layout, `FASTREID_DATASETS`, custom dataset
  registration, dataloaders, transforms, and samplers: use
  `../data-and-datasets/`.
- Environment setup, source-only import, config merge, `_BASE_` inheritance,
  recipe selection, and general `opts` syntax: use
  `../setup-and-configuration/`.
- Model registry, feature tensor contracts, `DefaultPredictor`, and no-download
  model construction: use `../modeling-and-inference/`.
- ONNX, Caffe, TensorRT, deployment runtimes, and project-extension export
  workflows: use `../deployment-and-projects/`.

## Bundled references

- [references/training-cli.md](references/training-cli.md) — use for safe
  train/eval command templates, parser flags, `opts` examples, device overrides,
  1-GPU to multi-GPU conversion, multi-machine launch, resume, and output
  conventions.
- [references/trainer-api.md](references/trainer-api.md) — use for
  `DefaultTrainer`, `launch`, solver/scheduler builders, hooks, writers,
  checkpoint APIs, and custom trainer/loop extension points.
- [references/evaluation.md](references/evaluation.md) — use for
  `DefaultTrainer.test`, `ReidEvaluator`, `inference_on_dataset`, rank/mAP/mINP
  metrics, AQE/rerank/ROC options, and metric-output interpretation.
- [references/troubleshooting.md](references/troubleshooting.md) — use for
  missing datasets, CUDA OOM, batch/world-size divisibility, resume/checkpoint
  confusion, `config.yaml` output, Python rank fallback, distributed launch
  failures, and stale tests or legacy imports.

## Bundled scripts

- [scripts/train_command_builder.py](scripts/train_command_builder.py) — build
  and print a FastReID train or eval-only shell command without executing it;
  validates eval-only checkpoint requirements and warns about distributed batch
  divisibility.
- [scripts/run_training_entrypoint.py](scripts/run_training_entrypoint.py) —
  bundled replacement for the source-tree training launcher; safe by default
  because it requires `--dry-run` or `--confirm-run`.
- [scripts/training_cli_help_check.py](scripts/training_cli_help_check.py) —
  import FastReID's standard parser from an explicit repo root and print the
  available CLI flags without launching training.

## Public facts to remember

- FastReID version `1.3` exposes the standard CLI parser through
  `fastreid.engine.default_argument_parser()`.
- Parser flags include `--config-file`, `--resume`, `--eval-only`,
  `--num-gpus`, `--num-machines`, `--machine-rank`, `--dist-url`, and trailing
  `opts` (`KEY VALUE` pairs).
- The standard launcher is
  `launch(main_func, num_gpus_per_machine, num_machines=1, machine_rank=0,
  dist_url=None, args=())`.
- `DefaultTrainer(cfg)` builds the standard train stack, and
  `DefaultTrainer.test(cfg, model)` runs evaluation over `cfg.DATASETS.TESTS`.
- `build_optimizer(cfg, model, contiguous=True)` returns optimizer state plus a
  parameter wrapper, and `build_lr_scheduler(cfg, optimizer, iters_per_epoch)`
  returns scheduler objects keyed by scheduler role.
- Full training/evaluation can require datasets, local checkpoints, CUDA, and
  long runtime; this skill's bundled scripts do not train, evaluate, download,
  or write destructive outputs.
