---
name: dataset-loaders
description: "Guides safe selection and use of PyTorch Geometric Temporal
  dataset loaders, including signatures, return signal types, cache and network
  side effects, and dataset-specific window parameters."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Dataset Loaders

Use this sub-skill when the task is to choose or call a built-in loader from `torch_geometric_temporal.dataset`, understand what `get_dataset` returns, plan traffic/PDE/JSON data access, or inspect loader signatures without triggering downloads.

Do **not** instantiate a loader until you have decided whether network access and cache writes are acceptable. Many loaders fetch data in `__init__`, not in `get_dataset`.

## Route here for

- Selecting among public `*DatasetLoader` classes exported by `torch_geometric_temporal.dataset`.
- Checking constructor signatures, `get_dataset` arguments, return signal types, and loader-specific lags/window/feature parameters.
- Planning `raw_data_dir` for METR-LA, PeMS-Bay, PeMS, PeMS-All-LA, and WindmillLarge before construction.
- Avoiding unintended downloads, partial cache files, zip extraction surprises, or unavailable WindmillSmall/WindmillMedium loaders.
- Explaining JSON/web loaders, traffic loaders, synthetic PDE loaders, and index-only PeMS loaders at a planning level.

## Route elsewhere

- Ordinary snapshot iteration, `temporal_signal_split`, slicing, and creating custom signals from arrays: use the temporal-signals sub-skill.
- `get_index_dataset`, dataloader return tuple unpacking, `index=True`, `allGPU`, `world_size`, `ddp_rank`, Dask-DDP, and sequence-to-sequence index batches: use the index-batching sub-skill.
- Model/training loops after a loader returns snapshots: use the recurrent-layers or attention-and-hetero-layers sub-skill.

## Safe planning workflow

1. **Inspect without constructing.** Run or read [`scripts/list_dataset_loaders.py`](scripts/list_dataset_loaders.py) to list exported loader classes and method signatures. This imports classes but never instantiates them.
2. **Choose by task and signal type.** Use [`references/dataset-loader-reference.md`](references/dataset-loader-reference.md) to match the loader to `StaticGraphTemporalSignal`, `DynamicGraphTemporalSignal`, or index-only behavior.
3. **Classify side effects.** Read [`references/data-sources.md`](references/data-sources.md) before constructing any loader. Treat constructor-time downloads as the default unless the reference says the loader is unavailable or can be fully pre-staged.
4. **Plan parameters before the first call.** Decide `lags`, `frames`, `num_timesteps_in`, `num_timesteps_out`, `target_var`, `feature_vars`, `event_id`, `N`, and `feature_mode` up front; changing them after construction is usually safe, but construction may already have downloaded data.
5. **Use an isolated cache for traffic loaders.** For loaders with `raw_data_dir`, pre-stage the expected files or point to an expendable cache directory. Do not use a shared working directory when evaluating unknown prompts.
6. **Validate only after loading is allowed.** Once data access is approved, instantiate the loader, call `get_dataset`, inspect one snapshot's `edge_index`, `edge_attr`, `x`, and `y`, then hand off iterator mechanics or model loops to the appropriate sub-skill.

## Quick loader selection

- **Small/static JSON benchmarks:** `ChickenpoxDatasetLoader`, `PedalMeDatasetLoader`, `WikiMathsDatasetLoader`, `MontevideoBusDatasetLoader`, `MTMDatasetLoader`.
- **Dynamic graph JSON benchmarks:** `EnglandCovidDatasetLoader`, `TwitterTennisDatasetLoader`.
- **Traffic window forecasting:** `METRLADatasetLoader` or `PemsBayDatasetLoader` with `get_dataset(num_timesteps_in=..., num_timesteps_out=...)`.
- **Index-only large PeMS:** `PemsDatasetLoader` and `PemsAllLADatasetLoader` do not provide ordinary `get_dataset`; plan index batching separately.
- **Synthetic PDE data:** `AdvectionDiffusionDatasetLoader`, `SIDiffusionDatasetLoader`, `WaveEquationDatasetLoader` download remote NumPy/PyTorch payloads at construction and return static graph temporal signals.
- **Avoid unavailable exports:** `WindmillOutputSmallDatasetLoader` and `WindmillOutputMediumDatasetLoader` are exported but raise a runtime error in the inspected source because their original host is unavailable.

## References

- [`references/dataset-loader-reference.md`](references/dataset-loader-reference.md) - class-by-class arguments, output types, side effects, and index support notes.
- [`references/data-sources.md`](references/data-sources.md) - remote source families, cache/pre-stage expectations, and no-download alternatives.
- [`references/troubleshooting.md`](references/troubleshooting.md) - failed downloads, missing optional packages, cache extraction, shape assumptions, and index-only loader errors.
