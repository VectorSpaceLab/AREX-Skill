---
name: distributed-tools
description: "Plan safe DGL distributed graph partitioning, launch commands,
  DistGraph usage, and partition metadata validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DGL Distributed Tools

Use this sub-skill when a task needs DGL distributed partitioning, `DistGraph` runtime setup, partition metadata validation, `ip_config.txt`, launch-command construction, or GraphBolt distributed partitioning notes.

## Start Here

- Read [references/api-reference.md](references/api-reference.md) for `dgl.distributed.initialize`, `DistGraph`, distributed dataloaders, `node_split`/`edge_split`, partition concepts, and launcher argument semantics.
- Read [references/workflows.md](references/workflows.md) for partition preflight, safe launch-command construction, trainer script changes, GraphBolt partition handoffs, and skip conditions.
- Read [references/data-formats.md](references/data-formats.md) for `ip_config.txt`, partition config JSON essentials, `part-*` entries, and canonical edge-type string rules.
- Read [references/troubleshooting.md](references/troubleshooting.md) when distributed setup fails due to shared workspace, SSH assumptions, relative paths, process-count mismatches, metadata errors, heterograph edge-type ambiguity, or cluster limits.
- Run `python scripts/check_partition_config.py --part-config PATH` to inspect partition metadata without loading partition graphs or mutating files.
- Run `python scripts/dgl_distributed_command_builder.py --help` to build a dry, printable `tools/launch.py`-style command; the script never SSHes or launches jobs.

## Route Elsewhere

- Single-machine sampling, `dgl.dataloading.DataLoader`, and GraphBolt `ItemSampler` pipelines belong in [dataloading-graphbolt](../dataloading-graphbolt/SKILL.md).
- Model layers, `GraphConv`/`SAGEConv`/`GATConv`, losses, and non-distributed training loops belong in [message-passing-training](../message-passing-training/SKILL.md).
- Raw CSV dataset layout, `DGLDataset`, graph serialization, and dataset cache design belong in [datasets-and-io](../datasets-and-io/SKILL.md).
- Homogeneous/heterogeneous graph construction and canonical edge-type basics belong in [graph-apis](../graph-apis/SKILL.md).

## Safety Notes

- Do not run launchers, SSH, rsync, dispatch data, or start cluster processes unless the user explicitly confirms the target cluster, shared workspace, and failure/cleanup plan.
- Prefer workspace-relative `--part_config` and `--ip_config` values for launch commands; validate them before constructing commands.
- Stop and ask for cluster details when network ports, passwordless SSH, shared storage, GPU/CUDA availability, or multi-host process counts are unknown.
