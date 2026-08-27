# POT batch solvers

Use this reference when a workflow has many OT problems with the same structural shape and should avoid a Python loop over `ot.solve` or `ot.dist`. POT exposes the batch API both as top-level functions such as `ot.solve_batch` and through `ot.batch`.

## Quick commands

```bash
# Run all deterministic NumPy backend-and-batch checks.
python scripts/backend_batch_smoke.py --case all

# Focus on the two difficult operating cases owned by this sub-skill.
python scripts/backend_batch_smoke.py --case mixed-backend
python scripts/backend_batch_smoke.py --case batch-linear
```

The script uses tiny in-memory fixtures only and does not depend on optional backend libraries.

## Verified signatures and defaults

| API | Verified signature/defaults | Main input shape | Main result |
| --- | --- | --- | --- |
| `ot.dist_batch` | `dist_batch(X1, X2=None, metric='sqeuclidean', p=2, nx=None)` | `X1: (B, n1, d)`, optional `X2: (B, n2, d)` | Cost tensor `M: (B, n1, n2)` |
| `ot.solve_batch` | `solve_batch(M, reg=None, a=None, b=None, max_iter=1000, tol=1e-05, method='auto', inner_iter=1, inner_reg=0.001, reg_type='entropy', grad='envelope')` | `M: (B, ns, nt)`, optional `a: (B, ns)`, `b: (B, nt)` | `OTResult` with batched `plan`, `value`, `value_linear`, `potentials`, `log` |
| `ot.solve_sample_batch` | `solve_sample_batch(X_a, X_b, reg=None, a=None, b=None, metric='sqeuclidean', p=2, max_iter=1000, tol=1e-05, method='auto', inner_iter=1, inner_reg=0.001, reg_type='entropy', grad='envelope')` | `X_a: (B, ns, d)`, `X_b: (B, nt, d)` | Same `OTResult` as `solve_batch`; internally builds `dist_batch` |
| `ot.solve_gromov_batch` | `solve_gromov_batch(Ca, Cb, reg=0.01, a=None, b=None, loss='sqeuclidean', symmetric=None, M=None, alpha=None, T_init=None, max_iter=50, tol=1e-05, max_iter_inner=50, tol_inner=1e-05, grad='envelope', logits=None)` | `Ca: (B, n, n)` or `(B, n, n, d)`, `Cb: (B, m, m)` or `(B, m, m, d)`; optional fused cost `M: (B, n, m)` | `OTResult` with `plan`, `value`, `value_linear`, `value_quad`, `potentials`, `log` |

Related validation helpers include `ot.batch.loss_linear_batch(M, T)`, `ot.batch.loss_linear_samples_batch(X, Y, T, metric='sqeuclidean')`, `ot.batch.tensor_batch(...)`, and `ot.batch.loss_quadratic_batch(...)`.

## Shape and data contracts

### Shared batch axis

- Use `B` as the leading batch dimension. All batched inputs must share the same `B`.
- `M[b]` is the cost matrix for problem `b`.
- `a[b]` and `b[b]` are the source and target weights for problem `b`. If omitted, POT creates uniform weights of shape `(B, ns)` and `(B, nt)`.
- Arrays must all be from the same backend. Convert before calling POT; do not pass a NumPy `M` with Torch `a`/`b`.

### `dist_batch`

`dist_batch(X1, X2)` vectorizes `ot.dist` over `B` problems. Valid metrics are:

| Metric | Meaning | Notes |
| --- | --- | --- |
| `'sqeuclidean'` | Squared Euclidean distance | Default and common for OT costs. |
| `'euclidean'` | Euclidean distance | Uses a square root after the squared computation. |
| `'minkowski'` | Lp norm | Controlled by `p`; returns the Lp norm rather than squared distance. |
| `'kl'` | KL-style feature divergence | Inputs should be positive feature/probability vectors; normalize if they represent distributions. |

### `solve_batch` methods

| Parameter | Valid values | Behavior |
| --- | --- | --- |
| `method` | `'auto'`, `'proximal'`, `'log_sinkhorn'`, `'sinkhorn'` | `auto` selects `'proximal'` when `reg is None` or `reg == 0`, otherwise `'log_sinkhorn'`. Sinkhorn methods require `reg > 0`. |
| `reg_type` | `'entropy'`, `'kl'` | Batch API validation expects lowercase strings. Use `'entropy'` for negative entropy regularization or `'kl'` for KL to the independent-product reference. |
| `grad` | `'detach'`, `'autodiff'`, `'last_step'`, `'envelope'` | `detach` is fastest/no gradients; `autodiff` differentiates plan/value/value_linear but can be memory-heavy; `last_step` saves memory by differentiating only the last iteration; `envelope` differentiates only `value` and is the default. |
| `inner_iter`, `inner_reg` | positive iteration/count and regularization values | Used by the proximal method, especially when `reg` is absent or zero. |

Use `grad='detach'` for pure validation scripts. Use `grad='envelope'` for value-based learning objectives. Use `grad='autodiff'` or `'last_step'` only after memory has been checked on a tiny fixture.

### `solve_gromov_batch` specifics

