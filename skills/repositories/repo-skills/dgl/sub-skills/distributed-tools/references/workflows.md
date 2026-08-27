# Distributed Workflows

## Partition Preflight

Before partitioning or launching, collect the following facts:

1. Graph type: homogeneous or heterograph; list node types and canonical edge types.
2. Task split: node masks or edge masks exist before partitioning as boolean node/edge data.
3. Scale: graph and features fit in one machine RAM, or require chunked/distributed preprocessing.
4. Cluster shape: number of machines, trainers per machine, sampler processes per trainer, servers per machine, CPU/GPU expectations.
5. Workspace: the same path exists on every machine and contains the trainer script, `ip_config.txt`, partition metadata JSON, and `part*/` folders.
6. Safety approval: user confirms SSH, shared storage, network ports, and cleanup plan before any real launcher or dispatcher runs.

For an in-memory graph that fits on one host, plan:

```python
dgl.distributed.partition_graph(
    g,
    graph_name="mygraph",
    num_parts=num_machines,
    out_path="data",
    num_hops=1,
    part_method="metis",
    balance_ntypes=g.ndata.get("train_mask"),
    balance_edges=True,
    return_mapping=True,
    graph_formats="csc",
)
```

For GraphBolt-compatible partitions, set `use_graphbolt=True` at partition time and carry that flag into runtime initialization/loading only if the installed DGL version supports the generated format.

Skip or pause partitioning when:

- The graph cannot fit in one host and no chunked graph data pipeline has been approved.
- METIS/ParMETIS, PyTorch, or DGL native libraries are missing.
- The user cannot provide enough disk space for feature shards and HALO nodes.
- The requested output path contains important data and overwrite behavior is unclear.

## Validate Partition Metadata Without Loading Graphs

Use the bundled checker first:

```bash
python scripts/check_partition_config.py --part-config data/mygraph.json --workspace .
```

It performs JSON and path preflight only. It does not import DGL, load `.dgl` graph binaries, inspect features, overwrite canonical etypes, or verify graph contents. If it reports warnings about old-style edge types, plan a migration or regenerate partitions before distributed heterograph training.

Escalate to native DGL verification only after the user approves runtime cost. Full partition verification can load all partitions and original data, so it is not a safe default for large graphs.

## Trainer Script Modifications

A distributed trainer usually differs from a single-machine trainer in these areas:

1. Initialize DGL first with `dgl.distributed.initialize(args.ip_config, use_graphbolt=args.use_graphbolt)`.
2. Initialize `torch.distributed` after DGL initialization.
3. Construct `g = dgl.distributed.DistGraph(args.graph_name, part_config=args.part_config)` for standalone/debug mode or explicit partition path.
4. Split train/validation/test masks with `node_split()` or `edge_split()` and the graph partition book.
5. Replace PyTorch multi-worker dataloading around DGL sampling with `DistDataLoader`, `DistNodeDataLoader`, or `DistEdgeDataLoader`.
6. Move minibatch features/labels from `g.ndata`/`g.edata` using global IDs stored in blocks or sampled IDs.
7. Keep model-layer code ordinary PyTorch/DGL; route layer details to `../message-passing-training/`.

Minimal argument set for a trainer script:

```text
--graph-name mygraph
--part-config data/mygraph.json
--ip-config ip_config.txt
--num-gpus 0
--use-graphbolt false
```

Use CPU/gloo for portable validation unless the user explicitly requires CUDA/NCCL and confirms devices exist on every host.

## Safe Launch Command Construction

Prefer generating a command the user can review:

```bash
python scripts/dgl_distributed_command_builder.py \
  --workspace ./shared-workspace \
  --part-config data/mygraph.json \
  --ip-config ip_config.txt \
  --num-trainers 2 \
  --num-samplers 4 \
  --num-servers 1 \
  --graph-format csc \
  --trainer-command "python train.py --graph-name mygraph --part-config data/mygraph.json --ip-config ip_config.txt"
```

The output uses a workspace-relative DGL launcher path, `tools/launch.py` by default. If the launcher lives elsewhere inside the shared workspace, pass `--launcher-path RELATIVE/PATH/launch.py`. The builder only prints text and does not require or execute the launcher.

Review before running:

- `--part-config` and `--ip-config` are relative to `--workspace` and exist under it.
- `num_parts` in the partition JSON equals the number of non-comment host lines in `ip_config.txt`.
- `num_trainers`, `num_samplers`, and `num_servers` match available CPU/GPU resources on each host.
- The final trainer command is quoted as a single argument and itself uses workspace-relative paths.
- The launch host is one of the worker hosts and has passwordless SSH to every host.

Do not run the printed command if any review item fails.

## GraphBolt Distributed Partition Notes

GraphBolt distributed assets are created during partitioning or dispatch with GraphBolt options. Use them when the requested runtime uses GraphBolt's distributed sampling/feature-fetch path. Key preflight points:

- Partitions must be generated with the same GraphBolt expectation as runtime loading; toggling `use_graphbolt` after the fact is not a format migration.
- Metadata should still preserve global graph counts, partition count, `node_map`, `edge_map`, canonical etype keys, and `part-*` references.
- GraphBolt partition tests check local ID order, inner node/edge masks, original ID recovery, partition book metadata, and dtype consistency.
- For ordinary single-machine GraphBolt `ItemSet`, `ItemSampler`, and `DataLoader`, route to `../dataloading-graphbolt/`.

## Stop Conditions

Stop and ask the user before proceeding when:

- The next step would SSH, start servers, rsync data, dispatch partitions, or modify a shared workspace.
- `ip_config.txt` contains hosts or ports the user has not confirmed.
- Partition metadata references paths outside the intended workspace or missing `part*` files.
- The graph requires GPUs, NCCL, or backend hardware that is not known to be present on all machines.
- Heterograph `edge_map`/`etypes` keys are old non-canonical strings and the migration source graph is unavailable.
