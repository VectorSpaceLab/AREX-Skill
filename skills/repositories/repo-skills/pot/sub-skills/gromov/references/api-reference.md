# POT GW/FGW API Reference

## Purpose and verification scope

Read this reference when selecting a POT Gromov-Wasserstein API, checking parameter names/defaults, or validating solver outputs. The signatures below were verified for POT `0.9.7.post1`. The generated skill's minimum verified backend is NumPy; PyTorch, JAX, TensorFlow, CuPy, PyTorch Geometric, NetworkX, scikit-learn, and plotting extras are optional unless the user's own environment verifies them.

## Core data model

| Object | Shape | Meaning | Validation |
| --- | --- | --- | --- |
| `C1`, `Ca` | `(ns, ns)` | Source structure/cost/similarity matrix. | Square, finite, floating-point. Usually symmetric for graph distances; set `symmetric=False` for directed/asymmetric structures. |
| `C2`, `Cb` | `(nt, nt)` | Target structure/cost/similarity matrix. | Square, finite, same semantic scale as `C1`; normalize each matrix when scales differ. |
| `M` | `(ns, nt)` | Cross-space feature/linear cost for FGW. | Required for FGW; rows align to source nodes, columns to target nodes. |
| `p`, `q`, `a`, `b` | `(ns,)`, `(nt,)` | Node/sample weights. | Nonnegative, one-dimensional, lengths match structures. Balanced solvers expect equal total mass; uniform weights are used when omitted. |
| `G0`, `plan_init`, `T_init` | `(ns, nt)` | Initial coupling. | For balanced solvers it must satisfy row and column marginal constraints; otherwise POT may assert or fail early. |

### Loss naming split

POT has two naming conventions:

- Unified API: `ot.solve_gromov(..., loss="L2")` or `loss="KL"`.
- Classical `ot.gromov.*` APIs: `loss_fun="square_loss"` or `loss_fun="kl_loss"`.

Do not pass `loss_fun` to `ot.solve_gromov`, and do not pass `loss="L2"` to the classical functions.

## Unified solver: `ot.solve_gromov`

```python
ot.solve_gromov(Ca, Cb, M=None, a=None, b=None, loss='L2', symmetric=None,
                 alpha=0.5, reg=None, reg_type='entropy', unbalanced=None,
                 unbalanced_type='KL', n_threads=1, method=None,
                 max_iter=None, plan_init=None, tol=None, verbose=False)
```

Use this when a future agent benefits from one result object across GW, FGW, entropic, semirelaxed, partial, and some unbalanced routes.

Return: `OTResult` with useful fields:

- `.plan`: coupling matrix.
- `.value`: full objective value used by the selected route.
- `.value_linear`: linear/feature/ordinary OT component when available.
- `.value_quad`: quadratic GW component when available.
- `.potentials`: dual potentials when the selected route computes them.
- `.marginal_a`, `.marginal_b`, or `.marginals`: inspect mass constraints when available.
- `.status` and `.log`: convergence/status details when available.

### `ot.solve_gromov` routing rules

| Parameters | Route | Notes |
| --- | --- | --- |
| `M is None`, `reg is None`, `unbalanced is None` | Balanced exact GW | Conditional-gradient GW; `alpha` is irrelevant unless `M` is supplied. |
| `M is not None`, `0 < alpha < 1`, no `reg`/`unbalanced` | Balanced exact FGW | Objective is `(1-alpha) * <T, M> + alpha * GW(T)`. |
| `alpha == 0`, `M is not None` | Ordinary Wasserstein on `M` | Route deeper vector-space OT questions to `core-solvers`. |
| `reg` set, `reg_type='entropy'` | Entropic GW/FGW | `method` defaults to `PGD` for entropic GW/FGW unless specified; common alternatives include `PPA` in classical APIs. |
| `unbalanced_type='semirelaxed'` | Semirelaxed GW/FGW | Keeps source marginal fixed; target marginal is induced by the plan. |
| `unbalanced_type='partial'`, `unbalanced=m` | Partial GW/FGW | `unbalanced` is transported mass `m`; it must be no larger than both total masses. |
| `unbalanced_type in {'KL', 'L2'}` with `unbalanced` set | Fused unbalanced GW or unbalanced Wasserstein depending on `alpha`/`M` | General UOT theory belongs in `unbalanced-partial`; validate the lower-level alpha convention before calling `ot.gromov.fused_unbalanced_gromov_wasserstein` directly. |

