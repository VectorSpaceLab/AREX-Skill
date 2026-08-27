---
name: training-configs
description: "Train, evaluate, resume, and inspect PaddleGAN models from YAML
  configs, checkpoints, AMP, distributed launch, VisualDL, and registry-backed
  builders."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# training-configs

Use this sub-skill for PaddleGAN training and evaluation command planning.

## Route here when you need to
- start training from a YAML config
- resume from a checkpoint or load weights for evaluation or fine-tuning
- override config values with dotted `key=value` paths
- inspect output/checkpoint layout, AMP, distributed launch, or VisualDL
- resolve model, dataset, metric, optimizer, or scheduler names from config blocks

## Do not use this sub-skill for
- dataset download or preprocessing details
- export / deployment / static inference
- image/video application inference recipes
- full native training or evaluation runs

## Bundled entry point
- `scripts/train_eval.py`

## Reference map
- `references/training-workflows.md` — command shapes, lifecycle decisions, output layout
- `references/config-reference.md` — config schema, override syntax, registry names
- `references/troubleshooting.md` — common parse, dataset, resume/load, AMP, VisualDL, and distributed failures

## Operating rules
- Prefer `--resume` for continuing an exact training run; use `--load` for weights only.
- `--evaluate-only` still builds the trainer, so train-side config blocks must remain valid.
- Use `--show-config` for safe parse / override checks before any training.
- Keep the repo's current field spellings, including `visiual_interval`.
- The generic trainer writes under `output_dir/<config-stem>-<timestamp>/`, not the model class name.
