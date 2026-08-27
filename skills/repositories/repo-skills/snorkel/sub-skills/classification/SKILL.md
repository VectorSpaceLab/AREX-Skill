---
name: classification
description: "Operate Snorkel PyTorch classification, training, logging, and
  evaluation APIs."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Classification

Use this sub-skill for Snorkel discriminative modeling workflows built around:
- `DictDataset`, `DictDataLoader`, and `collate_dicts`
- `Operation`, `Task`, `MultitaskClassifier`, and `cross_entropy_with_probs`
- `Trainer`, logging, checkpointing, and batch / learning-rate schedulers
- `Scorer`, `metric_score`, label utilities, and error-analysis helpers

## Route elsewhere when needed
- Weak labels, labeling functions, and `LabelModel`: [../labeling/SKILL.md](../labeling/SKILL.md)
- Slice-aware classifier internals and slice-function-driven tasks: [../slicing/SKILL.md](../slicing/SKILL.md)
- Generic preprocessors, mapping, and augmentation: [../data-transforms/SKILL.md](../data-transforms/SKILL.md)

## Start here
1. Read [references/api-reference.md](references/api-reference.md) for the public surface and defaults.
2. Use [references/training-and-evaluation.md](references/training-and-evaluation.md) for the end-to-end workflow.
3. Check [references/troubleshooting.md](references/troubleshooting.md) for common failures and fixes.
4. Run [scripts/classification_smoke.py](scripts/classification_smoke.py) for a tiny CPU-only validation.

## What to emphasize
- Build the shortest task graph that still exposes the behavior being debugged.
- Prefer in-memory tensors and small fixtures.
- Keep label semantics explicit: hard labels for scoring, probabilistic labels for soft-loss training.
- Use the metric namespace `task/dataset/split/metric` when reading scores, logs, and checkpoints.

## What this sub-skill does not own
- Weak supervision model training and LF analysis
- Slice-function authoring and slice-aware modeling details
- Data augmentation and generic preprocessing pipelines

When a request crosses those boundaries, route it to the adjacent sub-skill instead of stretching this one.