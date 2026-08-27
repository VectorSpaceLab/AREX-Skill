# Backend and batch troubleshooting

Use this reference when a POT backend or batched solver workflow fails before the mathematical OT model is the issue. For solver-family mistakes, route to the relevant solver sub-skill after fixing the backend or batch mechanics.

## Fast diagnostic checklist

```bash
python scripts/backend_batch_smoke.py --case backends
python scripts/backend_batch_smoke.py --case batch-linear
python scripts/backend_batch_smoke.py --case sample-batch
python scripts/backend_batch_smoke.py --case mixed-backend
```

If these pass in the user's environment, the installed POT package is adequate for NumPy backend discovery and the covered batch APIs; focus on the user's arrays, shapes, optional dependency setup, or gradient mode.

## Common failures and recoveries

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ValueError: All array should be from the same type/backend...` | Inputs mix NumPy, Torch, JAX, TensorFlow, CuPy, SciPy sparse, or Torch sparse arrays. | Convert every POT input to one backend before calling a solver. For NumPy, use `ot.backend.to_numpy`; for optional frameworks, use native constructors or `nx.from_numpy(..., type_as=template)`. Re-run `get_backend(*inputs).__name__` before solving. |
| `ValueError: The function takes at least one (non-None) parameter` from `get_backend` | All inputs passed to `get_backend` were `None`, or no input was provided. | Call `get_backend` only after at least one concrete array exists. Batch solvers can create default `a`/`b`, but `M`, `X_a`/`X_b`, or `Ca`/`Cb` must still be concrete arrays. |
| `ValueError: Unknown type of non implemented backend` | A Python scalar, list, pandas object, unsupported sparse type, or array from an unregistered optional backend was passed. | Convert lists/scalars to arrays first. Install and verify the optional backend, or set the corresponding `POT_BACKEND_DISABLE_*` variable and convert to NumPy. |
| Optional backend import is missing, e.g. no `torch`, `jax`, `tensorflow`, or `cupy` | Optional backend packages are not part of the base POT install. | Use NumPy, or install the documented optional backend route. Verify with `python scripts/backend_batch_smoke.py --case backends --require-optional <name>` before claiming that backend works. |
| TensorFlow arrays fail on NumPy-style operations | TensorFlow NumPy behavior was not enabled before creating arrays/POT calls. | At process start, run `from tensorflow.python.ops.numpy_ops import np_config; np_config.enable_numpy_behavior()`. Then import/use TensorFlow arrays for POT. Restart the Python process if needed. |
| TensorFlow or JAX imports allocate GPU memory or slow startup | `get_backend_list()` or importing POT with optional backends may initialize frameworks. | Set `POT_BACKEND_DISABLE_TENSORFLOW=1`, `POT_BACKEND_DISABLE_JAX=1`, or other disable variables before importing POT when those frameworks are not needed. Use `get_available_backend_implementations()` for names without forcing backend object instantiation. |
| GPU is visible but POT still runs on CPU | The arrays passed to POT are CPU NumPy or CPU Torch/JAX/TensorFlow arrays. | Create arrays on the intended backend/device first. POT follows the array backend/device; it does not move data to GPU automatically. The minimum verified skill runtime did not verify optional GPU backends. |
| CuPy import or CUDA runtime fails | The installed CuPy package does not match the CUDA runtime, or CuPy is not installed. | Install a CUDA-compatible CuPy distribution, such as the appropriate `cupy-cudaXX` wheel or a conda-forge CuPy package. POT's `backend-cupy` extra intentionally does not choose a CuPy wheel. Disable CuPy for POT import if the local CUDA stack is broken. |
| `to_numpy` appears to break gradients | Conversion to NumPy detaches or copies differentiable backend arrays. | Use `to_numpy` only for validation/logging after a computation. Keep loss construction and `.backward()`/gradient calls in the original backend. |
| PyTorch workflow consumes too much memory | `grad='autodiff'` stores operations for plan/value/value_linear, especially in iterative Sinkhorn or batch solvers. | For value-only learning objectives, use `grad='envelope'`. For validation, use `grad='detach'`. Try `grad='last_step'` for batch linear solvers when plan gradients are needed but full autodiff is too expensive. |
| PyTorch gradients are `None` | Inputs were not floating tensors with `requires_grad=True`, `grad='detach'` was used, or the checked output does not depend on that input under the selected gradient mode. | Rebuild tensors with floating dtype and `requires_grad=True`. Use `grad='envelope'` and call `res.value.sum().backward()` for value gradients, or `grad='autodiff'`/`'last_step'` if plan/value_linear gradients are required. |
| `ValueError: Sinkhorn methods require a strictly positive reg parameter` | `method='sinkhorn'` or `'log_sinkhorn'` was selected with `reg=None`, `reg=0`, or negative `reg`. | Use `method='proximal'`/`'auto'` for unregularized batch solves, or set a positive `reg` for Sinkhorn methods. |
| `Unknown method`, `Unknown reg_type`, or `Unknown grad` in batch solver | Batch API validates a limited set of strings. | Use `method` in `{'auto','proximal','log_sinkhorn','sinkhorn'}`, `reg_type` in `{'entropy','kl'}` with lowercase strings, and `grad` in `{'detach','autodiff','last_step','envelope'}` for `solve_batch`. |
| Batch cost shape error or wrong plan shape | The leading batch dimension was omitted, or `M` has shape `(n, m)` instead of `(B, n, m)`. | For one problem, add a batch axis with `M = M[None, :, :]` and weights `a = a[None, :]`, `b = b[None, :]`; otherwise stack same-shaped matrices with `np.stack`. |
| Weight shape or marginal mismatch in `solve_batch` | `a` and `b` are one-dimensional or have lengths that do not match `M.shape[1:]`. | Use `a.shape == (B, ns)` and `b.shape == (B, nt)`. Normalize each row for balanced OT unless the selected solver explicitly relaxes mass elsewhere. |
| `dist_batch` result has unexpected shape | `X1` or `X2` did not have shape `(B, n, d)`, or `X2` was omitted unintentionally. | Check `X1.ndim == 3`; if solving one sample-cloud problem, use `X1 = X1[None, :, :]`. Pass `X2` explicitly when source and target samples differ. |
| `metric='kl'` returns NaN/Inf or negative surprises | KL distance expects positive feature vectors and can be unstable around zeros. | Add a small positive floor where appropriate, normalize feature distributions along the feature axis, and validate `np.isfinite(ot.dist_batch(...)).all()` before solving. |
| `solve_gromov_batch` with fused cost raises about `M`/`alpha` | Fused GW requires `M` and `alpha` together, and `M` must be batched. | For pure GW, omit both `M` and `alpha`. For fused GW, pass `M.shape == (B, n, m)` and `0 <= alpha <= 1`. |
| `solve_gromov_batch` is slower or not equal to looping `ot.solve_gromov` | The batched GW solver uses a proximal/entropic algorithm, not the same conditional-gradient algorithm as non-batched GW. | Validate on a tiny fixture, compare plan marginals and objective trends, and treat exact solver-family decisions as `gromov` sub-skill territory. |
| Batch GW KL loss complains about logits or tensor shapes | `loss='kl'` needs explicit `logits=True`/`False` and compatible vector-valued cost tensors. | Start with `loss='sqeuclidean'` on scalar structure matrices. For KL feature costs, verify positive/logit semantics and shapes before solving. |
| SciPy sparse cost with Torch arrays fails | SciPy sparse matrices belong to the NumPy backend; Torch sparse matrices belong to the Torch backend. | Keep all sparse and dense arrays in one backend. Convert to dense NumPy for a NumPy solve, or build Torch sparse/dense tensors consistently for a Torch solve. |

## Mixed NumPy/Torch recovery recipe

If a user reports a mixed-backend failure, reduce it to this pattern:

```python
import numpy as np
import ot
from ot.backend import get_backend

