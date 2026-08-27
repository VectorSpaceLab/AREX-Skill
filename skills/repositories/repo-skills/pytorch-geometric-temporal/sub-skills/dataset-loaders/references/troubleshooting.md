# Dataset Loader Troubleshooting

## Purpose

Use this reference when loader planning, construction, or first-snapshot validation fails. It focuses on dataset-loader failures only; route iterator slicing/splitting issues to temporal-signals and `get_index_dataset` batch mechanics to index-batching.

## Failure matrix

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Importing `torch_geometric_temporal.dataset` fails with `ModuleNotFoundError: requests` or `ModuleNotFoundError: tqdm` | Some dataset modules import `requests` and `tqdm` at module import time, even before constructing a loader. | Install the missing packages or an extra set that includes them, then rerun `python scripts/list_dataset_loaders.py --format text`. If installation is not allowed, use already imported signal classes or custom arrays instead of built-in dataset loaders. |
| `ModuleNotFoundError: pandas`, `ModuleNotFoundError: tables`, or an HDF5 read error while using PeMS/PeMS-All-LA | `PemsDatasetLoader` and `PemsAllLADatasetLoader` read `.h5` speed files through pandas/PyTables and are index-only. | Install pandas and PyTables-compatible HDF support. If the task does not require index batching, choose METR-LA or PeMS-Bay ordinary `get_dataset`, or construct a custom signal from arrays. |
| Constructor prints `Downloading to ...` unexpectedly | Loader downloads data in `__init__`, not in `get_dataset`, and required files were missing. | Stop if network/cache writes were not approved. Read `data-sources.md`, choose a loader with pre-stage support, or use a custom temporal signal. For traffic loaders, pre-stage every expected filename before constructing. |
| Download hangs, returns HTML, or creates a tiny/corrupt `.zip`, `.h5`, `.pkl`, `.npy`, `.pt`, or `.json` | Remote host is unavailable, blocked, rate-limited, or requires redirected Box/GitHub access. | Delete the corrupt partial file, verify network permission, then retry only if downloads are allowed. For traffic loaders, prefer a verified pre-staged file. Do not treat a downloaded HTML error page as a valid dataset file. |
| `zipfile.BadZipFile`, missing extracted arrays, or `FileNotFoundError` after METR-LA/PeMS-Bay construction | Zip download was incomplete or the expected extracted filenames are absent. | Ensure the real zip file exists under `raw_data_dir` and can be opened. Remove incomplete extracted files, then let the constructor extract again or pre-extract the expected arrays. |
| File paths appear nested, or a relative cache directory creates unexpected subdirectories | Some download helpers combine `raw_data_dir` and save paths differently. Relative paths can expose nested-cache behavior. | Use a resolved cache directory, create it before construction, and keep expected filenames directly inside it. Avoid sharing that cache with unrelated experiments. |
| `WindmillOutputSmallDatasetLoader` or `WindmillOutputMediumDatasetLoader` raises a runtime error before loading | The inspected version deliberately raises because the historical source is no longer accessible. | Do not use these loaders for ordinary work. Use WindmillLarge if acceptable, or build a custom temporal signal from a user-supplied local copy. |
| `AttributeError` or missing `IndexDataset`/`pd` while calling `get_index_dataset` | Loader was constructed without `index=True`, or index-only PeMS loaders were constructed in ordinary mode. | Reconstruct with `index=True` and route tuple unpacking, `batch_size`, `allGPU`, `world_size`, `ddp_rank`, and `dask_batching` details to index-batching. |
| User asks why `PemsDatasetLoader` or `PemsAllLADatasetLoader` has no `get_dataset` | These are index-only loaders in the inspected public API. | Explain that ordinary snapshot datasets are unavailable for these classes; use `get_index_dataset` with `index=True` or choose METR-LA/PeMS-Bay for ordinary `StaticGraphTemporalSignal` loading. |
| Empty dataset, no snapshots, or index errors after setting a large `lags`, `frames`, or traffic window | Requested history/forecast window is too long for the stored time periods. | Reduce `lags`, `frames`, `num_timesteps_in`, or `num_timesteps_out`; validate by taking `len(list(dataset))` only on small datasets, or by checking one snapshot with `next(iter(dataset))`. |
| MontevideoBus raises stacking, standardization, or `None`-related errors with custom variables | `feature_vars` or `target_var` does not match the dataset schema. | Use default `target_var='y'` and `feature_vars=['y']` first. Validate custom variable names before constructing long workflows. |
| TwitterTennis raises `ValueError` for `event_id` or `feature_mode` | Constructor validates options before downloading. | Use `event_id='rg17'` or `'uo17'`; use `feature_mode=None`, `'encoded'`, or `'diagonal'`. Set `N` only when intentionally restricting popular nodes. |
| CUDA error when `allGPU` is set on an index-capable loader | `allGPU` triggers GPU preprocessing for index batching and requires CUDA-capable PyTorch plus a valid device id. | Set `allGPU=-1` for CPU preprocessing, or route to index-batching for GPU preflight and DDP planning. |
| First snapshot shape does not match the model's expected tensor order | Loader returns temporal signal snapshots, not model-ready batches for every architecture. Traffic `get_dataset` often returns `x` shaped `(nodes, features, time)`; index batching returns sequence batches shaped differently. | Inspect one snapshot and then route model-specific tensor layout to recurrent-layers or attention-and-hetero-layers. Route ordinary iterator shape mechanics to temporal-signals. |

## Constructor-side-effect checklist

Before running any constructor:

1. Confirm whether the selected class downloads in `__init__` using `dataset-loader-reference.md`.
2. If the loader has `raw_data_dir`, choose a cache directory and pre-stage expected files if downloads are forbidden.
3. If the loader has no `raw_data_dir`, assume no built-in offline path.
4. If the loader is index-only, do not call `get_dataset`; route to index-batching.
5. If the loader is unavailable in the inspected version, do not try to patch around it during normal use.

## Safe first-snapshot validation

After data access is approved and the loader has been constructed:

```python
dataset = loader.get_dataset(...)
snapshot = next(iter(dataset))
print("edges", None if snapshot.edge_index is None else tuple(snapshot.edge_index.shape))
print("edge_attr", None if snapshot.edge_attr is None else tuple(snapshot.edge_attr.shape))
print("x", None if snapshot.x is None else tuple(snapshot.x.shape))
print("y", None if snapshot.y is None else tuple(snapshot.y.shape))
```

This validates the loader output without starting a training loop. For dynamic graph loaders, repeat over a few snapshots if the task depends on edge-count variability.

## When to stop and ask

Stop before constructing a loader when:

- Network access is not explicitly allowed and the loader has no pre-stageable `raw_data_dir`.
- A traffic cache is incomplete and the task forbids downloads.
- The user asks for PeMS/PeMS-All-LA ordinary snapshots; the public API is index-only.
- The task requires WindmillSmall/WindmillMedium in this version; the constructors are intentionally unavailable.
- The user asks for GPU or distributed index preprocessing; that is index-batching scope, not ordinary dataset loading.
