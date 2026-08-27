# Distributed API Reference

## Core Runtime Order

A distributed trainer script must set up DGL before using distributed graph APIs:

```python
import dgl
import torch as th

dgl.distributed.initialize("ip_config.txt", use_graphbolt=False)
th.distributed.init_process_group(backend="gloo")
g = dgl.distributed.DistGraph("graph_name", part_config="data/graph_name.json")
```

Use `dgl.distributed.initialize(ip_config, net_type=None, num_servers=None, max_queue_size=None, role='default', use_graphbolt=False)` before `torch.distributed.init_process_group()` and before creating `DistGraph`, `DistTensor`, distributed samplers, or distributed dataloaders. If server-side UDFs or distributed embedding initializers are required, define them before `initialize()` because server processes may import and execute them during startup.

`use_graphbolt=True` is only appropriate when partitions were created with GraphBolt support and the runtime DGL version supports GraphBolt distributed loading for that partition format.

## `DistGraph`

Use `dgl.distributed.DistGraph(graph_name, gpb=None, part_config=None)` to access graph structure and partitioned features.

- Distributed mode: launched by DGL tooling; construct with `DistGraph("graph_name")` or pass `part_config` only when the script needs a portable explicit path.
- Standalone/debug mode: create a single-partition graph and pass `part_config="relative/path/graph_name.json"`.
- DGL allows one live `DistGraph` object in a process; destroying one and creating another is undefined.
- `g.ndata[name]` and `g.edata[name]` return distributed tensors, not ordinary backend tensors.
- `g.ntypes`, `g.etypes`, `g.canonical_etypes`, and `g.to_canonical_etype(etype)` are important for heterographs and partition metadata debugging.

Partitioned graph files contain global-to-local mappings, HALO nodes/edges, and feature shards. Use `dgl.distributed.load_partition(part_config, part_id, load_feats=True, use_graphbolt=False)` for local inspection only; do not call it inside every trainer unless the workflow intentionally bypasses the server/client runtime.

## Workload Splitting

Use boolean masks stored before partitioning, then split them at runtime:

```python
train_nids = dgl.distributed.node_split(
    g.ndata["train_mask"],
    partition_book=g.get_partition_book(),
    ntype="_N",
    force_even=True,
)
```

```python
train_eids = dgl.distributed.edge_split(
    g.edata["train_mask"],
    partition_book=g.get_partition_book(),
    etype="_E",
    force_even=True,
)
```

Important parameters:

- `nodes` / `edges`: 1D boolean mask or distributed tensor whose length equals the number of nodes/edges for that type.
- `partition_book`: required for regular tensors; inferred from `DistTensor` inputs.
- `ntype` / `etype`: type name for heterographs; use canonical etype tuples or canonical strings when ambiguity is possible.
- `rank`: defaults to the current trainer rank.
- `force_even=True`: balances workload across trainers, which matters for synchronous SGD.
- `node_trainer_ids` / `edge_trainer_ids`: use when the graph was partitioned with multiple trainers per machine and stored trainer assignments.

## Distributed Sampling and Dataloaders

Low-level distributed sampling uses `dgl.distributed.sample_neighbors(g, seeds, fanout, ...)` with `dgl.distributed.DistDataLoader(dataset, batch_size, shuffle=False, collate_fn=None, drop_last=False, queue_size=None)`.

```python
def sample_blocks(seeds):
    seeds = th.as_tensor(seeds, dtype=th.int64)
    blocks = []
    for fanout in [10, 25]:
        frontier = dgl.distributed.sample_neighbors(g, seeds, fanout, replace=True)
        block = dgl.to_block(frontier, seeds)
        seeds = block.srcdata[dgl.NID]
        blocks.insert(0, block)
    return blocks

dataloader = dgl.distributed.DistDataLoader(
    dataset=train_nids,
    batch_size=1024,
    collate_fn=sample_blocks,
    shuffle=True,
)
```

High-level wrappers include `DistNodeDataLoader` and `DistEdgeDataLoader`; they accept a `DistGraph`, split IDs, and a DGL sampler. In a distributed graph, dataloader worker processes are created by `dgl.distributed.initialize()`. Do not place distributed sampling inside a PyTorch `DataLoader` with worker processes.

For single-machine `dgl.dataloading.DataLoader`, `NeighborSampler`, and GraphBolt `ItemSampler` usage, route to `../dataloading-graphbolt/`.

## Partitioning Concepts

Use `dgl.distributed.partition_graph(g, graph_name, num_parts, out_path, num_hops=1, part_method='metis', balance_ntypes=None, balance_edges=False, return_mapping=False, num_trainers_per_machine=1, objtype='cut', graph_formats=None, use_graphbolt=False, **kwargs)` when the graph fits on one machine.

Key choices:

- `graph_name`: must match `DistGraph(graph_name)` and the metadata JSON basename convention.
- `num_parts`: normally equals the number of cluster machines for `tools/launch.py`.
- `out_path`: output folder containing `graph_name.json` and `part0/`, `part1/`, ... directories.
- `part_method`: `metis` for locality when available; `random` for simple tests or when METIS is unavailable.
- `num_hops`: HALO expansion; `1` is common for neighbor sampling.
- `balance_ntypes`: balances node types or train/valid/test mask categories.
- `balance_edges=True`: balances edge ownership in addition to node counts.
- `return_mapping=True`: returns original-ID mappings for post-training embedding/result reconstruction.
- `graph_formats`: commonly `csc` for sampling; may be comma-separated in launcher metadata.
- `use_graphbolt=True`: emits GraphBolt-compatible partition assets for supported workflows.

For massive graphs that cannot fit in one host, use a chunked graph data pipeline and dispatch flow. Treat chunking, partition assignment, and dispatch scripts as cluster/data-engineering operations with filesystem and multiprocessing side effects; do not run them without explicit user approval.

## Launch Roles and Arguments

DGL's `tools/launch.py` starts servers and trainers over SSH. A safe skill should construct commands, not execute them.

Important launcher arguments:

- `--workspace`: working directory visible on every machine. `launch.py` changes into this directory before running server/client commands.
- `--num_trainers`: trainer processes per machine; must be positive.
- `--num_samplers`: sampler processes per trainer; `0` is allowed.
- `--num_servers`: graph server processes per machine; must be positive.
- `--num_omp_threads`: OMP threads per trainer; if omitted, DGL estimates from local CPU count.
- `--num_server_threads`: OMP threads per server; keep small when servers and trainers share machines.
- `--part_config`: partition metadata JSON path relative to `--workspace`.
- `--ip_config`: IP configuration path relative to `--workspace`.
- `--graph_format`: partition graph format such as `csc`, `csr`, `coo`, or comma-separated forms.
- `--ssh_port` and `--ssh_username`: SSH connection details; never assume these are available.
- `--extra_envs`: optional `KEY=VALUE` entries such as `NCCL_DEBUG=INFO`.
- final quoted command: usually `python train.py --graph-name NAME --ip-config ip_config.txt ...`.

`tools/launch.py` checks that the partition config `num_parts` equals the number of hosts in `ip_config.txt`. It starts server commands with DGL environment variables such as `DGL_CONF_PATH`, `DGL_IP_CONFIG`, `DGL_NUM_SERVER`, and `DGL_SERVER_ID`, then wraps trainers with `torch.distributed.run`.

`tools/distgraphlaunch.py` is a narrower launcher for distributed graph server-style commands with `--num_proc_per_machine`, `--master_port`, and `--ip_config`. Prefer documenting its assumptions rather than using it unless the user has an existing DGL DistGraph service workflow.
