# Cross-cutting troubleshooting

Use this reference when a PDEBench command fails before the workflow-specific
troubleshooting guide gives a narrower diagnosis.

## Import and version failures

- **`ModuleNotFoundError: pdebench`**: install the public `pdebench` distribution
  into the Python that will run the command, then retry `import pdebench`.
  Avoid relying on a checkout-relative working directory.
- **NumPy/Torch/TorchVision resolver conflict**: keep the package's Python and
  NumPy constraints in view and install a matching PyTorch/TorchVision pair.
  Do not mix a 1.13 TorchVision wheel with a 2.x PyTorch wheel.
- **DeepXDE backend error**: set `DDE_BACKEND=pytorch` before importing PINN
  modules and verify that the selected backend package is importable.
- **Pyro import or tensor errors**: check Pyro and PyTorch as a pair; inspect
  `torch.__version__` and run a tiny tensor operation before inverse training.
- **Optional module missing (`phi`, `pytorch_lightning`, Clawpack)**: the
  affected generation/data-loader branch is optional. Install the documented
  workflow-specific dependency only after confirming that route and its backend.

## Paths, Hydra, and configuration

- **A documented file is not found after a Hydra launch**: Hydra may have
  changed the process directory. Use an explicit data/output path or a Hydra
  `to_absolute_path`-style resolution and print the resolved config before a
  long run.
- **Config group or override not found**: confirm the family, config group, and
  spelling, then render with the entry point's config-inspection option before
  adding overrides.
- **Outputs appear in an unexpected directory**: inspect the resolved Hydra
  runtime directory and set an explicit output root. Do not delete an unknown
  output directory to recover.
- **Checkpoint or dataset mismatch**: check `filename`, `data_path`,
  `single_file`, spatial/temporal reductions, channel counts, and `initial_step`
  together. A syntactically valid config can still describe the wrong tensor
  contract.

## Data and schema failures

- **Metadata checker rejects a CSV**: verify the required `PDE`, `Filename`,
  `URL`, `Path`, and `MD5` columns and use one of the canonical lowercase PDE
  names. The bundled checker is local-only and never repairs or downloads data.
- **HDF5 key or shape error**: inspect keys and coordinate arrays before model
  loading. Dataset families differ: some use `tensor`, some use `density`,
  `Vx/Vy/Vz`, and per-sample groups. Read the owning data sub-skill's format
  reference.
- **Vorticity converter rejects input**: require coordinate datasets and
  `Vx`, `Vy`, `Vz` with matching trial/time/spatial shapes. Confirm coordinates
  are regularly spaced and use the bundled converter's explicit output path.
- **Spectral vorticity validation fails**: input must be a five-dimensional
  array `[batch_or_time, sx, sy, sz, 3]`; use positive or negative spacings
  consistently. A malformed last axis is a validation error, not a backend
  issue.

## Backend, resource, and runtime failures

- **CUDA is unavailable**: treat it as an optional acceleration limitation
  unless the selected capability is explicitly GPU-required. Use the CPU route
  only for behavior it fully substitutes, and do not claim GPU verification.
- **Out-of-memory or very slow simulation/training**: stop the run; reduce the
  fixture, grid, batch, time horizon, workers, modes, or epochs only when the
  change is scientifically acceptable. Do not silently run a benchmark-sized
  command as a smoke test.
- **NLE/JAX compilation takes too long**: first use help/config rendering and a
  tiny bounded fixture. JIT compilation, large arrays, and multi-GPU shell loops
  are not default verification.
- **Plotting fails on a headless machine**: select a non-interactive Matplotlib
  backend and write to a deliberate output file. Visualization requires an
  existing local dataset; it is not a substitute for data validation.

## Network and credential boundaries

- **Download stalls or storage is insufficient**: stop before partial large
  transfers, check the shard size and destination capacity, and resume only
  with an explicit plan. PDEBench includes multi-GB and TB-scale datasets.
- **DaRUS upload/authentication fails**: do not print or copy tokens into logs or
  configs. Verify credentials and dataset permissions separately; upload is
  not a package smoke test.
- **The slower EasyDataverse route fails**: prefer the direct URL/metadata path
  for a deliberately selected shard, and keep network commands outside safe
  verification.
