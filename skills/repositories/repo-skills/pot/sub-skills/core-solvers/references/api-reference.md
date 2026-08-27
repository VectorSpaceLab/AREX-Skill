# Core Solver API Reference

This reference is for POT `0.9.7.post1` with import root `ot`. The minimum verified runtime used NumPy only; PyTorch, JAX, TensorFlow, CuPy, GeomLoss, plotting, and other extras are optional and must be verified separately before relying on backend-specific gradients, GPU execution, or lazy GeomLoss behavior.

## Core data conventions

- Histograms `a` and `b` are one-dimensional nonnegative weights. For balanced OT, they must have the same total mass; most examples use the simplex convention `a.sum() == b.sum() == 1`.
- `ot.solve` and `ot.solve_sample` use uniform weights when `a` or `b` is `None`. Classical `ot.emd`/`ot.emd2` also use uniform weights when empty lists are passed.
- A cost matrix `M` has shape `(len(a), len(b))`; `M[i, j]` is the cost of moving one unit of source mass `i` to target mass `j`.
- Sample matrices `X_a` and `X_b` have rows as samples and columns as features. `ot.solve_sample` computes `M = ot.dist(X_a, X_b, metric=...)` unless a lazy or method-specific path is selected.
- `ot.dist` defaults to squared Euclidean distance. If you compute `M = ot.dist(X, Y)` and call `ot.emd2`, the returned value is the squared Wasserstein-2 objective; take a square root only when the task asks for the metric `W_2` rather than the OT objective.
- Negative weights, NaNs, infs, and all-zero weights should be rejected before calling POT. Zero-weight entries are handled in several solvers but often complicate dual potentials and diagnostics.

## Unified result object (`OTResult`)

`ot.solve` and `ot.solve_sample` return an `OTResult`-style object with these commonly useful properties:

| Property | Meaning | Notes |
| --- | --- | --- |
| `plan` | Dense transport plan | For sparse/lazy results this may materialize a dense array; check memory first. |
| `sparse_plan` | Sparse transport plan | Available or derived when a sparse plan is returned. |
| `lazy_plan` | Symbolic/lazy plan | Used by lazy sample solvers; slice only small parts unless materialization is intended. |
| `value` | Full objective value | For exact balanced OT this equals the linear cost. For unified entropic/L2 solves it includes the regularization term. |
| `value_linear` | `sum(plan * M)` linear cost | Use this when comparing unified regularized results against `sinkhorn2` or a manually computed linear cost. |
| `potentials`, `potential_a`, `potential_b` | Dual potentials | Exact EMD and Sinkhorn-style solves provide two potential arrays when available. |
| `marginal_a`, `marginal_b`, `marginals` | Row/column sums of the plan | For balanced OT, validate against `a` and `b` within solver tolerance. |
| `status` | Solver status text or code | Exact balanced `solve` reports `"Converged"` when the native status is clean. |
| `log` | Solver-specific diagnostics | Keys differ by solver; inspect defensively. |

Validation pattern:

```python
res = ot.solve(M, a, b)
assert res.plan.shape == M.shape
np.testing.assert_allclose(res.marginal_a, a, atol=1e-8)
np.testing.assert_allclose(res.marginal_b, b, atol=1e-8)
np.testing.assert_allclose(res.value, np.sum(res.plan * M), atol=1e-10)
```

## Unified balanced OT APIs

### `ot.solve`

Verified signature:

```python
ot.solve(M, a=None, b=None, reg=None, c=None, reg_type='KL', unbalanced=None, unbalanced_type='KL', method=None, n_threads=1, max_iter=None, plan_init=None, potentials_init=None, tol=None, verbose=False, grad='autodiff')
```

Core balanced routes:

| Parameters | Solver route | Main outputs | Notes |
| --- | --- | --- | --- |
| `reg=None` or `reg=0`, `unbalanced=None` | Exact network-simplex OT through the EMD backend | `plan`, `value`, `value_linear`, `potentials`, `status` | `max_iter` defaults internally to a large EMD limit; `n_threads` is forwarded to the classical EMD compatibility parameter. |
| `reg>0`, `reg_type='KL'` or `'entropy'` | Entropic regularized OT | Dense `plan`, `value`, `value_linear`, log-domain potentials | The unified balanced branch uses a log-domain Sinkhorn implementation. |
| `reg>0`, `reg_type='L2'` | Quadratic/L2 regularized OT | Dense `plan`, `value`, `value_linear`, dual potentials | Useful when a denser-than-EMD but less fully entropic plan is desired. |
| `reg>0`, `reg_type=(f, df)` | Conditional-gradient generic regularization | Dense `plan`, `value`, `value_linear` | `f(G)` and `df(G)` must be deterministic functions of the plan. |

