# Troubleshooting

## Package stack issues

### NumPy / PyTorch incompatibility

**Symptoms**

- `torchvision` warns about NumPy.
- Imports fail with messages about `_ARRAY_API` or `numpy.lib.array_utils`.

**Likely cause**

- The environment has a NumPy 2.x build that is incompatible with the torch
  stack used by this repo.

**Recovery**

- Keep NumPy below 2 for this repository's runtime stack.
- Re-run `scripts/check_install.py` after adjusting the environment.

### `pip check` complains about triton / cmake / lit

**Symptoms**

- `pip check` reports that `triton` needs `cmake` or `lit`.

**Likely cause**

- The environment has the PyTorch stack but not the metadata-visible build
  helpers.

**Recovery**

- Install the missing helpers in the same environment.
- Re-run the install checker and `pip check`.

### `cvxpy` import errors

**Symptoms**

- `FedPAC` fails to import.
- Solver setup raises a NumPy or backend error.

**Likely cause**

- `cvxpy` was built against an incompatible NumPy version or the solver stack
  is incomplete.

**Recovery**

- Use a `cvxpy` build that matches the torch-compatible NumPy pin.
- Re-run the install checker before trying the algorithm again.

## Backend and device issues

### CUDA is missing or hidden

**Symptoms**

- `torch.cuda.is_available()` is false.
- `main.py` falls back to CPU.
- CUDA-only smoke tests fail.

**Likely cause**

- The driver/runtime is not visible to the environment or `CUDA_VISIBLE_DEVICES`
  hides every GPU.

**Recovery**

- Use `scripts/check_install.py` to confirm the backend.
- Adjust the visible device ids or use a CUDA-capable environment.
- Treat CPU-only runs as smoke checks, not as proof of GPU readiness.

## Working directory and path issues

### Relative paths do not resolve

**Symptoms**

- `main.py` cannot find `../dataset/` or `../results/`.
- A generator cannot see its `rawdata/` area.

**Likely cause**

- The script was launched from the wrong directory.

**Recovery**

- Use the bundled launcher scripts, which normalize the working directory for
  you.
- Do not rely on a manual shell `cd` sequence when a launcher already exists.

## Repository-layout issues

### Dataset split or registry paths are stale

**Symptoms**

- A dataset split exists but the experiment runner rejects it.
- A new algorithm or model is missing from the supported registry.

**Likely cause**

- The split tree, model registry, or algorithm registry changed without a
  corresponding update to the relevant helper or reference.

**Recovery**

- Re-run the scan helper for the registry surface.
- Re-run the dataset validator for the split tree.
- Refresh the relevant subskill if the repo changed.