## Classical balanced GW and FGW

| API | Verified signature | Return and log |
| --- | --- | --- |
| `ot.gromov.gromov_wasserstein` | `(C1, C2, p=None, q=None, loss_fun='square_loss', symmetric=None, log=False, armijo=False, G0=None, max_iter=10000.0, tol_rel=1e-09, tol_abs=1e-09, **kwargs)` | Returns `T`; with `log=True`, returns `(T, log)` and `log['gw_dist']`. |
| `ot.gromov.gromov_wasserstein2` | `(C1, C2, p=None, q=None, loss_fun='square_loss', symmetric=None, log=False, armijo=False, G0=None, max_iter=10000.0, tol_rel=1e-09, tol_abs=1e-09, **kwargs)` | Returns scalar GW loss; with `log=True`, log includes the transport under `log['T']`. |
| `ot.gromov.fused_gromov_wasserstein` | `(M, C1, C2, p=None, q=None, loss_fun='square_loss', symmetric=None, alpha=0.5, armijo=False, G0=None, log=False, max_iter=10000.0, tol_rel=1e-09, tol_abs=1e-09, **kwargs)` | Returns `T`; with `log=True`, log includes `fgw_dist`. |
| `ot.gromov.fused_gromov_wasserstein2` | `(M, C1, C2, p=None, q=None, loss_fun='square_loss', symmetric=None, alpha=0.5, armijo=False, G0=None, log=False, max_iter=10000.0, tol_rel=1e-09, tol_abs=1e-09, **kwargs)` | Returns scalar FGW loss; with `log=True`, log includes `T`, and in some routes `lin_loss`/`quad_loss`. |

Notes:

- `armijo=True` uses an Armijo line-search; use `False` for the closed-form line-search when convergence or speed is problematic.
- `symmetric=None` makes POT test matrix symmetry. Use `symmetric=True` for known symmetric costs to avoid repeated checks; use `False` for directed/asymmetric structures.
- These conditional-gradient implementations are backend-compatible at the interface, but internal calculations use NumPy/CPU in several paths. Do not claim GPU acceleration without separate backend verification.

## Entropic and BAPG GW/FGW

| API | Verified signature | When to use |
| --- | --- | --- |
| `entropic_gromov_wasserstein` | `(C1, C2, p=None, q=None, loss_fun='square_loss', epsilon=0.1, symmetric=None, G0=None, max_iter=1000, tol=1e-09, solver='PGD', warmstart=False, verbose=False, log=False, **kwargs)` | Smooth GW plans; can be faster for dense problems but introduces entropic bias. |
| `entropic_gromov_wasserstein2` | same plus scalar-return convention | Distance/loss version with log access to `T`. |
| `entropic_fused_gromov_wasserstein` | `(M, C1, C2, p=None, q=None, loss_fun='square_loss', epsilon=0.1, symmetric=None, alpha=0.5, G0=None, max_iter=1000, tol=1e-09, solver='PGD', warmstart=False, verbose=False, log=False, **kwargs)` | Smooth FGW plans. |
| `entropic_fused_gromov_wasserstein2` | same plus scalar-return convention | Distance/loss version. |
| `BAPG_gromov_wasserstein` | `(C1, C2, p=None, q=None, loss_fun='square_loss', epsilon=0.1, symmetric=None, G0=None, max_iter=1000, tol=1e-09, marginal_loss=False, verbose=False, log=False)` | Bregman alternating projected-gradient route. |
| `BAPG_fused_gromov_wasserstein` | `(M, C1, C2, p=None, q=None, loss_fun='square_loss', epsilon=0.1, symmetric=None, alpha=0.5, G0=None, max_iter=1000, tol=1e-09, marginal_loss=False, verbose=False, log=False)` | BAPG route for FGW. |

