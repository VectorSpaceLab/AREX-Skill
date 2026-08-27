---
name: scalable-distributed
description: "Scale PyTorch Geometric workloads with large-graph neighbor
  sampling, remote FeatureStore/GraphStore backends, distributed PyG loaders,
  multi-GPU or multi-node DDP recipes, CPU affinity, profiling, and backend
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# PyTorch Geometric Scalable and Distributed Workflows

Use this sub-skill when the task involves graphs that do not fit a simple full-batch loop, remote graph or feature storage, distributed neighbor sampling, multi-GPU or multi-node training, CPU worker affinity, PyG profiling, or optional sampling backend diagnostics.

## Quick routing

- Read `references/distributed-workflows.md` when partitioning a graph, constructing `LocalFeatureStore`/`LocalGraphStore`, using `DistNeighborLoader` or `DistLinkNeighborLoader`, wiring `DistContext`, RPC, DDP, or planning multi-node launch variables.
- Read `references/scaling-and-backends.md` when deciding between full-batch, `NeighborLoader`, remote `FeatureStore`/`GraphStore`, distributed PyG, multi-GPU DDP, CPU affinity, or `torch_geometric.profile` tools.
- Read `references/troubleshooting.md` when sampling extensions are missing, CUDA wheels mismatch, rendezvous hangs, partition metadata fails to load, remote stores return malformed tensors, CPU affinity slows the job, or profile output is empty.
- Run `scripts/check_sampling_backends.py --help` to inspect safe options, then run `scripts/check_sampling_backends.py` for actionable JSON about Torch, PyG, CUDA availability, and optional PyG sampling extensions.

## Minimal decision pattern

1. Start with the smallest scaling mechanism that solves the bottleneck: ordinary mini-batch loading for many small graphs, `NeighborLoader`/`LinkNeighborLoader` for one large in-memory graph, remote stores for out-of-process graph/features, and distributed PyG only after single-host sampling or storage is not enough.
2. For node supervision on a large graph, use `NeighborLoader(data, num_neighbors=[fanout_per_hop], input_nodes=seed_nodes, batch_size=...)` and compute loss only on seed-node outputs.
3. For distributed PyG, partition first, load each worker's `LocalFeatureStore.from_partition(root, pid)` and `LocalGraphStore.from_partition(root, pid)`, create a `DistContext`, initialize DDP/RPC consistently, then use `DistNeighborLoader` or `DistLinkNeighborLoader`.
4. For remote backends, expose graph structure through a `GraphStore`, features through a `FeatureStore`, and pass a sampler-aware store pair into PyG loaders; validate CRUD and sampling contracts before training.
5. For multi-GPU or multi-node training, keep one process per accelerator, shard seed nodes with distributed samplers or process-local masks, wrap the model with `DistributedDataParallel`, and keep sampling workers CPU-bound unless the backend explicitly supports device-side sampling.
6. Before blaming model code, run the backend checker and verify package versions, optional extensions, CUDA availability, partition metadata, rendezvous ports, worker counts, and CPU affinity masks.

## Safe command

```bash
python scripts/check_sampling_backends.py --require-neighbor-backend
```

The checker does not allocate GPUs, start services, download data, or write files. It reports JSON that future agents can assert against in usability tests or paste into troubleshooting notes.
