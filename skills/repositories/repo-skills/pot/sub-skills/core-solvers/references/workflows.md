# Core Solver Workflows

All workflows below are self-contained and use only installed POT, NumPy, and optional SciPy for sparse matrices. They do not require plotting or downloaded data.

## Quick solver selection

| Task | Prefer | Validate |
| --- | --- | --- |
| Small/medium balanced OT with a known cost matrix | `ot.solve(M, a, b)` | `res.plan.shape`, `res.marginal_a`, `res.marginal_b`, `res.value == np.sum(res.plan * M)` |
| Small/medium balanced OT between sample clouds | `ot.solve_sample(X_a, X_b, a, b, metric=...)` | Same `OTResult` checks plus compare to `ot.solve(ot.dist(...))` when debugging. |
| Need only classical plan or cost | `ot.emd` for plan, `ot.emd2` for cost | Row/column sums; `emd2 == np.sum(emd * M)` for a deterministic fixture. |
| Entropic regularization | `ot.solve(..., reg=...)` or `ot.sinkhorn`/`sinkhorn2` | For unified API compare `res.value_linear`, not `res.value`, against `sinkhorn2`. |
| Very small `reg` or convergence warnings | `ot.sinkhorn(..., method='sinkhorn_log'/'sinkhorn_stabilized')` | Marginals and warning log; increase `reg` or `numItermax` if needed. |
| One-dimensional supports | `ot.emd_1d`, `ot.emd2_1d`, or `ot.wasserstein_1d` | Compare against dense `ot.emd2` on `ot.dist` for a tiny case. |
| Circular coordinates on `[0, 1)` | `ot.wasserstein_circle` / `ot.binary_search_circle` | Confirm weights sum to same mass and coordinates are modulo `1`. |
| Sparse feasible graph | `ot.emd(a, b, M_sparse)` / `ot.emd2` | Sparse plan row/column sums and nonnegative cost. |
| Cost matrix too large but exact balanced sample OT is still needed | `ot.solve_sample(..., lazy=True)` | Avoid dense plan materialization; validate small slices or marginals. |

Run the bundled smoke helper from this sub-skill directory:

```bash
python scripts/core_solver_smoke.py --mode all
python scripts/core_solver_smoke.py --mode exact --json
python scripts/core_solver_smoke.py --mode invalid
```

## Common validation helpers

Use explicit validation before blaming POT solver internals:

```python
import numpy as np
import ot


def as_simplex(name, w, *, expected_len=None):
    w = np.asarray(w, dtype=float)
    if w.ndim != 1:
        raise ValueError(f"{name} must be a 1D weight vector, got shape {w.shape}")
    if expected_len is not None and len(w) != expected_len:
        raise ValueError(f"{name} length {len(w)} does not match expected {expected_len}")
    if not np.all(np.isfinite(w)):
        raise ValueError(f"{name} contains NaN or inf")
    if np.any(w < 0):
        raise ValueError(f"{name} contains negative weights")
    total = w.sum()
    if total <= 0:
        raise ValueError(f"{name} has zero total mass")
    return w / total


def validate_balanced_plan(plan, a, b, *, atol=1e-8):
    plan = np.asarray(plan)
    if np.any(plan < -atol):
        raise ValueError("transport plan contains negative entries beyond tolerance")
    np.testing.assert_allclose(plan.sum(axis=1), a, atol=atol)
    np.testing.assert_allclose(plan.sum(axis=0), b, atol=atol)
```

If the task intentionally has unequal total mass or outliers, do not normalize away the scientific meaning. Route to `unbalanced-partial` and use an unbalanced or partial solver instead.

## Workflow 1: exact balanced OT from a cost matrix

```python
import numpy as np
import ot

X_a = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]])
X_b = np.array([[0.0, 0.0], [1.0, 1.0]])
a = np.array([0.25, 0.50, 0.25])
b = np.array([0.60, 0.40])
M = ot.dist(X_a, X_b, metric="sqeuclidean")

res = ot.solve(M, a, b, n_threads=1)
G_classic = ot.emd(a, b, M)
W_classic = ot.emd2(a, b, M)

validate_balanced_plan(res.plan, a, b)
np.testing.assert_allclose(res.plan, G_classic, atol=1e-10)
np.testing.assert_allclose(res.value, W_classic, atol=1e-10)
np.testing.assert_allclose(res.value, np.sum(res.plan * M), atol=1e-10)

print(res.value, res.status)
```