`method` values accepted by `ot.solve` are `sinkhorn`, `sinkhorn_log`, `mm`, and `lbfgsb`; invalid values raise `ValueError`. For balanced regularized `ot.solve`, use `reg`, `reg_type`, `tol`, and `max_iter` as the main controls; the `method` argument is primarily relevant to unbalanced branches, which are routed to `unbalanced-partial`.

`grad` controls differentiable-backend memory for Sinkhorn branches:

- `'autodiff'`: differentiates through all Sinkhorn iterations and outputs; highest memory.
- `'envelope'`: gradients for `value` only, often much lower memory.
- `'last_step'`: differentiates the final Sinkhorn step; requires `max_iter > 0`.
- `'detach'`: no Sinkhorn gradients.

The minimum verified backend is NumPy, so treat non-NumPy gradient claims as optional until checked in the target backend.

### `ot.solve_sample`

Verified signature:

```python
ot.solve_sample(X_a, X_b, a=None, b=None, metric='sqeuclidean', reg=None, c=None, reg_type='KL', unbalanced=None, unbalanced_type='KL', lazy=False, batch_size=None, method=None, n_threads=1, max_iter=None, plan_init=None, rank=100, scaling=0.95, potentials_init=None, X_init=None, tol=None, verbose=False, grad='autodiff', random_state=None, debias=False, n_projections=50, projections=None, scaler=None)
```

Core balanced routes:

| Parameters | Solver route | Main outputs | Notes |
| --- | --- | --- | --- |
| `method=None`, `lazy=False` | Computes `M = ot.dist(X_a, X_b, metric)` then calls `ot.solve` | Dense `plan`, `value`, `value_linear`, potentials | Best default for small/medium sample clouds. |
| `method=None`, `lazy=True`, `reg=None`, balanced | Lazy exact EMD with on-the-fly distances | `value`, sparse/lazy-derived plan, potentials | Avoids precomputing the full cost matrix but dense plan access can still be expensive. |
| `method=None`, `lazy=True`, `reg>0`, balanced | Lazy empirical Sinkhorn | `value_linear`, `lazy_plan`, potentials | Use `batch_size` to limit memory. |
| `method='1d'` | 1D Wasserstein helper per feature | `value` only | For `metric='sqeuclidean'` uses `p=2`; for `metric='euclidean'`/`'cityblock'` uses `p=1`. |

Other `solve_sample` method names recognized by POT include `gaussian`, `gaussian_hd`, `lowrank`, `nystroem`, `factored`, `geomloss`, `geomloss_auto`, `geomloss_tensorized`, `geomloss_online`, `geomloss_multiscale`, `sliced`, `max_sliced`, and `bsp`. Route substantive use of those approximation or large-scale families to `sliced-gaussian-large-scale`; keep only the entry-point recognition here.

Invalid `solve_sample(method=...)` raises `ValueError`. Method-specific metric incompatibilities raise `NotImplementedError`.

## Classical exact EMD APIs

### `ot.emd`

Verified signature:

```python
ot.emd(a, b, M, numItermax=100000, log=False, center_dual=True, numThreads=1, check_marginals=True, potentials_init=None)
```

Returns the optimal transport plan. With `log=True`, returns `(G, log)` where `log` includes `cost`, dual potentials `u`/`v`, and status fields. Dense cost matrices should be numeric and compatible with shape `(len(a), len(b))`. Sparse cost matrices are supported for compatible backends; sparse inputs return sparse plans.

`check_marginals=True` raises an assertion if `a.sum()` and `b.sum()` differ. If you intentionally have different masses, route to `unbalanced-partial` rather than disabling the check for a balanced workflow.

`numThreads` is retained for compatibility but the network simplex solver no longer uses OpenMP; values other than `1` can emit a deprecation warning and should not be used as a performance promise.

### `ot.emd2`

Verified signature:

```python
ot.emd2(a, b, M, processes=1, numItermax=100000, log=False, return_matrix=False, center_dual=True, numThreads=1, check_marginals=True, potentials_init=None)
```

Returns the optimal linear cost. With `log=True`, returns `(cost, log)` for a single target histogram; when `b` is a matrix of several target histograms, it returns a list-like collection. Set `return_matrix=True` to include the optimal plan under `log['G']`.

`processes` is deprecated; run parallelism outside POT if needed.

## Classical Sinkhorn APIs

