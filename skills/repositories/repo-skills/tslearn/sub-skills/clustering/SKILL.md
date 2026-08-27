---
name: clustering
description: "Cluster time series with TimeSeriesKMeans, KernelKMeans, KShape,
  TimeSeriesDBSCAN, and silhouette scoring."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# Clustering

Use this sub-skill for tslearn clustering tasks on small or preprocessed time-series datasets.

Start here:

- [references/api-reference.md](references/api-reference.md)
- [references/workflows.md](references/workflows.md)
- [references/troubleshooting.md](references/troubleshooting.md)
- [scripts/clustering_smoke.py](scripts/clustering_smoke.py)

Route here for:

- `TimeSeriesKMeans` with `metric="euclidean"`, `"dtw"`, or `"softdtw"`.
- `KernelKMeans` with the GAK kernel or another pairwise-kernel metric.
- `KShape` on equal-length, mean-variance-normalized series.
- `TimeSeriesDBSCAN` with `dtw`, `ctw`, `frechet`, `softdtw_normalized`, `euclidean`, or `precomputed`.
- `silhouette_score` and other clustering-only score checks.
- `EmptyClusterError`, `TimeSeriesCentroidBasedClusteringMixin`, and centroid-utility debugging.

Do not handle here:

- Generic metric and backend explanations: [metrics-backends](../metrics-backends/)
- Scaling, resampling, imputation, and ragged-to-dense prep: [data-preparation](../data-preparation/)
- Supervised models: [supervised-models](../supervised-models/)
- Forecasting: [forecasting](../forecasting/)
- Serialization or persistence: [analysis-and-persistence](../analysis-and-persistence/)
- Matrix profile: return to the [tslearn router](../../SKILL.md)

Operating rules:

1. Choose the estimator by geometry and centroid need.
   - Need explicit centroids? Use `TimeSeriesKMeans` or `KShape`.
   - Need assignments only? Use `KernelKMeans` or `TimeSeriesDBSCAN`.
2. Keep centroid semantics straight.
   - `TimeSeriesKMeans.cluster_centers_` are barycenters: Euclidean means, DTW DBA, or Soft-DTW barycenters.
   - `KShape.cluster_centers_` are shape centroids after mean-variance scaling.
   - `KernelKMeans` and `TimeSeriesDBSCAN` do not produce centroids; DBSCAN exposes `components_` and `core_ts_indices_` instead.
3. Use `fit_predict` for the training set and `predict` only on estimators that implement it.
   - `TimeSeriesDBSCAN` is fit-only; there is no out-of-sample `predict`.
4. For variable-length series, prefer `TimeSeriesKMeans(metric="dtw"|"softdtw")`, `KernelKMeans` with GAK, or `TimeSeriesDBSCAN` with a supported metric.
   - `euclidean` KMeans, `KShape`, and Euclidean DBSCAN expect equal-length series.
5. Fix `random_state` and increase `n_init` on tiny datasets.
   - If a run ends without fitted attributes, lower `n_clusters`, adjust `init`, or improve the metric parameters.
6. Use `silhouette_score` with the same geometry you want to validate.
   - Pass `metric="precomputed"` only when `X` is already a square distance matrix.
   - For `metric="softdtw"`, pass the same `gamma` in `metric_params`.

If the task is outside clustering, return to the [tslearn router](../../SKILL.md).
