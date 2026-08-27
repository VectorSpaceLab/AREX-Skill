# Index-Batching Workflows

## Purpose

Read this reference when adapting PyTorch Geometric Temporal index-batching to a training loop, debugging `get_index_dataset` unpacking, deciding CPU versus GPU preprocessing, or using the low-level `IndexDataset` directly. It is self-contained runtime guidance; source examples and tests were distilled into the patterns below.

## Core behavior

`IndexDataset` is the low-level dataset behind index batching. Import it from the implementation module, not from the `signal` package namespace:

```python
from torch_geometric_temporal.signal.index_dataset import IndexDataset
```

Constructor and sample contract:

```python
IndexDataset(indices, data, horizon, lazy=False, gpu=False)
```

- `indices`: one-dimensional array of start positions.
- `data`: temporal tensor/array laid out as time first, commonly `[time, num_nodes, num_features]`.
- `horizon`: the window length. Built-in loaders pass the `lags` argument here.
- `lazy=True`: expects `data[start:stop]` slices to support `.compute()`; use it only with a Dask-like array or after verifying the built-in loader path.
- `gpu=True`: tells `IndexDataset` that `data` is already a torch tensor on GPU, so it returns GPU slices directly.

For an item at start index `i`, the dataset returns:

```text
X = data[i : i + horizon, ...]
y = data[i + horizon : i + 2 * horizon, ...]
```

A `DataLoader` collates those samples into sequence-to-sequence batches. For the common `[time, nodes, features]` data layout, the batch tensors are shaped like `[batch, lags, nodes, features]`.

Run the bundled no-network smoke test when you need to prove this contract in a new environment:

```bash
python sub-skills/index-batching/scripts/index_batching_smoke.py --help
python sub-skills/index-batching/scripts/index_batching_smoke.py --lags 3 --batch-size 2
python sub-skills/index-batching/scripts/index_batching_smoke.py --lazy --lags 3 --batch-size 2
```

## CPU index-batching setup

1. Install with index-batching dependencies available. In public package terms, this is the `index` extra. The extra supplies the optional data dependencies used by index loaders, including Dask/Pandas/PyTables-related packages.
2. Instantiate a supported loader with `index=True`.
3. Call `get_index_dataset(...)` and unpack according to the loader family.
4. Keep `allGPU=-1` for CPU preprocessing. The dataloader yields CPU tensors; move `X_batch`, `y_batch`, `edge_index`, `edge_weight`, and any stats to the model device inside the loop.
5. Keep model-specific tensor permutations near the model call, not in the loader wrapper.

Typical CPU pattern:

```python
loader = PemsBayDatasetLoader(index=True)
train_loader, val_loader, test_loader, edge_index, edge_weight, mean, std = (
    loader.get_index_dataset(
        lags=12,
        batch_size=64,
        shuffle=True,
        allGPU=-1,
        ratio=(0.7, 0.1, 0.2),
    )
)

for X_batch, y_batch in train_loader:
    X_batch = X_batch.to(device).float()
    y_batch = y_batch.to(device).float()
    edge_index = edge_index.to(device)
    edge_weight = edge_weight.to(device)
```

The supported loader methods compute start indices with `num_samples - (2 * lags - 1)`. If `lags` is too large for the available time axis, splits become empty or invalid.

## Return tuple formats

Unpack by loader, not by guessing from the dataset name string at runtime.

| Loader family | Constructor requirement | Main `get_index_dataset` parameters | Return format |
| --- | --- | --- | --- |
| `ChickenpoxDatasetLoader` | `index=True` | `lags=4`, `batch_size=4`, `shuffle=False`, `allGPU=-1`, `ratio=(0.7,0.1,0.2)`, `dask_batching=False` | 5-tuple: `(train_loader, val_loader, test_loader, edge_index, edge_weight)` |
| `WindmillOutputLargeDatasetLoader` | `index=True` | `lags=8`, `batch_size=64`, `shuffle=False`, `allGPU=-1`, `ratio=(0.7,0.1,0.2)`, `dask_batching=False` | 7-tuple: `(train_loader, val_loader, test_loader, edge_index, edge_weight, mean, std)` |
| `METRLADatasetLoader` | `index=True` | `lags=12`, `batch_size=64`, `shuffle=False`, `allGPU=-1`, `ratio=(0.7,0.1,0.2)`, `world_size=-1`, `ddp_rank=-1`, `dask_batching=False` | 7-tuple with stats |
| `PemsBayDatasetLoader` | `index=True` | same as METR-LA | 7-tuple with stats |
| `PemsAllLADatasetLoader` | `index=True`; index path only | same as METR-LA | 7-tuple with stats |
| `PemsDatasetLoader` | `index=True`; index path only | same as METR-LA | 7-tuple with stats |

Robust helper for user code that may receive either format:

