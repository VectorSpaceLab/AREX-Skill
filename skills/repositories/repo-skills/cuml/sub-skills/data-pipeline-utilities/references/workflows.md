# Workflows: data-pipeline utilities

Use these recipes to assemble support steps around cuML models. They intentionally stop at utility validation; route full fitting, prediction, and model-quality analysis to `python-estimators` unless this reference explicitly says otherwise.

## 1. Start with a tiny CUDA-gated utility smoke

From the generated skill root, run:

```bash
python sub-skills/data-pipeline-utilities/scripts/data_utility_smoke.py --case core
```

Expected signal: the script reports a visible CUDA device, generates tiny datasets, splits data, applies preprocessing, and computes metrics without importing any original repository checkout.

If this fails before imports or CUDA allocation, stop and use root troubleshooting first. Utility behavior cannot be validated with CPU-only import checks.

## 2. Generate, split, scale, and score utility outputs

Use this pattern when a downstream task needs a small, reproducible dataset and utility sanity checks before estimator work.

```python
import cupy as cp
from cuml.datasets import make_classification, make_regression, make_blobs
from cuml.model_selection import train_test_split, KFold
from cuml.preprocessing import StandardScaler, LabelEncoder
from cuml.metrics import accuracy_score, mean_squared_error, pairwise_distances
from cuml.metrics.cluster import adjusted_rand_score

X, y = make_classification(
    n_samples=128,
    n_features=8,
    n_informative=4,
    n_redundant=0,
    n_classes=2,
    random_state=7,
    order="F",
    dtype="float32",
)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=7, shuffle=True, stratify=y
)

X_train_scaled = StandardScaler().fit_transform(X_train)
y_train_encoded = LabelEncoder().fit_transform(y_train)

# Utility-only checks; do not treat these as model quality.
assert X_train_scaled.shape[0] == y_train_encoded.shape[0]
assert float(accuracy_score(y_test, y_test)) == 1.0

X_reg, y_reg = make_regression(
    n_samples=64, n_features=6, n_informative=4, noise=0.0, random_state=11
)
assert float(mean_squared_error(y_reg, y_reg)) == 0.0

X_blobs, labels = make_blobs(n_samples=64, centers=3, n_features=4, random_state=5)
assert float(adjusted_rand_score(labels, labels)) == 1.0
D = pairwise_distances(X_train_scaled[:4], metric="euclidean")
assert D.shape == (4, 4)

folds = list(KFold(n_splits=4, shuffle=True, random_state=3).split(X))
assert len(folds) == 4
```

Handoff points:

- If the next step is fitting `KMeans`, `LinearRegression`, `RandomForest`, `SVC`, `UMAP`, or another estimator, switch to `python-estimators`.
- If arrays need distributed partitioning before utility calls, switch to `distributed-dask`.
- If the user wants to keep existing scikit-learn code unchanged, switch to `sklearn-accel` instead of rewriting utility imports.

## 3. Leakage-aware TargetEncoder workflow

Use `TargetEncoder` for high-cardinality categorical features when label/ordinal encoding is too arbitrary and one-hot encoding is too wide. The key rule is that training and validation/test data are encoded differently.

```python
import cudf
from cuml.preprocessing import TargetEncoder

train = cudf.DataFrame({
    "city": ["a", "b", "b", "a", "c", "c"],
    "device": ["m", "m", "w", "w", "m", "w"],
})
y = cudf.Series([1, 0, 1, 1, 0, 0])
valid = cudf.DataFrame({"city": ["a", "d"], "device": ["m", "w"]})

encoder = TargetEncoder(
    n_folds=3,
    smooth=1,
    split_method="interleaved",
    stat="mean",
    multi_feature_mode="combination",
    output_type="numpy",
)

train_encoded = encoder.fit_transform(train[["city", "device"]], y)
valid_encoded = encoder.transform(valid[["city", "device"]])
assert train_encoded.shape == (len(train), 1)
assert valid_encoded.shape == (len(valid), 1)
```

Decision rules:

- Use `fit_transform(X_train, y_train)` for training rows so each row is encoded with out-of-fold target statistics.
- Use `transform(X_valid_or_test)` for validation/test rows so unseen categories receive the learned global statistic rather than leaking validation labels.
- Choose `multi_feature_mode="combination"` when the joint category tuple matters; choose `"independent"` when each input categorical feature should become its own encoded column.
- For externally-defined folds, set `split_method="customize"` and pass `fold_ids` to `fit` or `fit_transform`.
- If target encoding feeds a model, route the subsequent estimator fit/evaluation to `python-estimators`.

## 4. Text feature extraction workflow

Use cuML text vectorizers when the corpus is already in cuDF/pandas Series form and the downstream model can consume CuPy CSR sparse matrices or you will explicitly densify a tiny result.

```python
import cudf
from cuml.feature_extraction.text import CountVectorizer, HashingVectorizer, TfidfVectorizer

corpus = cudf.Series([
    "gpu text gpu",
    "cuml text vector",
    "gpu vector",
])

count = CountVectorizer(lowercase=True, ngram_range=(1, 1), min_df=1)
X_count = count.fit_transform(corpus)
terms = list(count.get_feature_names().to_pandas())

hashing = HashingVectorizer(n_features=2**8, norm="l2")
X_hash = hashing.fit_transform(corpus)

tfidf = TfidfVectorizer(lowercase=True, use_idf=True, smooth_idf=True)
X_tfidf = tfidf.fit_transform(corpus)

assert X_count.shape[0] == len(corpus)
assert X_hash.shape[0] == len(corpus)
assert X_tfidf.shape[0] == len(corpus)
```

