---
name: fair-graph-learning
description: "Use DIG's fair graph learning stack for NBA/POKEC datasets,
  Graphair training and evaluation, and fairness-aware graph representation
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Fair Graph Learning

Use this sub-skill for DIG workflows around Graphair, fairness metrics, and the NBA/POKEC datasets.

## Include

- `dig.fairgraph.dataset`: `NBA`, `POKEC`.
- `dig.fairgraph.method`: `run`, `graphair`, `aug_module`, `GCN`, `GCN_Body`, `Classifier`.
- `dig.fairgraph.utils.utils`: `accuracy`, `fair_metric`, `scipysp_to_pytorchsp`.
- Graphair training and evaluation workflows.

## Exclude

- Graph augmentation without fairness: use `../graph-augmentation/SKILL.md`.
- Molecular, 3D, SSL, explainability, GOOD, or large-scale graph workflows.

## Start Here

- Read `references/api-reference.md` for dataset fields, helper metrics, and the runner class.
- Read `references/workflows.md` for the Graphair training/evaluation path.
- Read `references/troubleshooting.md` when `.cuda()` assumptions or data downloads become a problem.
- Run `scripts/fairgraph_smoke.py` for a safe metric-only smoke check.

## Core Workflows

- **Dataset preparation**: instantiate NBA or POKEC, inspect sensitive attributes, and confirm the returned splits and metadata.
- **Graphair training**: use `run()` to construct the augmentation, encoder, adversary, and classifier stack, then train and evaluate.
- **Fairness metrics**: use `accuracy` and `fair_metric` for lightweight checks or reporting.
