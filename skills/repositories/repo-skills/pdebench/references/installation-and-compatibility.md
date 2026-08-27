# Installation and compatibility

Read this when choosing a Python version, resolving optional extras, or
interpreting a backend/import failure.

## Supported baseline

The package metadata declares Python `>=3.9,<3.11`, base dependencies including
NumPy `<2`, SciPy, Matplotlib, HDF5/pandas tooling, Hydra, PyTorch `1.13.x`,
TorchVision `0.14.x`, DeepXDE `1.1.x`, Pyro, and tqdm. Install into an isolated
Python 3.9 or 3.10 environment rather than modifying a system environment.

```bash
python -m pip install pdebench
python -c "import pdebench; print('pdebench import ok')"
```

The source distribution exposes the `velocity2vorticity` console command. Check
its parser without reading or writing data:

```bash
velocity2vorticity --help
```

## Optional dependency families

| Capability | Additional requirements | Default policy |
|---|---|---|
| Base models, metrics, metadata, local HDF5 work | Base package; CPU PyTorch/JAX as needed | Safe first route |
| NLE generation | JAX plus the selected package extra/config family | Bounded/help-only until approved |
| Navier–Stokes PhiFlow generation | PhiFlow and its `phi` modules | Optional; not part of the CPU baseline |
| Radial dam-break generation | Clawpack-compatible runtime | Optional; verify before running |
| PINN | DeepXDE and a selected backend | Set `DDE_BACKEND=pytorch` when using PyTorch |
| Inverse model | Pyro compatible with the installed PyTorch | Check `torch`/`pyro` versions together |
| CUDA acceleration | CUDA-capable framework builds and compatible driver | Optional; CPU import is not CUDA proof |

The `datagen39` and `datagen310` extras are broad and include direct VCS or
CUDA-oriented dependencies. Do not install them merely to inspect the package;
select them only for a planned generation family and verify the resulting
backend.

## Compatibility observations

- The generated skill was inspected with Python 3.10, NumPy 1.26, CPU PyTorch
  1.13, JAX CPU 0.4.38, DeepXDE 1.1.4, and Pyro 1.8.6. These are inspection
  facts, not a promise that every future release is interchangeable.
- The repository README documents newer Python/JAX/PyTorch/CUDA combinations
  for several components, but compatibility is component-specific. Prefer the
  package metadata and the selected workflow's own smoke check.
- Hydra changes the process working directory for many decorated entry points.
  Use explicit absolute or Hydra-resolved data locations and preserve outputs
  in a deliberate directory.
- A CPU baseline can validate numerical shape/API behavior where the package
  has an explicit fallback. It cannot establish CUDA speed, device placement,
  or a GPU-only path.
