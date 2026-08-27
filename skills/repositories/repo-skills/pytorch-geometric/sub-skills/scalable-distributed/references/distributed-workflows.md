# Distributed PyG Workflows

This reference covers PyG's distributed graph-learning path: partitioned graph data, local distributed stores, RPC-backed sampling, and DDP model training. Use it when a single-process `NeighborLoader` or `LinkNeighborLoader` is not enough for graph size, feature size, or sampling throughput.

## Core distributed objects

PyG 2.9 exposes these distributed building blocks from `torch_geometric.distributed`:

- `Partitioner(data, num_parts, root, recursive=False)`: writes partition metadata, node/edge maps, and per-partition graph/feature files for a `Data` or `HeteroData` object.
- `LocalFeatureStore`: implements PyG's `FeatureStore` interface for one partition's node and edge features; construct from partition files with `LocalFeatureStore.from_partition(root, pid)`.
- `LocalGraphStore`: implements PyG's `GraphStore` interface for one partition's graph structure; construct from partition files with `LocalGraphStore.from_partition(root, pid)`.
- `DistContext(rank, global_rank, world_size, global_world_size, group_name, role=DistRole.WORKER)`: identifies the current distributed worker and derives the RPC worker name as `f"{group_name}-{rank}"`.
- `DistNeighborLoader(data=(feature_store, graph_store), num_neighbors, input_nodes, current_ctx, ...)`: distributed node-neighborhood loader.
- `DistLinkNeighborLoader(data=(feature_store, graph_store), num_neighbors, edge_label_index, current_ctx, ...)`: distributed link-neighborhood loader.
- `DistNeighborSampler`: lower-level sampler used by the distributed loaders when a custom sampler lifecycle is needed.

## Partitioning checklist

Use partitioning as a separate preparation step and keep the training job read-only against the partition directory.

```python
from torch_geometric.distributed import Partitioner

partitioner = Partitioner(data, num_parts=4, root="/shared/pyg-partitions")
partitioner.generate_partition()
```

Validate the generated layout before training:

- `META.json` exists and records whether the graph is homogeneous or heterogeneous.
- Homogeneous graphs include `node_map.pt`, `edge_map.pt`, and `part_0/`, `part_1/`, ... directories.
- Heterogeneous graphs include `node_map/<node_type>.pt`, `edge_map/<edge_type>.pt`, and per-partition directories.
- Each partition directory contains `graph.pt`, `node_feats.pt`, and `edge_feats.pt` when the source data supplied those fields.
- `num_parts` used at training time matches the partition metadata.
- Each process uses a unique `pid` in `[0, num_parts - 1]`.

For tiny validation fixtures, create a synthetic `Data` object, partition it into two parts in a temporary directory, load both `LocalGraphStore.from_partition(...)` and `LocalFeatureStore.from_partition(...)`, and assert that `num_partitions`, `partition_idx`, `meta`, node partition books, and edge partition books are populated.

## Training skeleton

A distributed PyG job combines DDP for model gradients and RPC for remote sampling/feature lookup. A practical training process follows this order:

1. Read rank, world size, local rank, master address, and ports from the launcher environment.
2. Create `DistContext` for the process.
3. Initialize the DDP process group, typically with `gloo` for CPU-oriented sampling and `nccl` for CUDA model training when available.
4. Load this process's stores with `LocalFeatureStore.from_partition(partition_root, pid=rank)` and `LocalGraphStore.from_partition(partition_root, pid=rank)`.
5. Create `DistNeighborLoader` or `DistLinkNeighborLoader` with `(feature_store, graph_store)`, `current_ctx`, seed nodes or supervised edges for this process, and a conservative worker count.
6. Wrap the model in `torch.nn.parallel.DistributedDataParallel` after moving it to the process-local device.
7. Iterate the distributed loader, compute loss on seed nodes or supervised edges, call `loss.backward()`, and step the optimizer.
8. Shut down RPC and destroy the process group in `finally` blocks.

