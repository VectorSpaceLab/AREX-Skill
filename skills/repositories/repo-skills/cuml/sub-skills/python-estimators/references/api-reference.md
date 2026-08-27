# python-estimators API reference

The constructor signatures below were checked against the installed cuML build
used for this draft. Recheck them in your active environment if you pin a
different release.

## Import surface

The main estimator families are available both from the family modules and as
`cuml` top-level re-exports.

- `cuml.cluster`: `KMeans`, `DBSCAN`, `HDBSCAN`
- `cuml.linear_model`: `LinearRegression`, `LogisticRegression`, `Ridge`, `Lasso`, `ElasticNet`
- `cuml.ensemble`: `RandomForestClassifier`, `RandomForestRegressor`
- `cuml.decomposition`: `PCA`, `TruncatedSVD`
- `cuml.neighbors`: `NearestNeighbors`, `KNeighborsClassifier`, `KNeighborsRegressor`
- `cuml.svm`: `SVC`, `SVR`, `LinearSVC`, `LinearSVR`
- `cuml.manifold`: `UMAP`, `TSNE`
- `cuml.tsa`: `ARIMA`, `AutoARIMA`, `ExponentialSmoothing`

## Output control

- `set_global_output_type(output_type)`
- `using_output_type(output_type)`
- valid values in the current build: `input`, `numpy`, `cupy`, `cudf`, `pandas`
- pass `None` to reset or inherit the default behavior

Prefer `numpy` in smoke scripts and parity checks because it makes host-side
assertions and pickling validation simpler.

## Clustering

- `KMeans`
  `(*, n_clusters=8, max_iter=300, tol=0.0001, verbose=False, random_state=None, init='scalable-k-means++', n_init='auto', oversampling_factor=2.0, max_samples_per_batch=32768, device_buffer_samples=0, init_size=0, output_type=None)`
  - common methods: `fit`, `predict`, `transform`, `fit_predict`, `score`, `as_sklearn`, `from_sklearn`
  - notes: centroid clustering; `fit_predict` is handy for labels, `predict` is the reusable inference path

- `DBSCAN`
  `(*, eps=0.5, min_samples=5, metric='euclidean', algorithm='brute', verbose=False, max_mbytes_per_batch=None, output_type=None, calc_core_sample_indices=True)`
  - common methods: `fit`, `fit_predict`, `as_sklearn`, `from_sklearn`
  - notes: density-based clustering; `fit_predict` is the usual entry point

- `HDBSCAN`
  `(*, min_cluster_size=5, min_samples=None, cluster_selection_epsilon=0.0, max_cluster_size=0, metric='euclidean', alpha=1.0, p=None, cluster_selection_method='eom', allow_single_cluster=False, gen_min_span_tree=False, verbose=False, output_type=None, prediction_data=False, build_algo='brute_force', build_kwds=None, device_ids=None)`
  - common methods: `fit`, `fit_predict`, `as_sklearn`, `from_sklearn`
  - notes: if you need later approximate prediction or membership vectors, set `prediction_data=True` before fitting; helpers such as `all_points_membership_vectors`, `membership_vector`, and `approximate_predict` live under the clustering module

## Linear models

- `LinearRegression`
  `(*, algorithm='auto', fit_intercept=True, copy_X=True, verbose=False, output_type=None)`
  - common methods: `fit`, `predict`, `score`, `as_sklearn`, `from_sklearn`

- `LogisticRegression`
  `(*, penalty='l2', tol=0.0001, C=1.0, fit_intercept=True, class_weight=None, max_iter=1000, linesearch_max_iter=50, l1_ratio=None, solver='qn', lbfgs_memory=5, penalty_normalized=True, verbose=False, output_type=None)`
  - common methods: `fit`, `predict`, `score`, `as_sklearn`, `from_sklearn`

- `Ridge`
  `(alpha=1.0, *, fit_intercept=True, solver='auto', tol=0.0001, max_iter=None, copy_X=True, output_type=None, verbose=False)`
  - common methods: `fit`, `predict`, `score`, `as_sklearn`, `from_sklearn`

