# Troubleshooting mlxtend.evaluate workflows

Use this file when an evaluation workflow fails or produces surprising output. For signatures and return shapes, see [api-reference.md](api-reference.md); for choosing a workflow, see [workflows.md](workflows.md).

## Quick diagnosis table

| Symptom | Likely cause | Recovery |
|---|---|---|
| `y_target` and `y_predicted` length mismatch error | Prediction arrays do not describe the same samples. | Recompute predictions from the same rows; check that train/test indexing has not been shuffled independently; compare `len(y_true)` and `len(y_pred)` before calling metric helpers. |
| `One or more input arrays are not 1-dimensional.` | McNemar/Cochran/F-test helpers received column vectors, probability arrays, or DataFrames instead of 1D label arrays. | Convert labels with `np.asarray(labels).ravel()` after verifying it is safe; convert probabilities to labels with `argmax` or a threshold first. |
| Binary metric raises because labels are not binary | `scoring` binary metrics only support two labels; `lift_score(binary=False)` requires 0/1 inputs. | For multiclass tasks, use `accuracy`, `balanced accuracy`, or per-class metrics; for positive-vs-rest analysis, set `positive_label` and use helpers that support positive-vs-rest mapping. |
| `Chosen value of pos_label doesn't exist` | `accuracy_score(..., method='binary')` uses a positive label absent from `y_target`. | Check `np.unique(y_target)`; choose a valid `pos_label` or compute multiclass accuracy instead. |
| `metric not in ...` or invalid metric name | `scoring` and `feature_importance_permutation` use fixed metric-name vocabularies. | Use exact supported strings from [api-reference.md](api-reference.md); for feature importance, pass a custom `metric(y_true, y_pred)` when the built-in `accuracy` or `r2` is not enough. |
| sklearn scorer error such as unknown scoring string | Paired t-tests and combined F tests pass string scorers to sklearn `get_scorer`. | Use sklearn scoring names such as `accuracy`, `f1`, `roc_auc`, `r2`, or pass a callable `scorer(estimator, X, y)`. Do not pass `metric(y_true, y_pred)` to these APIs. |
| `Estimator must be a Classifier or Regressor` | Default scoring could not infer estimator type from sklearn tags or `_estimator_type`. | Pass `scoring='accuracy'`, `scoring='r2'`, or a compatible custom scorer explicitly; use sklearn-compatible estimator classes. |
| Probability scoring fails with missing `predict_proba` | `bootstrap_point632_score(..., predict_proba=True)` or `create_counterfactual(..., y_desired_proba=...)` requires a model with `predict_proba`. | Use an estimator that implements `predict_proba`; or set `predict_proba=False`; or set `y_desired_proba=None` and target labels via `predict`. |
| `method` invalid for bootstrap or permutation | `bootstrap_point632_score` only accepts `'.632'`, `'.632+'`, or `'oob'`; `permutation_test` only accepts `'exact'` or `'approximate'`. | Correct the spelling and punctuation exactly. Use `'.632'` with the leading dot. |
| `ci must be in range (0, 1)` | Ordinary bootstrap confidence level was supplied as `95` instead of `0.95` or outside the valid interval. | Use fractional confidence levels such as `0.90`, `0.95`, or `0.99`. |
| `func must return a scalar` in `bootstrap` | The statistic function returned a vector, array, Series, or multi-output object. | Wrap the statistic to return one scalar, e.g. `lambda x: float(np.mean(x))` or choose one component of a vector statistic. |
| Exact permutation appears to hang | `permutation_test(method='exact')` enumerates combinations or paired flips. | Switch to `method='approximate'`, set `num_rounds`, and fix `seed`. Reserve exact mode for tiny samples. |
| Resampling tests are slow | High `num_rounds`, `n_splits`, exact permutation, expensive estimators, or feature importance over many features. | Lower `num_rounds`/`n_splits`, use cheaper estimators for exploration, use grouped features, or run a smoke check before a full run. |
| Time-series split raises `Either train_size or n_splits should be defined` | `GroupTimeSeriesSplit` requires enough information to determine window count and width. | Provide `train_size` for rolling windows or `n_splits` when the train size should be inferred. |
| Time-series split raises invalid window type | `window_type` is not exactly `'rolling'` or `'expanding'`. | Use one of those two strings. For expanding windows, omit `train_size`. |
| Time-series split raises `The groups should be specified` | `GroupTimeSeriesSplit.split` was called without the `groups` argument. | Pass a 1D group array to sklearn's `groups=` parameter or directly to `split(X, y, groups)`. |
| Time-series split raises `The groups should be consecutive` | The same group label appears in multiple separated blocks. | Sort data by time/group so each group is contiguous; if groups are not temporal blocks, use another splitter. |
| Time-series split raises `Not enough data to split number of groups...` | `train_size + gap_size + test_size + shift requirements` exceed available groups. | Reduce `train_size`, `test_size`, `gap_size`, `n_splits`, or `shift_size`; remember these units are groups, not rows. |
| Counterfactual returns a vector but prediction did not change | `lammbda` is too small, the model boundary is far away, or optimization settled near the reference. | Increase `lammbda`, provide a richer `X_dataset` for initialization, or check that `y_desired` is reachable for the fitted model. |
| Counterfactual emits an optimization warning | SciPy optimizer did not satisfy its convergence criterion. | Treat the result as tentative; check the model prediction on the returned vector; retry with a different seed, a different `lammbda`, or a better starting dataset. |
| Permutation feature importance mutates unexpected values | The helper temporarily shuffles columns in the array it receives. | Pass `X.copy()` if the caller will reuse the original array after the call; avoid passing views when exact preservation matters. |

