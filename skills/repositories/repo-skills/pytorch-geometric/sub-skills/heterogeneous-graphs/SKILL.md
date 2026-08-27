---
name: heterogeneous-graphs
description: "Build and debug PyTorch Geometric heterogeneous graph data,
  loaders, HeteroConv models, to_hetero conversions, and hetero link-prediction
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Heterogeneous Graphs

Use this sub-skill when the task involves PyG `HeteroData`, typed metadata, heterogeneous mini-batches, `HeteroConv`, `to_hetero`, bipartite message passing, or heterogeneous link prediction.

## Quick Routing

- Read `references/hetero-api.md` when you need exact object shapes, metadata conventions, loader signatures, or model API choices for hetero graphs.
- Read `references/hetero-workflows.md` when implementing a complete workflow: constructing `HeteroData`, converting a homogeneous SAGE-style model with `to_hetero`, hand-writing `HeteroConv`, using hetero loaders, or preparing link prediction splits.
- Read `references/troubleshooting.md` when errors mention missing stores, invalid edge triplets, absent reverse edges, `to_hetero` metadata mismatch, or bipartite size inference.
- Run `scripts/hetero_metadata_check.py --help` to inspect a safe synthetic validator for tiny `HeteroData` metadata and reverse-edge expectations.

## Common Starting Points

- Build a typed graph with `data = HeteroData()`, then assign node stores such as `data['paper'].x` and edge stores such as `data['author', 'writes', 'paper'].edge_index`.
- Use `node_types, edge_types = data.metadata()` as the canonical metadata tuple for `to_hetero`, `HeteroConv` planning, and hetero loader dictionaries.
- For mini-batch node tasks, pass hetero neighbor budgets as `num_neighbors={edge_type: [fanout1, fanout2]}` and set `input_nodes=('paper', paper_indices)`.
- For link prediction, keep forward and reverse relation names explicit, and pass matching `edge_types` and `rev_edge_types` to `RandomLinkSplit` when reverse edges exist.
- For model conversion, prefer `SAGEConv((-1, -1), hidden_channels)` or other bipartite-capable layers in the homogeneous model before calling `to_hetero(model, data.metadata(), aggr='sum')`.

## Boundaries

- For homogeneous `Data`, dataset classes, transforms, and basic graph validation, use the sibling `data-and-datasets` skill.
- For generic training-loop design, metrics, pooling, and homogeneous GNN architecture choices, use the sibling `gnn-modeling` skill.
- For distributed graph stores, remote backends, multi-GPU, or service-based sampling, use the sibling `scalable-distributed` skill.
