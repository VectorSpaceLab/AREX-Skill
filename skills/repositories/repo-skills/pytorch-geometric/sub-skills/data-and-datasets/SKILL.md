---
name: data-and-datasets
description: "Create, validate, split, transform, and package PyTorch Geometric
  Data, HeteroData, Batch, Dataset, and InMemoryDataset objects with safe local
  fixtures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Data and Datasets

Use this sub-skill when the task is about graph containers, hetero graph containers, batching graph objects, local dataset classes, transforms, dataset splitting, or synthetic fixtures in PyTorch Geometric 2.9.

## Start Here

- Read [data formats](references/data-formats.md) to construct and validate `Data`, `HeteroData`, and `Batch` objects, including expected tensor shapes and metadata.
- Read [datasets and transforms](references/datasets-and-transforms.md) to implement `Dataset` or `InMemoryDataset`, choose `transform` vs `pre_transform`, create local layouts, and split nodes or links.
- Read [troubleshooting](references/troubleshooting.md) when validation fails, masks are missing, transforms run in the wrong order, or processed dataset caches look stale.
- Run [validate_basic_graph.py](scripts/validate_basic_graph.py) for a safe synthetic smoke check of homogeneous and heterogeneous graph containers.

## Quick Commands

```bash
python scripts/validate_basic_graph.py --fixture homogeneous
python scripts/validate_basic_graph.py --fixture hetero
python scripts/validate_basic_graph.py --fixture invalid --expect-invalid
```

Each command prints a JSON summary and uses only tiny in-memory tensors plus installed `torch` and `torch_geometric` APIs. No downloads, GPUs, network access, credentials, or destructive writes are required.

## Route Boundaries

- For mini-batch loaders, neighbor sampling, and link sampling loaders, use `../loaders-and-sampling/SKILL.md`.
- For model layers, `MessagePassing`, convolutions, pooling, and training loops, use `../gnn-modeling/SKILL.md`.
- For advanced heterogeneous modeling, `HeteroConv`, `to_hetero`, and hetero-specific training recipes, use `../heterogeneous-graphs/SKILL.md`.
- For distributed graph stores, remote backends, partitioning, and hardware scaling, use `../scalable-distributed/SKILL.md`.

## Safe Defaults

- Build graph fixtures with `torch_geometric.data.Data(x=..., edge_index=..., y=...)` or `HeteroData()` and call `.validate(raise_on_error=True)` before passing them to loaders or models.
- Set `data.num_nodes` explicitly when node features are absent or isolated nodes matter.
- Use `torch.long` COO `edge_index` tensors shaped `[2, num_edges]` with zero-based node ids.
- Prefer `InMemoryDataset` only when all processed graphs fit in CPU memory; otherwise implement `Dataset` with one processed file per graph.
- Keep runtime examples local and synthetic unless the user explicitly requests a dataset download.
