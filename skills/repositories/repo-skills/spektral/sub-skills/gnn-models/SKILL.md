---
name: gnn-models
description: "Guides Spektral graph neural network layers, pooling, ready-made
  models, message passing, and explanation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Spektral GNN Models

Use this sub-skill when the task is about building, selecting, debugging, or explaining graph neural network layers and models with Spektral.

## Read first

- `references/layer-catalog.md` for convolution, pooling, base layer, and mode-support summaries.
- `references/api-reference.md` for verified model, layer, utility, and explainer signatures.
- `references/workflows.md` for GCN, GeneralGNN, custom `MessagePassing`, batch-mask, and explainer recipes.
- `references/troubleshooting.md` for sparse/dense adjacency, mask propagation, Keras compatibility, layer-input, pooling, and explainer failures.
- `scripts/smoke_models.py` for a tiny no-download CPU model/layer sanity check.

## Core decisions

1. Decide the data mode with `../graph-data/SKILL.md` before selecting layers.
2. Match layer mode support to loader output:
   - `SingleLoader` and `DisjointLoader` usually work with sparse-aware layers.
   - `BatchLoader` emits dense padded tensors; use only layers that support batch mode.
   - `MixedLoader` shares one adjacency matrix and needs layers/models that support mixed mode.
3. Apply required adjacency preprocessing before training. Many layers implement `preprocess(a)` and can be paired with `LayerPreprocess`.
4. Use `GraphMasking` when `BatchLoader(mask=True)` appends a mask feature for dense padded batches.
5. Keep full training/benchmark runs separate from smoke checks; the bundled script only validates wiring.

## Start points

| Task | Start with | Notes |
| --- | --- | --- |
| Simple citation-style node prediction | `GCN` or `GCNConv` | `GCN` outputs node predictions and accepts `(x, a)` or `(x, a, i)` |
| General graph classification/regression | `GeneralGNN` plus `DisjointLoader` | Defaults use GeneralConv blocks and global sum pooling |
| Custom architecture | Keras functional/subclassed model plus Spektral layers | Use layer catalog to match data mode and edge-feature needs |
| Custom sparse message passing | `MessagePassing` subclass | Single/disjoint sparse adjacency only |
| Dense pooling | `BatchLoader(mask=True)`, `GraphMasking`, then dense pooling layer | MinCut/DiffPool-style layers expect batch-compatible shapes |
| Explanation | `GNNExplainer` | Node or graph explanations after a model is trained or otherwise produces predictions |

## Minimal validation

Run from the generated skill tree after installing Spektral:

```bash
python sub-skills/gnn-models/scripts/smoke_models.py
```

Expected signal: successful tiny forward passes for `GeneralGNN`, `GCN`, `GCNConv` with batch masking, and a custom `MessagePassing` subclass, followed by `smoke_ok`.

## Important compatibility note

This Spektral source revision was verified with TensorFlow `2.15.1` and Keras `2.15.0`. In a latest TensorFlow/Keras 3 environment, `GCN`/`GCNConv` mask handling may fail with an error about converting `None` to a tensor. If that happens, use the troubleshooting page to pin a TensorFlow/Keras 2.x-compatible stack or rewrite the model call path to avoid the incompatible mask behavior.

## Route away when

- The task is about constructing `Graph` or `Dataset` objects, choosing loaders, or configuring dataset downloads: use `../graph-data/SKILL.md`.
- The task is about generic Keras layer authoring unrelated to graph matrices: use TensorFlow/Keras guidance first.
- The task asks for PyTorch Geometric, DGL, or NetworkX-only algorithms without Spektral layers.