- `Lasso`
  `(alpha=1.0, *, fit_intercept=True, max_iter=1000, tol=0.001, solver='auto', selection='cyclic', output_type=None, verbose=False)`
  - common methods: `fit`, `predict`, `score`, `as_sklearn`, `from_sklearn`

- `ElasticNet`
  `(alpha=1.0, *, l1_ratio=0.5, fit_intercept=True, max_iter=1000, tol=0.001, solver='auto', selection='cyclic', output_type=None, verbose=False)`
  - common methods: `fit`, `predict`, `score`, `as_sklearn`, `from_sklearn`

## Forests

- `RandomForestClassifier`
  `(*, n_estimators=100, split_criterion='gini', bootstrap=True, max_samples=1.0, max_depth=None, max_leaves=-1, max_features='sqrt', n_bins=128, min_samples_leaf=1, min_samples_split=2, min_impurity_decrease=0.0, max_batch_size=4096, random_state=None, n_streams=4, oob_score=False, class_weight=None, verbose=False, output_type=None)`
  - common methods: `fit`, `predict`, `score`, `predict_proba`, `as_sklearn`, `from_sklearn`
  - notes: classifier targets are usually easiest to handle as integer labels

- `RandomForestRegressor`
  `(*, n_estimators=100, split_criterion='mse', bootstrap=True, max_samples=1.0, max_depth=None, max_leaves=-1, max_features=1.0, n_bins=128, min_samples_leaf=1, min_samples_split=2, min_impurity_decrease=0.0, max_batch_size=4096, random_state=None, n_streams=4, oob_score=False, verbose=False, output_type=None)`
  - common methods: `fit`, `predict`, `score`, `as_sklearn`, `from_sklearn`

## Decomposition

- `PCA`
  `(*, copy=True, iterated_power=15, n_components=None, svd_solver='auto', tol=1e-07, verbose=False, whiten=False, output_type=None)`
  - common methods: `fit`, `transform`, `fit_transform`, `inverse_transform`, `as_sklearn`, `from_sklearn`
  - notes: a direct dense reduction path; use when you want principal components and explained-variance-style workflows

- `TruncatedSVD`
  `(*, algorithm='full', n_components=1, n_iter=15, random_state=None, tol=1e-07, verbose=False, output_type=None)`
  - common methods: `fit`, `transform`, `fit_transform`, `inverse_transform`, `as_sklearn`, `from_sklearn`
  - notes: the better default for sparse or text-style matrices

## Neighbors

- `NearestNeighbors`
  `(*, n_neighbors=5, radius=1.0, algorithm='auto', metric='euclidean', p=2, algo_params=None, metric_params=None, n_jobs=None, verbose=False, output_type=None)`
  - common methods: `fit`, `kneighbors`, `as_sklearn`, `from_sklearn`
  - notes: exact search uses FAISS in the current implementation; distance comparisons may need a tolerance when you compare to scikit-learn

- `KNeighborsClassifier`
  `(*, n_neighbors=5, algorithm='auto', metric='euclidean', weights='uniform', p=2, algo_params=None, metric_params=None, n_jobs=None, verbose=False, output_type=None)`
  - common methods: `fit`, `predict`, `kneighbors`, `score`, `as_sklearn`, `from_sklearn`

- `KNeighborsRegressor`
  `(*, n_neighbors=5, algorithm='auto', metric='euclidean', weights='uniform', p=2, algo_params=None, metric_params=None, n_jobs=None, verbose=False, output_type=None)`
  - common methods: `fit`, `predict`, `kneighbors`, `score`, `as_sklearn`, `from_sklearn`

## SVMs

- `SVC`
  `(*, C=1.0, kernel='rbf', degree=3, gamma='scale', coef0=0.0, tol=0.001, cache_size=1024.0, max_iter=-1, nochange_steps=1000, verbose=False, output_type=None, random_state=None, class_weight=None, decision_function_shape='ovo')`
  - common methods: `fit`, `predict`, `score`, `as_sklearn`, `from_sklearn`

