---
name: execution-config
description: "Install PocketFlow, validate path.conf, preview safe launcher
  commands, inspect runtime prerequisites, and troubleshoot execution modes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# execution-config

Use this sub-skill for PocketFlow setup, launch plumbing, and safe command previews.

## Route here when the task involves
- editing or validating `path.conf` / `path.conf.template`
- previewing local, Docker, or Seven launcher arguments
- checking TensorFlow 1.x, GPU, Horovod, or TF-Plus availability
- staging a minimal isolated copy for container or cluster packaging
- converting AutoML hparams or parsing AutoML results

## Route elsewhere when the task is about
- learner selection, pruning, quantization, distillation, or RL tuning: `../compression-learners/SKILL.md`
- custom `ModelHelper` / `Dataset` code or built-in model/data wiring: `../custom-models-data/SKILL.md`
- checkpoint export, PB/TFLite conversion, or inference benchmarking: `../deployment-conversion/SKILL.md`

## Start with
- `references/configuration.md`
- `references/execution-modes.md`
- `references/automl.md`
- `references/troubleshooting.md`

## Bundled helpers
- `scripts/validate_path_conf.py` — validate a PocketFlow-style path config and preview launcher args without running training
- `scripts/check_runtime.py` — inspect TensorFlow 1.x, contrib.lite, GPU, Horovod, and TF-Plus readiness
- `scripts/create_minimal_copy.sh` — create an isolated minimal copy from explicit source and target paths
- `scripts/cvt_automl_hparams.py` — convert AutoML hparam files into PocketFlow CLI flags
- `scripts/parse_automl_results.py` — convert TensorFlow log output into AutoML result fields

These helpers are deterministic and safe by default; they do not download data or launch training.
