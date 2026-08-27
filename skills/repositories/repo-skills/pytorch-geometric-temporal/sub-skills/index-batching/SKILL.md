---
name: index-batching
description: "Guides memory-efficient PyTorch Geometric Temporal index-batching,
  GPU preprocessing flags, loader return tuples, and optional Dask-DDP
  training."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Index Batching

Use this sub-skill when the task asks about PyTorch Geometric Temporal index-batching, memory-efficient temporal mini-batches, `get_index_dataset`, `IndexDataset`, `allGPU`, `dask_batching`, `world_size`/`ddp_rank`, Dask-DDP, or errors caused by missing `index=True`.

## Route here when

- The user wants a `DataLoader` that yields sequence windows instead of a full temporal signal iterator.
- The user is adapting Chickenpox, WindmillLarge, METR-LA, PeMS-Bay, PeMS-All-LA, or full PeMS to index batching.
- The question is about 5-tuple versus 7-tuple `get_index_dataset` returns, normalization statistics, or batch tensor shape.
- The user needs to decide between CPU preprocessing (`allGPU=-1`), GPU index preprocessing (`allGPU=<device_id>`), or optional Dask-DDP distributed training.
- The error mentions `get_index_dataset requires 'index=True'`, missing `dask`/`pandas`/`tables`, CUDA not available, or `DistributedSampler` rank/replica problems.

## Do not handle here

- Ordinary temporal signal iterators such as `StaticGraphTemporalSignal`, dynamic graph signals, hetero signals, slicing, or `temporal_signal_split`; route those to the temporal-signals sub-skill.
- Ordinary `get_dataset()` loader workflows, download/cache planning, and non-index dataset catalogs; route those to the dataset-loaders sub-skill.
- Model architecture selection and recurrent/attention layer internals beyond the batched output shape needed to connect an index batch to a model loop; route those to the model sub-skills.
- Real multi-node cluster execution or scheduler launch scripts as a required verification step; this sub-skill only provides reference patterns and prerequisites.

## First facts to apply

- `IndexDataset` is not exported from `torch_geometric_temporal.signal`; import it explicitly with:

  ```python
  from torch_geometric_temporal.signal.index_dataset import IndexDataset
  ```

- Loader index batching is opt-in. Instantiate supported loaders with `index=True` before calling `get_index_dataset(...)`.
- `IndexDataset(indices, data, horizon, lazy=False, gpu=False)` stores start indices and returns `(X_window, y_window)`, where both windows have length `horizon`/`lags` along time.
- Batches yielded by built-in index dataloaders have sequence-to-sequence layout close to `[batch, lags, num_nodes, num_features]` before any model-specific permutation.
- Chickenpox returns a 5-tuple; WindmillLarge, METR-LA, PeMS-Bay, PeMS-All-LA, and PeMS return a 7-tuple with normalization statistics.

## What to read or run

1. Read [workflows.md](references/workflows.md) for CPU/GPU index-batching setup, supported loader return formats, tuple unpacking, normalization statistics, ratio/lags behavior, and model-loop shape notes.
2. Read [distributed-ddp.md](references/distributed-ddp.md) only when the user asks for Dask-DDP, multi-GPU, multi-node, `world_size`, `ddp_rank`, `DistributedSampler`, or scheduler-file behavior.
3. Read [troubleshooting.md](references/troubleshooting.md) when an index-batching call fails or when optional dependencies, CUDA, Dask, ranks, tuple lengths, downloads, or empty splits are involved.
4. Run or adapt [index_batching_smoke.py](scripts/index_batching_smoke.py) for a deterministic no-network synthetic `IndexDataset` sanity check.

## Minimal safe workflow

```python
from torch_geometric_temporal.dataset import PemsBayDatasetLoader

loader = PemsBayDatasetLoader(index=True)
train_loader, val_loader, test_loader, edge_index, edge_weight, mean, std = (
    loader.get_index_dataset(lags=12, batch_size=64, shuffle=True, allGPU=-1)
)

for X_batch, y_batch in train_loader:
    # CPU preprocessing path: move tensors to the model device inside the loop.
    # X_batch/y_batch are sequence windows, typically [B, T, N, F].
    pass
```

For Chickenpox, unpack five values instead:

```python
train_loader, val_loader, test_loader, edge_index, edge_weight = (
    ChickenpoxDatasetLoader(index=True).get_index_dataset(lags=4, batch_size=4)
)
```

If the task requires exact loader-specific shapes, DDP behavior, or de-normalization, open the references instead of expanding this router.
