# Cross-Cutting Troubleshooting

## Purpose

Use this when a PyTorch Geometric Temporal workflow fails before you know which sub-skill owns the problem. It covers install/import issues, optional dependencies, backend mismatches, downloads, and package-version quirks shared across the repo skill.

## Quick recovery ladder

1. Run `python scripts/check_environment.py --json` from this skill root or with an absolute path.
2. Read the relevant sub-skill troubleshooting page.
3. Run the matching synthetic smoke script.
4. Only then try a real loader or model example if network, data, or GPU use is allowed.

## Common failures

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `ModuleNotFoundError` importing `torch_geometric_temporal`, `torch`, or `torch_geometric` | PyTorch/PyG/PGT are not installed together, or the wheel set is incompatible with the backend | Reinstall with compatible PyTorch and PyG wheels, then rerun `scripts/check_environment.py` |
| `torch_geometric_temporal.__version__` does not match package metadata | The source tree's `__version__` constant is stale relative to the packaged release | Prefer distribution metadata for install checks; if the mismatch matters, refresh the repo skill snapshot |
| `ModuleNotFoundError: requests` or `ModuleNotFoundError: tqdm` when importing `torch_geometric_temporal.dataset` | Some loader modules import those packages at module import time | Install the missing dependency or the loader's required extra, then rerun loader introspection |
| `ModuleNotFoundError: pandas`, `ModuleNotFoundError: tables`, or HDF errors in PeMS loaders | Index-only traffic loaders need HDF/PyTables support | Install the index extra and HDF-compatible dependencies; route tuple unpacking to index-batching |
| `IndexDataset` import error | The helper is not exported from `torch_geometric_temporal.signal` | Import it explicitly from `torch_geometric_temporal.signal.index_dataset` |
| `get_index_dataset requires 'index=True'` | The loader was constructed in ordinary mode | Reconstruct the loader with `index=True` and retry |
| `Downloading to ...` appears during loader construction | The loader downloads in `__init__` because the expected cache file was missing | Stop if network/cache writes are not approved; pre-stage the file or choose a custom-iterator route |
| `zipfile.BadZipFile`, HTML content saved as a dataset, or missing extracted arrays | A remote download failed or was incomplete | Delete the partial file and retry only if downloads are allowed |
| `Torch not compiled with CUDA enabled` or CUDA device errors | GPU preprocessing or model code was asked to use CUDA on a CPU-only wheel | Use CPU mode or install a CUDA-compatible PyTorch/PyG stack |
| `WindmillOutputSmallDatasetLoader` or `WindmillOutputMediumDatasetLoader` raises `RuntimeError` | Those loaders are intentionally unavailable in the inspected source | Use WindmillLarge or another supported loader |
| A real dataset example starts a long download or many training epochs | The public example is a benchmark recipe, not a smoke check | Use the bundled synthetic smoke script, then adapt the model skeleton only |
| `torch_geometric_temporal.__version__` and the installed distribution version disagree | Source constant mismatch in the inspected checkout | Record both values and rely on the distribution version for packaging comparisons |

## Backend-specific guidance

### CPU vs CUDA

- CPU-only is enough for the selected core workflows in this generated skill.
- CUDA is optional unless the task explicitly asks for GPU preprocessing (`allGPU`) or GPU model execution.
- If the user wants GPU behavior but `torch.cuda.is_available()` is false, explain that a CUDA wheel or hardware is missing instead of silently falling back.

### Dask/DDP

- Dask/DDP is optional and belongs to the index-batching route.
- Do not pretend to have verified multi-node behavior if only a CPU synthetic smoke passed.
- If the user needs DDP, require the distributed runtime, scheduler/client setup, and a valid rank/world-size mapping.

## When to stop and ask

Stop instead of guessing when:

- The loader requires network access and the user has not approved downloads.
- The required backend is unavailable for a workflow that truly needs it.
- An HDF/traffic cache file is missing and the user did not pre-stage it.
- The task asks for the unavailable WindmillSmall/Medium loaders.

## Route-specific references

- [`sub-skills/temporal-signals/references/troubleshooting.md`](../sub-skills/temporal-signals/references/troubleshooting.md)
- [`sub-skills/dataset-loaders/references/troubleshooting.md`](../sub-skills/dataset-loaders/references/troubleshooting.md)
- [`sub-skills/recurrent-layers/references/troubleshooting.md`](../sub-skills/recurrent-layers/references/troubleshooting.md)
- [`sub-skills/attention-and-hetero-layers/references/troubleshooting.md`](../sub-skills/attention-and-hetero-layers/references/troubleshooting.md)
- [`sub-skills/index-batching/references/troubleshooting.md`](../sub-skills/index-batching/references/troubleshooting.md)