`epsilon` is an entropic regularization strength. If it is too small, expect slow iterations, numerical underflow, or near-sparse plans. If it is too large, the plan may be too diffuse for matching.

## Semirelaxed and partial GW/FGW

| Family | Key APIs | Semantics |
| --- | --- | --- |
| Semirelaxed GW | `semirelaxed_gromov_wasserstein(C1, C2, p=None, loss_fun='square_loss', symmetric=None, log=False, G0=None, max_iter=10000.0, tol_rel=1e-09, tol_abs=1e-09, random_state=0, **kwargs)` | Source marginal is fixed; target mass is inferred. Use for graph-to-prototype or cluster reweighting. |
| Semirelaxed FGW | `semirelaxed_fused_gromov_wasserstein(M, C1, C2, p=None, loss_fun='square_loss', symmetric=None, alpha=0.5, G0=None, log=False, max_iter=10000.0, tol_rel=1e-09, tol_abs=1e-09, random_state=0, **kwargs)` | Semirelaxed route with node features. |
| Entropic semirelaxed | `entropic_semirelaxed_gromov_wasserstein(...)`, `entropic_semirelaxed_fused_gromov_wasserstein(...)` | Add `epsilon`, `tol`, and `max_iter`; produces smoother plans. |
| Partial GW | `partial_gromov_wasserstein(C1, C2, p=None, q=None, m=None, loss_fun='square_loss', nb_dummies=1, G0=None, thres=1, numItermax=10000.0, tol=1e-08, symmetric=None, warn=True, log=False, verbose=False, **kwargs)` | Transports exactly mass `m`, with row/column sums bounded by `p` and `q`. |
| Partial FGW | `partial_fused_gromov_wasserstein(M, C1, C2, p=None, q=None, m=None, loss_fun='square_loss', alpha=0.5, nb_dummies=1, G0=None, thres=1, numItermax=10000.0, tol=1e-08, symmetric=None, warn=True, log=False, verbose=False, **kwargs)` | Partial route with feature cost. |
| Entropic partial | `entropic_partial_gromov_wasserstein(...)`, `entropic_partial_fused_gromov_wasserstein(...)` | Adds `reg`; validate finite output and `T.sum() ≈ m`. |

Use semirelaxed when one side can be reweighted, partial when outliers should be ignored with a known transported mass, and unbalanced when marginal mismatch should be penalized instead of fixed.

## Fused unbalanced GW and cross-space divergences

| API | Verified signature | Notes |
| --- | --- | --- |
| `fused_unbalanced_gromov_wasserstein` | `(Cx, Cy, wx=None, wy=None, reg_marginals=10, epsilon=0, divergence='kl', unbalanced_solver='mm', alpha=0, M=None, init_duals=None, init_pi=None, max_iter=100, tol=1e-07, max_iter_ot=500, tol_ot=1e-07, log=False, verbose=False, **kwargs_solve)` | Lower-bound FUGW for similarity matrices. Direct API uses `alpha` as the coefficient of the linear term; this differs from `ot.solve_gromov`, where `alpha` weights the quadratic GW term. |
| `fused_unbalanced_across_spaces_divergence` | `(X, Y, wx_samp=None, wx_feat=None, wy_samp=None, wy_feat=None, reg_marginals=10, epsilon=0, reg_type='joint', divergence='kl', unbalanced_solver='sinkhorn', alpha=0, M_samp=None, M_feat=None, rescale_plan=True, init_pi=None, init_duals=None, max_iter=100, tol=1e-07, max_iter_ot=500, tol_ot=1e-07, log=False, verbose=False, **kwargs_solver)` | Cross-space/coupled sample-feature divergence route. |
| `unbalanced_co_optimal_transport` | `(X, Y, wx_samp=None, wx_feat=None, wy_samp=None, wy_feat=None, reg_marginals=10, epsilon=0, divergence='kl', unbalanced_solver='mm', alpha=0, M_samp=None, M_feat=None, rescale_plan=True, init_pi=None, init_duals=None, max_iter=100, tol=1e-07, max_iter_ot=500, tol_ot=1e-07, log=False, verbose=False, **kwargs_solve)` | COOT-related; route non-GW UOT fundamentals elsewhere. |

