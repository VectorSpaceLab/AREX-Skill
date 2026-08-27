---
name: pytorch-geometric-temporal
description: "Routes PyTorch Geometric Temporal tasks for temporal graph
  signals, built-in datasets, recurrent and attention graph neural layers,
  index-batching, and optional Dask-DDP workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# PyTorch Geometric Temporal

Use this repo skill when a task involves the `torch-geometric-temporal` / `torch_geometric_temporal` package: temporal graph signal iterators, built-in spatiotemporal datasets, temporal graph neural network layers, memory-efficient index-batching, or optional distributed Dask-DDP training patterns.

This skill is self-contained. Do not require the original repository checkout for runtime use; use the bundled references and scripts below.

## Start here

1. **Check installation and versions.** Read [install and compatibility](references/install-and-compatibility.md), then run [check_environment.py](scripts/check_environment.py) if you need an import/backend smoke check.
2. **Choose the route.** Use the sub-skill map below. Open the nearest sub-skill before writing task-specific code.
3. **Validate with synthetic smoke first.** Prefer the bundled no-download scripts before adapting network-backed dataset examples or long training loops.
4. **Treat real dataset loaders as side-effectful.** Many loader constructors download remote files; read the dataset-loader route before constructing them.

## Sub-skill map

| User task | Read |
| --- | --- |
| Build a temporal signal from arrays, slice snapshots, use `temporal_signal_split`, add optional attributes, or debug `Data`/`Batch`/`HeteroData` outputs | [temporal-signals](sub-skills/temporal-signals/SKILL.md) |
| Choose a built-in dataset loader, understand `get_dataset` signatures, plan `raw_data_dir`, or avoid constructor-time downloads | [dataset-loaders](sub-skills/dataset-loaders/SKILL.md) |
| Use recurrent temporal graph layers such as `DCRNN`, `GConvGRU`, `TGCN`, `A3TGCN`, `AGCRN`, `MPNNLSTM`, or manage hidden states | [recurrent-layers](sub-skills/recurrent-layers/SKILL.md) |
| Use attention or heterogeneous layers such as `STConv`, `ASTGCN`, `MSTGCN`, `GMAN`, `MTGNN`, `AAGCN`, `DNNTSP`, or `HeteroGCLSTM` | [attention-and-hetero-layers](sub-skills/attention-and-hetero-layers/SKILL.md) |
| Use `IndexDataset`, `get_index_dataset`, `index=True`, `allGPU`, 5-tuple/7-tuple loader returns, or optional Dask-DDP | [index-batching](sub-skills/index-batching/SKILL.md) |

## Package facts to remember

- Public distribution name: `torch-geometric-temporal` / installed metadata `torch_geometric_temporal`.
- Import package: `torch_geometric_temporal`.
- Base install expects compatible PyTorch and PyTorch Geometric first or through dependency resolution.
- Public extras: `torch-geometric-temporal[index]` for index-batching data dependencies; `torch-geometric-temporal[ddp]` for Dask-DDP-oriented dependencies.
- The inspected source metadata reports distribution version `0.56.2`, while `torch_geometric_temporal.__version__` reports `0.54.0`; use distribution metadata for package install/version comparisons and note the in-package constant mismatch when debugging.
- The package exposes no main CLI. Workflows are Python API-first.

## Shared references and scripts

- [Repository provenance](references/repo-provenance.md): source commit, package versions, evidence paths, and refresh cues.
- [Router metadata](references/repo-routing-metadata.json): structured scenario placement for managed repo-skill import tooling.
- [Install and compatibility](references/install-and-compatibility.md): install commands, optional extras, PyTorch/PyG/CUDA/DDP notes, and import checks.
- [Model and data map](references/model-and-data-map.md): compact catalog of signal classes, loaders, model families, sub-skill owners, and validation paths.
- [Cross-cutting troubleshooting](references/troubleshooting.md): install/import, optional dependencies, backend, downloads, and version mismatch recovery.
- [check_environment.py](scripts/check_environment.py): safe import/version/backend smoke check with JSON output.

## Safe validation ladder

Run checks in this order when diagnosing user code:

1. `python scripts/check_environment.py --json` from this skill root or with an absolute script path.
2. The relevant sub-skill smoke script, for example `sub-skills/temporal-signals/scripts/signal_iterator_smoke.py --mode all --json`.
3. A tiny user-shaped synthetic case using the selected sub-skill references.
4. Real dataset loader construction or original benchmark-scale behavior only after the user accepts network/cache/runtime costs.

## Avoid using this skill when

- The task is only generic PyTorch Geometric static graph modeling with no temporal signal, dataset loader, or PGT class involved.
- The user asks for general time-series forecasting without graph structure.
- The user is editing the package source as a maintainer; use a repository-maintenance workflow rather than this operating skill.
