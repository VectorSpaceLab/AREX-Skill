# API reference: sliced, Gaussian, GMM, and large-scale POT alternatives

This reference is the quick API map for the `sliced-gaussian-large-scale` sub-skill. It is intentionally self-contained: use the signatures and validation notes here instead of reopening POT source examples.

## Verified runtime baseline

- Public distribution/import: `POT`, import root `ot`.
- Verified package version for this skill draft: `0.9.7.post1`.
- Minimum prepared backend: NumPy/CPU. Optional PyTorch, JAX, TensorFlow, CuPy, plotting, DR, GNN, and broad extras are optional and were not verified for this sub-skill.
- Most APIs accept backend arrays, but the guidance below assumes NumPy unless it explicitly says otherwise.

## Common conventions

| Concept | Expected shape/meaning | Validation before scaling |
| --- | --- | --- |
| Sample clouds | `X_s`/`X_t` shaped `(n_source, dim)` and `(n_target, dim)` | Same `dim`; finite values; normalize features when scales differ. |
| Histograms | `a`/`b` shaped `(n_source,)` and `(n_target,)`; uniform when `None` for many APIs | Nonnegative, finite, sum to 1 when using balanced solvers. |
| Projection matrix | Usually `(dim, n_projections)` for Euclidean sliced; `(n_projections, dim, 2)` for spherical sliced | If passed explicitly, `seed` and `n_projections` no longer control projection sampling. |
| Gaussian means/covariances | Means `(d,)`, `(1, d)`, or batched `(k, d)`; covariances `(d, d)` or `(k, d, d)` | Symmetric PSD covariances; add small diagonal jitter only as a documented numerical repair. |
| GMM parameters | Means `(k, d)`, covariances `(k, d, d)`, weights `(k,)` per mixture | Component counts must agree with weights and covariance leading dimensions. |
| `log=True` | Adds a second or third returned object depending on the function | Keep code branch-specific: do not unpack logs when `log=False`. |

## High-level sample solver shortcuts

Use `ot.solve_sample` when a task wants POT's unified sample-cloud result object but should avoid dense exact OT.

```python
ot.solve_sample(
    X_a, X_b, a=None, b=None, metric="sqeuclidean", reg=None, c=None,
    reg_type="KL", unbalanced=None, unbalanced_type="KL", lazy=False,
    batch_size=None, method=None, n_threads=1, max_iter=None,
    plan_init=None, rank=100, scaling=0.95, potentials_init=None,
    X_init=None, tol=None, verbose=False, grad="autodiff", random_state=None,
    debias=False, n_projections=50, projections=None, scaler=None,
)
```

Typical approximation-oriented `method` choices for this sub-skill are `"sliced"`, `"max_sliced"`, `"lowrank"`, `"nystroem"`, `"factored"`, `"gaussian"`, and `"bsp"` when supported by the installed POT version. Validate the returned `OTResult` attributes on a small problem before relying on the result at scale. For exact EMD/Sinkhorn fundamentals, route to `core-solvers`.

## Sliced Wasserstein distances and plans

