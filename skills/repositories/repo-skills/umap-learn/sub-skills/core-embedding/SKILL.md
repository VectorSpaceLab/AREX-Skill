---
name: core-embedding
description: "Use base umap.UMAP for unsupervised embedding, transforms, input
  formats, metrics, reproducibility, and core API troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Core UMAP Embedding

Use this sub-skill when the task is about the base `umap.UMAP` estimator: dimensionality reduction, `fit`/`fit_transform`, using `embedding_`, transforming held-out data, approximate inverse transforms, appending data with `update`, dense/sparse/precomputed inputs, metric selection, precomputed k-NN, reproducibility, and sklearn-style pipeline use.

## Fast routing

Read these bundled references for self-contained operating guidance:

- [API reference](references/api-reference.md): verified constructor and method signatures, fitted attributes, estimator behavior, and precomputed k-NN helpers.
- [Workflows](references/workflows.md): recipes for basic embedding, train/test transform, inverse transform, update, reproducibility, sklearn pipelines, and script usage.
- [Data and metrics](references/data-and-metrics.md): accepted data formats, sparse and precomputed-distance rules, metric categories, custom metric constraints, and parameter selection.
- [Troubleshooting](references/troubleshooting.md): recovery steps for shape, non-finite, metric, transform, disconnected-vertex, memory, parallelism, and optional TBB issues.

Bundled safe scripts:

- [`scripts/umap_core_smoke.py`](scripts/umap_core_smoke.py): fits a tiny local sklearn dataset, optionally checks transform, inverse, sparse, precomputed-distance, precomputed k-NN, and update paths, and prints JSON.
- [`scripts/inspect_umap_estimator.py`](scripts/inspect_umap_estimator.py): prints installed `umap` version/signatures and optionally diagnoses a trusted fitted estimator pickle.

## Choose this sub-skill for

- Creating a low-dimensional embedding with `umap.UMAP(...).fit_transform(X)` or `mapper.fit(X); mapper.embedding_`.
- Fitting UMAP inside an sklearn `Pipeline`, usually after scaling or vectorization, then passing the embedding to an estimator.
- Transforming held-out samples into an already learned UMAP space with `mapper.transform(X_new)`.
- Calling `inverse_transform` for approximate reconstruction from low-dimensional coordinates.
- Calling `update` to append new samples to an existing unsupervised, non-precomputed UMAP model.
- Using dense arrays, pandas/scikit-learn data, `scipy.sparse` matrices, `metric="precomputed"`, or `precomputed_knn`.
- Deciding base parameters such as `n_neighbors`, `min_dist`, `n_components`, `metric`, `output_metric`, `random_state`, `n_jobs`, `low_memory`, `force_approximation_algorithm`, and `transform_seed`.
- Recovering from core API misuse: wrong distance-matrix shape, unsupported metrics, non-finite input, transform before a usable fit, unexpected `n_jobs` behavior, or disconnected vertices.

## Route elsewhere

- Supervised labels, `target_metric*`, densMAP, density preservation, clustering, or outlier-analysis workflows belong in `../supervised-density/SKILL.md`.
- `AlignedUMAP` and UMAP model composition operators belong in `../aligned-composition/SKILL.md`.
- `umap.plot` and visual diagnostics belong in `../plotting-diagnostics/SKILL.md`.
- TensorFlow/Keras `ParametricUMAP` belongs in `../parametric-umap/SKILL.md`.

## Core operating rules

1. Treat `umap.UMAP` as an sklearn-style transformer: rows are samples, columns are features, and `fit` returns the estimator while `fit_transform` returns the embedding.
2. `embedding_` is the fitted training embedding with shape `(n_samples, n_components)` when `transform_mode="embedding"`.
3. For reproducible layouts, set `random_state`; expect UMAP to disable unsafe parallelism by overriding effective `n_jobs` to `1`. Leave `random_state=None` only when speed and multicore use matter more than exact repeatability.
4. `transform_seed` controls stochastic details of `transform`, not the original fitted layout.
5. Use `metric="precomputed"` only when fitting on a square train-train distance matrix; transform then needs a new-to-train distance matrix with shape `(n_new, n_train)`.
6. `precomputed_knn` can save neighbor-search time only when the neighbor graph matches the fit data and has at least `n_neighbors` columns. A two-array `(indices, distances)` tuple fits but cannot transform new raw samples because it lacks a search index.
7. `inverse_transform` is approximate and unavailable for sparse input, precomputed input, metrics without gradients, densMAP, and graph transform mode.
8. `update` mutates the fitted estimator, appending unsupervised non-precomputed data; it is not a general replacement for refitting when distribution shift is large.
9. Optional `plot`, `parametric_umap`, and `tbb` extras are not required for core UMAP. Treat them as optional and unverified unless the active environment has installed them.
