---
name: graph-augmentation
description: "Use DIG's graph augmentation stack for GraphAug, S-Mixup,
  augmentation configs, degree transforms, subset/triplet datasets, and
  augmentation-driven graph classification workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Graph Augmentation

Use this sub-skill for DIG workflows that learn or apply graph augmentations.

## Include

- `dig.auggraph.dataset`: `DegreeTrans`, `AUG_trans`, `Subset`, `TripleSet`.
- `dig.auggraph.method.GraphAug`: `RunnerAugCls`, `RunnerGenerator`, `RunnerRewardGen`.
- `dig.auggraph.method.SMixup`: `smixup`.
- GraphAug configuration enums and constants for dataset names, augmentation types, and model types.

## Exclude

- Fairness workflows that rely on Graphair: use `../fair-graph-learning/SKILL.md`.
- Molecular, 3D, SSL, explainability, GOOD, or large-scale loader workflows.

## Start Here

- Read `references/api-reference.md` for the public classes and config constants.
- Read `references/workflows.md` for the three GraphAug runner flows and S-Mixup.
- Read `references/troubleshooting.md` when CUDA, TU datasets, or label layouts are problematic.
- Run `scripts/augmentation_config_smoke.py` for a safe import-and-transform smoke check.

## Core Workflows

- **Reward generator training**: train a label-discriminating reward model on TU datasets.
- **Augmentation generator training**: use a trained reward model to update the augmentation generator.
- **Augmented classifier training**: combine the generator with a classifier to evaluate the augmentation policy.
- **S-Mixup**: compute soft alignments and mix graph pairs for graph classification.
