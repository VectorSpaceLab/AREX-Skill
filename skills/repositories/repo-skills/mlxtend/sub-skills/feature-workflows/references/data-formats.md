# Data Formats: Feature Workflows

Use this reference to align array, DataFrame, transaction, selector-metric, sparse, and one-hot schemas before running mlxtend feature workflows.

## Core tabular schemas

| Data | Accepted schema | Notes |
| --- | --- | --- |
| `X` for selectors | 2D NumPy ndarray, SciPy sparse matrix, or pandas DataFrame with shape `(n_samples, n_features)` | DataFrames preserve column names for fitted selector attributes. Sparse matrices may work for selectors but not all downstream estimators/scorers accept them. |
| `y` for selectors and LDA | 1D array-like with shape `(n_samples,)` | Must align row-for-row with `X`. For LDA, contiguous integer class labels starting at 0 are safest. |
| `groups` for grouped CV | 1D array-like with shape `(n_samples,)` | Pass to `selector.fit(X, y, groups=groups)`. If precomputing splits, pass an iterable/list of `(train, test)` arrays as `cv`. |
| `X` for PCA/LDA/RBFKernelPCA | 2D NumPy-like array with shape `(n_samples, n_features)` | Lists are rejected by feature extraction base checks; convert with `np.asarray(..., dtype=float)`. |
| preprocessing arrays | pandas DataFrame or NumPy ndarray for scaling; list/ndarray for some transformers | `standardize` and `minmax_scaling` require objects with `.astype`; use arrays/DataFrames rather than raw nested lists. |

## DataFrame vs ndarray feature identities

| Input type | Selector index fields | Selector name fields | String groups/fixed features? |
| --- | --- | --- | --- |
| NumPy ndarray | Raw integer positions, e.g. `(1, 3)` | Stringified positions, e.g. `("1", "3")` | No. Use integer indices. |
| pandas DataFrame | Raw integer positions, e.g. `(1, 3)` | Column labels, e.g. `("sepal_width", "petal_width")` | Yes, if every referenced name is present. |

`ColumnSelector` returns NumPy arrays for both ndarray and DataFrame inputs. It does not preserve a DataFrame object.

## Feature group schema

`feature_groups` is either all integers or all strings:

```python
feature_groups = [[0], [1, 2], [3]]
# or, with DataFrame input:
feature_groups = [["sepal_len"], ["sepal_width", "petal_len"], ["petal_width"]]
```

Rules:

1. Outer list length is the number of groups.
2. Inner lists contain one or more raw features.
3. Every raw feature in `X` appears exactly once across all groups.
4. Groups do not overlap.
5. `k_features`, `min_features`, and `max_features` count groups when this schema is used.
6. `fixed_features` values must be the same type as the group values.
7. If a fixed feature belongs to a multi-feature group, every feature in that group must also be listed as fixed.

## Selector fitted attributes

### SequentialFeatureSelector

| Attribute | Schema |
| --- | --- |
| `k_feature_idx_` | `tuple[int, ...]` raw selected column indices. |
| `k_feature_names_` | `tuple[str, ...]` selected names or stringified indices. |
| `k_score_` | `float` average score for selected subset. |
| `subsets_` | `dict[int, dict]` keyed by selected feature count or selected group count. |

`subsets_[k]` schema:

```python
{
    "feature_idx": tuple[int, ...],
    "feature_names": tuple[str, ...],
    "cv_scores": np.ndarray,       # shape (n_cv_scores,)
    "avg_score": float,
}
```

`get_metric_dict(confidence_interval=...)` adds:

```python
{
    "ci_bound": float,
    "std_dev": float,
    "std_err": float,
}
```

### ExhaustiveFeatureSelector

| Attribute | Schema |
| --- | --- |
| `best_idx_` | `tuple[int, ...]` raw selected column indices. |
| `best_feature_names_` | `tuple[str, ...]` selected names or stringified indices. |
| `best_score_` | `float` average score for best subset. |
| `subsets_` | `dict[int, dict]` keyed by evaluated-combination iteration. |

`subsets_[iteration]` has the same value schema as SFS. `get_metric_dict(top_k=N)` returns only top-scoring entries while preserving original iteration keys.

