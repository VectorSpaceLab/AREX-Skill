# Core Solver Troubleshooting

Use this guide when POT core balanced OT code fails, gives surprising values, or consumes too much memory. For intentionally unequal masses, outliers, or transported-mass constraints, route to `unbalanced-partial` instead of forcing a balanced solver.

## Failure matrix

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `AssertionError: a and b vector must have the same sum` from `emd`/`emd2` | Balanced EMD enforces equal total mass when `check_marginals=True`. | If the data should be balanced, normalize both histograms to the same total. If unequal mass is meaningful, use an unbalanced or partial OT workflow. Do not silence the check as a first response. |
| Dimension mismatch assertion | `len(a) != M.shape[0]`, `len(b) != M.shape[1]`, or sample arrays were transposed. | Print `a.shape`, `b.shape`, `M.shape`; rows of sample arrays are samples. Recompute `M = ot.dist(X_a, X_b)` after correcting shapes. |
| Negative, NaN, inf, or all-zero weights | POT solvers assume nonnegative finite masses with positive total mass. | Reject bad weights before solving. Do not clip negatives silently; trace the upstream data bug. Normalize only when the scientific problem is balanced. |
| Solver returns a plan but row/column sums do not match | Regularized solver tolerance too loose, plan materialized from a lazy object incorrectly, or the problem is actually unbalanced. | Validate with `np.testing.assert_allclose(plan.sum(1), a)` and `plan.sum(0)`. Tighten `tol`/`stopThr`, increase iterations, or route to unbalanced/partial if masses differ. |
| `Sinkhorn did not converge` warning | `reg` too small, costs too large in scale, `numItermax` too low, or the desired plan is too close to exact EMD. | Increase `reg`; scale/normalize the cost matrix; increase `numItermax`; use `method='sinkhorn_log'`, `sinkhorn_stabilized`, or `sinkhorn_epsilon_scaling`; if `reg` must be near zero, compare with exact `emd`. |
| `Warning: numerical errors at iteration ...` | Underflow/overflow in Sinkhorn scaling, often with tiny `reg` or large costs. | Use `sinkhorn_log` or stabilized/epsilon-scaling variants; rescale `M`; start from a larger `reg`; check for zero or nearly zero weights. |
| `ValueError: Unknown method ...` from `ot.solve` | `method` is not one of the limited unified `solve` method names. | For balanced core `ot.solve`, usually omit `method`. Valid names accepted by `ot.solve` are `sinkhorn`, `sinkhorn_log`, `mm`, and `lbfgsb`; the latter two are for unbalanced routes. |
| `ValueError: Unknown method ...` from `ot.sinkhorn`/`sinkhorn2` | Misspelled Sinkhorn variant. | Use `sinkhorn`, `sinkhorn_log`, `sinkhorn_stabilized`, `sinkhorn_epsilon_scaling`, or `greenkhorn` where supported. `screenkhorn` is exposed through `ot.bregman.screenkhorn`, not the top-level wrapper. |
| `ValueError: Unknown method ...` from `ot.solve_sample` | Misspelled sample method or using a large-scale method without its required constraints. | For core balanced sample OT, start with `method=None`. Use `method='1d'` only for 1D-style distances. Route Gaussian, sliced, low-rank, Nystroem, factored, GeomLoss, and BSP-heavy workflows to `sliced-gaussian-large-scale`. |
| `NotImplementedError: Not implemented reg_type=...` | `reg_type` is not supported by unified balanced OT. | Use `reg_type='KL'`, `'entropy'`, `'L2'`, or a tuple `(f, df)` of custom regularizer and gradient functions. Keep tuple functions deterministic and shape-compatible. |
| `NotImplementedError` for a `solve_sample` method with a metric | Method-specific metric restriction. | For `method='1d'`, use `metric='sqeuclidean'`, `'euclidean'`, or `'cityblock'`. For Gaussian/low-rank/Nystroem/factored paths, use squared Euclidean and route deeper to `sliced-gaussian-large-scale`. |
| `BSP-OT solver requires the same number of samples...` | `method='bsp'` requires equal sample counts and uniform weights. | Use another solver, resample to equal counts with a clear statistical reason, or route to the large-scale approximation sub-skill for BSP-specific guidance. |
| Import error mentioning EMD/compiled extension | POT was installed without the compiled EMD extension or the wheel/build failed. | Prefer a prebuilt wheel or conda-forge package. For source builds, ensure a C++ compiler, Cython, NumPy/SciPy build dependencies, and required bundled C++ headers are available before reinstalling. Verify with `python -c "import ot; import ot.lp.emd_wrap"`. |
| Build/install failure mentioning Cython or compiler | Source installation is compiling native extensions. | Install `cython`, `numpy`, and `scipy` before building, or use `pip install POT`/`conda install -c conda-forge pot` to get a compatible wheel/package. |
| Warning or confusion around `numThreads`/`n_threads` | The exact network simplex no longer uses OpenMP; `numThreads` is a deprecated compatibility parameter. | Keep `n_threads=1` or omit it. Do not rely on `numThreads` for speed. Parallelize independent problems outside POT if needed. |
| Sparse EMD returns infeasible-looking output or errors | Sparse matrix omits required transport edges or backend sparse support is unavailable. | Ensure the sparse graph can satisfy every row/column mass. With NumPy, use SciPy COO-style sparse matrices. Convert to dense for unsupported JAX/TensorFlow sparse paths or switch to a verified backend. |
| `ModuleNotFoundError: scipy` while using sparse smoke | Sparse helper requires SciPy sparse matrices. | Install SciPy or run only non-sparse modes. POT itself normally depends on SciPy, so this often indicates a broken environment. |
| Dense plan or cost matrix is too large | Core exact and Sinkhorn matrix workflows are `O(n*m)` memory for cost/plan. | Use 1D helpers, sparse EMD, `ot.solve_sample(..., lazy=True)`, or route large-scale approximation families to `sliced-gaussian-large-scale`. Avoid materializing `lazy_plan[:]` unless necessary. |
| `res.value` differs from `ot.sinkhorn2` | Unified regularized `OTResult.value` includes the regularization term; `sinkhorn2` returns the linear cost. | Compare `res.value_linear` to `ot.sinkhorn2(...)`, and compare `np.sum(res.plan * M)` to `res.value_linear`. |
| Multiple target histograms produce unexpected return shape | `emd2` and `sinkhorn2` can accept `b` as a matrix of target histograms and return per-target values/logs. | If the task expects one scalar, pass `b[:, k]`. If multiple targets are intended, iterate over results and validate each target marginal separately. |
| Gradients consume too much memory or are missing | Default `grad='autodiff'` stores all Sinkhorn iterations; exact EMD gradients rely on backend support; minimum verified runtime is NumPy. | For differentiable backends, use `grad='envelope'` when only `value` gradients are needed, `grad='last_step'` for a cheaper approximate path, or `grad='detach'` when gradients are unnecessary. Verify optional backend behavior separately. |
| `greenkhorn` fails on JAX or TensorFlow arrays | Greenkhorn is not compatible with those backends. | Use `sinkhorn`, `sinkhorn_log`, or a backend verified by the backend sub-skill. |
| Circle helper raises a shape error | Circle helpers expect one coordinate per sample, optionally batched consistently. | Convert unit-circle points to angular coordinates on `[0, 1)`, pass arrays with matching batch dimensions, and keep weights aligned with samples. |
| 1D helper raises metric error | `emd_1d`/`emd2_1d` only support selected Minkowski-style metrics. | Use `sqeuclidean`, `minkowski`, `cityblock`, or `euclidean`; otherwise fall back to dense `ot.dist` + `ot.emd` if the metric is supported there. |

## Minimal diagnostic snippets

### Check an installation and compiled EMD import

```bash
python - <<'PY'
import ot
print("POT", getattr(ot, "__version__", "unknown"))
import ot.lp.emd_wrap
print("compiled EMD import ok")
PY
```

### Catch mass and shape problems before solving

```python
import numpy as np

if M.shape != (len(a), len(b)):
    raise ValueError(f"M shape {M.shape} does not match weights {(len(a), len(b))}")
if np.any(np.asarray(a) < 0) or np.any(np.asarray(b) < 0):
    raise ValueError("negative weights are invalid for balanced core OT")
if not np.isclose(np.sum(a), np.sum(b)):
    raise ValueError("balanced core OT requires equal total source and target mass")
```

### Inspect a unified result safely

```python
res = ot.solve(M, a, b, reg=0.5, grad="detach")
print("value", res.value)
print("linear", res.value_linear)
print("status", res.status)
if res.plan is not None and res.plan.size <= 10_000:
    print("row error", np.max(np.abs(res.plan.sum(1) - a)))
    print("col error", np.max(np.abs(res.plan.sum(0) - b)))
```

For large lazy or sparse problems, replace dense `res.plan` inspection with sparse/lazy-aware marginal checks and avoid full materialization.