Notes:

- `ot.solve` is the best default when a later agent wants `OTResult` semantics.
- Use `ot.emd` when a legacy workflow expects only a plan matrix.
- Use `ot.emd2(..., log=True, return_matrix=True)` when you need a cost plus duals and the plan in one call.

## Workflow 2: convert classical sample-cloud EMD to `solve_sample`

Classical sample workflows often compute a cost matrix manually:

```python
M = ot.dist(X_a, X_b, metric="sqeuclidean")
G = ot.emd(a, b, M)
value = ot.emd2(a, b, M)
```

Convert to unified sample-cloud code when you want one result object:

```python
res = ot.solve_sample(X_a, X_b, a=a, b=b, metric="sqeuclidean", n_threads=1)

validate_balanced_plan(res.plan, a, b)
np.testing.assert_allclose(res.value, value, atol=1e-10)
np.testing.assert_allclose(res.value_linear, value, atol=1e-10)
assert res.plan.shape == (len(a), len(b))
assert res.potentials is None or len(res.potentials) == 2

# For reports, keep both the objective and correspondence information.
summary = {
    "value": float(np.asarray(res.value)),
    "value_linear": float(np.asarray(res.value_linear)),
    "plan_shape": tuple(res.plan.shape),
    "status": res.status,
}
```

Use `metric='euclidean'` when the task wants a Wasserstein-1 ground cost. Use the default `metric='sqeuclidean'` when the task wants the squared Wasserstein-2 objective.

## Workflow 3: entropic and L2 regularized OT

```python
reg = 0.25
res_sink = ot.solve(M, a, b, reg=reg, reg_type="KL", max_iter=1000, tol=1e-9, grad="detach")
G_sink = ot.sinkhorn(a, b, M, reg=reg, method="sinkhorn_log", numItermax=1000, stopThr=1e-9)
W_sink_linear = ot.sinkhorn2(a, b, M, reg=reg, method="sinkhorn_log", numItermax=1000, stopThr=1e-9)

validate_balanced_plan(res_sink.plan, a, b, atol=1e-6)
np.testing.assert_allclose(np.sum(G_sink * M), W_sink_linear, atol=1e-8)
np.testing.assert_allclose(res_sink.value_linear, W_sink_linear, atol=1e-6)

res_l2 = ot.solve(M, a, b, reg=1.0, reg_type="L2", max_iter=1000, tol=1e-9)
validate_balanced_plan(res_l2.plan, a, b, atol=1e-6)
```

Regularization choices:

- `reg_type='KL'`: default unified entropic regularization against `a b^T`.
- `reg_type='entropy'`: original Sinkhorn entropy form.
- `reg_type='L2'`: quadratic regularization.
- `reg_type=(f, df)`: custom smooth regularization for conditional gradient; keep the functions deterministic and shape-preserving.

For differentiable backends, start with `grad='envelope'` if only `value` gradients are needed. Use `grad='autodiff'` only when gradients through `plan` or all outputs are worth the extra memory. Optional backends were not verified in the minimum runtime.

## Workflow 4: diagnose invalid weights and invalid regularization mode

This covers the common difficult case where histograms are mismatched and the regularization mode is misspelled.

```python
raw_a = np.array([0.5, 0.5, 0.2])      # sums to 1.2
raw_b = np.array([0.4, 0.6])           # sums to 1.0
M = np.ones((3, 2))

try:
    a = as_simplex("a", raw_a, expected_len=M.shape[0])
    b = as_simplex("b", raw_b, expected_len=M.shape[1])
except ValueError as err:
    raise RuntimeError(f"Fix weights before solving OT: {err}")

# If normalization is scientifically valid, a and b are now comparable simplex vectors.
# If total mass difference matters, route to unbalanced-partial instead.

try:
    ot.solve(M, a, b, reg=1.0, reg_type="wrong_mode")
except NotImplementedError as err:
    raise RuntimeError("Use reg_type='KL', 'entropy', 'L2', or a (f, df) tuple") from err
```

