# API reference: data-pipeline utilities

This reference covers cuML utilities that prepare, split, transform, explain, and score data for GPU ML workflows. It is intentionally focused on support APIs; route estimator fitting and prediction to `python-estimators` unless the task is only validating utility behavior.

## Runtime assumptions

- cuML utility calls execute through the installed cuML package and normally require an NVIDIA CUDA backend for meaningful runtime validation.
- cuML accepts common host and device containers across many APIs: NumPy arrays, pandas objects, CuPy arrays, cuDF DataFrames/Series, and CUDA array-interface objects. Individual APIs have narrower requirements, especially text vectorizers, time-series, and sparse/pairwise routines.
- Outputs usually follow the input type, the estimator `output_type`, or the global cuML output setting. When exact container type matters, set `output_type` explicitly where supported or validate the returned type before chaining.
- Prefer `float32` for small GPU utility checks unless the API or task requires `float64` precision.

## Dataset generators

Import from `cuml.datasets` for explicit code. Some versions also expose selected generators at the `cuml` top level.

| API | Signature | Returns | Notes |
| --- | --- | --- | --- |
| `make_blobs` | `make_blobs(n_samples=100, n_features=2, centers=None, cluster_std=1.0, center_box=(-10.0, 10.0), shuffle=True, random_state=None, return_centers=False, order='F', dtype='float32')` | `X`, `y`, and optionally `centers` as device arrays | Clustering toy data. `centers=None` defaults to 3 centers for integer `n_samples`; array-like `n_samples` gives per-center counts. `order` may be `F` or `C` and is useful when validating downstream layout requirements. |
| `make_classification` | `make_classification(n_samples=100, n_features=20, n_informative=2, n_redundant=2, n_repeated=0, n_classes=2, n_clusters_per_class=2, weights=None, flip_y=0.01, class_sep=1.0, hypercube=True, shift=0.0, scale=1.0, shuffle=True, random_state=None, order='F', dtype='float32')` | `X`, `y` as device arrays | Classification toy data. Ensure `n_informative + n_redundant + n_repeated <= n_features`; also ensure `n_classes * n_clusters_per_class <= 2**n_informative`. `random_state` gives reproducible generated data. |
| `make_regression` | `make_regression(n_samples=100, n_features=2, n_informative=2, n_targets=1, bias=0.0, effective_rank=None, tail_strength=0.5, noise=0.0, shuffle=True, coef=False, random_state=None, dtype='float32')` | `X`, `y`, and optionally `coef` | Regression toy data. If `coef=True`, a third device array with underlying coefficients is returned. `n_targets>1` returns a 2-D target. |
| `make_arima` | `make_arima(batch_size=1000, n_obs=100, order=(1, 1, 1), seasonal_order=(0, 0, 0, 0), intercept=False, random_state=None, dtype='float64')` | Array of shape `(n_obs, batch_size)` | Generates synthetic ARIMA time-series batches. This API is deprecated with `cuml.tsa`; use only when a task explicitly needs cuML time-series compatibility. `dtype` must be float32 or float64. |

## Model-selection utilities

| API | Signature | Notes |
| --- | --- | --- |
| `train_test_split` | `train_test_split(*arrays, test_size=None, train_size=None, random_state=None, shuffle=True, stratify=None)` | Splits one or more arrays with consistent first dimension. Inputs may be cuDF, CuPy, NumPy, pandas, or array-like. Outputs preserve input container families where possible. `stratify` is useful for class-balanced splits; validate class counts before using small data. |
| `KFold` | `KFold(n_splits=5, *, shuffle=False, random_state=None)` | `split(X, y=None)` yields CuPy train/test index arrays. `n_splits` must be at least 2 and no greater than the sample count. `random_state` affects only `shuffle=True`. |

## Preprocessing: scalers, transforms, and imputers

These follow cuML's scikit-learn-style transformer contract: instantiate, `fit`, `transform`, or `fit_transform`; preserve or configure output type; and validate the transformed shape before passing to estimators.

Common classes:

- Scaling/normalization: `StandardScaler`, `MinMaxScaler`, `MaxAbsScaler`, `RobustScaler`, `Normalizer`, `PowerTransformer`, `QuantileTransformer`.
- Feature construction: `PolynomialFeatures`, `KernelCenterer`, `FunctionTransformer`, `KBinsDiscretizer`, `add_dummy_feature`.
- Thresholding/functions: `Binarizer`, `binarize`, `scale`, `minmax_scale`, `maxabs_scale`, `robust_scale`, `normalize`.
- Missingness: `SimpleImputer`, `MissingIndicator`.