| API | Signature | Returns | Use when |
| --- | --- | --- | --- |
| `ot.sliced.sliced_wasserstein_distance` | `(X_s, X_t, a=None, b=None, n_projections=50, p=2, projections=None, seed=None, log=False, scaler=None)` | Scalar cost; with `log=True`, `(cost, log)` where `log` has projections and projected EMDs | Fast Monte Carlo approximation of high-dimensional Wasserstein distance. |
| `ot.sliced.max_sliced_wasserstein_distance` | `(X_s, X_t, a=None, b=None, n_projections=50, p=2, projections=None, seed=None, log=False, scaler=None)` | Scalar max-sliced cost; optional log | A stronger but still projection-based discrepancy. |
| `ot.sliced.sliced_wasserstein_sphere` | `(X_s, X_t, a=None, b=None, n_projections=50, p=2, projections=None, seed=None, log=False)` | Scalar spherical sliced cost; optional log | Samples lie on a sphere and should be compared through spherical projections. |
| `ot.sliced.sliced_wasserstein_sphere_unif` | `(X_s, a=None, n_projections=50, projections=None, seed=None, log=False)` | Scalar distance-to-uniform on the sphere; optional log | Compare one spherical sample cloud to the uniform spherical distribution. |
| `ot.sliced.linear_sliced_wasserstein_sphere` | `(X_s, X_t=None, a=None, b=None, n_projections=50, projections=None, seed=None, log=False)` | Scalar linear spherical sliced cost; optional log | Linearized spherical sliced discrepancy. |
| `ot.sliced.sliced_plans` | `(X_s, X_t, a=None, b=None, metric="sqeuclidean", p=1, projections=None, n_projections=None, seed=None, batch_size=None, log=False)` | Per-projection plans/permutations depending on weights and dimensions | Inspect or reuse individual one-dimensional projected couplings. |
| `ot.sliced.min_sliced_transport_plan` | `(X_s, X_t, a=None, b=None, projections=None, metric="sqeuclidean", p=2, n_projections=None, seed=None, batch_size=None, dense=True, log=False)` | `(plan, cost)` or `(plan, cost, log)` | Approximate a transport plan by keeping the best projected plan. |
| `ot.sliced.expected_sliced_plan` | `(X_s, X_t, a=None, b=None, projections=None, metric="sqeuclidean", p=2, n_projections=None, beta=0.0, seed=None, dense=True, batch_size=None, log=False)` | `(plan, cost)` or `(plan, cost, log)` | Average projected plans; increase `beta` to move toward the min-sliced plan. |

Top-level aliases such as `ot.sliced_wasserstein_distance` and `ot.min_sliced_transport_plan` may be available, but module-qualified names are clearer in generated code.

### Sliced API notes

- `n_projections` trades speed for variance. Fix `seed` or pass `projections` for reproducibility.
- `scaler` can be an `ot.utils.DataScaler` or callable for Euclidean sliced distances; fit it once on representative data to avoid batch-wise normalization drift.
- `metric` for sliced plans is limited to `"sqeuclidean"`, `"minkowski"`, `"cityblock"`, or `"euclidean"`.
- `dense=False` can return a sparse `coo_matrix` for sliced plans under NumPy/SciPy. Some optional tensor backends may return only dense plans.
- For spherical sliced, normalize rows onto the unit sphere before calling the API.

## Gaussian and Bures-Wasserstein APIs

| API | Signature | Returns | Use when |
| --- | --- | --- | --- |
| `ot.gaussian.bures_wasserstein_distance` | `(ms, mt, Cs, Ct, paired=False, log=False)` | Scalar, cross-distance matrix, or paired vector; optional log | Closed-form W2 distance between Gaussian distributions. |
| `ot.gaussian.bures_wasserstein_mapping` | `(ms, mt, Cs, Ct, log=False)` | `(A, b)` or `(A, b, log)` | Affine optimal map `x -> x @ A + b` between Gaussian distributions. |
| `ot.gaussian.bures_wasserstein_distance_hd` | `(ms, mt, Us, Ut, ls, lt, sigma2_s, sigma2_t, log=False)` | Scalar distance | High-dimensional covariance represented as low-rank subspace plus isotropic noise. |
| `ot.gaussian.bures_wasserstein_mapping_hd` | `(ms, mt, Us, Ut, ls, lt, sigma2_s, sigma2_t, log=False)` | `(A, b)` or `(A, b, log)` | High-dimensional affine Gaussian map without forming all covariance algebra naively. |
| `ot.gaussian.empirical_bures_wasserstein_mapping` | `(xs, xt, reg=1e-06, ws=None, wt=None, bias=True, log=False)` | `(A, b)` or `(A, b, log)` | Estimate Gaussian map from samples. |
| `ot.gaussian.empirical_bures_wasserstein_distance` | `(xs, xt, reg=1e-06, ws=None, wt=None, bias=True, log=False)` | Scalar distance; optional log | Estimate Gaussian distance from samples. |
| `ot.gaussian.bures_wasserstein_barycenter` | `(m, C, weights=None, method="fixed_point", num_iter=1000, eps=1e-07, log=False, step_size=1, batch_size=None)` | `(mean, covariance)` or `(mean, covariance, log)` | Bures barycenter of Gaussian distributions. |
| `ot.gaussian.gaussian_gromov_wasserstein_distance` | `(Cov_s, Cov_t, log=False)` | Scalar; optional log | Structured Gaussian/Gromov comparison by covariance. |
| `ot.gaussian.gaussian_gromov_wasserstein_mapping` | `(mu_s, mu_t, Cov_s, Cov_t, sign_eigs=None, log=False)` | Mapping objects/arrays; optional log | Gaussian Gromov map when covariance structures, not point locations alone, matter. |

