# Core UMAP Troubleshooting

Use this table for base `umap.UMAP` issues before escalating to optional plotting, supervised/density, aligned, or parametric workflows.

## Fit and validation errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ValueError: n_neighbors must be greater than 1` | `n_neighbors < 2`. | Use an integer at least `2`. For tiny datasets also keep `n_neighbors < n_samples` when possible. |
| Warning: `n_neighbors is larger than the dataset size; truncating to X.shape[0] - 1` | `n_neighbors >= n_samples` after optional duplicate collapsing. | Lower `n_neighbors`; if duplicates dominate, consider `unique=True` and review effective sample count. |
| `ValueError: min_dist must be less than or equal to spread` or `min_dist cannot be negative` | Invalid embedding spacing parameters. | Choose `0 <= min_dist <= spread`; common default is `min_dist=0.1, spread=1.0`. |
| `ValueError: n_components must be ...` | Non-integer or non-positive `n_components`. | Use a positive integer. Use `2` for visualization or a larger integer for ML features. |
| `ValueError: metric is neither callable nor a recognised string` | Misspelled or unsupported `metric`. | Check metric catalog in [data-and-metrics.md](data-and-metrics.md); test import and a tiny fit before long runs. |
| `ValueError: Metric <name> is not supported for sparse data` | Dense-only metric used with sparse input. | Choose a sparse-supported metric such as `cosine`, `correlation`, `euclidean`, `manhattan`, `jaccard`, `dice`, or densify only if memory-safe. |
| `Metric 'hellinger' does not support negative values` | Hellinger metric used with negative data. | Use non-negative features or choose another metric. |
| `output_metric cannnot be 'precomputed'` or output metric gradient error | Output metric must have gradients. | Use default `output_metric='euclidean'` unless a gradient-backed output metric is required. |
| `n_jobs must be a postive integer, or -1` | `n_jobs=0` or `< -1`. | Use `-1` for all available threads or a positive integer. |
| Non-finite input rejected | Default `ensure_all_finite=True`. | Clean/impute the data. If the algorithm really should accept missing values, call `fit(..., ensure_all_finite='allow-nan')` for NaNs only or `False` for NaN/inf, then verify downstream behavior carefully. |
| `unique is poorly defined on a precomputed metric` | `unique=True` with `metric='precomputed'`. | Do duplicate handling before distance-matrix construction, or set `unique=False`. |

## Transform errors and surprises

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Transform before fitting raises an sklearn fitted-state error or missing internal attributes. | The estimator was not fitted. | Call `mapper.fit(X_train)` or use a fitted object loaded from a trusted pickle/joblib file. |
| `Transform unavailable when model was fit with only a single data sample.` | UMAP cannot transform new data from a one-row fit. | Fit with more training samples. |
| `NotImplementedError: Transforming data into an existing embedding not supported for densMAP.` | `densmap=True` model. | Route to density workflow; for ordinary transform, refit with `densmap=False`. |
| `NotImplementedError` mentioning `No search index available` | Model was fit with a two-array `precomputed_knn=(indices, dists)` tuple. | Refit with the full tuple from `nearest_neighbors`, including `knn_search_index`, or do not use `transform` for new raw samples. |
| Precomputed transform fails with assertion or shape error. | For `metric='precomputed'`, transform received wrong distance shape. | Pass distances from new points to original training points with shape `(n_new, n_train)`. Do not pass a square new-new matrix. Validate `D_new_to_train.shape[1] == mapper._raw_data.shape[0]` before calling. |
| Sparse precomputed transform says each row needs at least `n_neighbors` distances. | A sparse new-to-train distance row has too few stored entries. | Store at least `n_neighbors` nearest distances per new sample, with training-column indices. |
| `transform` is slower than expected on first call. | numba JIT compilation and neighbor search overhead. | Warm up with a tiny transform or ignore the first timing. Keep a fitted mapper alive for repeated transforms. |
| Transformed embeddings are not exactly same as training fit from a separately fitted model. | Transform places new points into an existing manifold; it is not equivalent to refitting on combined data. | Use `transform` for stable train/test evaluation; use `update` or refit when the manifold itself should change. |

## Inverse transform errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Inverse transform not available for sparse input.` | Original fit used sparse data. | Use dense data if inverse transform is required, or use a separate reconstruction model. |
| `Inverse transform not available for given metric.` | Metric lacks gradient support, including `metric='precomputed'` or many custom/string/binary metrics. | Use a gradient-backed metric such as `euclidean`, or define a numba custom metric returning `(distance, gradient)`. |
| `Inverse transform not available for densMAP.` | densMAP fit. | Route to density workflow; inverse is unavailable for this estimator configuration. |
| `Inverse transform not available for transform_mode = 'graph'`. | The mapper was fitted in graph mode. | Fit with default `transform_mode='embedding'`. |
| Warning for `n_components >= 8` or strange reconstructions. | Inverse transform is approximate and degrades in high-dimensional latent spaces or outside the embedding convex hull. | Keep inverse-query points inside the learned embedding region; consider ParametricUMAP/autoencoder workflows for robust inverse mappings. |