## Preprocessing output schemas

| API | Input schema | Output schema |
| --- | --- | --- |
| `standardize(array, columns=None, ...)` | DataFrame or ndarray, 1D or 2D | Selected standardized columns. DataFrame input returns a DataFrame slice; ndarray input returns an ndarray. One-dimensional ndarray becomes shape `(n_rows, 1)`. With `return_params=True`, returns `(out, {"avgs": ..., "stds": ...})`. |
| `minmax_scaling(array, columns, min_val, max_val)` | DataFrame or ndarray, 1D or 2D | Selected scaled columns. DataFrame input returns a DataFrame slice; ndarray input returns an ndarray. Constant columns become `min_val`. |
| `MeanCenterer().fit_transform(X)` | List or ndarray-like numeric data | Float ndarray copy with column means subtracted. List input becomes one column. |
| `DenseTransformer().transform(X)` | SciPy sparse matrix or dense array | Sparse input becomes dense ndarray; dense input is copied or returned depending on `return_copy`. |
| `CopyTransformer().transform(X)` | list, ndarray, or SciPy sparse matrix | List becomes ndarray; ndarray/sparse input returns a copy. |
| `one_hot(y, num_labels, dtype)` | 1D integer labels | 2D ndarray with shape `(len(y), max(y)+1)` for `num_labels="auto"`, or `(len(y), num_labels)` for integer width. |
| `shuffle_arrays_unison([A, B, ...])` | List of ndarrays with equal first-axis length | List of ndarrays with same shared row permutation. |

## Feature extraction output schemas

| API | Fit input | Main output | Fitted metadata |
| --- | --- | --- | --- |
| `PrincipalComponentAnalysis` | `X` shape `(n_samples, n_features)` | `transform(X)` shape `(n_samples, n_components_used)` | `w_`, `e_vals_`, `e_vecs_`, `e_vals_normalized_`, `loadings_`. |
| `LinearDiscriminantAnalysis` | `X` shape `(n_samples, n_features)`, `y` shape `(n_samples,)` | `transform(X)` shape `(n_samples, n_discriminants_used)` | `w_`, `e_vals_`, `e_vecs_`. |
| `RBFKernelPCA` | `X` shape `(n_samples, n_features)` | `X_projected_` for training data and `transform(X_new)` for new data | `e_vals_`, `e_vecs_`, `X_projected_`, `X_`. |

If `n_components`/`n_discriminants` is `None` or larger than `n_features`, mlxtend uses `n_features` components/discriminants.

## Transaction schemas

Input is a list of transactions:

```python
transactions = [
    ["Apple", "Beer", "Rice"],
    ["Apple", "Beer"],
    ["Milk", "Beer", "Rice"],
]
```

`TransactionEncoder.fit(transactions)` derives:

```python
encoder.columns_          # sorted unique item labels
encoder.columns_mapping_  # item -> column index
```

Dense transform schema:

```python
array = encoder.transform(transactions, sparse=False)
array.dtype == bool
array.shape == (n_transactions, n_unique_items)
```

Sparse transform schema:

```python
matrix = encoder.transform(transactions, sparse=True)
# scipy.sparse.csr_matrix, dtype bool, same shape as dense output
```

Pandas one-hot DataFrame schema:

```python
onehot_df = pd.DataFrame(array, columns=encoder.columns_)
# columns are item labels, values are bools
```

When sklearn output configuration is available:

```python
onehot_df = TransactionEncoder().set_output(transform="pandas").fit_transform(transactions)
```

`inverse_transform(array)` returns `list[list[item]]`; item order follows `encoder.columns_`, not necessarily the original transaction order.

## Sparse and dense memory notes

- `TransactionEncoder(..., sparse=True)` is the safest output for very wide transaction vocabularies, but itemset mining usually expects a pandas one-hot DataFrame; route that next step to `../frequent-patterns/SKILL.md`.
- `DenseTransformer` expands sparse matrices to dense arrays. Estimate memory as `n_samples * n_features * dtype_size` before densifying.
- PCA/RBFKernelPCA are dense numerical workflows; if input starts sparse, densify only after deciding the resulting array fits memory.