M = np.array([[0.0, 1.0], [1.0, 0.0]])
a = np.array([0.5, 0.5])
# b is accidentally a Torch tensor in the user's code.

# Diagnosis:
# get_backend(a, b, M) raises a ValueError because arrays are from different backends.

# NumPy recovery:
b = np.asarray([0.5, 0.5], dtype=M.dtype)
assert get_backend(a, b, M).__name__ == "numpy"
res = ot.solve(M, a, b, n_threads=1)
```

For a Torch recovery, build `M`, `a`, and `b` all as Torch tensors on the same dtype/device instead of converting only one array.

## Batch vectorization recovery recipe

When a batch workflow gives different results from a loop:

1. Check that every problem has the same `ns` and `nt`; pad or split batches if shapes differ.
2. Recompute `M_loop = np.stack([ot.dist(X[i], Y[i]) for i in range(B)])` and compare it against `ot.dist_batch(X, Y)`.
3. Solve with `grad='detach'`, explicit `method`, `reg`, `reg_type`, `max_iter`, and `tol` to remove gradient and auto-routing ambiguity.
4. Compare `value_linear` and marginals before comparing every plan entry.
5. Tighten `tol` or increase `max_iter`/`inner_iter` only after the tiny fixture reproduces the discrepancy.

## Optional backend claim policy

- It is safe to say that NumPy backend behavior is covered by this skill's smoke checks.
- It is not safe to say that PyTorch, JAX, TensorFlow, CuPy, or GPU behavior is verified unless the user has run an optional-backend smoke in the same environment.
- If optional imports are broken and the task does not require them, prefer disabling them before POT import instead of trying to repair GPU packages.
- If the task requires an optional backend, verify import, backend registration, one tiny solver call, and (for gradients) one tiny gradient call before scaling.
