---
name: spektral
description: "Helps with Spektral graph neural network workflows, from graph
  data loading and transforms to layers and models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Spektral

Use this skill when the task mentions **Spektral**, **graph neural networks**, graph datasets, loaders, pooling, message passing, or ready-made graph models.

## Quick install

- Public install: `pip install spektral`
- Spektral pulls in TensorFlow and the scientific Python stack declared in `pyproject.toml`.
- For this Spektral `1.3.1` source revision, prefer TensorFlow/Keras 2.x when model calls hit Keras 3 mask behavior errors; `tensorflow==2.15.1` with `keras==2.15.0` was verified for CPU workflows. Some older source paths also assume NetworkX/SciPy matrix-era APIs, so check the troubleshooting guide for dependency-version drift.
- For a fast sanity check, run `scripts/check_install.py`.
- If an editable install complains about multiple top-level packages, use a clean checkout or a source tree that exposes only the `spektral` package.

## Quick import check

```bash
python -I -c "import spektral; from spektral.data import Graph, Dataset, SingleLoader, DisjointLoader, BatchLoader; from spektral.layers import GCNConv, GeneralConv"
```

## Route by task family

### `graph-data`
Use this route for graph containers, dataset classes, built-in datasets, transforms, loader selection, data-mode selection, and custom dataset pipelines.

Typical requests:
- "How do I define a custom Dataset?"
- "Which loader should I use for graph classification?"
- "How do I preprocess graphs for a GCN?"
- "Why is my dataset in mixed mode?"

Read:
- `sub-skills/graph-data/SKILL.md`
- `sub-skills/graph-data/references/api-reference.md`
- `sub-skills/graph-data/references/workflows.md`
- `sub-skills/graph-data/references/dataset-catalog.md`
- `sub-skills/graph-data/references/troubleshooting.md`
- `sub-skills/graph-data/scripts/smoke_data_modes.py`

### `gnn-models`
Use this route for convolution layers, pooling layers, custom message passing, ready-made models, graph explanation, and utility ops around graph math and sparse tensors.

Typical requests:
- "How do I build a GCN/GNN?"
- "How do I write a custom MessagePassing layer?"
- "Why does batch mode need GraphMasking?"
- "How do I explain a prediction with GNNExplainer?"

Read:
- `sub-skills/gnn-models/SKILL.md`
- `sub-skills/gnn-models/references/api-reference.md`
- `sub-skills/gnn-models/references/workflows.md`
- `sub-skills/gnn-models/references/layer-catalog.md`
- `sub-skills/gnn-models/references/troubleshooting.md`
- `sub-skills/gnn-models/scripts/smoke_models.py`

## When to read the shared references

- `references/api-overview.md` for the package module map and ownership split.
- `references/workflows.md` for the root-level workflow map and routing hints.
- `references/troubleshooting.md` for install/import, dataset download, mode mismatch, and masking issues.
- `references/repo-provenance.md` to check whether this skill still matches the current repository snapshot.

## What this skill covers

- Graph objects, dataset containers, and loader behavior.
- Built-in benchmark datasets and transform pipelines.
- Data-mode choices: single, disjoint, batch, and mixed.
- Convolution, pooling, message passing, and readout layers.
- Ready-made models such as `GCN` and `GeneralGNN`, plus `GNNExplainer`.
- Utility helpers for sparse tensors, graph math, logging, and serialization.

## What this skill does not do

- It does not replace TensorFlow or general Keras guidance.
- It does not cover DGL or PyG.
- It does not require the original repository checkout at runtime; the bundled references and scripts should be enough.

## If you are unsure where a request belongs

- Start with `graph-data` if the pain point is shapes, loaders, datasets, transforms, or download/configuration.
- Start with `gnn-models` if the pain point is layer behavior, pooling, masking, message passing, or model architecture.
- If the task crosses both, read the graph-data route first when the user is defining inputs, and the gnn-models route first when the user is defining the network.
