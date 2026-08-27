---
name: clustering
description: "Provides elbow-curve analysis for clusterers and direct
  cluster-count workflows in scikit-plot."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Clustering

Use this sub-skill when the user wants to choose `K`, compare clustering inertia across cluster counts, or render an elbow curve for a cloneable scikit-learn-style clusterer.

## What this covers
- `scikitplot.cluster.plot_elbow_curve`
- elbow-curve analysis for KMeans-like estimators
- cluster-count sweeps over a finite `cluster_ranges`
- optional elapsed-time overlays and Matplotlib `Axes` reuse

## Route elsewhere when
- you need deprecated instance-method injection such as `clustering_factory` -> [legacy-factories](../legacy-factories/SKILL.md)
- you need silhouette plots from fitted labels or label-based clustering metrics -> [metrics](../metrics/SKILL.md)
- you need feature-importance or learning-curve routes -> [estimators](../estimators/SKILL.md)
- you need decomposition or PCA routes -> [decomposition](../decomposition/SKILL.md)

## Use this route
1. Start from `scikitplot.cluster.plot_elbow_curve`.
2. Confirm the clusterer is clone-compatible and exposes `n_clusters`, `fit`, and `score`.
3. Pick a small finite cluster range such as `range(1, 11)`.
4. Keep `n_jobs=1` for the most predictable smoke run unless you are explicitly checking the parallel path.
5. Set `show_cluster_time=True` only when you want the timing overlay.
6. Pass `ax=` only when embedding into an existing figure.
7. Use `ax.figure` to save or close the result if needed.

## Read next
- [references/api-reference.md](references/api-reference.md) for the exact function contract and implementation notes.
- [references/workflows.md](references/workflows.md) for K-selection and comparison recipes.
- [references/troubleshooting.md](references/troubleshooting.md) for interface, range, parallelism, and import failures.
- [scripts/clustering_smoke.py](scripts/clustering_smoke.py) for a tiny Agg-backed elbow-curve smoke run.
