---
name: datasets-and-io
description: "Build and validate DGL datasets, CSV dataset folders, graph
  serialization caches, and GraphBolt OnDiskDataset handoffs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DGL Datasets and IO

Use this sub-skill when the task is about getting graph data into or out of DGL before model code runs.

## Use When

- Creating a `dgl.data.DGLDataset` subclass with `process()`, `save()`, `load()`, and `has_cache()`.
- Loading a folder of CSV node, edge, and graph files with `dgl.data.CSVDataset`.
- Fixing `meta.yaml`, feature parsing, split masks, graph-level labels, or cache reload behavior.
- Saving/loading `DGLGraph` objects with `dgl.save_graphs()` / `dgl.load_graphs()` and dataset metadata with `save_info()` / `load_info()`.
- Preparing a data-format handoff for GraphBolt `OnDiskDataset` or DGL-Go CSV ingestion.

## Start Here

- Read `references/workflows.md` for custom dataset lifecycle, caching, serialization, CSV loading, and built-in dataset caveats.
- Read `references/data-formats.md` for `meta.yaml` schemas, CSV required columns, heterograph conventions, and `OnDiskDataset` metadata routing.
- Read `references/troubleshooting.md` when `CSVDataset`, cache reloads, downloads, feature dtypes, or split masks fail.
- Run `python scripts/csv_dataset_linter.py DATASET_DIR` before calling `dgl.data.CSVDataset(DATASET_DIR)` on a custom CSV folder.

## Route Elsewhere

- Route raw graph construction details to `../graph-apis/` after validating files and before writing a `DGLGraph` manually.
- Route GraphBolt datapipes, `ItemSet`, `ItemSampler`, `DataLoader`, sampled minibatches, and feature fetch execution to `../dataloading-graphbolt/`.
- Route partition configs and distributed training output formats to `../distributed-tools/`.
- Route model layers, message passing, losses, and training loops to `../message-passing-training/`.
- Route DGL-Go CLI training and CSV project commands to `../dglgo-cli/`; this sub-skill only covers making the CSV folder valid enough to hand off.

## Core APIs

- `dgl.data.DGLDataset(name, url=None, raw_dir=None, save_dir=None, hash_key=(), force_reload=False, verbose=False, transform=None)`.
- `dgl.data.CSVDataset(data_path, force_reload=False, verbose=True, ndata_parser=None, edata_parser=None, gdata_parser=None, transform=None)`.
- `dgl.save_graphs(filename, g_list, labels=None, formats=None)` and `dgl.load_graphs(filename, idx_list=None)`.
- `dgl.data.utils.save_info(path, info)` and `dgl.data.utils.load_info(path)`.

## Safety Notes

- Keep generated dataset code independent from local checkout paths; accept `raw_dir`, `save_dir`, or a dataset folder from the caller.
- Prefer tiny local fixtures for validation; avoid downloadable built-in datasets unless the user explicitly allows network access.
- Treat `CSVDataset` `meta.yaml`, GraphBolt `metadata.yaml`, and distributed partition JSON/configs as separate formats with different owners.
