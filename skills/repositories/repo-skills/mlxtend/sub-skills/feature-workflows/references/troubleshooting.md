# Troubleshooting: Feature Workflows

Use this guide when mlxtend feature selectors, extraction transforms, preprocessing helpers, or transaction encoders fail or produce surprising shapes.

## DataFrame vs ndarray columns

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| String `fixed_features` or `feature_groups` fail | Input `X` is an ndarray, so there are no feature names to resolve. | Use a pandas DataFrame with matching column names, or switch to integer indices. |
| `ColumnSelector` raises about mixed types | `cols` contains both integers and strings. | Use all integer positions or all string names. |
| DataFrame selection returns a NumPy array | This is `ColumnSelector` behavior. | Wrap output in a DataFrame yourself if column labels must be preserved downstream. |
| One selected column has shape `(n_samples,)` instead of `(n_samples, 1)` | `drop_axis=True` was used. | Set `drop_axis=False` when downstream expects 2D feature arrays. |
| Selector name fields are `("0", "2")` instead of original names | Input was an ndarray. | Fit on a DataFrame if name preservation matters. |

## Feature groups and fixed features

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `feature_group` must contain all features / no common feature | Groups do not cover every column exactly once. | Build groups from the full column list and check for duplicates/missing columns. |
| Error about group values having mixed types | A group mixes strings and integers. | Use one type consistently. |
| Error about names not present in input `X` | A string group/fixed feature was used with ndarray input or a misspelled DataFrame column. | Fit on a DataFrame and validate `set(names) <= set(X.columns)`. |
| Error requiring group-mates as fixed features | `fixed_features` included only part of a multi-feature group. | Add every feature from that group to `fixed_features`, or split the group. |
| `k_features`/`min_features`/`max_features` bounds seem wrong | With groups, sizes count groups rather than raw columns. Fixed groups raise the lower bound. | Recompute size bounds in group units. |

Quick validation helper:

```python
flat = [item for group in feature_groups for item in group]
assert len(flat) == len(set(flat))
assert set(flat) == set(X.columns)  # for DataFrame names
```

## Slow or memory-heavy SFS/EFS searches

| Symptom | Cause | Fix |
| --- | --- | --- |
| EFS takes too long | It evaluates every combination in the configured range. | Reduce `max_features`, combine raw columns into groups, use `top_k` only for metrics display, or switch to SFS. |
| Parallel search uses too much memory | Too many candidate jobs are dispatched at once. | Set `n_jobs` modestly and lower `pre_dispatch`, e.g. `pre_dispatch="1*n_jobs"`. |
| SFS still expensive | Repeated CV fits dominate runtime. | Use fewer CV folds, simpler estimator settings, narrower `k_features`, or `tol` early stopping when acceptable. |
| Search logs clutter output | `verbose` or `print_progress` enabled. | Use `verbose=0` for SFS and `print_progress=False` for EFS in scripts. |

## Scoring and cross-validation mismatch

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Error inferring scoring from estimator | `scoring=None` and estimator does not expose classifier/regressor type. | Pass an explicit sklearn scoring string or callable. |
| Regression selector optimizes accuracy | Default EFS scoring is `"accuracy"`. | Set a regression scorer such as `"r2"` or `"neg_mean_squared_error"`. |
| Callable scorer fails | Signature is wrong. | Use `scorer(estimator, X, y)` or wrap metrics with sklearn `make_scorer`. |
| `cv` generator object is rejected | SFS/EFS explicitly reject generator objects. | Use `cv=list(splitter.split(X, y, groups))` or pass the splitter object itself when supported. |
| Group CV ignores groups | Groups were not passed to `fit`. | Call `selector.fit(X, y, groups=groups)`. |
| Non-clonable estimator fails | `clone_estimator=True` requires sklearn clone support. | Use a sklearn-compatible estimator, or set `clone_estimator=False`, `cv=0`, and `n_jobs=1`. |

## Selector transform and metric surprises

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `transform` says selector has not been fitted | `fit` did not complete or was interrupted. | Run `fit` successfully first. If interrupted and `subsets_` exists, consider `finalize_fit()` only if partial results are acceptable. |
| SFS `subsets_` keys are group counts | `feature_groups` was provided. | Interpret keys as selected group count; inspect `feature_idx` for raw columns. |
| EFS metric dict is huge | All evaluated subsets are returned by default. | Use `get_metric_dict(top_k=N)` before formatting/reporting. |
| Selected names are sorted differently than group order | mlxtend returns raw selected indices sorted by column index. | Compare as sets when order is not semantically important. |

