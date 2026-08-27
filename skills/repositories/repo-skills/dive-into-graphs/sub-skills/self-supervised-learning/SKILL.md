---
name: self-supervised-learning
description: "Use DIG's graph self-supervised learning stack for GraphCL, GRACE,
  InfoGraph, MVGRL, NodeMVGRL, pGRACE, contrastive objectives, and
  TUDataset/Planetoid-based SSL evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Self-Supervised Learning

Use this sub-skill for DIG workflows that pretrain graph encoders with contrastive or mutual-information objectives.

## Include

- `dig.sslgraph.method`: `Contrastive`, `GraphCL`, `GRACE`, `InfoGraph`, `MVGRL`, `NodeMVGRL`, `pGRACE`.
- `dig.sslgraph.method.contrastive.views_fn`: `NodeAttrMask`, `EdgePerturbation`, `Diffusion`, `DiffusionWithSample`, `UniformSample`, `RWSample`, `RandomView`, `Sequential`, `AdaEdgePerturbation`, `AdaNodeAttrMask`.
- `dig.sslgraph.method.contrastive.objectives`: `NCE_loss`, `JSE_loss`.
- `dig.sslgraph.dataset`: `TUDatasetExt`, `get_dataset`, `get_node_dataset`.
- `dig.sslgraph.evaluation`: `GraphSemisupervised`, `GraphUnsupervised`, `NodeUnsupervised`.
- `dig.sslgraph.utils`: `Encoder`, `setup_seed`.

## Exclude

- 2D/3D molecule generation: use the molecular or 3D sub-skills.
- Explainability, OOD, augmentation, fairness, or large-scale loaders: route to sibling sub-skills.

## Start Here

- Read `references/api-reference.md` for the constructor and objective names.
- Read `references/workflows.md` for graph-level and node-level SSL workflows.
- Read `references/troubleshooting.md` when augmentations, labels, or datasets are misconfigured.
- Run `scripts/sslgraph_smoke.py` for a tiny CPU-only pretraining smoke check.

## Core Workflows

- **Graph-level SSL**: use `get_dataset(..., task='semisupervised'|'unsupervised')`, build an `Encoder`, choose `GraphCL`/`GRACE`/`InfoGraph`/`MVGRL`, pretrain, and evaluate with `GraphUnsupervised` or `GraphSemisupervised`.
- **Node-level SSL**: use `get_node_dataset`, build node-level encoders, choose `GRACE` or `NodeMVGRL`, and evaluate with `NodeUnsupervised`.
- **Custom contrastive design**: compose view functions such as `NodeAttrMask`, `EdgePerturbation`, `Diffusion`, or `RandomView` and pass them into `Contrastive` directly.

## Quick Validation

```bash
python scripts/sslgraph_smoke.py --help
python scripts/sslgraph_smoke.py
```