### `ot.sinkhorn`

Verified signature:

```python
ot.sinkhorn(a, b, M, reg, method='sinkhorn', numItermax=1000, stopThr=1e-09, verbose=False, log=False, warn=True, warmstart=None, **kwargs)
```

Returns the entropic regularized transport plan. `reg` must be positive for Sinkhorn. Supported `method` values include:

- `sinkhorn`: classic Sinkhorn-Knopp scaling.
- `sinkhorn_log`: log-domain scaling; useful for small regularization or differentiable-backend stability.
- `sinkhorn_stabilized`: stabilized Sinkhorn; useful when standard scaling has numerical issues.
- `sinkhorn_epsilon_scaling`: decreasing-regularization schedule; useful for sharper plans.
- `greenkhorn`: greedy coordinate updates; not supported for JAX or TensorFlow arrays.
- `screenkhorn`: exposed through `ot.bregman.screenkhorn`, not the top-level `ot.sinkhorn` wrapper.

`warmstart` is a pair of log scaling vectors for Sinkhorn variants. For warm starts from exact EMD duals, pass the dual pair only after confirming shapes and solver semantics.

### `ot.sinkhorn2`

Verified signature:

```python
ot.sinkhorn2(a, b, M, reg, method='sinkhorn', numItermax=1000, stopThr=1e-09, verbose=False, log=False, warn=False, warmstart=None, **kwargs)
```

Returns the linear loss `sum(G * M)` for the entropic plan, not the full entropic objective. For unified `ot.solve(..., reg=...)`, compare `solve_result.value_linear` to `ot.sinkhorn2(...)`, not necessarily `solve_result.value`.

## Cost and weight utilities

Verified signatures:

```python
ot.dist(x1, x2=None, metric='sqeuclidean', p=2, w=None, backend='auto', nx=None, use_tensor=False)
ot.unif(n, type_as=None)
```

Use `ot.unif(n)` for a uniform simplex vector. Use `ot.dist(X, Y, metric='sqeuclidean')` for default squared Euclidean costs, `metric='euclidean'` for Wasserstein-1 style costs on sample locations, `metric='cityblock'` for Manhattan costs, and `metric='minkowski', p=...` where supported. Some scipy distance names are NumPy/scipy-only and may not work on other backends.

## 1D and circle helpers

Additional core-helper signatures verified by inspection:

```python
ot.emd_1d(x_a, x_b, a=None, b=None, metric='sqeuclidean', p=1.0, dense=True, log=False, check_marginals=True)
ot.emd2_1d(x_a, x_b, a=None, b=None, metric='sqeuclidean', p=1.0, dense=True, log=False)
ot.wasserstein_1d(u_values, v_values, u_weights=None, v_weights=None, p=1, require_sort=True, return_plans=False)
ot.wasserstein_circle(u_values, v_values, u_weights=None, v_weights=None, p=1, Lm=10, Lp=10, tm=-1, tp=1, eps=1e-06, require_sort=True)
ot.binary_search_circle(u_values, v_values, u_weights=None, v_weights=None, p=1, Lm=10, Lp=10, tm=-1, tp=1, eps=1e-06, require_sort=True, log=False)
ot.semidiscrete_wasserstein2_unif_circle(u_values, u_weights=None)
```

Use `emd_1d`/`emd2_1d` when samples are truly one-dimensional and a plan or cost is needed. Supported 1D metrics are `sqeuclidean`, `minkowski`, `cityblock`, and `euclidean`; other strings raise `ValueError`.

Use `wasserstein_1d` when you need backend-friendly or differentiable computation of the 1D OT loss `W_p^p`; set `return_plans=True` or `"coo_tuple"` only when you need sparse plan details.

Circle helpers expect coordinates on `[0, 1)` and reduce values modulo `1`. If points are on the unit circle in 2D, convert them to circular coordinates before calling these helpers. TensorFlow and JAX are not reliable targets for the circle binary-search implementation; use NumPy unless another backend has been verified.

## Sparse and lazy helper notes

- Sparse EMD treats absent edges as forbidden/infinite cost. The sparse graph must contain a feasible transport path for the requested marginals.
- NumPy sparse workflows use SciPy sparse COO-style matrices. JAX and TensorFlow sparse matrices are not supported by the exact sparse EMD path.
- `ot.solve_sample(..., lazy=True)` can reduce cost-matrix memory, but materializing `res.plan`, `res.sparse_plan`, or `res.lazy_plan[:]` can still create large arrays.
- Optional GeomLoss methods require the external `geomloss` package and are not part of the minimum verified backend.
