---
name: training-and-evaluation
description: "Compose safe distributed BEVFormer training, evaluation, and FP16
  launch commands while explaining launcher, checkpoint, and runtime gates."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---
# training-and-evaluation

Compose command-only guidance for BEVFormer train/eval flows.

## Use this sub-skill for
- distributed training launches for `tools/train.py`
- distributed evaluation launches for `tools/test.py`
- FP16 training launches for `tools/fp16/train.py`
- `--work-dir`, `--resume-from`, `--cfg-options`, launcher, and port questions
- checkpoint and GPU/NCCL prerequisite triage

## Route away when
- data layout, CAN bus, or annotation files need validation -> `dataset-preparation`
- config summaries, model-family choices, or install/import issues need analysis -> `installation-and-configs`
- logs, plots, throughput, or visual outputs are the goal -> `analysis-and-utilities`

## Bundled helpers
- `scripts/bevformer_train_command.py`
- `scripts/bevformer_eval_command.py`

## Read first
- `references/training-and-evaluation.md`
- `references/cli-reference.md`
- `references/troubleshooting.md`

## Operating rules
- Do not run training or evaluation from this sub-skill.
- Prefer distributed launch commands; the repo's eval path does not support a non-distributed shortcut.
- Keep data and checkpoint prerequisites explicit in every command handoff.