### Gaussian API notes

- `bures_wasserstein_distance` supports scalar and batched/cross-distance shapes. Set `paired=True` only when the source and target batches align one-to-one.
- `bures_wasserstein_mapping` returns an affine map. If samples are stored row-wise, POT examples/tests apply it as `X_mapped = X @ A + b`.
- High-dimensional helpers expect orthogonal subspace matrices `U*`, principal variances `l*`, and residual variances `sigma2_*`; they are for the covariance model `U diag(l) U.T + sigma2 I`.

## GMM APIs

| API | Signature | Returns | Use when |
| --- | --- | --- | --- |
| `ot.gmm.gmm_ot_loss` | `(m_s, m_t, C_s, C_t, w_s, w_t, log=False)` | Scalar loss; optional log | Compare two Gaussian mixtures in component space. |
| `ot.gmm.gmm_ot_plan` | `(m_s, m_t, C_s, C_t, w_s, w_t, log=False)` | Component plan `(k_s, k_t)`; optional log | Transport between GMM components using Bures component costs. |
| `ot.gmm.gmm_ot_apply_map` | `(x, m_s, m_t, C_s, C_t, w_s, w_t, plan=None, method="bary", seed=None)` | Mapped points with same shape as `x` | Apply barycentric or random GMM OT map to samples. |
| `ot.gmm.gmm_ot_plan_density` | `(x, y, m_s, m_t, C_s, C_t, w_s, w_t, plan=None, atol=0.01)` | Density matrix over evaluation points | Evaluate a density-like plan on source/target grids or sample points. |
| `ot.gmm.gmm_barycenter_fixed_point` | `(means_list, covs_list, w_list, means_init, covs_init, weights, w_bar=None, iterations=100, log=False, barycentric_proj_method="euclidean")` | `(means, covs)` or `(means, covs, log)` | Fixed-point barycenter of GMMs with chosen barycenter component count. |

GMM component weights must be nonnegative and should sum to one for each mixture. The component plan should satisfy `plan.sum(axis=1) == w_s` and `plan.sum(axis=0) == w_t` up to numerical tolerance.

## Low-rank, factored, BSP, semidiscrete, SGOT, COOT, and stochastic APIs

