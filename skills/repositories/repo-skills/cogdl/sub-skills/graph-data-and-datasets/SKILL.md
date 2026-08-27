---
name: graph-data-and-datasets
description: "Use CogDL graph data objects, custom datasets, built-in dataset
  selection, masks, batching, and no-download data validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# CogDL Graph Data and Datasets

Use this sub-skill when the task is about CogDL data objects rather than model
architecture or training orchestration.

## Use when

- Creating or inspecting `cogdl.data.Graph`, `Adjacency`, `Dataset`,
  `NodeDataset`, `GraphDataset`, `generate_random_graph`, or `DataLoader`.
- Building a no-download custom node-classification or graph-classification
  fixture.
- Choosing a built-in dataset name while making download/cache/dependency
  effects explicit.
- Debugging `edge_index`, CSR fields, masks, labels, node features, subgraphs,
  `local_graph`, self-loops, normalization, or batched graph objects.

## Route elsewhere

- Training loops, wrapper matching, checkpoints, loggers, or `Trainer` details:
  `../training-wrappers-and-customization/SKILL.md`.
- High-level `experiment()` calls, CLI flags, variants, or AutoML:
  `../experiments-and-cli/SKILL.md`.
- Model, layer, sparse operator, PyG/Jittor/DGL, or CUDA acceleration details:
  `../models-layers-and-operators/SKILL.md`.
- Application pipelines such as OAG-BERT, recommendation, visualization, or
  embedding pipelines: `../pipelines-and-applications/SKILL.md`.

## Operating checklist

1. Prefer a self-contained `Graph` or custom dataset artifact before loading a
   built-in dataset. Built-in datasets may download data and write caches when
   missing.
2. Validate node-classification fixtures before handing them to experiments or
   wrappers. Use the bundled `scripts/validate_graph_masks.py` on a saved
   `Graph` or `NodeDataset` artifact.
3. For quick no-download examples, use
   `scripts/create_tiny_graph_dataset.py --output-dir <directory>` to create
   deterministic node and graph classification artifacts.
4. Keep `Graph` schemas explicit: tensor `x`, tensor `y`, COO `edge_index`, and
   boolean or index masks with node-count-compatible lengths.
5. For graph classification, save a list of local-node-indexed `Graph` objects
   and batch them with `cogdl.data.DataLoader`; if node features are absent,
   route the degree-feature training decision to the training-wrapper sub-skill.

## Reference map

- `references/graph-and-dataset-api.md`: verified public data APIs and graph
  methods.
- `references/data-formats.md`: COO/CSR formats, masks, batching, mutation
  semantics, and validation checklist.
- `references/built-in-datasets.md`: dataset families, registered names, and
  network/cache/dependency caveats.
- `references/troubleshooting.md`: common failures and recovery steps for graph
  data construction.