## Label-shape recovery patterns

### Metrics and scoring

```python
import numpy as np

y_true = np.asarray(y_true)
y_pred = np.asarray(y_pred)
assert y_true.shape[0] == y_pred.shape[0]
```

Prefer 1D arrays for labels. If you have a probability matrix, convert it deliberately:

```python
y_pred = proba.argmax(axis=1)       # multiclass labels
# or
y_pred = (proba[:, 1] >= 0.5).astype(int)  # binary threshold
```

### McNemar, Cochran, and F tests

These helpers compare predicted labels, not probabilities and not fitted estimators. Every array should be 1D and aligned to the same samples:

```python
y_true = np.asarray(y_true).ravel()
y_model1 = np.asarray(y_model1).ravel()
y_model2 = np.asarray(y_model2).ravel()
assert y_true.shape == y_model1.shape == y_model2.shape
```

Do not use `.ravel()` blindly on multi-output predictions unless you intentionally want to flatten all outputs.

## Scorer-contract recovery

mlxtend evaluation APIs use two distinct scorer conventions.

### sklearn scorer convention

Used by `paired_ttest_resampled`, `paired_ttest_kfold_cv`, `paired_ttest_5x2cv`, and `combined_ftest_5x2cv`.

- String scorer: `scoring='accuracy'`, `scoring='r2'`, etc.
- Callable scorer: `scorer(estimator, X, y)`.

Recovery:

```python
from sklearn.metrics import make_scorer, f1_score

scorer = make_scorer(f1_score)
t_stat, p = paired_ttest_5x2cv(est1, est2, X, y, scoring=scorer, random_seed=1)
```

### Prediction metric convention

Used by `bootstrap_point632_score(scoring_func=...)` and `feature_importance_permutation(metric=...)`.

- `scoring_func(y_true, y_pred)` for bootstrap .632.
- `metric(y_true, y_pred)` for permutation importance.

Recovery:

```python
def accuracy_metric(y_true, y_pred):
    return (y_true == y_pred).mean()

scores = bootstrap_point632_score(est, X, y, scoring_func=accuracy_metric)
```

Do not pass a sklearn `make_scorer` object to `scoring_func`; it expects an estimator and will fail when called with arrays.

## `predict_proba` expectations

Use probability mode only when the estimator supports it.

- `bootstrap_point632_score(..., predict_proba=True)` calls `estimator.predict_proba(X)` and, for binary labels, uses the positive-class probability column.
- `create_counterfactual(..., y_desired_proba=value)` calls `model.predict_proba` and indexes the probability for `y_desired`.

Recovery options:

1. Choose a classifier with `predict_proba`.
2. Use a calibration wrapper if probability estimates are required by the evaluation protocol.
3. Disable probability mode and evaluate labels instead.

## Invalid method names

Use exact values:

- `accuracy_score(method=...)`: `'standard'`, `'binary'`, `'average'`, `'balanced'`.
- `bootstrap_point632_score(method=...)`: `'.632'`, `'.632+'`, `'oob'`.
- `permutation_test(method=...)`: `'exact'`, `'approximate'`.
- `permutation_test(func=...)`: `'x_mean != y_mean'`, `'x_mean > y_mean'`, `'x_mean < y_mean'`, or a callable.
- `GroupTimeSeriesSplit(window_type=...)`: `'rolling'`, `'expanding'`.

If a method string comes from user input, validate it before launching expensive resampling.

## Time-series split size checklist

For `GroupTimeSeriesSplit`, all size parameters count groups.

1. Count unique consecutive group blocks.
2. Ensure `test_size > 0`.
3. If using rolling windows, ensure `train_size + gap_size + test_size` fits at least once.
4. If using `n_splits`, ensure `(n_splits - 1) * shift_size` also fits.
5. If using expanding windows, remove `train_size`.
6. Confirm group labels are contiguous by time order.

When a configuration fails, reduce one dimension at a time. The error message includes the computed train size, split count, test size, gap size, and shift size.

## Expensive resampling controls

Before full runs:

- Set `seed` or `random_seed` for reproducibility.
- Use smoke values: `num_rounds=5`, `n_splits=3`, `cv=3`, or a tiny feature subset.
- Prefer approximate permutation for samples larger than toy examples.
- Avoid exact permutation with paired samples beyond small `2 ** n` enumeration.
- For feature importance, group one-hot columns and run one or two rounds first.
- For estimator-comparison tests, use simpler estimators to validate scoring plumbing before running expensive models.

After the pipeline works, scale one cost driver at a time and record the runtime budget with the result.
