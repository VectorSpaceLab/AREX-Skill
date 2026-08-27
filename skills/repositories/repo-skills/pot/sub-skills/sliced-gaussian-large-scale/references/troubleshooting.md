# Troubleshooting: sliced, Gaussian/GMM, and large-scale POT alternatives

Use this matrix when a workflow from this sub-skill gives unstable values, shape errors, optional dependency failures, convergence warnings, or memory blowups.

## Quick triage

1. Run the bundled deterministic smoke check:

   ```bash
   python scripts/sliced_gaussian_smoke.py --mode all
   ```

2. If `import ot` fails, confirm POT is installed in the active Python environment. Route installation/backend issues to `backend-and-batch`.
3. If a dense plan or cost matrix is being materialized, estimate memory as `n_source * n_target * 8` bytes for float64 before retrying.
4. If an approximate method is used, reproduce with fixed seeds and a tiny dense baseline before changing many parameters at once.

## Failure matrix

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'ot'` | POT is not installed in the current Python environment | Install/activate POT using the repo root guidance or route to `backend-and-batch`; do not edit scripts to import from a checkout. |
| Sliced distance changes every run | Random projections changed | Pass `seed=...` or a fixed `projections` matrix. Report mean/std across seeds if stochastic uncertainty matters. |
| Sliced distance hides an obvious low-scale feature shift | Feature scales differ by orders of magnitude | Fit `ot.utils.DataScaler(norm="standard")` once on representative data and pass `scaler=scaler`. |
| `ValueError` or assertion for sliced sample shapes | Source and target dimensions differ | Ensure `X_s.shape[1] == X_t.shape[1]`; weights should be one-dimensional and match sample counts. |
| Sliced plan rejects `metric` | Unsupported metric string | Use `"sqeuclidean"`, `"minkowski"`, `"cityblock"`, or `"euclidean"`. Route custom cost-matrix workflows to `core-solvers`. |
| Sliced plan memory error | `dense=True` or downstream materialized an `(n, m)` plan | Use `dense=False` where NumPy/SciPy sparse output is acceptable, use `batch_size` during evaluation, or switch to scalar sliced distance/low-rank factors. |
| Spherical sliced result looks wrong | Rows are not unit-norm spherical points | Normalize rows with `X / np.linalg.norm(X, axis=1, keepdims=True)` and handle zero vectors before calling spherical APIs. |
| Gaussian distance/mapping fails or returns NaNs | Covariance is not symmetric PSD or is ill-conditioned | Symmetrize covariance, inspect eigenvalues, and add a small diagonal jitter only for numerical noise. Increase empirical `reg` for sample-estimated covariances. |
| Gaussian batch output shape is unexpected | Cross-distance vs paired mode misunderstood | Without `paired=True`, batched means/covariances produce cross-distances. Use `paired=True` only for aligned batches of equal length. |
| High-dimensional Gaussian helper shape error | `U`, `l`, and residual variance dimensions do not match | Check `U.shape == (p, d_sub)`, `l.shape == (d_sub,)`, and nonnegative `sigma2`; verify `U.T @ U` is close to identity. |
| GMM plan row/column sums do not match weights | Weights are not normalized or component dimensions mismatch | Normalize `w_s`/`w_t`; check means `(k,d)`, covariances `(k,d,d)`, and weights `(k,)` for each mixture. |
| GMM random map is not reproducible | `method="rand"` without seed | Use `method="bary"` for deterministic mapping or pass `seed` for random mapping. |
| `gmm_barycenter_fixed_point` raises unknown method | Invalid `barycentric_proj_method` | Use `"euclidean"` or `"bures"`. Start with a small iteration count and validate shapes. |
| Low-rank Sinkhorn warning: did not converge | Rank/reg/tolerance/iteration budget too aggressive | Increase `numItermax`, loosen `stopThr`, increase `reg`, or increase `rank`. Keep `warn=False` only for exploratory smoke checks. |
| Low-rank `ValueError` for `alpha` | `alpha` must be below `1 / rank` | Use the default `alpha=1e-10` or set a smaller value relative to rank. |
| Low-rank `init="kmeans"` raises `ImportError` | scikit-learn is optional and not installed | Use `init="random"` or `"deterministic"`; install scikit-learn only if the workflow explicitly needs k-means initialization. |
| Lazy low-rank plan causes memory blowup | Code calls `log["lazy_plan"][:]` on a large problem | Keep factors `Q`, `R`, `g` or lazy plan operations; materialize only on tiny validation cases. |
| Nystroem approximation is poor or errors on anchors | Too few anchors or invalid anchor count | Increase `anchors`, set `random_state`, and compare to dense Sinkhorn on a small subset. |
| Factored OT output does not look like a full plan | The method returns two plans through an intermediate support | Use `Ga`, `Gb`, and `X_mid` directly; materialize `Ga @ Gb` only when a dense composed plan is required. |
| BSP import/build failure mentions C++/Eigen or compiled extension | POT was built without the BSP extension or its C++ dependency | Use an installed POT build with BSP support or route environment repair to `backend-and-batch`; runtime workflows should not require source files. |
| BSP permutation is invalid or low quality | Input point clouds have unequal sizes, too few plans, or hard local minima | BSP requires equal sizes. Increase `n_plans`, set `seed`, and compare cost to a small exact baseline when possible. |
| Semidiscrete solver raises unknown sampler | Bad `sampler_source` string | Use `"unif"`, `"unif_cube"`, `"ball"`, `"unif_ball"`, `"normal"`, or pass a callable `sampler(batch_size)`. |
| Semidiscrete potentials fail to stabilize | Learning rate, batch size, `max_cost`, or iteration count unsuitable | Increase `max_iter`, tune `batch_size`, set `max_cost` from a ground-cost upper bound, and compare empirical cell masses. |
| Stochastic dual solver diverges or produces poor marginals | Learning rate too large, batch too small, `reg` too small, or not enough iterations | Start with `reg=1`, smaller `lr`, larger `batch_size`, and compare against Sinkhorn on a tiny case. |
| SGOT raises shape or metric errors | Eigenvalue/eigenvector dimensions or `grassmann_metric` invalid | Eigenvalues must be one-dimensional; left/right eigenvectors should be `(ambient_dim, rank)`; use `"geodesic"`, `"chordal"`, `"procrustes"`, or `"martin"`. |
| COOT raises `ValueError` for `epsilon`, `alpha`, or `method_sinkhorn` | Wrong scalar/length-2 parameter form or invalid method name | Use scalar or length-2 `epsilon`/`alpha`; use a valid Sinkhorn method such as `"sinkhorn"`; verify warmstart keys if provided. |
| COOT is slow on matrices with many rows and features | BCD alternates sample and feature couplings | Reduce dimensions for validation, increase entropic `epsilon`, lower `nits_bcd`/`nits_ot` for exploration, then refine. |
| DMMOT objective disagrees with LP barycenter objective | The methods optimize different objectives | Compare resulting distributions qualitatively or with a downstream metric; do not compare raw objective values. |
| Optional backend or plotting import fails | Minimum baseline is NumPy-only | Route backend installation and optional plotting/DR/GNN extras to `backend-and-batch`; this sub-skill does not claim those runtimes are verified. |

## Safe recovery pattern for approximation failures

1. Reduce to a deterministic tiny fixture.
2. Run `python scripts/sliced_gaussian_smoke.py --mode all`.
3. Validate shapes, weights, covariance PSD, and memory footprint.
4. Compare to a dense baseline only on a small subset.
5. Change one approximation knob at a time: projections, rank, anchors, `n_plans`, `reg`, `lr`, or `batch_size`.
6. Document the accepted approximation tolerance and the validation signal used.