## Approximate and scalable GW routes

| API | Verified signature | Trade-off |
| --- | --- | --- |
| `pointwise_gromov_wasserstein` | `(C1, C2, p, q, loss_fun, alpha=1, max_iter=100, threshold_plan=0, log=False, verbose=False, random_state=None)` | Stochastic Frank-Wolfe estimator; cheaper but returns estimator variance/logs rather than exact CG behavior. |
| `sampled_gromov_wasserstein` | `(C1, C2, p, q, loss_fun, nb_samples_grad=100, epsilon=1, max_iter=500, log=False, verbose=False, random_state=None)` | Samples gradient terms; validate with seeds and small exact subsets. |
| `lowrank_gromov_wasserstein_samples` | `(X_s, X_t, a=None, b=None, reg=0, rank=None, alpha=1e-10, gamma_init='rescale', rescale_cost=True, cost_factorized_Xs=None, cost_factorized_Xt=None, stopThr=0.0001, numItermax=1000, stopThr_dykstra=0.001, numItermax_dykstra=10000, seed_init=49, warn=True, warn_dykstra=False, log=False)` | Sample-cloud low-rank coupling approximation; use when a low-rank model is meaningful. |
| `quantized_fused_gromov_wasserstein` | `(C1, C2, npart1, npart2, p=None, q=None, C1_aux=None, C2_aux=None, F1=None, F2=None, alpha=1.0, part_method='fluid', rep_method='random', log=False, armijo=False, max_iter=10000.0, tol_rel=1e-09, tol_abs=1e-09, random_state=0, **kwargs)` | Two-level graph approximation. `alpha=1` gives qGW; provide `F1`/`F2` for fused methods. |
| `quantized_fused_gromov_wasserstein_partitioned` | `(CR1, CR2, list_R1, list_R2, list_p1, list_p2, MR=None, alpha=1.0, build_OT=False, log=False, armijo=False, max_iter=10000.0, tol_rel=1e-09, tol_abs=1e-09, nx=None, **kwargs)` | Expert route when partitions/representants are precomputed. |
| `quantized_fused_gromov_wasserstein_samples` | `(X1, X2, npart1, npart2, p=None, q=None, F1=None, F2=None, alpha=1.0, method='kmeans', log=False, armijo=False, max_iter=10000.0, tol_rel=1e-09, tol_abs=1e-09, random_state=0, **kwargs)` | Point-cloud wrapper; `method='kmeans'` needs scikit-learn. |

Quantized helper methods may use NetworkX (`louvain`, `fluid`, `pagerank`) or scikit-learn (`spectral`, `kmeans`). If those packages are missing, some helpers warn and fall back to `random`; do not confuse that fallback with a validated graph-partitioning method.

## Barycenters and dictionaries

