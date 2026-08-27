---
name: deep-gcns-torch
description: "Use the DeepGCNs PyTorch operating guide for graph convolution
  layers, dynamic and dilated KNN blocks, point-cloud classification or
  segmentation, PPI, OGB/DeeperGCN, and reversible memory-efficient GNN
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DeepGCNs Torch

Use this router when a task names DeepGCNs, DeeperGCN, `deep_gcns_torch`,
`gcn_lib`, GENConv, dynamic KNN graph blocks, ModelNet40/S3DIS/PartNet point
clouds, PPI, OGB graph benchmarks, RevGNN, or RevGAT.

## Operating boundary

This is a self-contained guide distilled from a historical PyTorch repository.
It does not download datasets, fetch external checkpoints, launch long
training, start distributed jobs, or open visualization windows. First stage
caller-owned data and checkpoints, then follow the relevant workflow. Read
[repository provenance](references/repo-provenance.md) when deciding whether a
source checkout has drifted, and read [troubleshooting](references/troubleshooting.md)
when installation or version behavior is unclear.

## Minimal environment check

The source repository has no `pyproject.toml`, `setup.py`, or console entry
point. Use a coherent PyTorch/PyG stack rather than the obsolete repository
installer. At minimum, install PyTorch, PyTorch Geometric, matching
`torch-scatter` and `torch-cluster` wheels, and add `ogb`, h5py, scikit-learn,
or tensorboard only for the selected workflows. Run the bundled checks before
using a real model:

```bash
python scripts/check_env.py
python scripts/checkpoint_roundtrip.py
```

For a CUDA task, use `python scripts/check_env.py --cuda`; CUDA availability is
not proof of dataset-scale memory or benchmark reproduction. Match every
compiled PyG extension to the installed PyTorch and CPU/CUDA build. Do not run
the old one-shot installer: it mutates environments and pins obsolete CUDA
10.2-era packages.

## Route by the user's task

- **Layer or architecture API** — sparse/dense `GraphConv`, `DynConv`,
  `GENConv`, aggregators, KNN/dilation, blocks, or reversible primitives:
  read [graph-layers](sub-skills/graph-layers/SKILL.md).
- **Point clouds** — ModelNet40, S3DIS dense/sparse, PartNet, segmentation
  layouts, point-cloud checkpoints, or optional OBJ visualization: read
  [point-cloud-workflows](sub-skills/point-cloud-workflows/SKILL.md).
- **OGB/DeeperGCN** — `ogbn-*`, `ogbg-*`, `ogbl-collab`, graph pooling,
  partitions, atom/bond features, RevGNN, or DGL RevGAT: read
  [ogb-workflows](sub-skills/ogb-workflows/SKILL.md).
- **PPI** — PPI multilabel node classification, F1 metrics, or PPI checkpoint
  alignment: read [ppi-workflows](sub-skills/ppi-workflows/SKILL.md).

If a request crosses routes, start here, state the data layout and backend,
then read each owning sub-skill. Generic layer semantics belong to
`graph-layers`; task-specific data and metrics remain with their workflow.

## Fast safety gates

1. Identify CPU versus CUDA, PyG extension compatibility, data root, checkpoint
   availability, and expected metric before running anything.
2. Use the owning sub-skill's bundled synthetic helper first. These helpers are
   offline, deterministic, and do not import the original checkout.
3. Never treat a CPU shape smoke as proof of GPU memory, a historical benchmark
   number, or a dataset split result.
4. Keep the source task's working-directory import quirks and external download
   requirements explicit; do not turn them into hidden runtime dependencies.
5. For a changed source revision or package API, compare provenance and use a
   refresh workflow rather than silently applying stale claims.

## Shared references and checks

- [API overview](references/api-overview.md) summarizes shared tensor, module,
  and utility contracts before choosing a focused route.
- [Troubleshooting](references/troubleshooting.md) covers cross-cutting install,
  import, data, checkpoint, backend, and version failures.
- [Environment check](scripts/check_env.py) is a safe dependency/backend probe.
- [Checkpoint roundtrip](scripts/checkpoint_roundtrip.py) verifies basic PyTorch
  checkpoint serialization without touching caller data.
