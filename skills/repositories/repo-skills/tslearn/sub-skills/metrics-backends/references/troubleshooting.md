# Troubleshooting Metrics and Backends

## Missing torch

**Symptoms**

- `ValueError: Could not use the PyTorch backend since torch is not installed`
- `ValueError: Could not use SoftDTWLossPyTorch since torch is not installed`
- Import failure while constructing `SoftDTWLossPyTorch` or using
  `be="pytorch"`.

**Recovery**

1. If the task is ordinary distances, paths, `cdist_*`, performance metrics, or
   barycenters, switch to NumPy/list inputs and leave `be=None` or set
   `be="numpy"`.
2. If the task explicitly needs gradients or `SoftDTWLossPyTorch`, install a
   compatible torch build in the working environment.
3. Re-run a tiny check from the `metrics-backends/` sub-skill directory:

   ```bash
   python scripts/metrics_smoke.py dtw --backend numpy
   python scripts/metrics_smoke.py softdtw-loss
   ```

## Backend string confusion

**Symptoms**

- A user passes `be="cuda"`, `be="gpu"`, or another backend-like string and
  gets NumPy behavior.
- A check prints `backend_string == "pytorch"` even though existing code used
  `Backend("torch")`.

**Recovery**

- Prefer `be="numpy"` or `be="pytorch"` in public code.
- `"torch"` also selects PyTorch in the current backend selector, but the
  canonical string remains `"pytorch"`.
- Verify the backend explicitly:

  ```python
  from tslearn.backend import instantiate_backend
  assert instantiate_backend("pytorch").backend_string == "pytorch"
  assert instantiate_backend("cuda").backend_string == "numpy"
  ```

- Do not use backend strings to choose GPU devices. Device placement belongs to
  the torch tensors themselves and still needs workload-specific profiling.

## Empty input, all-NaN input, or feature-size mismatch

**Symptoms**

- `ValueError: One of the input time series contains only nans or has zero length.`
- `ValueError: All input time series must have the same feature size.`
- A variable-length dataset padded with NaNs fails after a specific series is
  reduced to no valid timestamps.

**Recovery**

1. Convert each series to `(sz, d)` before calling pairwise metrics.
2. Drop or impute all-NaN series before metric calls.
3. Ensure both pair inputs have the same `d`; univariate arrays can be passed as
   `(sz,)` but mixing `(sz,)` with `(sz, 2)` is invalid.
4. For variable-length datasets, use barycenter APIs documented for
   variable-length support or convert each series intentionally before pairwise
   loops.

## Warping-constraint mistakes

**Symptoms**

- `RuntimeWarning` about both `sakoe_chiba_radius` and `itakura_max_slope` being
  set while `global_constraint` is not set.
- `RuntimeWarning: 'itakura_max_slope' constraint is unfeasible ...`
- `ValueError: Cannot find a path of length ...` from limited warping length.
- Constrained DTW unexpectedly equals Euclidean distance.

**Recovery**

- Specify one constraint family at a time:

  ```python
  dtw(x, y, global_constraint="sakoe_chiba", sakoe_chiba_radius=2)
  dtw(x, y, global_constraint="itakura", itakura_max_slope=2.0)
  ```

- Use `compute_mask(len_x, len_y, ...)` to inspect the admissible region before
  large `cdist_*` calls. For `compute_mask`, use numeric codes (`0`, `1`, `2`),
  `GLOBAL_CONSTRAINT_CODE[...]`, or inference from one supplied constraint
  parameter rather than raw string names.
- `sakoe_chiba_radius=0` or `itakura_max_slope=1.0` on equal-length series
  enforces the diagonal, so DTW/Soft-DTW can reduce to Euclidean or squared
  Euclidean behavior.
- For `dtw_limited_warping_length`, choose `max_length >= max(len(s1), len(s2))`.

## Soft-DTW gradient issues

**Symptoms**

- `x.grad is None` after `backward()`.
- `AssertionError` inside `SoftDTWLossPyTorch.forward`.
- A custom `dist_func` breaks the graph or returns shape errors.
- Training behaves oddly because raw Soft-DTW is negative.

**Recovery**

1. For top-level metric autodiff, construct torch tensors with
   `requires_grad=True` and keep `be="pytorch"` or rely on tensor
   auto-detection.
2. For `SoftDTWLossPyTorch`, pass tensors shaped `(batch, length, dim)` with
   equal batch size and feature dimension.
3. Aggregate per-example losses before backpropagation:

   ```python
   loss = SoftDTWLossPyTorch(gamma=1.0, normalize=True)(x, y).mean()
   loss.backward()
   ```

4. Keep custom distance functions entirely in torch and return shape
   `(batch, m, n)`.
5. Use `normalize=True` when the loss must be nonnegative and zero for identical
   inputs; remember that it costs about three Soft-DTW evaluations.
6. Keep `gamma` positive for `SoftDTWLossPyTorch`; use small positive values for
   DTW-like behavior rather than `0`.

## CPU correctness vs CUDA acceleration

**Symptoms**

- A CPU smoke passes but a user expects CUDA speedups without profiling.
- CUDA is available, but Soft-DTW loss is slower than expected.
- The task confuses PyTorch backend support with guaranteed GPU acceleration.

**Recovery**

- Treat NumPy/CPU as the correctness baseline for this sub-skill.
- Use PyTorch only for tensor/autodiff needs, then verify tensor device and
  profile the real shape/length workload.
- Do not claim `SoftDTWLossPyTorch` is fully GPU-accelerated solely because the
  environment has CUDA; its dynamic-programming implementation performs
  CPU-side array work and can move data between device and CPU.

## GAK sigma and numerical overflow

**Symptoms**

- `ZeroDivisionError: Sigma must be non-zero.`
- Very long time series produce unstable or overflowing GAK values.

**Recovery**

- Never pass `sigma=0` to `gak`, `unnormalized_gak`, or `cdist_gak`.
- Start with `sigma_gak(dataset, n_samples=..., random_state=...)` for a
  reproducible estimate.
- If long series overflow or saturate, try a smaller positive sigma and verify
  the kernel matrix diagonal remains near `1` for normalized GAK.

## MASE divide-by-zero

**Symptoms**

- `RuntimeWarning: divide by zero` and `inf` from `performance.mase`.

**Recovery**

- Check whether the in-sample `train_data` has zero seasonal differences under
  the selected `seasonal_period`.
- Use a meaningful nonconstant training history or report MASE as undefined for
  that series/feature.
