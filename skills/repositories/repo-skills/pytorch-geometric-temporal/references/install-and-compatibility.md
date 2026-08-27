# Install and Compatibility

## Purpose

Read this before any runtime inspection or generated workflow use. It summarizes the public install pattern, optional extras, version caveats, and the smallest safe smoke checks for PyTorch Geometric Temporal.

## Baseline install

The public project expects compatible PyTorch and PyTorch Geometric first, then the temporal package:

```bash
python -m pip install torch torch-geometric
python -m pip install torch-geometric-temporal
```

If you want editable development against a local checkout while distilling a skill, use the repository only in your private inspection environment, not in the generated runtime skill.

## Optional extras

- `torch-geometric-temporal[index]` adds the index-batching data dependencies used by `IndexDataset` and the large traffic loaders.
- `torch-geometric-temporal[ddp]` adds Dask distributed support and the extra dependencies used by Dask-DDP-oriented examples.

Examples:

```bash
python -m pip install "torch-geometric-temporal[index]"
python -m pip install "torch-geometric-temporal[ddp]"
```

## Version and backend caveats

- The inspected source reports package version `0.56.2`, while the package constant `torch_geometric_temporal.__version__` currently reports `0.54.0` in the examined checkout.
- Many dataset loader modules import `requests` and `tqdm` at module import time. If imports fail, install those packages or use the bundled loader-inspection helper before constructing loaders.
- `torch_geometric` and PyTorch wheels must match the backend you intend to use. CPU-only installs are fine for the selected core workflows in this skill; CUDA is optional unless you are explicitly using GPU preprocessing or model execution.
- Real traffic, weather, and benchmark loaders may download data in `__init__`. If network or cache writes are not allowed, do not instantiate them.

## Safe smoke ladder

1. Run the bundled environment check:

   ```bash
   python scripts/check_environment.py --json
   ```

2. Check that the installed package and PyG import cleanly:

   ```bash
   python -m pip check
   python -c "import torch_geometric_temporal, torch_geometric, torch; print('ok')"
   ```

3. Run the relevant sub-skill smoke script for the exact workflow you need.

## When to install more

Install additional packages only when the workflow needs them:

- `dask`, `pandas`, `tables` for index-batching and HDF-backed traffic loaders.
- CUDA-enabled PyTorch/PyG wheels only when the task truly needs GPU execution or `allGPU` preprocessing.
- Dask distributed runtime only when the user actually asks for Dask-DDP or cluster launch behavior.

If a user asks for a loader or model behavior that needs a missing optional backend, route to the appropriate sub-skill and explain the missing package or backend explicitly rather than guessing a fallback.
