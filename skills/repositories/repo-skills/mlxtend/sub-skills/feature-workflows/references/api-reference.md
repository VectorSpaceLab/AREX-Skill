# API Reference: Feature Workflows

This reference covers mlxtend feature selection, feature extraction, transaction encoding, and preprocessing helpers. It intentionally excludes frequent itemset mining, estimator ensemble design, and plotting.

## Imports

```python
from mlxtend.feature_selection import (
    ColumnSelector,
    ExhaustiveFeatureSelector,
    SequentialFeatureSelector,
)
from mlxtend.feature_extraction import (
    LinearDiscriminantAnalysis,
    PrincipalComponentAnalysis,
    RBFKernelPCA,
)
from mlxtend.preprocessing import (
    CopyTransformer,
    DenseTransformer,
    MeanCenterer,
    TransactionEncoder,
    minmax_scaling,
    one_hot,
    shuffle_arrays_unison,
    standardize,
)
```

## Feature selection

### `ColumnSelector`

Verified constructor and methods:

```python
ColumnSelector(cols=None, drop_axis=False)
fit(X, y=None)
transform(X, y=None)
fit_transform(X, y=None)
```

| Argument | Contract |
| --- | --- |
| `cols` | Column index/name or list/tuple of indices/names. For pandas input, all elements must be all `int` or all `str`; integers use positional `iloc`, strings use label `loc`. For ndarray input, normal NumPy column indexing is used. |
| `drop_axis` | If `True` and one column is selected, return shape `(n_samples,)`; otherwise one-column output is reshaped to `(n_samples, 1)`. |

Output is a NumPy array slice, not a pandas DataFrame, even when input is a DataFrame.

### `SequentialFeatureSelector`

Verified constructor and methods:

```python
SequentialFeatureSelector(
    estimator,
    k_features=1,
    forward=True,
    floating=False,
    verbose=0,
    scoring=None,
    cv=5,
    n_jobs=1,
    pre_dispatch="2*n_jobs",
    clone_estimator=True,
    fixed_features=None,
    feature_groups=None,
    tol=None,
)
fit(X, y, groups=None, **fit_params)
transform(X)
fit_transform(X, y, groups=None, **fit_params)
get_metric_dict(confidence_interval=0.95)
finalize_fit()
```

| Argument | Contract and notes |
| --- | --- |
| `estimator` | sklearn-style classifier or regressor. If `scoring=None`, the estimator must expose classifier/regressor type so mlxtend can infer `accuracy` or `r2`. |
| `k_features` | `int`, `(min_k, max_k)`, `"best"`, or `"parsimonious"`. With `feature_groups`, this counts selected groups, not raw columns. |
| `forward`, `floating` | `forward=True` performs forward selection; `False` performs backward selection. `floating=True` adds conditional removal/inclusion steps. |
| `scoring` | sklearn scoring string or callable `scorer(estimator, X, y)`. Use explicit scoring for custom estimators or regression loss metrics. |
| `cv` | Integer or iterable of `(train, test)` splits. `None`, `False`, or `0` disables cross-validation and scores on the fitted data. Generator objects are rejected; materialize them with `list(...)`. |
| `groups` | Passed to the cross-validator through `fit(...)`, not the constructor. |
| `n_jobs`, `pre_dispatch` | Parallelize candidate subset scoring. Lower `pre_dispatch` to limit memory for large searches. |
| `clone_estimator` | If `False`, the original estimator is reused; pair with `cv=0` and `n_jobs=1` for non-clonable estimators. |
| `fixed_features` | Tuple/list of fixed column indices or names. Values must be all the same type; names require DataFrame input. |
| `feature_groups` | List of lists of column indices or names. Groups must cover every feature exactly once and must not overlap. Names require DataFrame input. |
| `tol` | Optional early-stop tolerance checked against the previous subset score after at least two steps. |

Fitted attributes:

| Attribute | Meaning |
| --- | --- |
| `k_feature_idx_` | Tuple of selected raw column indices. |
| `k_feature_names_` | Tuple of selected feature names; ndarray inputs use stringified indices. |
| `k_score_` | Average score for the selected subset. |
| `subsets_` | Dict keyed by selected size/group-count; each value contains `feature_idx`, `feature_names`, `cv_scores`, and `avg_score`. |
| `interrupted_`, `fitted` | Whether a `KeyboardInterrupt` occurred and whether final selection completed. |

`get_metric_dict()` returns a deep copy of `subsets_` with `std_dev`, `std_err`, and `ci_bound` added for each entry. Plotting this metric dictionary belongs to `../plotting-and-utilities/SKILL.md`.

### `ExhaustiveFeatureSelector`

Verified constructor and methods:

```python
ExhaustiveFeatureSelector(
    estimator,
    min_features=1,
    max_features=1,
    print_progress=True,
    scoring="accuracy",
    cv=5,
    n_jobs=1,
    pre_dispatch="2*n_jobs",
    clone_estimator=True,
    fixed_features=None,
    feature_groups=None,
)
fit(X, y, groups=None, **fit_params)
transform(X)
fit_transform(X, y, groups=None, **fit_params)
get_metric_dict(confidence_interval=0.95, top_k=None)
finalize_fit()
```

| Argument | Contract and notes |
| --- | --- |
| `min_features`, `max_features` | Inclusive subset-size bounds. With `feature_groups`, counts groups. Must satisfy bounds implied by fixed groups and total groups. |
| `print_progress` | Writes combination progress to stderr when `True`. Disable for scripts/tests. |
| `scoring`, `cv`, `groups`, `n_jobs`, `pre_dispatch`, `clone_estimator`, `fixed_features`, `feature_groups` | Same practical contracts as `SequentialFeatureSelector`. |

Fitted attributes:

| Attribute | Meaning |
| --- | --- |
| `best_idx_` | Tuple of selected raw column indices for the best-scoring subset. |
| `best_feature_names_` | Tuple of selected feature names; ndarray inputs use stringified indices. |
| `best_score_` | Average score for the best subset. |
| `subsets_` | Dict keyed by evaluated-combination iteration; each value contains `feature_idx`, `feature_names`, `cv_scores`, and `avg_score`. |

`get_metric_dict(top_k=N)` returns only the top-N subsets ranked by `avg_score` while preserving original iteration keys. `top_k=None` returns all evaluated subsets.

## Feature extraction

### `PrincipalComponentAnalysis`

Verified constructor and methods:

```python
PrincipalComponentAnalysis(n_components=None, solver="svd", whitening=False)
fit(X, y=None)
transform(X)
```

| Argument | Contract |
| --- | --- |
| `n_components` | Number of projected components. `None` or a value larger than `n_features` keeps `n_features` components. Must be positive when provided. |
| `solver` | Either `"svd"` or `"eigen"`. Component signs can differ between solvers; compare absolute projections/loadings when needed. |
| `whitening` | If `True`, rescales transformed components so their covariance is closer to identity. |

Input `X` must be a NumPy-like 2D array with shape `(n_samples, n_features)`. Fitted attributes include `w_`, `e_vals_`, `e_vecs_`, `e_vals_normalized_`, and `loadings_`. `transform(X)` returns an ndarray of shape `(n_samples, n_components_used)`.

### `LinearDiscriminantAnalysis`

Verified constructor and methods:

```python
LinearDiscriminantAnalysis(n_discriminants=None)
fit(X, y, n_classes=None)
transform(X)
```

| Argument | Contract |
| --- | --- |
| `n_discriminants` | Number of supervised discriminant axes. `None` or a value larger than `n_features` keeps `n_features` axes. Must be positive when provided. |
| `n_classes` | Optional class-count override for partial training sets. Use contiguous integer labels starting at 0 for safest behavior. |

Input `X` must be 2D and `y` must have one label per row. Fitted attributes include `w_`, `e_vals_`, and `e_vecs_`. `transform(X)` returns shape `(n_samples, n_discriminants_used)`.

### `RBFKernelPCA`

Verified constructor and methods:

```python
RBFKernelPCA(gamma=15.0, n_components=None, copy_X=True)
fit(X)
transform(X)
```

| Argument | Contract |
| --- | --- |
| `gamma` | RBF kernel coefficient; larger values make the kernel more local. |
| `n_components` | Number of projected kernel components. `None` or a value larger than `n_features` uses `n_features` components. Must be positive when provided. |
| `copy_X` | If `True`, stores a copy of training `X` for later projection of new samples. If `False`, later mutation of the original `X` can change transforms. |

Fitted attributes include `e_vals_`, `e_vecs_`, `X_projected_`, and `X_`. Kernel computations require memory proportional to training-sample pairwise distances.

## Preprocessing and encoding

### `TransactionEncoder`

Verified constructor and methods:

```python
TransactionEncoder()
fit(X)
transform(X, sparse=False)
fit_transform(X, sparse=False)
inverse_transform(array)
get_feature_names_out()
```

`X` is a Python list of transactions, where each transaction is a list of items. `fit` stores sorted unique item labels in `columns_` and an internal `columns_mapping_`. Dense `transform` returns a boolean ndarray of shape `(n_transactions, n_unique_items)`. `sparse=True` returns a boolean CSR matrix. `inverse_transform` maps one-hot rows back to item lists in `columns_` order.

With compatible sklearn versions, `TransactionEncoder().set_output(transform="pandas")` returns a pandas DataFrame with column names from `columns_`.

### `standardize`

Verified signature:

```python
standardize(array, columns=None, ddof=0, return_params=False, params=None)
```

Accepts a pandas DataFrame or NumPy ndarray. `columns=None` standardizes all columns; otherwise pass column labels for DataFrames or integer indices for ndarrays. One-dimensional arrays are treated as a single column. Constant columns are mapped to `0.0`, and their returned std parameter is forced to `1.0`. If `return_params=True`, returns `(standardized_columns, {"avgs": ..., "stds": ...})`; pass that dictionary as `params` to reuse training means/stds on new data.

### `minmax_scaling`

Verified signature:

```python
minmax_scaling(array, columns, min_val=0, max_val=1)
```

Accepts a pandas DataFrame or NumPy ndarray and rescales selected columns to `[min_val, max_val]`. Constant columns are flattened to `min_val` instead of producing NaNs. The return value is the selected scaled columns, not a whole-table wrapper around untouched columns.

### `MeanCenterer`

Verified constructor and methods:

```python
MeanCenterer()
fit(X)
transform(X)
fit_transform(X)
```

Stores `col_means` on `fit`. `transform` returns a copied, column-centered NumPy array and requires fitting first. List input is converted to a one-column float array.

### `DenseTransformer`

Verified constructor and methods:

```python
DenseTransformer(return_copy=True)
fit(X, y=None)
transform(X, y=None)
fit_transform(X, y=None)
```

Sparse input is converted with `.toarray()`. Dense input is copied when `return_copy=True`; otherwise the original object is returned. `fit` is a no-op except for setting an internal fitted flag.

### `CopyTransformer`

Verified constructor and methods:

```python
CopyTransformer()
fit(X, y=None)
transform(X, y=None)
fit_transform(X, y=None)
```

List input becomes a NumPy array. NumPy arrays and SciPy sparse arrays are copied. Other input types raise `ValueError`.

### `one_hot`

Verified signature:

```python
one_hot(y, num_labels="auto", dtype="float")
```

`y` must be one-dimensional integer labels used as direct column indices. `num_labels="auto"` uses `max(y) + 1`, so missing intermediate labels still create columns. Pass an integer `num_labels` to force width. The output is an ndarray with shape `(n_labels, num_labels_used)` and dtype `dtype`.

### `shuffle_arrays_unison`

Verified signature:

```python
shuffle_arrays_unison(arrays, random_seed=None)
```

`arrays` is a list of NumPy arrays with equal first-axis length. Returns a list of arrays permuted by the same random permutation. A non-zero `random_seed` seeds NumPy before shuffling.
