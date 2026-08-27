---
name: dgl
description: "Route DGL graph learning tasks across graph APIs, datasets,
  message passing, GraphBolt, distributed tools, and DGL-Go workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DGL Repo Skill

Use this repo skill when a task names DGL, Deep Graph Library, DGLGraph, GraphBolt, DGL-Go, DGL sparse, DGL distributed training, or graph neural network workflows implemented with DGL.

## Quick Start

Install a public DGL package that matches the target backend and Python version, then verify imports before using deeper workflows:

```bash
python -m pip install dgl
python - <<'PY'
import dgl
print(dgl.__version__)
print(dgl.graph(([0, 1], [1, 2]), num_nodes=3))
PY
```

For PyTorch workflows that use GraphBolt, keep the installed `torch` version compatible with the DGL wheel's bundled GraphBolt library. If `import dgl` reports a missing `libgraphbolt_pytorch_<version>` file, read [references/troubleshooting.md](references/troubleshooting.md).

## Route By Task

- Use [graph-apis](sub-skills/graph-apis/SKILL.md) for `dgl.graph`, `dgl.heterograph`, canonical etypes, features, transforms, batching, subgraphs, `to_block`, and graph-level smoke checks.
- Use [datasets-and-io](sub-skills/datasets-and-io/SKILL.md) for `DGLDataset`, `CSVDataset`, `meta.yaml`, graph save/load, dataset caches, download/cache environment variables, and CSV/OnDiskDataset handoffs.
- Use [message-passing-training](sub-skills/message-passing-training/SKILL.md) for `update_all`, `dgl.function`, PyTorch GNN layers, full-graph training loops, heterograph modules, readout, and `dgl.sparse`.
- Use [dataloading-graphbolt](sub-skills/dataloading-graphbolt/SKILL.md) for stochastic minibatch sampling, `dgl.dataloading.DataLoader`, `NeighborSampler`, GraphBolt `ItemSet`/`ItemSampler`, feature fetching, OnDiskDataset, GPU sampling, and UVA decisions.
- Use [distributed-tools](sub-skills/distributed-tools/SKILL.md) for partition configs, `DistGraph`, `DistDataLoader`, `node_split`, `edge_split`, `ip_config.txt`, dry launch-command construction, and safe distributed preflight.
- Use [dglgo-cli](sub-skills/dglgo-cli/SKILL.md) for DGL-Go `configure`, `recipe`, `train`, `export`, `configure-apply`, `apply`, YAML config linting, and recipe/custom CSV workflows.

## Shared References And Scripts

- Read [references/install-and-build.md](references/install-and-build.md) before source builds, backend selection, DGL-Go installs, or native library troubleshooting.
- Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting import, backend, GraphBolt, sparse, dataset cache, and build failures.
- Read [references/repo-development.md](references/repo-development.md) when editing the DGL repository itself or selecting focused native tests.
- Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is stale for a checkout.
- Run `python scripts/check_dgl_environment.py` for a safe import/backend/native-library diagnostic.

## Routing Rules

- If the user asks for a DGL data folder or `meta.yaml`, route to `datasets-and-io` before any model or dataloader work.
- If the user asks for blocks, sampled minibatches, GraphBolt, or UVA, route to `dataloading-graphbolt`; then route model `forward()` details to `message-passing-training`.
- If the user asks for a cluster, partition JSON, `ip_config.txt`, or `DistGraph`, route to `distributed-tools` and do not run SSH/cluster launchers without explicit approval.
- If the user asks for a ready-to-run CLI experiment or YAML recipe, route to `dglgo-cli`; use `datasets-and-io` for custom CSV data validation and `message-passing-training` for exported script edits.
- If the request is only about constructing or debugging graph objects, stay in `graph-apis` and avoid training or dataset assumptions.

## Safety Defaults

- Prefer CPU-safe synthetic smoke checks unless the user explicitly requests CUDA, distributed execution, downloads, or long training.
- Treat source builds and distributed launches as environment-mutating or side-effectful; summarize prerequisites and ask before broad builds, SSH, multi-host processes, or data dispatch.
- Do not rely on original DGL checkout docs, examples, tests, or tools at runtime. Use this skill's bundled references and scripts.
