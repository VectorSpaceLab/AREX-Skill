# Distributed Troubleshooting

## Missing Shared Workspace

Signals:

- Launcher command uses `--workspace`, but remote hosts cannot find the trainer script, partition JSON, `ip_config.txt`, or `part*/` folders.
- Errors mention missing `DGL_CONF_PATH`, `graph.dgl`, `node_feats.dgl`, or `edge_feats.dgl` after SSH.

Actions:

- Confirm `--workspace` is the same path on every host or that data has been copied to identical relative locations.
- Keep `--part_config` and `--ip_config` relative to `--workspace`.
- Run the bundled command builder and partition checker locally before any launch.
- Stop if the next step requires copying large data or mutating shared storage without user approval.

## SSH and Launcher Assumptions

Signals:

- Launcher hangs or fails before Python training starts.
- Errors mention SSH permission denied, unknown host, unavailable port, or cleanup failures.

Actions:

- Confirm the launch host is one of the worker hosts.
- Confirm passwordless SSH from the launch host to every host in `ip_config.txt`.
- Confirm `--ssh_port` and `--ssh_username` if defaults are not valid.
- Confirm firewall rules allow DGL server ports and PyTorch distributed rendezvous.
- Do not retry repeatedly against an unconfirmed cluster; ask for cluster/network details.

## Wrong Relative Paths

Signals:

- `num_parts` can be read locally, but launch fails remotely.
- `part_config` exists as an absolute local path but not inside the shared workspace.
- Trainer arguments use paths different from launcher `--part_config`/`--ip_config`.

Actions:

- Make `--part_config data/mygraph.json` and `--ip_config ip_config.txt` workspace-relative.
- Ensure the final trainer command uses the same relative paths.
- Avoid embedding local checkout paths, virtualenv paths, or source-tree tool paths in reusable commands.

## Server, Sampler, and Trainer Mismatch

Signals:

- Assertion that `num_trainers` or `num_servers` must be positive.
- `node_split`/`edge_split` asserts total clients are not a multiple of partitions.
- Training hangs after servers start.

Actions:

- Set `--num_servers >= 1` and `--num_trainers >= 1` per machine.
- Set `--num_samplers >= 0`; each trainer creates that many sampler processes through `dgl.distributed.initialize()`.
- Check `num_parts == number_of_ip_config_hosts` for `tools/launch.py`.
- If using `node_trainer_ids` or `edge_trainer_ids`, verify they were produced during partitioning for the intended `num_trainers_per_machine`.
- Keep `--num_server_threads` small when servers and trainers share CPU cores.

## Partition Metadata Errors

Signals:

- Missing `graph_name`, `num_parts`, `node_map`, `edge_map`, or `part-0` fields.
- `node_map`/`edge_map` range lengths differ from `num_parts`.
- Range starts/ends are non-integer, decreasing, or non-contiguous.
- `part-N` references do not exist under the workspace.

Actions:

- Run `python scripts/check_partition_config.py --part-config PATH --workspace WORKSPACE`.
- Regenerate partitions if metadata is structurally inconsistent.
- Use `dgl.distributed.load_partition(part_config, part_id)` for deeper local inspection only when partition files are small enough and DGL is installed.
- Treat GraphBolt-specific metadata conservatively; validate common fields and path existence first.

## Heterograph Edge-Type Mismatch

Signals:

- Errors mention ambiguous edge type, canonical etype format, or `to_canonical_etype()` failure.
- `edge_map`/`etypes` keys look like `plays` instead of `user:plays:game`.
- Link prediction code uses relation-only reverse etypes in a heterograph.

Actions:

- Use canonical edge types for partition metadata and distributed dataloading: `src:relation:dst` strings in JSON; `(src, relation, dst)` tuples in Python APIs where accepted.
- Do not guess canonical endpoints for old heterograph configs. The native migration logic needs partition graph structure to infer endpoints.
- If a homogeneous graph has old-style keys, document the intended single node type before migration.
- Align reverse edge mappings with canonical keys for edge prediction.

## GraphBolt Partition Issues

Signals:

- Runtime `use_graphbolt=True` fails while ordinary partition loading works.
- Errors mention missing CSC graph assets, node/edge attribute dtypes, `inner_node`, `inner_edge`, or original IDs.

Actions:

- Confirm partitions were generated with GraphBolt support rather than toggling runtime only.
- Confirm installed DGL, GraphBolt, PyTorch, and torchdata versions are compatible.
- Validate common partition config fields first, then use native GraphBolt partition tests or `load_partition(..., use_graphbolt=True)` only when safe.
- Route single-machine GraphBolt data-pipe design to `../dataloading-graphbolt/`.

## Cluster, Hardware, and Network Limits

Signals:

- GPU/NCCL failures vary by host.
- CPU memory or disk fills during partitioning or dispatch.
- Network timeouts occur under sampling load.

Actions:

- Start with CPU/gloo smoke validation unless the user explicitly requested GPU/NCCL.
- Confirm every host has matching DGL backend, PyTorch, CUDA/NCCL, drivers, and visible GPUs before GPU launch.
- Do not run chunking, dispatch, SSH launch, or multi-host recovery as a default validation step.
- Stop and ask for hardware/network requirements when the task needs resources not visible from the local environment.
