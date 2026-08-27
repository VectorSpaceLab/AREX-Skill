---
name: dataloading-graphbolt
description: "Build stochastic minibatch, DGL dataloading, and GraphBolt
  pipelines for DGL training."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DGL Dataloading and GraphBolt

Use this sub-skill when a task needs stochastic minibatch training, neighbor sampling, block/MFG handoff, GraphBolt datapipes, `ItemSet`/`ItemSampler`, `OnDiskDataset` task sets, feature fetching, or GPU/UVA dataloader choices.

## Start Here

- Read `references/api-reference.md` for classic `dgl.dataloading` and `dgl.graphbolt` constructors, outputs, and object contracts.
- Read `references/workflows.md` for node/link neighbor sampling, `DataLoader` vs GraphBolt decisions, feature prefetch/fetch, and GPU/UVA setup.
- Read `references/data-formats.md` when preparing or validating GraphBolt `metadata.yaml` and `OnDiskDataset` task splits.
- Read `references/troubleshooting.md` for device mismatches, CUDA worker rules, GraphBolt native-library issues, feature-key errors, and empty seed batches.
- Run `python scripts/graphbolt_pipeline_sanity.py --help` for available CPU-safe checks.

## Route Elsewhere

- Full GNN layer implementation, block-compatible model `forward()` methods, losses, and training loops belong in `../message-passing-training/`.
- Raw CSV validation, `DGLDataset`, `CSVDataset`, graph serialization, and initial OnDiskDataset file preparation belong in `../datasets-and-io/`.
- Graph construction, heterograph canonical edge types, `dgl.to_block()` details, batching, and graph transforms belong in `../graph-apis/`.
- Cluster launch, graph partitioning, distributed sampling/training, and DDP process orchestration belong in `../distributed-tools/`.

## Safety Defaults

- Prefer tiny CPU synthetic graphs and local metadata validation for smoke checks; do not download datasets by default.
- Use GraphBolt for pipelined CPU/pinned-memory large-graph workflows, but use classic `dgl.dataloading.DataLoader` for GPU neighbor sampling and UVA sampling.
- Keep scripts and examples independent from external repositories; pass user data paths explicitly.
