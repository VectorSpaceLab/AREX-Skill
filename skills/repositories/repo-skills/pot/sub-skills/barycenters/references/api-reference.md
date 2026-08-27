# POT barycenter API reference

Use this reference when selecting an API, checking data shapes, or interpreting a barycenter result. The signatures below were verified against POT `0.9.7.post1`; optional non-NumPy backends were not part of the minimum runtime check.

## Fixed-support histogram barycenters

Fixed-support APIs assume every input distribution is already represented on the same support/grid.

| API | Main signature | Input contract | Return contract | Notes |
| --- | --- | --- | --- | --- |
| `ot.bregman.barycenter` | `barycenter(A, M, reg, weights=None, method='sinkhorn', numItermax=10000, stopThr=0.0001, verbose=False, log=False, warn=True, **kwargs)` | `A` has shape `(n_bins, n_hists)`: each histogram is a **column**. `M` has shape `(n_bins, n_bins)`. `reg > 0`. `weights` has length `n_hists` and should be nonnegative and sum to one. | Barycenter histogram shape `(n_bins,)`; if `log=True`, returns `(barycenter, log)` with error history and iteration count. | Methods are `sinkhorn`, `sinkhorn_stabilized`, and `sinkhorn_log`. Use stabilized/log variants when small `reg` causes numerical problems. |
| `ot.bregman.barycenter_debiased` | `barycenter_debiased(A, M, reg, weights=None, method='sinkhorn', numItermax=10000, stopThr=0.0001, verbose=False, log=False, warn=True, **kwargs)` | Same `A`, `M`, `reg`, and `weights` contract as `ot.bregman.barycenter`. | Barycenter histogram shape `(n_bins,)`; optional `(barycenter, log)`. | Uses a debiased Sinkhorn-divergence objective. Prefer it when ordinary entropic barycenters become too diffuse at usable `reg`. |
| `ot.lp.barycenter` | `barycenter(A, M, weights=None, verbose=False, log=False, solver='highs-ipm')` | Same fixed-grid `A` and square cost matrix `M`. Best for small problems because the LP scales poorly in memory and time. | Barycenter histogram shape `(n_bins,)`; if `log=True`, returns `(barycenter, solver_result)`. | Default SciPy `highs-ipm` is available in the base install. `cvxopt`/GLPK/MOSEK paths are optional and should not be assumed. |

### Fixed-support checklist

- Normalize each histogram column: `A = A / A.sum(axis=0, keepdims=True)` when the columns are nonzero.
- If your data is shaped `(n_hists, n_bins)`, transpose once before calling these APIs.
- Build `M` with a real metric, for example `M = ot.dist(x, x)` on support coordinates, then optionally normalize it by `M.max()`.
- For tiny exact-vs-regularized sanity checks, run `python scripts/barycenter_smoke.py --case fixed-support`.

## Free-support barycenters over discrete measures

Free-support solvers optimize barycenter locations while keeping barycenter weights fixed unless the selected advanced method explicitly changes them.

| API | Main signature | Input contract | Return contract | Notes |
| --- | --- | --- | --- | --- |
| `ot.lp.free_support_barycenter` | `free_support_barycenter(measures_locations, measures_weights, X_init, b=None, weights=None, numItermax=100, stopThr=1e-07, verbose=False, log=None, numThreads=1)` | `measures_locations` is a list of arrays `(k_i, d)`. `measures_weights` is a list of arrays `(k_i,)` matching each location array and usually summing to one. `X_init` has shape `(k, d)`. `b` has shape `(k,)`; default is uniform. `weights` has length `n_measures`; default is uniform. | Barycenter support locations `X` with shape `(k, d)`; if `log=True`, returns `(X, log)` with displacement norms. | Exact 2-Wasserstein fixed-point updates. `numThreads` is a compatibility parameter and should not be used as a performance promise. |
| `ot.bregman.free_support_sinkhorn_barycenter` | `free_support_sinkhorn_barycenter(measures_locations, measures_weights, X_init, reg, b=None, weights=None, numItermax=100, numInnerItermax=1000, stopThr=1e-07, verbose=False, log=None, **kwargs)` | Same list-of-clouds contract as exact free support, plus entropic `reg > 0`. | Barycenter support locations `X` with shape `(k, d)`; if `log=True`, returns `(X, log)` with displacement norms. | Uses Sinkhorn for each inner transport plan. Tune both outer `numItermax` and inner `numInnerItermax` when convergence is poor. |

Related advanced free-support APIs include `ot.lp.generalized_free_support_barycenter` for measures living in different projected subspaces and `ot.lp.free_support_barycenter_generic_costs` for generic cost functions. Use them only when the basic Euclidean free-support contract is insufficient; callable generic-cost workflows may require a PyTorch backend or an explicit `ground_bary` function.

For a tiny exact/Sinkhorn free-support sanity check, run `python scripts/barycenter_smoke.py --case free-support`.