## Update errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Update does not currently support precomputed metrics` | Fitted with `metric='precomputed'`. | Refit from an updated full distance matrix or use raw-feature UMAP. |
| `Updating supervised models is not currently supported` | Fitted with labels `y`. | Refit supervised UMAP on combined data, or use unsupervised UMAP if update is required. |
| Updated embedding changed old coordinates. | `update` mutates and reoptimizes the estimator. | Copy/serialize the original mapper before update if previous coordinates must remain unchanged. |
| Shape error on update. | New rows have different feature count or incompatible sparse/dense representation. | Ensure `X_new.shape[1] == original_feature_count` and use compatible preprocessing. |

## Precomputed k-NN issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Warning that `precomputed_knn` has fewer neighbors than `n_neighbors` and will be ignored. | `knn_indices.shape[1] < mapper.n_neighbors`. | Recompute k-NN with at least `n_neighbors` columns. |
| Warning that `precomputed_knn` has a different sample count and will be ignored. | k-NN rows do not match the fit data rows. | Recompute k-NN for exactly the same `X` passed to `fit`. |
| Transform unavailable after precomputed k-NN fit. | You supplied `(indices, dists)` without a search index. | Supply the full tuple returned by `umap.umap_.nearest_neighbors` if raw-data transform is required. |
| Reproducibility differs despite same UMAP seed. | The precomputed neighbor graph changed. | Keep k-NN random seed, k used for neighbor computation, neighbor data, and UMAP `random_state` fixed. |

## Disconnected vertices and NaN embeddings

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Warning: a few or many vertices were disconnected from the manifold. | `disconnection_distance` removed edges, or bounded/binary metrics produced maximally distant isolated points. | Inspect disconnected points with `umap.utils.disconnected_vertices(mapper)`. Filter them for visualization or remove/repair isolated rows before refitting. |
| `embedding_` contains `NaN` rows. | Fully disconnected vertices are assigned NaN coordinates. | Identify rows with `np.isnan(mapper.embedding_).any(axis=1)` or `disconnected_vertices`; decide whether to filter, impute features, change metric, increase `n_neighbors`, or adjust `disconnection_distance`. |
| Binary/Jaccard-like data collapses or pulls unrelated points together. | Rows share no features and are equally maximally distant. | Remove empty/near-empty rows, choose a more suitable metric/preprocessing, or tune `disconnection_distance`. |

## Memory, performance, and threading

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| High memory use in neighbor search. | Large dense data, high dimensions, or exact small-data distance matrix path. | Keep `low_memory=True`; use sparse input when natural; use precomputed k-NN for repeated fits; reduce sample/feature count if needed. |
| Fit is single-threaded even though `n_jobs=-1`. | `random_state` was set. | This is expected: reproducibility overrides parallelism. For speed, set `random_state=None`; for repeatability, keep the seed and accept slower execution. |
| Warning: `n_jobs value 1 overridden to 1 by setting random_state` or similar. | UMAP mutates `n_jobs` to 1 when seeded. | Treat as informational. Choose between reproducible and multicore modes explicitly. |
| First run is much slower than later runs. | numba JIT compilation. | Warm up on a small problem before timing or ignore first-run timings. |
| Too many CPU cores are used. | numba parallel sections use available threads. | Set `NUMBA_NUM_THREADS` before starting Python, or use a positive `n_jobs` when not setting `random_state`. |
| User asks about TBB. | Optional `umap-learn[tbb]` acceleration not installed in the minimum verified environment. | Explain that TBB is optional CPU optimization only; install the `tbb` extra in a suitable environment if performance tuning requires it. Do not make it a core dependency. |
| User asks for GPU acceleration in this package. | Core `umap.UMAP` does not provide verified GPU acceleration. | Do not promise GPU support from `umap-learn`; choose a separate GPU UMAP implementation only if the user explicitly wants one. |

## Optional dependency confusion

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `import umap.plot` raises ImportError. | Plotting extra not installed. | Core embedding does not require plotting. Route plotting tasks to `../../plotting-diagnostics/SKILL.md` and install/check the optional plot stack there. |
| `ParametricUMAP` raises TensorFlow/Keras ImportError. | Parametric extra not installed. | Route neural/parametric workflows to `../../parametric-umap/SKILL.md`; do not install TensorFlow for core embedding tasks. |
| No `umap` command exists. | Package has no console entry points. | Use Python imports and bundled scripts rather than expecting a CLI. |

## Minimal debug checklist

1. Print versions and signatures:
   ```bash
   python ../scripts/inspect_umap_estimator.py --json
   ```
2. Run a tiny local smoke:
   ```bash
   python ../scripts/umap_core_smoke.py --all --json
   ```
3. Confirm input shape: raw features `(n_samples, n_features)`, fit precomputed distances `(n_train, n_train)`, transform precomputed distances `(n_new, n_train)`.
4. Confirm data validity: finite values unless intentionally using `ensure_all_finite=False` or `'allow-nan'`.
5. Confirm metric/data compatibility: sparse metric for sparse data; gradient-backed metric for inverse transform; Euclidean output unless needed otherwise.
6. Decide reproducibility versus speed: `random_state` for repeatability, no seed for parallel speed.
