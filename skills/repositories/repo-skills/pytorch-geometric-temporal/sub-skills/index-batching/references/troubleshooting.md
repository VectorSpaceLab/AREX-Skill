# Index-Batching Troubleshooting

## Purpose

Use this guide when `get_index_dataset`, `IndexDataset`, GPU preprocessing, Dask lazy mode, or DDP index batching fails. Prefer the bundled smoke script for deterministic no-network checks before involving real web datasets or clusters.

```bash
python sub-skills/index-batching/scripts/index_batching_smoke.py --lags 3 --batch-size 2
```

## Symptom-to-fix table

| Symptom or error fragment | Likely cause | Fix |
| --- | --- | --- |
| `ValueError: get_index_dataset requires 'index=True' in the constructor.` | The loader was created without `index=True`. | Recreate the loader as `LoaderClass(index=True, ...)`, then call `get_index_dataset(...)`. |
| `AttributeError` for `IndexDataset` or `pd` on PeMS/PeMS-All-LA loader | The index-only loader was created without `index=True`; those loaders do not provide an ordinary `get_dataset` path. | Use `PemsDatasetLoader(index=True)` or `PemsAllLADatasetLoader(index=True)`. |
| `No module named 'dask'`, `No module named 'pandas'`, HDF/PyTables import errors | Optional index/DDP dependencies are missing. | Install with the public `index` extra for basic index batching, or the `ddp` extra for Dask-DDP. PeMS HDF readers also need Pandas plus PyTables support. |
| `'numpy.ndarray' object has no attribute 'compute'` when `dask_batching=True` | `IndexDataset(lazy=True)` expects Dask-like slices, but the data object is NumPy. | Set `dask_batching=False`, or construct a low-level `IndexDataset` with a Dask array and verify with the smoke script's `--lazy` mode. |
| `Torch not compiled with CUDA enabled`, `CUDA error`, or invalid `cuda:<id>` | `allGPU` requested GPU preprocessing on a CPU-only or mismatched PyTorch/PyG stack. | Use `allGPU=-1`/`--gpu False`, or install a CUDA-compatible PyTorch and PyG stack and verify `torch.cuda.is_available()` before calling the loader. |
| `DistributedSampler` invalid rank/replica errors | A DDP rank was supplied without a valid world size, or rank is outside `[0, world_size)`. | In DDP, pass `world_size=dist.get_world_size()` and `ddp_rank=dist.get_rank()` together. Outside DDP, leave both at `-1`. |
| `sampler` has no `set_epoch` | Code calls `train_loader.sampler.set_epoch(...)` on a non-DDP sampler. | Call `set_epoch` only when `ddp_rank != -1` and the loader created a `DistributedSampler`. |
| Not enough or too many values to unpack | Chickenpox returns 5 values; other supported index loaders return 7 values with stats. | Use loader-specific unpacking or the robust `len(result)` pattern in [workflows.md](workflows.md). |
| Empty train/validation/test loader | Time series too short for `2 * lags` windows, or split ratios round a small sample count to zero. | Reduce `lags`, provide more timesteps, or adjust `ratio`. Check that `num_timesteps - (2 * lags - 1) > 0`. |
| Loss shape mismatch after switching models | Model expects a different tensor order than `[B, T, N, F]`. | For BatchedDCRNN-style loops use sequence-first windows; for A3TGCN2/TGCN2-style loops permute to `[B, N, F, T]` near the model call. Consult the model sub-skill for architecture-specific shapes. |
| De-normalized loss broadcasts incorrectly | `mean`/`std` shape does not align with model output shape. | Move stats to the same device and add singleton dimensions with `view`/`unsqueeze` until broadcasting is explicit. For PeMS speed-only metrics, select the speed feature consistently. |
| Each DDP worker downloads data or fails on missing files | Dataset files are not pre-staged on shared storage before worker dispatch. | Prepare `raw_data_dir` and files once before launching workers. Avoid network loader tests unless downloads are explicitly allowed. |

## `index=True` gate

Always set `index=True` in the constructor for supported index batching:

```python
loader = PemsBayDatasetLoader(index=True)
train_loader, val_loader, test_loader, edge_index, edge_weight, mean, std = (
    loader.get_index_dataset(batch_size=64, lags=12)
)
```

For loaders that accept a data directory, keep `raw_data_dir` explicit when working with pre-staged files. Many real loaders may download or extract remote data during construction if files are missing.

## Optional dependency checks

Index batching imports the low-level `IndexDataset` implementation, which depends on Dask being importable. Traffic loaders for PeMS-style HDF data also depend on Pandas and PyTables. Dask-DDP adds `dask.distributed` and `dask_pytorch_ddp`.

Minimal checks:

```python
from torch_geometric_temporal.signal.index_dataset import IndexDataset
import dask
import pandas
import tables
```

If the task does not need DDP, do not install or debug Dask-DDP packages just to use CPU index batches.

## GPU preprocessing checks

`allGPU` is a device id, not a boolean:

- CPU path: `allGPU=-1`.
- First CUDA device: `allGPU=0`.

Before using `allGPU=0`, check:

```python
import torch
assert torch.cuda.is_available()
```

If CUDA is unavailable, keep `allGPU=-1`, move each CPU batch to the selected model device in the loop, and state that GPU index preprocessing remains unverified.

## DDP/rank checks

Use DDP arguments only after distributed initialization:

```python
worker_rank = dist.get_rank()
world_size = dist.get_world_size()
train_loader, val_loader, test_loader, edge_index, edge_weight, mean, std = (
    loader.get_index_dataset(
        batch_size=batch_size,
        world_size=world_size,
        ddp_rank=worker_rank,
    )
)
```

If a user asks for DDP on CPU/no cluster, offer a CPU index-batching dry run and list the missing distributed prerequisites instead of pretending the DDP path was exercised.

## Web dataset downloads

The real Chickenpox, WindmillLarge, METR-LA, PeMS-Bay, PeMS-All-LA, and PeMS loader paths may fetch or extract remote files when their expected local files are absent. For offline debugging or verification, do not instantiate those loaders. Use the synthetic smoke script first:

```bash
python sub-skills/index-batching/scripts/index_batching_smoke.py --timesteps 16 --nodes 4 --features 2 --lags 3
```

Then use real loaders only after the user confirms network/cache behavior or provides pre-staged files.