| Family | API | Signature | Return shape/meaning |
| --- | --- | --- | --- |
| Low-rank couplings | `ot.lowrank.lowrank_sinkhorn` | `(X_s, X_t, a=None, b=None, reg=0, rank=None, alpha=1e-10, rescale_cost=True, init="random", reg_init=0.1, seed_init=49, gamma_init="rescale", numItermax=2000, stopThr=1e-07, warn=True, log=False)` | `Q`, `R`, `g`; with log, lazy plan and objective values. |
| Low-rank cost factors | `ot.lowrank.compute_lr_sqeuclidean_matrix` | `(X_s, X_t, rescale_cost, nx=None)` | Factors whose product reconstructs the squared Euclidean cost. |
| Nystroem kernel | `ot.lowrank.kernel_nystroem` | `(X_s, X_t, anchors=50, sigma=1.0, random_state=None)` | Left and right kernel factors. |
| Low-rank kernel Sinkhorn | `ot.lowrank.sinkhorn_low_rank_kernel` | `(K1, K2, a=None, b=None, numItermax=1000, stopThr=1e-09, verbose=False, log=False, warn=True, warmstart=None)` | Sinkhorn scaling vectors; with log, lazy plan. |
| Factored OT | `ot.factored.factored_optimal_transport` | `(Xa, Xb, a=None, b=None, reg=0.0, r=100, X0=None, stopThr=1e-07, numItermax=100, verbose=False, log=False, **kwargs)` | `Ga`, `Gb`, intermediate support `X`; optional log. |
| BSP bijection | `ot.bsp.compute_bspot_bijection` | `(X, Y, n_plans=64, p=2, initial_perm=None, gaussian_slicing="auto", seed=0)` | `(cost, perm, perms)` where `perm` maps `X[i]` to `Y[perm[i]]`. |
| BSP merge | `ot.bsp.merge_bijections` | `(X, Y, perms, p=2)` | Merged permutation/cost helper for BSP workflows. |
| Semidiscrete solver | `ot.semidiscrete.solve_semidiscrete` | `(X_target, sampler_source="unif", a_target=None, metric=None, reg=0.0, max_iter=10000, batch_size=32, lr0=None, lr_exponent=0.6666666666666666, init_potential=None, decreasing_reg=True, decreasing_reg_initial_eps=0.1, decreasing_reg_exponent=0.5, max_cost=None, polyak_average=True, log=False)` | Semi-dual potential, optional info log. |
| Semidiscrete map/weights | `ot.semidiscrete.semidiscrete_atom_weights`, `semidiscrete_ot_map`, `semidiscrete_c_transform` | `(X_target, X_source, semi_dual_potential, a_target=None, metric=None, reg=0.0)` | Row-stochastic atom weights, mapped points, or c-transform values. |
| SGOT metric | `ot.sgot.sgot_metric` | `(Ds, Rs, Ls, Dt, Rt, Lt, eta=0.5, p=2, q=1, r=2, grassmann_metric="chordal", eigen_scaling=None, Ws=None, Wt=None, nx=None, eps=1e-12)` | Nonnegative spectral-Grassmann OT distance. |
| SGOT cost matrix | `ot.sgot.sgot_cost_matrix` | `(Ds, Rs, Ls, Dt, Rt, Lt, eta=0.5, p=2, q=1, grassmann_metric="chordal", eigen_scaling=None, nx=None, eps=1e-12)` | Ground cost between spectral atoms. |
| COOT | `ot.coot.co_optimal_transport` | `(X, Y, wx_samp=None, wx_feat=None, wy_samp=None, wy_feat=None, epsilon=0, alpha=0, M_samp=None, M_feat=None, warmstart=None, nits_bcd=100, tol_bcd=1e-07, eval_bcd=1, nits_ot=500, tol_sinkhorn=1e-07, method_sinkhorn="sinkhorn", early_stopping_tol=1e-06, log=False, verbose=False)` | Sample and feature couplings; optional log. |
| COOT distance | `ot.coot.co_optimal_transport2` | Same main parameters as `co_optimal_transport` | Scalar COOT objective/distance. |
| Stochastic semidual | `ot.stochastic.solve_semi_dual_entropic` | `(a, b, M, reg, method, numItermax=10000, lr=None, log=False)` | Transport plan; optional semi-dual logs. |
| Stochastic dual | `ot.stochastic.solve_dual_entropic` | `(a, b, M, reg, batch_size, numItermax=10000, lr=1, log=False)` | Transport plan; optional dual logs. |
| Stochastic plan from potentials | `ot.stochastic.plan_dual_entropic` | `(u, v, xs, xt, reg=1, ws=None, wt=None, metric="sqeuclidean")` | Primal entropic plan from dual potentials. |
| DMMOT 1-D grid note | `ot.lp.dmmot_monge_1dgrid_optimize` | `(A, niters=100, lr_init=1e-05, lr_decay=0.995, print_rate=100, verbose=False, log=False)` | Optimized one-dimensional grid distributions; objective differs from classical barycenter. |

See [large-scale-solvers.md](large-scale-solvers.md) for selection guidance and caveats. Many of these methods save memory by avoiding a fully dense `n_source x n_target` plan, but materializing a lazy plan with `[:]` or requesting dense sliced plans still allocates the full matrix.
