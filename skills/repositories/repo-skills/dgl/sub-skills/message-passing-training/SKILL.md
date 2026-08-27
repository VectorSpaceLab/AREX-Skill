---
name: message-passing-training
description: "Use DGL message passing, PyTorch GNN layers, full-graph training
  loops, heterograph modules, readout, and DGL sparse APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Message Passing Training

Use this sub-skill when a task asks you to implement or debug DGL message passing, full-graph GNN training, built-in DGL PyTorch layers, heterograph relation modules, readout/pooling, or `dgl.sparse` operations.

## Start Here

- For API and layer selection, read [references/api-reference.md](references/api-reference.md).
- For full-graph node, edge/link, graph, heterograph, and sparse workflows, read [references/workflows.md](references/workflows.md).
- For DGL-specific failure modes, read [references/troubleshooting.md](references/troubleshooting.md).
- To verify a local DGL/PyTorch install before editing a model, run `python scripts/training_smoke.py` from this sub-skill directory.
- To verify optional `dgl.sparse` availability, run `python scripts/sparse_api_smoke.py` from this sub-skill directory.

## Route Elsewhere

- CSV/custom dataset layout, feature fields, train/validation/test masks, and graph save/load setup belong in `../datasets-and-io/`.
- Stochastic neighbor sampling, `dgl.dataloading.DataLoader`, `NeighborSampler`, GraphBolt datapipes, and minibatch block training belong in `../dataloading-graphbolt/`.
- Generated training projects, YAML config generation, and DGL-Go commands belong in `../dglgo-cli/`.
- Distributed launches, DDP trainer setup, partitioning, and multi-process execution belong in `../distributed-tools/`.

## Safety Defaults

- Prefer CPU-safe synthetic graphs for smoke checks and examples; do not download datasets unless the user explicitly asks.
- Keep model code framework-specific: this sub-skill covers PyTorch DGL APIs.
- Prefer DGL built-ins (`dgl.function`, `dgl.nn.pytorch`, `dgl.sparse`) over reimplementing kernels unless a custom UDF or layer is required.
