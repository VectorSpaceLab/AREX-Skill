# Metrics, Paths, Constraints, and Barycenters

## Purpose

Read this for concrete `tslearn.metrics` and `tslearn.barycenters` API usage.
For backend selection and gradients, pair it with [backends](backends.md). For
forecasting/regression error metrics, read [performance](performance.md).

## Data contracts shared by metric APIs

- A single time series is accepted as `(sz, d)` or as `(sz,)` for univariate
  data. A dataset is accepted as `(n_ts, sz, d)`, `(n_ts, sz)`, or compatible
  lists that tslearn can normalize as a time-series dataset.
- Pairwise metrics require both series to have the same feature dimension after
  conversion. Empty series and all-NaN series are invalid for DTW, Soft-DTW,
  and Fréchet workflows.
- Most scalar pair metrics also have path-returning variants and `cdist_*`
  variants. When `dataset2=None`, `cdist_*` computes the self matrix for
  `dataset1`; otherwise it returns shape `(n_ts1, n_ts2)`.
- Many helpers accept `be=None` or `be="numpy"`/`be="pytorch"`. Leave `be=None`
  for NumPy/list correctness; use `be="pytorch"` only for tensor/autodiff
  needs.

## Metric families

| Family | Use when | Main APIs | Notes |
| --- | --- | --- | --- |
| DTW | Time axes can stretch and an optimal alignment path or DTW distance is needed. | `dtw`, `dtw_path`, `cdist_dtw`, `dtw_path_from_metric` | `dtw` returns the Euclidean distance along the optimal path. `dtw_path_from_metric` returns cumulative custom/precomputed cost, not necessarily the square-rooted DTW score. |
| Limited/subsequence DTW | You need a maximum path length or to locate a query in a longer sequence. | `dtw_limited_warping_length`, `dtw_path_limited_warping_length`, `subsequence_cost_matrix`, `subsequence_path`, `dtw_subsequence_path`, `lb_envelope`, `lb_keogh` | `max_length` must be at least `max(len(s1), len(s2))`. `subsequence_path` expects the accumulated cost matrix and an endpoint index. |
| Soft-DTW | You need a smoothed DTW objective, normalized divergence, soft alignment, or differentiable metric. | `soft_dtw`, `soft_dtw_normalized`, `soft_dtw_alignment`, `cdist_soft_dtw`, `cdist_soft_dtw_normalized`, `gamma_soft_dtw`, `SoftDTW`, `SquaredEuclidean` | `gamma=0` reduces top-level Soft-DTW to squared DTW. Raw Soft-DTW can be negative; normalized Soft-DTW is zero on identical inputs and nonnegative in ordinary use. |
| GAK | You need a similarity kernel rather than a distance. | `sigma_gak`, `gak`, `unnormalized_gak`, `cdist_gak` | Larger values mean more similar series. `gak(x, x)=1` for normalized GAK. `sigma` must be non-zero; `sigma_gak` estimates a bandwidth. |
| LCSS | You need a longest-common-subsequence-style similarity robust to gaps/outliers. | `lcss`, `lcss_path`, `lcss_path_from_metric` | `eps` is the matching threshold. Scores are similarity ratios relative to the shorter input, not distances. |
| Fréchet | You need the discrete Fréchet distance and path. | `frechet`, `frechet_path`, `frechet_path_from_metric`, `cdist_frechet`, `frechet_accumulated_matrix` | Distance is the maximum point distance along the path. With `metric="sqeuclidean"`, the returned score is squared relative to Euclidean Fréchet. |
| CTW | You need Canonical Time Warping, especially when feature spaces differ or a learned subspace alignment matters. | `ctw`, `ctw_path`, `cdist_ctw` | `ctw_path` returns `(path, cca, dist)`. CTW uses DTW internally but is not the same metric; `n_components` and `max_iter` control the canonical-correlation loop. |
| Masks/constraints | You need to inspect or precompute an admissible warping region. | `sakoe_chiba_mask`, `itakura_mask`, `compute_mask` | Public pair metrics accept string constraints; `compute_mask` also accepts internal numeric codes. |

## Path helpers and custom metrics

Use path helpers whenever downstream work needs index correspondences, not just
scores.

- `dtw_path(s1, s2, ...) -> (path, dist)`, where `path` is a list of
  `(i, j)` index pairs and `dist` is the DTW distance.
- `dtw_path_from_metric(s1, s2=None, metric="euclidean", ...)` accepts a
  scikit-learn-compatible metric string, a callable on rows, or
  `metric="precomputed"` with `s1` as a distance matrix. If the metric is
  squared Euclidean, compare `sqrt(cost)` to `dtw_path(...)[1]`.
- `lcss_path(s1, s2, eps=..., ...) -> (path, similarity)` and
  `lcss_path_from_metric(...)` return similarity ratios, not distances.
- `frechet_path(s1, s2, ...) -> (path, dist)` and
  `frechet_path_from_metric(...)` return maximum-on-path costs. Under the
  PyTorch backend, use only `"precomputed"`, `"euclidean"`, `"sqeuclidean"`,
  or torch-compatible callable metrics.
- `ctw_path(...) -> (path, cca, dist)` also returns the fitted CCA object.
  Include `cca` only when the user needs the learned projection, not when they
  only need the alignment score.