Functional helper signatures verified in the package:

```python
add_dummy_feature(X, value=1.0)
binarize(X, *, threshold=0.0, copy=True)
maxabs_scale(X, *, axis=0, copy=True)
minmax_scale(X, feature_range=(0, 1), *, axis=0, copy=True)
normalize(X, norm='l2', *, axis=1, copy=True, return_norm=False)
robust_scale(X, *, axis=0, with_centering=True, with_scaling=True, quantile_range=(25.0, 75.0), copy=True)
scale(X, *, axis=0, with_mean=True, with_std=True, copy=True)
```

Practical notes:

- Many preprocessing transforms expect dense numeric inputs; text vectorizers return sparse matrices and should be routed only to estimators that accept sparse input.
- `copy=False` can reduce memory pressure but may mutate inputs. Use it only when downstream code does not reuse the raw data.
- `with_mean=True` on sparse data is commonly invalid because centering destroys sparsity; choose sparse-compatible paths when needed.

## Preprocessing: encoders

| API | Signature | Notes |
| --- | --- | --- |
| `LabelEncoder` | `LabelEncoder(*, handle_unknown='error', verbose=False, output_type=None)` | Encodes 1-D labels or categorical values to integers. Fit on the union of categories required at transform time or set behavior for unknowns when supported by the chosen version. |
| `LabelBinarizer` | `LabelBinarizer(*, neg_label=0, pos_label=1, sparse_output=False, verbose=False, output_type=None)` | Converts labels to binary/one-vs-rest indicator form. Validate label order and output type before using the result as a target matrix. |
| `label_binarize` | `label_binarize(y, classes, neg_label=0, pos_label=1, sparse_output=False)` | Functional label binarization. Pass the full class list explicitly. |
| `OneHotEncoder` | `OneHotEncoder(*, categories='auto', drop=None, sparse_output=True, dtype=np.float32, handle_unknown='error', verbose=False, output_type=None)` | Encodes categorical columns into sparse or dense indicators. Use `sparse_output=True` for high-cardinality categories unless a downstream estimator requires dense input. |
| `OrdinalEncoder` | `OrdinalEncoder(*, categories='auto', dtype=np.float64, handle_unknown='error', verbose=False, output_type=None)` | Converts categorical feature columns to ordinal numbers. Do not treat the numeric order as semantic unless the task actually has ordered categories. |
| `TargetEncoder` | `TargetEncoder(*, n_folds=4, smooth=0, seed=42, split_method='interleaved', verbose=False, output_type=None, stat='mean', multi_feature_mode='combination')` | Leakage-aware target encoding. Use `fit_transform` for training data and `transform` for validation/test data. Supports `stat` in `mean`, `var`, or `median`; `split_method` in `interleaved`, `random`, `continuous`, or customized folds with `fold_ids`; `multi_feature_mode='combination'` returns one joint feature while `'independent'` returns one feature per input column. |

TargetEncoder method notes:

```python
encoder.fit(X, y, *, fold_ids=None)
encoder.fit_transform(X, y, *, fold_ids=None)
encoder.transform(X)
```

- Training data is encoded with fold-out statistics to limit leakage; test data is encoded with global learned category statistics.
- Unseen categories are imputed with the learned global statistic.
- For multi-feature input, `combination` encodes the joint category tuple. Use `independent` for one output column per original feature and better scikit-learn conversion compatibility.

## Metrics

### Classification and ranking