The distributed loaders wrap sampler-process initialization and cleanup. They inherit from PyG's node/link loader families, but batch creation differs from a single-node loader because sampling and remote feature fetching are integrated to reduce RPC traffic.

## Launch recipe

For one host with multiple processes, prefer the native PyTorch launcher:

```bash
torchrun --standalone --nproc_per_node=4 train_dist_pyg.py \
  --partition-root /shared/pyg-partitions \
  --num-neighbors 15 10 \
  --batch-size 1024
```

For multiple nodes, every node must agree on rendezvous address, rendezvous port, world size, and partition root visibility:

```bash
torchrun --nnodes=2 --nproc_per_node=4 \
  --rdzv_backend=c10d --rdzv_endpoint "$MASTER_ADDR:$MASTER_PORT" \
  train_dist_pyg.py --partition-root /shared/pyg-partitions
```

Keep RPC and DDP ports distinct if the script initializes both manually. Avoid binding rendezvous ports to interfaces that other nodes cannot reach.

## Node and link distributed sampling

For node tasks, route seed nodes through `DistNeighborLoader`:

```python
loader = DistNeighborLoader(
    data=(feature_store, graph_store),
    num_neighbors=[15, 10],
    input_nodes=train_node_ids_for_this_rank,
    batch_size=1024,
    current_ctx=current_ctx,
    num_workers=2,
)
```

For link tasks, route supervised edges through `DistLinkNeighborLoader`:

```python
loader = DistLinkNeighborLoader(
    data=(feature_store, graph_store),
    num_neighbors=[20, 10],
    edge_label_index=edge_label_index_for_this_rank,
    edge_label=edge_label_for_this_rank,
    batch_size=1024,
    current_ctx=current_ctx,
    num_workers=2,
)
```

Validation points:

- Confirm the loader string starts with `DistNeighborLoader` or `DistLinkNeighborLoader` after construction.
- Check that `loader.dist_sampler` is a `DistNeighborSampler` when a custom sampler was not supplied.
- Inspect one batch on a tiny partition fixture before starting long training.
- Confirm global seed IDs map to expected partition IDs through `LocalGraphStore.get_partition_ids_from_nids(...)` or edge partition IDs through `get_partition_ids_from_eids(...)`.

## Heterogeneous distributed graphs

For hetero graphs, keep node and edge types canonical throughout partitioning and training:

- Use node type strings such as `"paper"` and edge type tuples such as `("author", "writes", "paper")`.
- Preserve the same metadata used by the model, loaders, partitioner, and loss code.
- Validate `num_nodes_dict`, `edge_index_dict`, and per-type feature tensors before partitioning.
- For link prediction, keep supervision edge types and reverse edge types explicit; route hetero modeling details to the `heterogeneous-graphs` sub-skill if the task is mainly about `HeteroData`, `HeteroConv`, or `to_hetero`.

## Multi-GPU and multi-node variants

Use ordinary DDP with PyG loaders when the graph fits each process's memory or when a remote/distributed sampler supplies batches:

- Run one process per accelerator or CPU shard.
- Use process-local `device = torch.device(f"cuda:{local_rank}")` only after confirming CUDA is available.
- Move the model and each batch to the process-local device; keep storage and sampling on CPU unless a backend explicitly supports GPU sampling.
- Use `DistributedSampler` for graph-level datasets with ordinary `DataLoader`.
- Use process-local seed splits for a single large graph with `NeighborLoader` or distributed stores.
- Avoid dataset downloads, service startup, and GPU allocation in smoke tests; verify launch scripts with tiny synthetic data or dry-run argument parsing first.

## Safe verification approach

Public skill checks should rely on synthetic fixtures and environment reports rather than repository-local files:

- Use the bundled backend checker for import, CUDA-visibility, and optional-extension assertions.
- Use a tiny temporary graph for partition metadata sanity checks when partitioning dependencies are available.
- Use one synthetic batch to validate distributed-loader construction before any long training loop.
- Skip hardware, service, and multi-node examples unless the requested environment explicitly provides devices, ports, shared storage, and service credentials.
