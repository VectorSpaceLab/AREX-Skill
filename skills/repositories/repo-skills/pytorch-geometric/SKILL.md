---
name: pytorch-geometric
description: "Use PyTorch Geometric to build graph data, loaders, GNN models,
  heterogeneous workflows, explainers, scalable/distributed jobs, and GraphGym
  experiments."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# PyTorch Geometric

Use this repo skill when a task involves PyTorch Geometric (PyG), the `torch_geometric` Python package, graph neural networks, graph data containers, mini-batch/neighbor loaders, heterogeneous graphs, explainability, distributed graph learning, or GraphGym experiment configs.

## First Checks

- Read [repo provenance](references/repo-provenance.md) before deciding whether this skill matches a local PyG checkout or should be refreshed.
- Read [install and optional dependencies](references/install-and-optional-dependencies.md) when setting up PyG, choosing CPU/GPU wheels, or deciding which extras/extensions are needed.
- Read [cross-cutting troubleshooting](references/troubleshooting.md) for import failures, missing `torch`, optional extension issues, dataset downloads, CUDA/backend mismatches, or stale generated skill concerns.
- Run [check_pyg_environment.py](scripts/check_pyg_environment.py) for a safe import/backend diagnostic that does not download data, allocate GPUs by default, or write files.

## Minimal Install Pattern

PyG imports `torch`, so install a compatible PyTorch build first, then install PyG:

```bash
python -m pip install torch
python -m pip install torch-geometric
python - <<'PY'
import torch
import torch_geometric
print(torch.__version__)
print(torch_geometric.__version__)
PY
```

For CUDA, ROCm, Apple Silicon, or extension-heavy sampling workflows, choose the PyTorch wheel and optional PyG extension wheels that match the target backend. Do not mix CPU PyTorch with CUDA-only extension wheels.

## Route by Task

- Use [data-and-datasets](sub-skills/data-and-datasets/SKILL.md) for `Data`, `HeteroData`, `Batch`, custom `Dataset`/`InMemoryDataset`, transforms, dataset splitting, and local graph validation.
- Use [loaders-and-sampling](sub-skills/loaders-and-sampling/SKILL.md) for `DataLoader`, `NeighborLoader`, `LinkNeighborLoader`, mini-batching, sampler parameters, temporal/link sampling, and optional sampler backend errors.
- Use [gnn-modeling](sub-skills/gnn-modeling/SKILL.md) for `MessagePassing`, common convolution layers, pooling, metrics, training loops, `torch.compile`, TorchScript/JIT, and tiny model smoke tests.
- Use [heterogeneous-graphs](sub-skills/heterogeneous-graphs/SKILL.md) for typed graph metadata, `HeteroData`, `HeteroConv`, `to_hetero`, hetero loaders, bipartite relations, and hetero link prediction.
- Use [explainability](sub-skills/explainability/SKILL.md) for `Explainer`, `GNNExplainer`, masks, thresholds, explanation metrics, and model-config recovery.
- Use [scalable-distributed](sub-skills/scalable-distributed/SKILL.md) for large-graph scaling, remote `FeatureStore`/`GraphStore`, distributed PyG, multi-GPU/multi-node planning, CPU affinity, profiling, and backend diagnostics.
- Use [graphgym-experiments](sub-skills/graphgym-experiments/SKILL.md) for GraphGym YAML configs, custom registry hooks, run-single/run-batch concepts, and safe config validation.

## Shared Decision Rules

- Prefer tiny synthetic `Data` or `HeteroData` fixtures for smoke checks before running dataset-download or benchmark examples.
- Validate graph tensors early: `edge_index` is `torch.long` with shape `[2, num_edges]`, node features align with `num_nodes`, masks index the right supervision target, and hetero edge types are `(src, relation, dst)` triplets.
- Treat optional packages as workflow-specific: `pyg-lib`, `torch-sparse`, `torch-scatter`, and related extension wheels are often needed for fast sampling or sparse operations, while GraphGym and RAG workflows need their own extras.
- Keep training, explainability, GraphGym, distributed, and multi-GPU runs small unless the user explicitly accepts downloads, long runtime, result writes, credentials, or hardware use.
- When a task spans routes, start with the data/schema owner, then move to loaders/modeling/explainability/scaling as needed.

## Safe Shared Command

```bash
python scripts/check_pyg_environment.py --json
```

Use `--require-torch`, `--require-pyg`, or `--require-neighbor-backend` when the user needs a hard pass/fail diagnostic for a specific workflow.