## Sample-cloud barycenter API

Use `ot.solvers.solve_bary_sample` when the measures are sample clouds and the barycenter support must be learned. This is the clearest route for unequal sample counts.

```python
ot.solvers.solve_bary_sample(
    X_a_list,
    n,
    a_list=None,
    w=None,
    X_b_init=None,
    b=None,
    metric='sqeuclidean',
    reg=None,
    c=None,
    reg_type='KL',
    unbalanced=None,
    unbalanced_type='KL',
    lazy=False,
    method=None,
    auto_bary_method='L2_barycentric_proj',
    warmstart=True,
    stopping_criterion='loss',
    max_iter_bary=1000,
    tol_bary=1e-05,
    random_state=0,
    verbose=False,
    **kwargs,
)
```

Input contract:

- `X_a_list`: list of arrays `(n_i, d)`; `n_i` may differ across distributions.
- `n`: number of barycenter support points to learn.
- `a_list`: optional list of source weights `(n_i,)`; defaults to uniform for each cloud.
- `w`: barycentric coefficients of length `len(X_a_list)`; defaults to uniform.
- `X_b_init`: optional initialization `(n, d)`; if absent, POT uses a deterministic `random_state`.
- `b`: optional barycenter weights `(n,)`; defaults to uniform.
- `metric`: `sqeuclidean` or `euclidean` for closed-form barycenter updates. Callable metrics are balanced-only and require backend-specific care.
- `reg`, `reg_type`, `unbalanced`, and `unbalanced_type`: passed to the inner `ot.solve_sample` problems.
- `lazy=True` is not implemented for this barycenter solver.

Return contract:

- Returns a `BaryResult` with `X`, `b`, `value`, `value_linear`, `log`, and `list_res`.
- `res.X` is the learned barycenter support `(n, d)`.
- `res.b` is the barycenter weight vector `(n,)`.
- `res.list_res[k]` is an `OTResult` for source cloud `k`; inspect `plan`, `value`, `value_linear`, `marginals`, and `potentials` for per-source validation.
- `res.log['stopping_criterion']` is available because the implementation records the BCD criterion by default.

Specialized `method` values such as `1d`, `gaussian`, `gaussian_hd`, `lowrank`, `nystroem`, `factored`, `geomloss`, `sliced`, `max_sliced`, and `bsp` route through sample-OT variants. For Gaussian, GMM, sliced, low-rank, or large-scale approximation tasks, consult the `sliced-gaussian-large-scale` sub-skill before relying on this barycenter reference alone.

For a tiny deterministic `BaryResult` sanity check, run `python scripts/barycenter_smoke.py --case sample-cloud`.

## Convolutional and debiased image barycenters

Use these when images lie on a common 2D regular grid and can be stacked on axis 0.

| API | Main signature | Input contract | Return contract | Notes |
| --- | --- | --- | --- | --- |
| `ot.bregman.convolutional_barycenter2d` | `convolutional_barycenter2d(A, reg, weights=None, method='sinkhorn', numItermax=10000, stopThr=0.0001, verbose=False, log=False, warn=True, **kwargs)` | `A` has shape `(n_hists, height, width)` and each image should be nonnegative and normalized. `weights` has length `n_hists`. | Image barycenter shape `(height, width)`; optional `(image, log)`. | Methods are `sinkhorn` and `sinkhorn_log`. The log-domain implementation is not available for JAX/TF arrays. |
| `ot.bregman.convolutional_barycenter2d_debiased` | `convolutional_barycenter2d_debiased(A, reg, weights=None, method='sinkhorn', numItermax=10000, stopThr=0.001, verbose=False, log=False, warn=True, **kwargs)` | Same stacked-image contract. | Image barycenter shape `(height, width)`; optional `(image, log)`. | Uses debiased Sinkhorn scaling for images; useful when ordinary convolutional barycenters are visibly over-smoothed. |

For a tiny image sanity check, run `python scripts/barycenter_smoke.py --case convolutional`.

## Cross-links to other barycenter families

- Gaussian Bures-Wasserstein barycenter: `ot.gaussian.bures_wasserstein_barycenter(m, C, weights=None, method='fixed_point', num_iter=1000, eps=1e-07, log=False, step_size=1, batch_size=None)`. Treat this as a Gaussian/GMM-family workflow, not a histogram-grid barycenter.
- GMM barycenter: `ot.gmm.gmm_barycenter_fixed_point(means_list, covs_list, w_list, means_init, covs_init, weights, w_bar=None, iterations=100, log=False, barycentric_proj_method='euclidean')`. Route detailed GMM setup to the `sliced-gaussian-large-scale` sub-skill.
- Graph or structured barycenters: use the `gromov` sub-skill and GW/FGW barycenter APIs such as `ot.gromov.gromov_barycenters` or `ot.gromov.fgw_barycenters`.
