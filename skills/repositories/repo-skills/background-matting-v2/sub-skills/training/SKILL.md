---
name: training
description: "Routes BackgroundMattingV2 base and refine training, data layout,
  and benchmark setup workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# training

Use this sub-skill when the task is about configuring datasets, launching the
training scripts, or validating the paired image layout used by the repo.

## Typical triggers

- `train_base.py`
- `train_refine.py`
- `data_path.py`
- paired foreground / alpha / background data layout
- checkpoint, log, or TensorBoard output setup
- CUDA, NCCL, or multi-GPU assumptions
- the benchmark script in `eval/`

## Read first

- `references/workflows.md` for the base/refine training flow and the data path
  shape.
- `references/troubleshooting.md` for dataset, CUDA, batch-size, and flag-name
  pitfalls.
- `scripts/check_data_layout.py` before editing `data_path.py` or launching a
  long run.
- `scripts/run_training.py` when you want a dry-run or execute wrapper around
  the checkout's training CLIs.

## What this sub-skill owns

- training dataset configuration and validation
- `data_path.py` editing guidance
- checkpoint and log directory conventions
- base vs refine training behavior
- distributed GPU assumptions in refine training
- benchmark layout and metric expectations

## What it does not own

- demo inference; use `inference-and-demo`
- TorchScript or ONNX export; use `export-and-backends`

## Recommended first checks

1. Validate the data layout before touching the training loop.
2. Confirm the dataset name is one of the real foreground/alpha datasets.
3. Use the dry-run wrapper before any expensive launch.

## Cross-links

- `../inference-and-demo/SKILL.md`
- `../export-and-backends/SKILL.md`
- `../../references/data-formats.md`