Decision rules:

- Prefer `HashingVectorizer` for streaming or memory-constrained workflows where storing a vocabulary is not required.
- Prefer `CountVectorizer` when feature names and inverse transforms are needed.
- Prefer `TfidfVectorizer` when document-frequency reweighting is required.
- Do not pass unsupported scikit-learn-only parameters such as custom tokenizers or callable analyzers; pre-clean the text in cuDF/pandas before vectorization instead.
- For distributed text vectorization, route to `distributed-dask` because data partitioning and optional dependencies change the workflow.

## 5. Metric selection workflow

Use metrics to validate containers, scoring direction, and expected numeric ranges before heavier training.

- Classification labels or class probabilities:
  - Accuracy: `accuracy_score(y_true, y_pred)`.
  - Confusion counts/rates: `confusion_matrix(y_true, y_pred, labels=..., normalize=...)`.
  - Binary ranking: `roc_auc_score(y_true, y_score)` and `precision_recall_curve(y_true, probs_pred)`; verify both classes are present.
  - Probabilistic loss: `log_loss(y_true, y_pred_proba)`; verify probability shape and no all-one-class target.
- Regression:
  - Absolute/squared error: `mean_absolute_error`, `mean_squared_error`, `median_absolute_error`.
  - Log-scale error: `mean_squared_log_error`, but only with nonnegative targets and predictions.
  - Explained variance-style score: `r2_score` with explicit `multioutput` when multiple targets are present.
- Clustering:
  - Use `adjusted_rand_score`, `homogeneity_score`, `completeness_score`, `v_measure_score`, or `mutual_info_score` when matching labels against known groupings.
  - Use `silhouette_score` or `silhouette_samples` to evaluate compactness/separation; set `chunksize` to reduce peak memory.
- Pairwise utilities:
  - Use `pairwise_distances` for dense/sparse distance matrices.
  - Use `nan_euclidean_distances` when NaNs or a sentinel missing value must be ignored and reweighted.
  - Use `pairwise_kernels` for kernel matrices; choose `precomputed` only when `X` is already a kernel matrix.

Always assert the shape of metric inputs before calling. Most failures are caused by inconsistent sample counts, 2-D label arrays where 1-D labels are expected, mixed dense/sparse containers, or unsupported metric/keyword combinations.

## 6. Explainer setup workflow

Use explainers after the model is already available. Keep the background set small during setup.

### Kernel or permutation explainer

```python
from cuml.explainer import KernelExplainer, PermutationExplainer

# `model_predict` must accept either GPU arrays or CPU arrays consistently.
explainer = KernelExplainer(
    model=model_predict,
    data=background_X,
    nsamples="auto",
    is_gpu_model=True,
    output_type="numpy",
)
values = explainer.shap_values(X_to_explain[:2])
```

- Use `is_gpu_model=True` when the callable accepts CuPy/cuDF inputs and returns GPU-friendly outputs.
- Use `is_gpu_model=False` for CPU callables; expect data transfers to dominate small runs.
- Use `PermutationExplainer(...).shap_values(X, npermutations=...)` when permutation semantics are preferred or Kernel SHAP cost is too high.

### Tree explainer

```python
from cuml.explainer import TreeExplainer

explainer = TreeExplainer(model=trained_tree_model, data=background_X)
values = explainer.shap_values(X_to_explain[:2])
```

- Supported model families include XGBoost, LightGBM, cuML RandomForest, scikit-learn RandomForest, and Treelite model objects.
- If `data` is omitted, tree-path-dependent statistics are used. If `data` is supplied, the interventional approach is used and runtime scales with background rows.
- Route model training and random-forest-specific behavior to `python-estimators` before using this explainer.

## 7. Time-series schema utility workflow

The time-series APIs are deprecated, but existing tasks may still need schema handling or small compatibility checks.

```python
import warnings
from cuml.datasets import make_arima

with warnings.catch_warnings():
    warnings.simplefilter("ignore", FutureWarning)
    y = make_arima(
        batch_size=2,
        n_obs=24,
        order=(1, 0, 0),
        seasonal_order=(0, 0, 0, 0),
        intercept=True,
        random_state=5,
        dtype="float32",
    )
assert y.shape == (24, 2)
```

Schema rules for ARIMA-like APIs:

- `endog` is shaped `(n_obs, batch_size)`; each column is one time series.
- Missing endogenous observations can be represented with `NaN`, including leading padding for unequal lengths; early predictions over padded ranges may be constant or unavailable.
- Seasonal order is `(P, D, Q, s)` and model constraints can reject excessive AR/seasonal combinations.
- Exogenous variables are shaped `(n_obs, batch_size * n_exog)`; future exogenous rows for forecasts are shaped `(nsteps, batch_size * n_exog)`.
- Exogenous variables cannot contain missing values. Duplicate shared exogenous variables per series if multiple series need the same covariate.

Route actual ARIMA/AutoARIMA/ExponentialSmoothing fitting, forecasts, confidence intervals, and model-selection decisions to `python-estimators`.
