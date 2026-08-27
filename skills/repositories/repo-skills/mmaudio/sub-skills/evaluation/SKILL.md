---
name: evaluation
description: "Operate MMAudio batch evaluation, evaluation dataset wiring, and
  onset metrics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MMAudio Evaluation

Use this sub-skill when the task is to generate batched MMAudio evaluation outputs, configure evaluation datasets, or score onset timing on generated audio.

## What this route owns

- Batch generation with `batch_eval.py` through Hydra and `torchrun`.
- AudioCaps, AudioCaps-full, VGGSound, and MovieGen evaluation data configuration.
- Output naming, run-directory expectations, DDP/CUDA launch assumptions, and per-GPU batch sizing.
- Safe command construction for batch evaluation without launching the model.
- CPU onset scoring for predicted `.flac`/`.wav` files against ground-truth onset text files.

## Route elsewhere

- Single prompt, single video, API generation, video compositing, or Gradio usage -> `inference`.
- Feature extraction, training memmaps, or manifest preparation -> `data-preparation`.
- DDP training, checkpoints, EMA, or TensorBoard training outputs -> `training`.

## Operating rules

1. Use `torchrun` even for one GPU. The batch evaluator reads distributed environment variables at import time and initializes NCCL.
2. Treat CUDA as required for practical batch evaluation. CPU is only suitable for helper scripts and onset scoring.
3. Do not expect video composites from batch evaluation; it writes generated audio files only.
4. Check dataset paths and schemas before launching: most empty-output problems are bad CSV/JSONL/media naming rather than model failures.
5. Be explicit about `duration_s`, `dataset`, `model`, `output_name`, `batch_size`, `num_workers`, `compile`, and any `eval_data.*` path overrides.
6. Model weights and external module checkpoints may be downloaded when the real batch command runs if they are absent; command builders in this sub-skill never download them.
7. Use onset scoring only for 8-second-style onset benchmarks unless you deliberately override sample rate, duration, and naming assumptions.

## Start here

- [`references/batch-evaluation.md`](references/batch-evaluation.md) for launch patterns, Hydra keys, outputs, and validation.
- [`references/evaluation-data-formats.md`](references/evaluation-data-formats.md) for dataset schemas and onset input conventions.
- [`references/troubleshooting.md`](references/troubleshooting.md) for distributed, dataset, download, OOM, and onset failures.
- [`scripts/build_batch_eval_command.py`](scripts/build_batch_eval_command.py) to render a safe `torchrun batch_eval.py ...` command.
- [`scripts/evaluate_onsets.py`](scripts/evaluate_onsets.py) to run deterministic CPU onset scoring.

## Evidence labels

This sub-skill was distilled from these source evidence labels: `docs/EVAL.md`, `batch_eval.py`, `eval_onsets.py`, `config/eval_config.yaml`, `config/eval_data/base.yaml`, and the `mmaudio/data/eval` package. The runtime guidance above is self-contained; do not send future agents back to those source files for normal operation.