- Pure GW: pass `Ca`, `Cb`, leave `M=None` and `alpha=None`.
- Fused GW: pass `M` with shape `(B, n, m)` and an explicit `alpha` in `[0, 1]`.
- `loss='sqeuclidean'` is the default. For `loss='kl'`, the cost features must be positive unless using logits; pass `logits=True` or `False` explicitly for KL workflows.
- `symmetric=None` asks POT to test symmetry. Set `symmetric=True` or `False` explicitly for speed and reproducibility when you know the structure matrices.
- The batch GW algorithm is proximal/entropic and is not an exact drop-in loop replacement for the non-batched conditional-gradient `ot.solve_gromov`. Validate values and plans on a tiny sample before using it for model selection.
- Use `max_iter_inner` and `tol_inner` to control the inner Bregman projection; for tiny diagnostics, low values are enough, but production accuracy may require tighter settings.

## Workflow: verify `dist_batch` against `ot.dist`

```python
import numpy as np
import ot

rng = np.random.default_rng(0)
X = rng.normal(size=(3, 4, 2))
Y = X + 0.05 * rng.normal(size=(3, 4, 2))

M_batch = ot.dist_batch(X, Y, metric="sqeuclidean")
M_loop = np.stack([ot.dist(X[i], Y[i], metric="sqeuclidean") for i in range(X.shape[0])])
np.testing.assert_allclose(M_batch, M_loop, atol=1e-12)
```

## Workflow: vectorize many small balanced OT problems

This covers the common difficult case where a user wants `solve_batch` to match a loop over `ot.solve`.

```python
import numpy as np
import ot

rng = np.random.default_rng(1)
B, n, m = 4, 3, 5
M = rng.random((B, n, m))
a = np.tile(np.array([0.2, 0.3, 0.5]), (B, 1))
b = np.tile(np.ones(m) / m, (B, 1))

loop_values = []
loop_plans = []
for i in range(B):
    res_i = ot.solve(M[i], a[i], b[i], max_iter=5000, tol=1e-6)
    loop_values.append(res_i.value_linear)
    loop_plans.append(res_i.plan)

res = ot.solve_batch(M, a=a, b=b, method="auto", max_iter=5000, tol=1e-6, grad="detach")
np.testing.assert_allclose(res.value_linear, np.asarray(loop_values), atol=1e-4)
np.testing.assert_allclose(res.plan.sum(axis=2), a, atol=1e-5)
np.testing.assert_allclose(res.plan.sum(axis=1), b, atol=1e-5)
```

If exact unregularized proximal batch plans differ slightly from a loop, compare `value_linear` and marginals first; proximal tolerances control the batched solver's approximation.

## Workflow: regularized sample-cloud batch

```python
import numpy as np
import ot

rng = np.random.default_rng(2)
X = rng.normal(size=(3, 4, 2))
Y = X + 0.2 * rng.normal(size=(3, 5, 2))
a = np.full((3, 4), 1.0 / 4)
b = np.full((3, 5), 1.0 / 5)

res_samples = ot.solve_sample_batch(
    X,
    Y,
    a=a,
    b=b,
    metric="sqeuclidean",
    reg=0.5,
    method="log_sinkhorn",
    reg_type="entropy",
    max_iter=1000,
    tol=1e-6,
    grad="detach",
)
M = ot.dist_batch(X, Y)
res_matrix = ot.solve_batch(M, a=a, b=b, reg=0.5, method="log_sinkhorn", max_iter=1000, tol=1e-6, grad="detach")
np.testing.assert_allclose(res_samples.value_linear, res_matrix.value_linear, atol=1e-6)
```

## Workflow: tiny batched GW smoke

```python
import numpy as np
import ot

rng = np.random.default_rng(3)
X = rng.normal(size=(2, 4, 2))
Y = X[:, [1, 0, 3, 2], :] + 0.01 * rng.normal(size=(2, 4, 2))
Ca = ot.dist_batch(X, X)
Cb = ot.dist_batch(Y, Y)

res = ot.solve_gromov_batch(
    Ca,
    Cb,
    reg=0.5,
    symmetric=True,
    max_iter=20,
    max_iter_inner=200,
    tol=1e-5,
    tol_inner=1e-5,
    grad="detach",
)
assert res.plan.shape == (2, 4, 4)
np.testing.assert_allclose(res.plan.sum(axis=2), np.full((2, 4), 0.25), atol=1e-3)
np.testing.assert_allclose(res.plan.sum(axis=1), np.full((2, 4), 0.25), atol=1e-3)
assert np.isfinite(res.value).all()
```

## Validation checklist

After any batched solve:

1. Check `res.plan.shape == (B, ns, nt)` or `(B, n, m)` for GW.
2. Check `res.value.shape == (B,)` and `np.isfinite(ot.backend.to_numpy(res.value)).all()`.
3. For balanced OT, verify row marginals `res.plan.sum(axis=2) ≈ a` and column marginals `res.plan.sum(axis=1) ≈ b`.
4. Recompute linear value with `ot.batch.loss_linear_batch(M, res.plan)` when a cost matrix is available.
5. For sample batches, confirm `ot.dist_batch(X_a, X_b, metric=...)` has the expected shape before solving.
6. Compare a small batch against a loop over `ot.solve` or `ot.dist` before scaling; do not rely on speedups without correctness checks.
7. For optional backends, convert the validation quantities with `ot.backend.to_numpy` for assertions, but keep differentiable training losses in the original backend.
