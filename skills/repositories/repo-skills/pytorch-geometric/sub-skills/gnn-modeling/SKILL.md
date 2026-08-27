---
name: gnn-modeling
description: "Design, train, debug, and smoke-test PyTorch Geometric GNN modules
  with MessagePassing, common convolution layers, pooling, metrics, and
  compile/JIT-aware workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# GNN Modeling

Use this sub-skill when building or troubleshooting PyTorch Geometric neural network modules: custom `MessagePassing` layers, homogeneous GNN stacks, graph-level pooling models, link prediction scorers, metrics, profiling, `torch.compile`, TorchScript/JIT migration, and tiny deterministic training checks.

Do not use this sub-skill for heterogeneous graph data modeling details, explainability configuration, distributed or multi-GPU training, dataset construction, or sampling-loader design. Route those to sibling sub-skills when present.

## Start Here

- Read `references/modeling-api.md` when selecting PyG neural network APIs, implementing a custom `MessagePassing` operator, choosing a convolution/pooling layer, or checking tensor contracts.
- Read `references/training-workflows.md` when writing node classification, graph classification, link prediction, metric, profiling, `torch.compile`, or TorchScript-aware training loops.
- Read `references/troubleshooting.md` when a model fails on `edge_index`, feature dimensions, cached convolutions, sparse optional extensions, dynamic compilation, or over-smoothing.
- Run `scripts/tiny_gcn_smoke.py --epochs 8` before or after editing model code to prove the installed PyG runtime can train a tiny synthetic GCN without downloads, GPUs, or external data.

## Common Tasks

- Build a homogeneous node model with `GCNConv`, `GATConv`, `SAGEConv`, or higher-level models such as `GCN`, `GraphSAGE`, `GIN`, then validate `out.shape == [num_nodes, num_classes]` for node classification.
- Implement a custom layer by subclassing `MessagePassing`, calling `super().__init__(aggr=...)`, validating `edge_index` as `torch.long` with shape `[2, num_edges]`, and using `propagate(edge_index, x=x, ...)`.
- Add graph-level prediction by applying convolution layers to node features, then pooling with `global_mean_pool`, `global_add_pool`, or `global_max_pool` using the mini-batch `batch` vector.
- Add link prediction by encoding nodes with a GNN, scoring endpoint embeddings, and evaluating ranking/classification metrics from `torch_geometric.metrics` where applicable.
- Keep smoke tests tiny and deterministic: use synthetic `Data`, fixed seeds, CPU tensors, one or a few optimizer steps, and assertions on loss finiteness and tensor shapes.

## Safe Validation

```bash
python scripts/tiny_gcn_smoke.py --epochs 8
python scripts/tiny_gcn_smoke.py --help
```

Expected output includes initial/final loss, predicted labels for a six-node synthetic graph, and `tiny_gcn_smoke: ok`.
