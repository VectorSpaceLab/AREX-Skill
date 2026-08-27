---
name: "training-and-inference"
description: "Routes training, fine-tuning, validation, checkpoint, and
  inference workflows for 3D ResNets PyTorch."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# training-and-inference

Use this sub-skill when you need to train, fine-tune, validate, resume, or run inference for this repository's `main.py`-style workflows without reopening the source checkout.

## Use this route for

- Fresh training runs and stage-wise fine-tuning.
- Checkpoint save/resume, optimizer state recovery, and milestone handling.
- Loading pretrained weights with a different final class count.
- Validation, multi-clip inference, and result scoring.
- DataParallel checkpoint cleanup before reuse or inspection.

## Do not use this route for

- Raw video extraction or annotation JSON creation. Use [data-preparation](../data-preparation/SKILL.md).
- Repo-wide routing or root skill selection. Use [the root router](../../SKILL.md).
- Model conversion or export outside the `main.py` training loop.

## Read first

- `references/workflows.md`
- `references/model-catalog.md`
- `references/troubleshooting.md`
- [the root router](../../SKILL.md)
- [the root run helper](../../scripts/run_main.py)
- [data-preparation](../data-preparation/SKILL.md) when dataset layout is not ready

## Skill-owned scripts

- `scripts/evaluate_results.py` — score top-k recognition results against a ground-truth JSON.
- `scripts/strip_dataparallel.py` — remove `module.` prefixes from checkpoint state dicts.

## Typical flow

1. Confirm the dataset tree and annotation JSON already exist.
2. Pick a model family and depth from `references/model-catalog.md`.
3. Choose scratch train, resume, or fine-tune flags in `references/workflows.md`.
4. Run the root-level `main.py` wrapper from the repo skill tree.
5. Evaluate results with `scripts/evaluate_results.py` or clean checkpoints with `scripts/strip_dataparallel.py` when needed.

## Cross-links

- Dataset preparation and layout prerequisites: [data-preparation](../data-preparation/SKILL.md)
- Repo-level routing: [root router](../../SKILL.md)
- Root `main.py` wrapper: [run_main helper](../../scripts/run_main.py)