## PCA, LDA, and RBFKernelPCA

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `X must be a 2D array` | A single row/vector was passed. | Use `X[:, np.newaxis]` for one feature or `X[None, :]` for one sample. |
| `X must be a numpy array` | A Python list was passed to feature extraction. | Convert with `np.asarray(X, dtype=float)`. |
| PCA signs differ between runs/solvers | Eigenvector signs are arbitrary. | Compare absolute values or downstream predictions, not raw signs. |
| LDA fails on singular matrix | Redundant features or too few samples per class make within-class scatter singular. | Remove constant/duplicate columns, standardize, collect more samples, reduce dimensions first, or use a regularized alternative outside this sub-skill. |
| LDA projections look wrong with labels | Labels are not contiguous integer classes starting at 0. | Encode labels to `0..n_classes-1`; pass `n_classes` when fitting partial class sets. |
| RBFKernelPCA uses too much memory | Pairwise kernel matrix scales with training sample count. | Downsample, reduce sample count, or use a different method. |
| New RBFKernelPCA transform changes after fitting | `copy_X=False` and original training array was mutated. | Keep `copy_X=True` unless mutation is impossible. |

## Scaling and preprocessing

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `standardize`/`minmax_scaling` rejects input | Raw lists do not have the expected DataFrame/ndarray interface. | Convert to `np.asarray(...)` or `pd.DataFrame(...)`. |
| Only selected columns are returned | Scaling functions return the selected scaled columns, not the whole original table. | Assign the result back to a copy of the original table if you need a full table. |
| Train/test scaling inconsistent | Test data recomputed its own means/stds. | Use `X_train_std, params = standardize(X_train, return_params=True)` then `standardize(X_test, params=params)`. |
| Constant columns produce all zeros/lower bound | This is intentional. | Drop constant columns if they are not useful; otherwise keep the deterministic output. |
| Densification causes memory errors | Sparse data was converted to a dense ndarray. | Avoid `DenseTransformer` unless the next estimator requires dense input and the estimated dense size fits memory. |
| `CopyTransformer` rejects input | Input is not list, NumPy ndarray, or SciPy sparse matrix. | Convert unsupported containers before passing them in. |

## `one_hot` label encoding

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Output has extra empty columns | `num_labels="auto"` uses `max(y) + 1`, not number of unique labels. | Map labels to contiguous integers or pass explicit `num_labels`. |
| Multidimensional labels raise an error | `y` must be one-dimensional. | Flatten or select the label vector explicitly. |
| Negative or non-integer labels fail or index wrong columns | Labels are used directly as NumPy indices. | Encode classes to non-negative integer indices first. |
| Single class `[0]` encodes as `[[0.0]]` | This is mlxtend's historical behavior. | If downstream expects `[[1.0]]`, handle that case outside `one_hot`. |

## TransactionEncoder and one-hot transactions

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Unknown item raises a mapping error during `transform` | New transactions contain items unseen during `fit`. | Fit on the full item vocabulary or filter/map unknown items before transform. |
| One-hot columns are in unexpected order | `columns_` is sorted unique items, not first-seen order. | Always use `encoder.columns_` as the source of column labels. |
| Duplicate items in a transaction affect dense and sparse paths differently | Dense output naturally sets one boolean cell; sparse path deduplicates each transaction with a set. | Treat transactions as item sets; remove duplicates upstream if item multiplicity matters. |
| Sparse transaction output cannot be mined directly | Frequent-pattern APIs generally expect pandas one-hot DataFrames. | Convert with `pd.DataFrame(sparse_or_dense, columns=encoder.columns_)` when memory allows, then route to `../frequent-patterns/SKILL.md`. |
| `set_output(transform="pandas")` is unavailable | sklearn output configuration support is version-dependent. | Use `pd.DataFrame(encoder.fit_transform(transactions), columns=encoder.columns_)`. |
| `inverse_transform` order differs from original transactions | It emits items in `columns_` order. | Compare sets when transaction item order is irrelevant. |

## Routing mistakes

- Do not mine frequent itemsets or association rules here; route one-hot transaction DataFrames to `../frequent-patterns/SKILL.md`.
- Do not document or tune ensemble estimators here beyond passing an estimator into SFS/EFS; route to `../estimators-and-ensembles/SKILL.md`.
- Do not plot selector metrics or PCA/LDA/RBFKernelPCA graphics here; route to `../plotting-and-utilities/SKILL.md`.
