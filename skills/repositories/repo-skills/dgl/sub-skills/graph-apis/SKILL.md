---
name: graph-apis
description: "Construct, inspect, transform, batch, and debug homogeneous and
  heterogeneous DGL graphs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DGL Graph APIs

Use this sub-skill when a task needs to create, inspect, transform, batch, or debug DGL homogeneous or heterogeneous graphs before model training or data loading.

## Start Here

- For constructors, object relationships, feature views, idtype/device rules, conversions, blocks, batching, and subgraph APIs, read [references/api-reference.md](references/api-reference.md).
- For compact recipes, including homogeneous graphs, heterographs, canonical edge types, transforms, batching, and validation checks, read [references/workflows.md](references/workflows.md).
- For failure diagnosis around canonical edge-type ambiguity, feature schema mismatches, device/idtype errors, zero-node assumptions, batching, and import/native-library errors, read [references/troubleshooting.md](references/troubleshooting.md).
- To verify a local DGL install can run the graph basics safely, run `python scripts/graph_smoke.py` from this sub-skill directory.

## Route Elsewhere

- CSV ingestion, `DGLDataset`, `CSVDataset`, graph caching, and persistent save/load depth belong in [datasets-and-io](../datasets-and-io/SKILL.md).
- Neighbor sampling, minibatch `DataLoader`, and GraphBolt pipelines belong in [dataloading-graphbolt](../dataloading-graphbolt/SKILL.md).
- Message passing, `update_all`, built-in functions, GNN layers, and training loops belong in [message-passing-training](../message-passing-training/SKILL.md).
- Distributed partitioning, launchers, and cluster/runtime tools belong in [distributed-tools](../distributed-tools/SKILL.md).