Do not set `check_marginals=False` as a shortcut for genuinely unbalanced data. That bypasses a useful guard and may return a plan that does not match the intended problem.

## Workflow 5: 1D and circle helpers

```python
x_a = np.array([0.0, 1.0, 3.0])
x_b = np.array([0.0, 2.0])
a = np.array([0.2, 0.3, 0.5])
b = np.array([0.4, 0.6])

G_1d, log_1d = ot.emd_1d(x_a, x_b, a, b, metric="sqeuclidean", log=True)
W_1d = ot.emd2_1d(x_a, x_b, a, b, metric="sqeuclidean")
W1_loss = ot.wasserstein_1d(x_a, x_b, a, b, p=1)

validate_balanced_plan(G_1d, a, b)
np.testing.assert_allclose(W_1d, log_1d["cost"], atol=1e-12)

u = np.array([0.05, 0.25, 0.75])
v = np.array([0.10, 0.50, 0.80])
wu = np.array([0.3, 0.2, 0.5])
wv = np.array([0.3, 0.4, 0.3])
W_circle = ot.wasserstein_circle(u, v, wu, wv, p=1)
```

1D helpers are faster and can be more numerically direct for monodimensional supports. Circle helpers operate on coordinates modulo `1`; convert 2D unit-circle points to angular coordinates before use.

## Workflow 6: sparse EMD on a feasible graph

```python
import numpy as np
import ot
import scipy.sparse as sp

n = 4
a = ot.unif(n)
b = ot.unif(n)
rows = np.array([0, 1, 2, 3, 0, 1, 2, 3])
cols = np.array([0, 1, 2, 3, 1, 2, 3, 0])
data = np.array([0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0])
coo_ctor = getattr(sp, "coo_array", sp.coo_matrix)
M_sparse = coo_ctor((data, (rows, cols)), shape=(n, n))

G_sparse, log = ot.emd(a, b, M_sparse, log=True)
G_dense = G_sparse.toarray()
validate_balanced_plan(G_dense, a, b)
np.testing.assert_allclose(ot.emd2(a, b, M_sparse), log["cost"], atol=1e-12)
```

Sparse matrices encode allowed edges only. If the graph cannot satisfy the row and column masses, add feasible edges or use a dense cost matrix; do not interpret infeasibility as an ordinary convergence issue.

## Workflow 7: lazy sample-cloud exact or Sinkhorn OT

```python
# Exact balanced sample OT without precomputing M.
res_lazy_exact = ot.solve_sample(X_a, X_b, a=a, b=b, lazy=True, metric="sqeuclidean")
print(res_lazy_exact.value)

# Regularized lazy empirical Sinkhorn.
res_lazy_sink = ot.solve_sample(
    X_a,
    X_b,
    a=a,
    b=b,
    reg=0.5,
    lazy=True,
    batch_size=64,
    metric="sqeuclidean",
    max_iter=1000,
    tol=1e-8,
)
```

Avoid calling `res_lazy_sink.lazy_plan[:]` on large problems unless the task explicitly needs the dense plan. For many evaluation workflows, `value`, `value_linear`, small slices, and marginals are enough.

## Handoff checklist for later verification

For a new core-solver use case, record:

1. Inputs: cost matrix or sample clouds, shapes, metrics, and whether weights are normalized or intentionally unequal.
2. Solver family: exact, entropic, L2, 1D, circle, sparse, or lazy.
3. Parameters: `reg`, `reg_type`, `method`, `max_iter`/`numItermax`, `tol`/`stopThr`, `n_threads`/`numThreads`, warm starts, and gradient mode.
4. Validation: plan nonnegativity, row/column sums, objective recomputation, `OTResult` properties, and warnings.
5. Routing: barycenters, GW/FGW, unbalanced/partial, optional backends, batched arrays, or large-scale approximations should be handed to their owning sub-skills.
