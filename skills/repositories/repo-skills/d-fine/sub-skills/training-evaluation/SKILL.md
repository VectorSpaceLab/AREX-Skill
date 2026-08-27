---
name: training-evaluation
description: "Construct, review, and troubleshoot D-FINE train.py commands for
  training, test-only evaluation, resume, tuning, distributed launch, AMP/EMA,
  output/summary dirs, and CLI overrides."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Training and Evaluation

Use this sub-skill for command construction and troubleshooting around `train.py`.

## Route here
- Training, `--test-only` evaluation, `--resume`, and `--tuning`
- Single-process or `torchrun` launch planning
- AMP, EMA, output directories, summary directories, and YAML overrides
- Checkpoint loading behavior and safe preflight checks

## Do not use this sub-skill for
- Dataset schema or class-count editing: see `../data-and-configs/SKILL.md`
- Model internals or registry changes: see `../architecture-api/SKILL.md`
- ONNX / TensorRT / OpenVINO / deployment commands: see `../inference-export/SKILL.md`

## Bundled helpers
- `scripts/dfine_train_command.py` builds shell-quoted `train.py` commands without executing them.
- `references/training-and-evaluation.md` explains flags, launch topologies, checkpoints, and output files.
- `references/troubleshooting.md` covers the common failures and fast fixes.

## Safe defaults
- Use `--mode train|test|resume|tune` instead of mixing checkpoints by hand.
- Use `--single-process` for one-process commands; otherwise let the helper infer `torchrun` from `--devices` or `--nproc`.
- Use `--update` only for config keys, not for dedicated command flags.