- `subsequence_cost_matrix(subseq, longseq)` plus
  `subsequence_path(cost_matrix, idx_path_end)` lets you inspect multiple
  candidate matches; `dtw_subsequence_path(subseq, longseq)` returns the best
  one directly.

## Warping constraints and numeric parameters

- Pairwise DTW, Soft-DTW, LCSS, Fréchet, and CTW APIs accept
  `global_constraint=None`, `"sakoe_chiba"`, or `"itakura"`.
- `compute_mask` is lower-level: use numeric codes (`0` none, `1` Itakura,
  `2` Sakoe-Chiba), `GLOBAL_CONSTRAINT_CODE[...]`, or let it infer from exactly
  one supplied constraint parameter. Do not pass raw strings to `compute_mask`.
- `sakoe_chiba_radius` controls the band width. If `global_constraint` is
  `"sakoe_chiba"` and no radius is supplied, tslearn uses radius `1`.
- `itakura_max_slope` controls the parallelogram. If `global_constraint` is
  `"itakura"` and no slope is supplied, tslearn uses slope `2.0`.
- Do not set both `sakoe_chiba_radius` and `itakura_max_slope` without an
  explicit `global_constraint`; tslearn raises a `RuntimeWarning` and cannot
  infer the intended mask.
- An Itakura slope can be infeasible for very different sequence lengths; use
  `compute_mask` on the intended sizes before running an expensive `cdist_*`.
- For `SoftDTWLossPyTorch`, keep `gamma` strictly positive. For top-level
  `soft_dtw`, `gamma=0` is explicitly handled as squared DTW.
- For GAK, `sigma=0` raises `ZeroDivisionError`. Start with `sigma_gak(X)` for
  an estimate; note that very long series may still need a smaller sigma to
  avoid numerical overflow.
- For LCSS, increasing `eps` makes matching more permissive; decreasing it
  makes exact or near-exact subsequences matter more.

## Barycenter APIs

`tslearn.barycenters` computes representative time series under several
geometries. These workflows are CPU-sufficient unless the caller separately
requires torch tensors for another step.

| API | Choose when | Important parameters | Output |
| --- | --- | --- | --- |
| `euclidean_barycenter(X, weights=None)` | Series are aligned in time and an arithmetic mean is intended. | `weights` length must match `len(X)`; validate manually rather than relying on the current internal fallback for invalid lengths. | Array shaped like one series. |
| `dtw_barycenter_averaging(X, barycenter_size=None, init_barycenter=None, max_iter=30, tol=1e-5, weights=None, metric_params=None, verbose=False, n_init=1, n_jobs=None)` | You need DBA under DTW. | Use `metric_params={"global_constraint": ..., "sakoe_chiba_radius": ...}` or `{"itakura_max_slope": ...}` for constrained DTW. `n_init` matters only without an explicit `init_barycenter`. | NumPy array `(barycenter_size, d)` or inferred length. |
| `dtw_barycenter_averaging_petitjean(...)` | You specifically need the Petitjean DBA variant or to compare with the MM variant. | Similar to `dtw_barycenter_averaging`; `n_jobs` can parallelize assignments. | NumPy array. |
| `dtw_barycenter_averaging_subgradient(..., initial_step_size=0.05, final_step_size=0.005, random_state=None, ...)` | You need the stochastic subgradient DBA variant. | Seed `random_state` for reproducibility. | NumPy array. |
| `softdtw_barycenter(X, gamma=1.0, weights=None, tol=1e-3, max_iter=50, init=None, n_jobs=None, **metric_params)` | You need a Soft-DTW barycenter and a tunable smoothing `gamma`. | `init` fixes the starting barycenter and target length. With `max_iter=0`, it returns the initial Euclidean/resampled average. | NumPy array matching the initial/inferred barycenter length. |

Variable-length guidance:

- The public barycenters module documents variable-length support for
  `dtw_barycenter_averaging` and `softdtw_barycenter`. Prefer those two when
  the dataset contains unequal lengths.
- Set `barycenter_size` or `init`/`init_barycenter` when the target length is
  part of the scientific question; otherwise tslearn infers it from the data or
  the initial barycenter.
- Keep `metric_params` aligned with the metric workflows above; impossible
  warping masks affect barycenter assignment/optimization just as they affect
  pairwise metrics.

## Tiny examples

```python
from tslearn.metrics import dtw_path, soft_dtw_normalized, cdist_gak
from tslearn.barycenters import dtw_barycenter_averaging

path, dist = dtw_path([1, 2, 3], [1.0, 2.0, 2.0, 3.0])
assert path == [(0, 0), (1, 1), (1, 2), (2, 3)]
assert float(dist) == 0.0

score = soft_dtw_normalized([1, 2, 2, 3], [1.0, 2.0, 3.0, 4.0], gamma=1.0)
K = cdist_gak([[1, 2, 2, 3], [1.0, 2.0, 3.0, 4.0]], sigma=2.0)
bar = dtw_barycenter_averaging([[1, 2, 3, 4], [1, 2, 4, 5]], max_iter=5)
```

For assertion-backed examples without plotting, run
[`../scripts/metrics_smoke.py`](../scripts/metrics_smoke.py).