| API | Verified signature | Output |
| --- | --- | --- |
| `gromov_barycenters` | `(N, Cs, ps=None, p=None, lambdas=None, loss_fun='square_loss', symmetric=True, armijo=False, max_iter=1000, tol=1e-09, stop_criterion='barycenter', warmstartT=False, verbose=False, log=False, init_C=None, random_state=None, **kwargs)` | Barycenter structure matrix of size `N`. |
| `fgw_barycenters` | `(N, Ys, Cs, ps=None, lambdas=None, alpha=0.5, fixed_structure=False, fixed_features=False, p=None, loss_fun='square_loss', armijo=False, symmetric=True, max_iter=100, tol=1e-09, stop_criterion='barycenter', warmstartT=False, verbose=False, log=False, init_C=None, init_X=None, random_state=None, **kwargs)` | Feature matrix and structure barycenter for attributed structures. |
| `entropic_gromov_barycenters` | `(N, Cs, ps=None, p=None, lambdas=None, loss_fun='square_loss', epsilon=0.1, symmetric=True, max_iter=1000, tol=1e-09, stop_criterion='barycenter', warmstartT=False, verbose=False, log=False, init_C=None, random_state=None, **kwargs)` | Entropic GW barycenter. |
| `entropic_fused_gromov_barycenters` | `(N, Ys, Cs, ps=None, p=None, lambdas=None, loss_fun='square_loss', epsilon=0.1, symmetric=True, alpha=0.5, max_iter=1000, tol=1e-09, stop_criterion='barycenter', warmstartT=False, verbose=False, log=False, init_C=None, init_Y=None, fixed_structure=False, fixed_features=False, random_state=None, **kwargs)` | Entropic attributed barycenter. |
| `semirelaxed_gromov_barycenters` | `(N, Cs, ps=None, lambdas=None, loss_fun='square_loss', symmetric=True, max_iter=1000, tol=1e-09, stop_criterion='barycenter', warmstartT=False, verbose=False, log=False, init_C=None, G0='product', random_state=None, **kwargs)` | Semirelaxed structure prototype. |
| `semirelaxed_fgw_barycenters` | `(N, Ys, Cs, ps=None, lambdas=None, alpha=0.5, fixed_structure=False, fixed_features=False, p=None, loss_fun='square_loss', symmetric=True, max_iter=100, tol=1e-09, stop_criterion='barycenter', warmstartT=False, verbose=False, log=False, init_C=None, init_X=None, G0='product', random_state=None, **kwargs)` | Semirelaxed attributed prototype. |
| `gromov_wasserstein_dictionary_learning` | `(Cs, D, nt, reg=0.0, ps=None, q=None, epochs=20, batch_size=32, learning_rate=1.0, Cdict_init=None, projection='nonnegative_symmetric', use_log=True, tol_outer=1e-05, tol_inner=1e-05, max_iter_outer=20, max_iter_inner=200, use_adam_optimizer=True, verbose=False, random_state=None, **kwargs)` | Learned structure atoms. |
| `gromov_wasserstein_linear_unmixing` | `(C, Cdict, reg=0.0, p=None, q=None, tol_outer=1e-05, tol_inner=1e-05, max_iter_outer=20, max_iter_inner=200, symmetric=None, **kwargs)` | Convex weights, embedded reconstruction, plan, reconstruction error. |
| `fused_gromov_wasserstein_dictionary_learning` | `(Cs, Ys, D, nt, alpha, reg=0.0, ps=None, q=None, epochs=20, batch_size=32, learning_rate_C=1.0, learning_rate_Y=1.0, Cdict_init=None, Ydict_init=None, projection='nonnegative_symmetric', use_log=False, tol_outer=1e-05, tol_inner=1e-05, max_iter_outer=20, max_iter_inner=200, use_adam_optimizer=True, verbose=False, random_state=None, **kwargs)` | Learned structure and feature atoms. |
| `fused_gromov_wasserstein_linear_unmixing` | `(C, Y, Cdict, Ydict, alpha, reg=0.0, p=None, q=None, tol_outer=1e-05, tol_inner=1e-05, max_iter_outer=20, max_iter_inner=200, symmetric=True, **kwargs)` | Attributed unmixing against FGW dictionary. |

For barycenters and dictionaries, set `random_state`, small `max_iter`, and explicit `tol` during prototyping; then increase budgets only after the tiny workflow is validated.

## Optional GNN route

`ot.gnn` is not imported by default and depends on PyTorch plus PyTorch Geometric. In the minimum verified environment it was not available. Treat these as optional, user-environment-verified APIs:

- `TFGWPooling(n_features, n_tplt=2, n_tplt_nodes=2, alpha=None, train_node_weights=True, multi_alpha=False, feature_init_mean=0.0, feature_init_std=1.0)` computes template FGW distances for graph pooling.
- `TWPooling(n_features, n_tplt=2, n_tplt_nodes=2, train_node_weights=True, feature_init_mean=0.0, feature_init_std=1.0)` computes template Wasserstein distances for pooling.
- Utility functions include `FGW_distance_to_templates` and `wasserstein_distance_to_templates`.

Route installation, CUDA, and mixed tensor backend issues to `backend-and-batch` before using this path.