| API | Signature | Notes |
| --- | --- | --- |
| `accuracy_score` | `accuracy_score(y_true, y_pred, *, sample_weight=None, normalize=True)` | Scalar sample weights are accepted as equivalent to constant weighting; shape consistency is enforced. |
| `confusion_matrix` | `confusion_matrix(y_true, y_pred, labels=None, sample_weight=None, normalize=None)` | Returns a CuPy array. `normalize` supports the scikit-learn-style modes accepted by the installed version; invalid labels or normalization raise `ValueError`. |
| `log_loss` | `log_loss(y_true, y_pred, eps=1e-15, normalize=True, sample_weight=None)` | Requires probabilities and at least two classes. Check probability shape for binary vs multiclass tasks. |
| `roc_auc_score` | `roc_auc_score(y_true, y_score)` | Binary score utility. Fails when the target contains only one class. |
| `precision_recall_curve` | `precision_recall_curve(y_true, probs_pred)` | Binary curve utility. Fails when all targets are one class. |
| `kl_divergence` | `kl_divergence(P, Q)` | Distribution divergence; validate nonnegative inputs and matching shapes. |
| `trustworthiness` | `trustworthiness(X, X_embedded, n_neighbors=5, metric='euclidean', batch_size=512)` | Embedding quality metric; use small `batch_size` when device memory is constrained. |

### Regression

```python
mean_absolute_error(y_true, y_pred, sample_weight=None, multioutput='uniform_average')
mean_squared_error(y_true, y_pred, sample_weight=None, multioutput='uniform_average', squared=True)
mean_squared_log_error(y_true, y_pred, sample_weight=None, multioutput='uniform_average', squared=True)
median_absolute_error(y_true, y_pred, *, sample_weight=None, multioutput='uniform_average')
r2_score(y_true, y_pred, *, sample_weight=None, multioutput='uniform_average', force_finite=True)
```

Notes:

- `multioutput` supports uniform averaging, raw values, and custom output weights where implemented.
- `mean_squared_log_error` rejects negative targets or predictions.
- `r2_score(force_finite=True)` replaces non-finite constant-target cases with finite values.

### Clustering

```python
from cuml.metrics import cluster
cluster.adjusted_rand_score(labels_true, labels_pred)
cluster.entropy(clustering, base=None)
cluster.homogeneity_score(labels_true, labels_pred)
cluster.completeness_score(labels_true, labels_pred)
cluster.mutual_info_score(labels_true, labels_pred)
cluster.v_measure_score(labels_true, labels_pred, beta=1.0)
cluster.silhouette_score(X, labels, metric='euclidean', chunksize=None)
cluster.silhouette_samples(X, labels, metric='euclidean', chunksize=None)
```

Silhouette methods can use `chunksize` to trade memory for additional computation. Label permutation-invariant metrics should be preferred when validating clustering outputs.

### Pairwise distances and kernels

```python
pairwise_distances(X, Y=None, metric='euclidean', **kwds)
nan_euclidean_distances(X, Y=None, *, squared=False, missing_values=np.nan, copy=True)
pairwise_kernels(X, Y=None, metric='linear', *, filter_params=False, **kwds)
```

Distance metrics:

- Dense and sparse: `canberra`, `chebyshev`, `cityblock`, `cosine`, `euclidean`, `hellinger`, `l1`, `l2`, `manhattan`, `minkowski`, `sqeuclidean`.
- Dense only: `correlation`, `hamming`, `jensenshannon`, `kldivergence`, `nan_euclidean`, `russellrao`.
- Sparse only: `dice`, `inner_product`, `jaccard`.
- `minkowski` accepts `p`; `nan_euclidean` accepts `squared`, `missing_values`, and `copy`.

Kernel metrics: `linear`, `additive_chi2`, `chi2`, `cosine`, `laplacian`, `polynomial`/`poly`, `rbf`, `sigmoid`, `precomputed`, or a Numba CUDA device callable. `chi2` and `additive_chi2` require nonnegative inputs. Use `filter_params=True` to ignore unsupported keyword parameters when matching scikit-learn-style code.

## Text feature extraction

Import from `cuml.feature_extraction.text`.