- `SVR`
  `(*, C=1.0, kernel='rbf', degree=3, gamma='scale', coef0=0.0, tol=0.001, epsilon=0.1, cache_size=1024.0, max_iter=-1, nochange_steps=1000, verbose=False, output_type=None)`
  - common methods: `fit`, `predict`, `score`, `as_sklearn`, `from_sklearn`

- `LinearSVC`
  `(*, penalty='l2', loss='squared_hinge', C=1.0, fit_intercept=True, penalized_intercept=False, class_weight=None, tol=0.0001, max_iter=1000, linesearch_max_iter=100, lbfgs_memory=5, n_streams=1, multi_class='ovr', verbose=False, output_type=None)`
  - common methods: `fit`, `predict`, `score`, `as_sklearn`, `from_sklearn`

- `LinearSVR`
  `(*, epsilon=0.0, penalty='l1', loss='epsilon_insensitive', C=1.0, fit_intercept=True, penalized_intercept=False, tol=0.0001, max_iter=1000, linesearch_max_iter=100, lbfgs_memory=5, verbose=False, output_type=None)`
  - common methods: `fit`, `predict`, `score`, `as_sklearn`, `from_sklearn`

## Manifold

- `UMAP`
  `(*, n_neighbors=15, n_components=2, metric='euclidean', metric_kwds=None, n_epochs=None, learning_rate=1.0, min_dist=0.1, spread=1.0, set_op_mix_ratio=1.0, local_connectivity=1.0, repulsion_strength=1.0, negative_sample_rate=5, transform_queue_size=4.0, init='spectral', a=None, b=None, target_n_neighbors=-1, target_weight=0.5, target_metric='categorical', hash_input=False, random_state=None, force_serial_epochs=None, precomputed_knn=None, callback=None, build_algo='auto', build_kwds=None, device_ids=None, verbose=False, output_type=None)`
  - common methods: `fit`, `transform`, `fit_transform`, `as_sklearn`, `from_sklearn`
  - notes: direct UMAP control lives here; unchanged UMAP code can route to `sklearn-accel`; `device_ids` exists on the direct estimator for device selection in supported setups

- `TSNE`
  `(*, n_components=2, perplexity=30.0, early_exaggeration=12.0, late_exaggeration=1.0, learning_rate=200.0, max_iter=1000, n_iter_without_progress=300, min_grad_norm=1e-07, metric='euclidean', metric_params=None, init='random', random_state=None, method='fft', angle=0.5, n_neighbors=90, perplexity_max_iter=100, exaggeration_iter=250, pre_momentum=0.5, post_momentum=0.8, learning_rate_method='adaptive', square_distances=True, precomputed_knn=None, verbose=False, output_type=None)`
  - common methods: `fit`, `fit_transform`, `as_sklearn`, `from_sklearn`
  - notes: embedding-only workflow; use `fit_transform` to get coordinates

## Time series

The `cuml.tsa` family is deprecated and should be treated as a special-case
compatibility path rather than a primary long-term route.

- `ARIMA`
  `(endog, *, order=(1, 1, 1), seasonal_order=(0, 0, 0, 0), exog=None, fit_intercept=True, simple_differencing=True, verbose=False, output_type=None)`
  - common methods: `fit`, `predict`, `forecast`
  - notes: estimator-like time-series modeling for explicit ARIMA workflows

- `AutoARIMA`
  `(endog, *, simple_differencing=True, verbose=False, output_type=None)`
  - common methods: `fit`, `predict`, `forecast`
  - notes: automatic order search for the same deprecated time-series family

- `ExponentialSmoothing`
  `(endog, *, seasonal='additive', seasonal_periods=2, start_periods=2, ts_num=1, eps=0.00224, verbose=False, output_type=None)`
  - common methods: `fit`, `forecast`, `score`, `get_level`, `get_trend`, `get_season`
  - notes: keep this as a deliberate compatibility workflow; it is still useful when the problem is clearly time-series smoothing rather than a general tabular estimator

## Interoperability

Most of the estimators above also expose `as_sklearn()` and `from_sklearn()` for
conversion when a scikit-learn-shaped object is the right downstream artifact.
That is distinct from the safe persistence path in this sub-skill: for stored
artifacts, use only trusted local `pickle` or `joblib` files.
