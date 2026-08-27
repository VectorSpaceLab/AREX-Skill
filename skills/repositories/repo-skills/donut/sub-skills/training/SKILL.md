---
name: training
description: "Teach Donut fine-tuning, dataset layout, checkpoint handling, and evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Training

Use this sub-skill when the request is about Donut fine-tuning, dataset JSONL layout, validation metrics, checkpoint layout, or checkpoint evaluation.

## Route here for
- training or fine-tuning Donut on CORD, DocVQA, RVL-CDIP, TrainTicket, or a similar structured-document task
- inspecting `metadata.jsonl`
- understanding `gt_parse` versus `gt_parses`
- comparing validation metrics or test scores
- resuming a run from a saved checkpoint

## Do not route here for
- single-image inference or prompt construction details → `../inference/SKILL.md`
- the Gradio demo or app launch → `../inference/SKILL.md`
- SynthDoG dataset generation → `../synthdog/SKILL.md`

## Read first
- `references/workflows.md`
- `references/configuration.md`
- `references/troubleshooting.md`

## Fast rules
- Training requires CUDA; the bundled `scripts/train_donut.py` preserves the source GPU, DDP, and 16-bit execution assumptions.
- `scripts/train_donut.py` exposes only `--config` and `--exp_version`; all other overrides are passed through `sconf`.
- `metadata.jsonl` stores `file_name` plus a JSON-encoded `ground_truth` string with either `gt_parse` or `gt_parses`.
- `val_metric` is normalized edit distance, so lower is better.
- `test.py` reports TED-based accuracy and F1, so higher is better.

## Useful links inside this skill tree
- Core API reference: `../../references/api-reference.md`
- Prompt-level prediction notes: `../inference/SKILL.md`
- Synthetic data creation: `../synthdog/SKILL.md`

## Bundled helpers
- `scripts/train_donut.py` plus `scripts/lightning_module.py`
- `scripts/check_training_config.py`
- `scripts/evaluate_dataset.py`
- `references/configs/train_*.yaml`

## Default workflow
1. Validate the config and local metadata with `scripts/check_training_config.py`.
2. Train with the bundled `scripts/train_donut.py` or compare a checkpoint with `scripts/evaluate_dataset.py`.
3. Use the tables in `references/configuration.md` and `references/workflows.md` before comparing runs.