| API | Signature | Output | Notes |
| --- | --- | --- | --- |
| `CountVectorizer` | `CountVectorizer(input=None, encoding=None, decode_error=None, strip_accents=None, lowercase=True, preprocessor=None, tokenizer=None, stop_words=None, token_pattern=None, ngram_range=(1, 1), analyzer='word', max_df=1.0, min_df=1, max_features=None, vocabulary=None, binary=False, dtype=np.float32, delimiter=' ')` | CuPy CSR sparse matrix | Learns a cuDF `vocabulary_`. `raw_documents` should be a cuDF or pandas Series of strings. Unsupported scikit-learn parameters such as non-`None` `input`, `encoding`, `decode_error`, `strip_accents`, `tokenizer`, or `token_pattern` raise errors. Callable analyzers are not supported. |
| `HashingVectorizer` | `HashingVectorizer(input=None, encoding=None, decode_error=None, strip_accents=None, lowercase=True, preprocessor=None, tokenizer=None, stop_words=None, token_pattern=None, ngram_range=(1, 1), analyzer='word', n_features=1048576, binary=False, norm='l2', alternate_sign=True, dtype=np.float32, delimiter=' ')` | CuPy CSR sparse matrix | Stateless; supports `fit`, `partial_fit`, `transform`, `fit_transform`. No inverse vocabulary because hashed features can collide. `norm` is `l1`, `l2`, or `None`. |
| `TfidfVectorizer` | `TfidfVectorizer(..., norm='l2', use_idf=True, smooth_idf=True, sublinear_tf=False)` with the same core vocabulary parameters as `CountVectorizer` | CuPy CSR sparse matrix | Equivalent to count vectorization followed by TF-IDF transformation. `idf_`, `vocabulary_`, and `stop_words_` are available after fitting. |

## Explainers

Use explainers only after a model is already trained elsewhere. This sub-skill owns the explainer setup and failure modes, not estimator selection.

| API | Signature | Use when |
| --- | --- | --- |
| `KernelExplainer` | `KernelExplainer(*, model, data, nsamples='auto', link='identity', verbose=False, random_state=None, is_gpu_model=None, dtype=np.float32, output_type=None)` | Model-agnostic SHAP with a prediction callable and dense tabular background data. Good for fast GPU model callables; CPU callables work but may be transfer-bound. |
| `PermutationExplainer` | `PermutationExplainer(*, model, data, masker_type='independent', link='identity', is_gpu_model=None, random_state=None, dtype=np.float32, output_type=None, verbose=False)` | Model-agnostic permutation SHAP; `shap_values(X, npermutations=10, as_list=True)` controls cost. |
| `TreeExplainer` | `TreeExplainer(*, model, data=None)` | Tree SHAP for XGBoost, LightGBM, cuML RandomForest, scikit-learn RandomForest, or Treelite models. Optional `data` switches to an interventional background approach. Multi-target tree models are not supported. |

Explainer `shap_values(X)` outputs feature-attribution arrays. Keep background data small (for example, tens to hundreds of rows for smoke checks) before scaling.

## Time-series utility APIs

The `cuml.tsa` surface is deprecated and scheduled for removal in a future cuML release. Route full ARIMA or ExponentialSmoothing model work to `python-estimators`; use this section only to prepare schemas, generate small synthetic batches, or diagnose utility-level data layout.

| API | Signature | Notes |
| --- | --- | --- |
| `cuml.tsa.ARIMA` | `ARIMA(endog, *, order=(1, 1, 1), seasonal_order=(0, 0, 0, 0), exog=None, fit_intercept=True, simple_differencing=True, verbose=False, output_type=None)` | `endog` is shaped `(n_obs, batch_size)`. Seasonal order is `(P, D, Q, s)`. Exogenous data must align as `(n_obs, batch_size * n_exog)` and future exogenous values must be supplied for forecasts. |
| `cuml.tsa.auto_arima.AutoARIMA` | `AutoARIMA(endog, *, simple_differencing=True, verbose=False, output_type=None)` | Automated order selection for batches. Higher cost than schema checks; keep sample sizes small unless explicitly requested. |
| `cuml.tsa.ExponentialSmoothing` | `ExponentialSmoothing(endog, *, seasonal='additive', seasonal_periods=2, start_periods=2, ts_num=1, eps=0.00224, verbose=False, output_type=None)` | Batch-friendly seasonal smoothing. Validate `seasonal_periods`, `ts_num`, and forecast horizon. |

Useful method signatures:

```python
ARIMA.fit(start_params=None, opt_disp=-1, h=1e-8, maxiter=1000, method='ml', truncate=0)
ARIMA.predict(start=0, end=None, level=None, exog=None)
ARIMA.forecast(nsteps, level=None, exog=None)
AutoARIMA.fit(h=1e-8, maxiter=1000, method='ml', truncate=0)
AutoARIMA.predict(start=0, end=None, level=None)
AutoARIMA.forecast(nsteps, level=None)
ExponentialSmoothing.fit()
ExponentialSmoothing.forecast(h=1, index=None)
ExponentialSmoothing.score(index=None)
```