```python
result = loader.get_index_dataset(batch_size=batch_size, lags=lags)
if len(result) == 5:
    train_loader, val_loader, test_loader, edge_index, edge_weight = result
    mean = std = None
elif len(result) == 7:
    train_loader, val_loader, test_loader, edge_index, edge_weight, mean, std = result
else:
    raise RuntimeError(f"unexpected get_index_dataset return length: {len(result)}")
```

## Parameter notes

- `lags`: input window length and target window length for `IndexDataset`; built-in index loaders are sequence-to-sequence with equal input/output horizon.
- `batch_size`: passed to `torch.utils.data.DataLoader` for each split.
- `shuffle`: used directly when no DDP rank is supplied. When `ddp_rank != -1`, the loader builds a `DistributedSampler(..., shuffle=shuffle)` and passes the sampler to the dataloader.
- `ratio`: three values for train, validation, and test fractions. The implementation rounds train and test counts and assigns the remaining samples to validation.
- `allGPU=-1`: CPU preprocessing. `data` remains NumPy-like, and batch tensors should be moved to the model device in the loop.
- `allGPU=<device_id>`: GPU preprocessing. Loader preprocessing creates a torch tensor on `cuda:<device_id>` and `IndexDataset(gpu=True)` returns slices from that device. Use only when CUDA is available and the PyTorch/PyG stack matches the GPU runtime.
- `dask_batching`: forwarded as `lazy=True` to `IndexDataset`. Low-level lazy mode requires a Dask-like `data` object. If a built-in loader path still passes NumPy arrays, `dask_batching=True` can fail at sample time; prove the path before relying on it.
- `world_size` and `ddp_rank`: only meaningful for loaders whose signature includes them. Supply both from the initialized distributed process group; leave both at `-1` outside DDP.

## Normalization statistics

The 7-tuple loaders return `mean` and `std` for reversing the standardization applied during preprocessing. Use them for losses/metrics that should be reported in original units:

```python
prediction_original = (prediction_standardized * std) + mean
target_original = (y_batch * std) + mean
```

Shape and device rules:

- On the CPU path, returned stats are torch tensors on CPU. Move them to the model device before combining with model outputs.
- On the GPU preprocessing path, stats may already be on the selected CUDA device. Still check `prediction.device == std.device` before arithmetic.
- METR-LA and PeMS-Bay stats are feature-channel statistics for the standardized traffic tensor.
- PeMS-All-LA and PeMS add a time-of-day feature beside speed; examples often evaluate speed with `mean[0]`/`std[0]` or `y_batch[..., 0]` when the metric should ignore the auxiliary time feature.
- WindmillLarge stats are computed from the windmill output series. Check broadcasting explicitly and `unsqueeze` stats when a model output keeps a trailing singleton feature dimension.
- Chickenpox returns no stats. Its index batches still contain sequence targets; when comparing to ordinary one-step temporal-signal targets, select the appropriate target step instead of assuming the whole target window is one snapshot.

## Model-loop shape notes

Index batching owns the dataloader windows; model-specific sub-skills own architecture details. These are the minimum bridge rules observed in the bundled examples:

- Batched DCRNN-style loops use `X_batch` directly in sequence-first form, typically `[B, T, N, F]`, and expect model output compatible with `[B, T, N, out_channels]` before loss computation.
- A3TGCN2 examples permute `X_batch` to `[B, N, F, T]` and often select the first target feature with `y_batch[..., 0].permute(0, 2, 1)` to obtain `[B, N, T]`.
- TGCN2 batch examples also permute to `[B, N, F, T]`, then iterate over the time dimension internally and concatenate predictions back into a sequence.
- Always align `edge_index` and `edge_weight` with the model device. Some attention-style examples use only `edge_index`; recurrent diffusion layers usually also consume `edge_weight`.
- If `allGPU=False`, move batches inside each loop. If `allGPU=True`, do not call `.to(device)` on each batch unless you intentionally copy to a different GPU.

## Source-script adaptation map

| Source pattern distilled | Runtime replacement here | Decision |
| --- | --- | --- |
| Single-GPU `*_main.py` index-batching loops | CPU/GPU setup and shape notes in this reference plus the synthetic smoke script | Adapted without network download or training side effects |
| DCRNN/A3TGCN/TGCN loop comments | Shape bridge notes above | Adapted as prose only; detailed architectures belong to model sub-skills |
| Masked MAE helper from example utilities | De-normalization and masked-loss notes in this reference | Selected formula only; original utility files also contain dataset/metrics side effects |
| Dask-DDP PeMS examples | See [distributed-ddp.md](distributed-ddp.md) | Reference-only because they require Dask, distributed workers, and real datasets |
| HPC scheduler submission script | Not bundled | Excluded because it is scheduler- and supercomputer-specific |
