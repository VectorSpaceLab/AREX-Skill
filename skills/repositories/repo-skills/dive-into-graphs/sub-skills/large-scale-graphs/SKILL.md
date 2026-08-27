---
name: large-scale-graphs
description: "Use DIG's large-scale graph stack for GraphFMOB/GraphFMIB-style
  workflows, METIS partitioning, subgraph loaders, feature momentum, and async
  graph-memory helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Large-Scale Graphs

Use this sub-skill for DIG workflows that scale graph learning to large node-classification graphs or the GraphFMOB/GraphFMIB code paths.

## Include

- `dig.lsgraph.dataset`: `get_data`, `SubgraphLoader`, `EvalSubgraphLoader`.
- `dig.lsgraph.method.FM`: `FeatureMomentum`.
- `dig.lsgraph.method.GraphFMOB`: `AsyncIOPool`, `metis`, `permute`, `compute_micro_f1`, `gen_masks`, `dropout`, and GraphFMOB loaders when `dig_ext` is available.
- `examples/lsgraph/GraphFMOB` style workflows and the `GraphFMIB` example path.
- OGB/Reddit/Flickr/Yelp/SBM-style large-graph loading patterns.

## Exclude

- Molecular, 3D, SSL, explainability, GOOD, augmentation, or fairness workflows unless they are used only as supporting examples.

## Start Here

- Read `references/api-reference.md` for the loader and memory helpers.
- Read `references/workflows.md` for the partition/load/train/inference pattern.
- Read `references/troubleshooting.md` when `dig_ext` or sparse extensions are missing.
- Run `scripts/lsgraph_feature_momentum_smoke.py` for a safe, extension-aware smoke check.

## Core Workflows

- **Partitioned training**: use METIS partitioning, `SubgraphLoader`, and `EvalSubgraphLoader` to batch a large graph into local neighborhoods.
- **Feature memory**: use `FeatureMomentum` and `AsyncIOPool` to keep node embeddings or async transfer buffers aligned with the partitioned loader.
- **Model evaluation**: use `compute_micro_f1` on the loaded data and masks after training.

## Important Limitation

`dig.lsgraph.dataset` and the async helper code depend on a compiled `dig_ext` extension in the source tree. If that extension is not present, document the limitation and restrict yourself to extension-independent API guidance. `FeatureMomentum` can be imported directly from `dig.lsgraph.method.FM`, but some CPU-only PyTorch builds still fail its pinned-memory allocation and should be reported as a backend limitation rather than treated as a dataset failure.
