---
name: loaders-and-sampling
description: "Mini-batch PyTorch Geometric Data objects, configure
  DataLoader/NeighborLoader/LinkNeighborLoader, choose sampler parameters, and
  troubleshoot loader or optional sampling-backend failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# PyTorch Geometric Loaders and Sampling

Use this sub-skill when the task involves mini-batching graphs, sampling neighborhoods from large graphs, building link-prediction loaders, adding temporal or weighted sampling, or debugging loader output shapes and optional sampler backends.

## Quick routing

- Read `references/loader-api.md` when batching a list or dataset of `Data`/`HeteroData` objects, using `follow_batch`/`exclude_keys`, validating `batch`, `ptr`, `num_graphs`, or overriding `Data.__inc__`/`Data.__cat_dim__` for custom attributes.
- Read `references/sampling-workflows.md` when configuring `NeighborLoader`, `LinkNeighborLoader`, `num_neighbors`, `input_nodes`, `edge_label_index`, temporal options, negative sampling, `subgraph_type`, or heterogeneous sampling dictionaries.
- Read `references/troubleshooting.md` when batches have wrong assignment vectors, sampling fails because `pyg-lib` or `torch-sparse` is missing, `input_nodes`/`edge_label_index` are malformed, temporal sampling arguments conflict, or directed subgraphs do not match model depth.
- Run `scripts/loader_smoke_test.py --help` to inspect safe checks, then run `scripts/loader_smoke_test.py` to validate basic installed APIs on tiny synthetic graphs without downloads, GPUs, network access, or writes.

## Minimal decision pattern

1. Use `torch_geometric.loader.DataLoader` for many independent graph examples; it merges graphs into one disconnected `Batch` and increments index-like tensors between examples.
2. Use `NeighborLoader` for node mini-batches on one large graph; set `input_nodes`, `num_neighbors`, and `batch_size`, then compute loss only on `batch[:batch.batch_size]` seed-node outputs.
3. Use `LinkNeighborLoader` for edge/link supervision; pass `edge_label_index` and optional `edge_label`, and keep supervision edges disjoint from message-passing edges when leakage matters.
4. For heterogeneous graphs, pass node or edge types explicitly and use `num_neighbors` as either a shared list or a dictionary with equal hop counts per edge type.
5. Validate loader output before training: inspect `batch.batch`, `batch.ptr`, `batch.n_id`, `batch.e_id`, `batch.input_id`, `batch.edge_label_index`, and per-type stores for hetero data.

## Safe command

```bash
python scripts/loader_smoke_test.py --check-neighbor
```

The smoke test always verifies `DataLoader` batching and reports an actionable optional-backend message if neighbor sampling cannot iterate in the current installation.
