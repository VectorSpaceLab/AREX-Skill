# mlxtend.evaluate API Reference

Import public objects with:

```python
from mlxtend.evaluate import accuracy_score, paired_ttest_5x2cv
```

All notes below are verified against the installed `mlxtend.evaluate` public API and behavior tests. Links stay within this generated sub-skill; use [workflows.md](workflows.md) for decision recipes and [troubleshooting.md](troubleshooting.md) for recovery patterns.

## Prediction metrics and contingency helpers

| API | Signature | Returns and notes |
|---|---|---|
| `accuracy_score` | `accuracy_score(y_target, y_predicted, method='standard', pos_label=1, normalize=True)` | `float` fraction by default, or correct-count when `normalize=False`. `method='standard'` is overall accuracy; `'binary'` maps `pos_label` to positive-vs-rest; `'average'` computes average per-class accuracy; `'balanced'` computes sklearn-style balanced accuracy. Raises when target/prediction lengths differ or `method` is not one of the allowed names. |
| `scoring` | `scoring(y_target, y_predicted, metric='error', positive_label=1, unique_labels='auto')` | `float` metric. Multiclass-safe metrics: `accuracy`, `error`, `average per-class accuracy`, `average per-class error`, `balanced accuracy`. Binary-only metrics: `false_positive_rate`, `true_positive_rate`, `true_negative_rate`, `precision`, `recall`, `sensitivity`, `specificity`, `matthews_corr_coef`, `f1`; these require at most two labels after considering predictions. |
| `confusion_matrix` | `confusion_matrix(y_target, y_predicted, binary=False, positive_label=1)` | NumPy array with shape `(n_classes, n_classes)`. Rows are true labels and columns are predicted labels in sorted combined-label order. `binary=True` maps `positive_label` to `1` and all other labels to `0`. If only one class appears, the result is expanded to a 2x2 matrix. |
| `lift_score` | `lift_score(y_target, y_predicted, binary=True, positive_label=1)` | `float` lift, computed from positive co-occurrence support. With `binary=True`, labels are mapped positive-vs-rest. With `binary=False`, inputs must already be binary 0/1 arrays or an error is raised. Multi-dimensional inputs are transposed internally; prefer 1D arrays unless multi-label support is intended. |
| `proportion_difference` | `proportion_difference(proportion_1, proportion_2, n_1, n_2=None)` | `(z, p)` floats for a difference-of-proportions statistic. Proportions must be in `[0, 1]`; if `n_2=None`, it uses `n_1` for both samples. The returned p-value is from the standard normal CDF at `z`; for paired predictions prefer McNemar/Cochran tests instead. |

## Bootstrap, permutation, and bias-variance routines

| API | Signature | Returns and notes |
|---|---|---|
| `bootstrap` | `bootstrap(x, func, num_rounds=1000, ci=0.95, ddof=1, seed=None)` | `(original, standard_error, (lower_ci, upper_ci))`. `x` must be a NumPy array with samples along axis 0. `func(x_sample)` must return a scalar. `ci` must be in `(0, 1)`. Runtime is `num_rounds` statistic evaluations. |
| `BootstrapOutOfBag` | `BootstrapOutOfBag(n_splits=200, random_seed=None)` | sklearn-compatible splitter. `split(X, y=None, groups=None)` yields bootstrap train indices sampled with replacement and test indices that were out-of-bag. `get_n_splits(...)` returns `n_splits`. Use with `cross_val_score`/`GridSearchCV` when OOB validation is desired. |
| `bootstrap_point632_score` | `bootstrap_point632_score(estimator, X, y, n_splits=200, method='.632', scoring_func=None, predict_proba=False, random_seed=None, clone_estimator=True, **fit_params)` | NumPy array of length `n_splits`, one score per bootstrap replicate. `method` is `'.632'`, `'.632+'`, or `'oob'`. Estimator must implement sklearn-style `fit` and `predict`; default scorer is accuracy for classifiers and MSE-derived logic for regressors. `scoring_func` has signature `scoring_func(y_true, y_pred)`, not a sklearn scorer. `predict_proba=True` requires `estimator.predict_proba`; for binary labels the positive-class probability column is used. Pandas `X`/`y` are converted to arrays. |
| `bias_variance_decomp` | `bias_variance_decomp(estimator, X_train, y_train, X_test, y_test, loss='0-1_loss', num_rounds=200, random_seed=None, **fit_params)` | `(avg_expected_loss, avg_bias, avg_var)` floats. `loss` is `'0-1_loss'` for classification-style predictions or `'mse'` for regression. Draws `num_rounds` bootstrap samples from the training set and repeatedly fits the estimator. Pandas inputs are converted to arrays. For MSE, `avg_bias` is the squared-bias term. |
| `permutation_test` | `permutation_test(x, y, func='x_mean != y_mean', method='exact', num_rounds=1000, seed=None, paired=False)` | `float` p-value. Built-in `func` strings are `'x_mean != y_mean'`, `'x_mean > y_mean'`, and `'x_mean < y_mean'`; custom functions must accept `(x, y)` and return a scalar statistic where larger means more extreme. `method='exact'` enumerates all permutations and is only feasible for small samples; `'approximate'` draws `num_rounds` random permutations. `paired=True` requires equal lengths and flips paired observations. |

## Model-comparison statistical tests

| API | Signature | Returns and notes |
|---|---|---|
| `paired_ttest_resampled` | `paired_ttest_resampled(estimator1, estimator2, X, y, num_rounds=30, test_size=0.3, scoring=None, random_seed=None)` | `(t, p)` floats for the resampled paired t-test. Repeatedly splits the same dataset, fits both estimators on each train split, and compares score differences on the test split. `scoring=None` defaults to `accuracy` for classifiers and `r2` for regressors; a string uses sklearn `get_scorer`; a callable must follow `scorer(estimator, X, y)`. |
| `paired_ttest_kfold_cv` | `paired_ttest_kfold_cv(estimator1, estimator2, X, y, cv=10, scoring=None, shuffle=False, random_seed=None)` | `(t, p)` floats for k-fold paired t-test. Uses `KFold`; `random_seed` only matters when `shuffle=True`. Same scorer contract as other paired t-tests. |
| `paired_ttest_5x2cv` | `paired_ttest_5x2cv(estimator1, estimator2, X, y, scoring=None, random_seed=None)` | `(t, p)` floats for Dietterich's 5x2cv paired t-test. Performs five randomized 50/50 split pairs. Sign of `t` reflects estimator1 minus estimator2 for the first split; p-value is the main inferential result. |
| `combined_ftest_5x2cv` | `combined_ftest_5x2cv(estimator1, estimator2, X, y, scoring=None, random_seed=None)` | `(f, p)` floats for Alpaydin's combined 5x2cv F-test. Same sklearn estimator/scorer expectations as paired t-tests. F is non-directional; inspect per-model scores separately for effect direction. |
| `ftest` | `ftest(y_target, *y_model_predictions)` | `(f, p)` floats for comparing two or more classifiers from prediction arrays on the same samples. Inputs must be 1D and equal length. It tests an overall null of equal classifier performance; it does not say which model is best. |
| `mcnemar_table` | `mcnemar_table(y_target, y_model1, y_model2)` | 2x2 integer NumPy array for two models: `[0,0]` both correct, `[0,1]` model1 correct/model2 wrong, `[1,0]` model2 correct/model1 wrong, `[1,1]` both wrong. Inputs must be 1D arrays with matching sample counts. |
| `mcnemar_tables` | `mcnemar_tables(y_target, *y_model_predictions)` | Dictionary mapping pair labels such as `'model_0 vs model_1'` to 2x2 contingency arrays for every pair among two or more prediction arrays. All arrays must be 1D and equal length. |
| `mcnemar` | `mcnemar(ary, corrected=True, exact=False)` | `(chi2, p)` for a 2x2 McNemar table. With `exact=True`, `chi2` is `None` and p comes from an exact binomial calculation; prefer exact mode when discordant counts `b+c` are small. With `exact=False`, optional continuity correction is applied before the chi-square survival function. |
| `cochrans_q` | `cochrans_q(y_target, *y_model_predictions)` | `(q, p)` floats for comparing two or more related classifiers on the same examples. Inputs must be 1D and equal length. For exactly two models, it is related to McNemar's test; for more models, use it as an omnibus test before pairwise follow-up. |

## Validation splitters

| API | Signature | Returns and notes |
|---|---|---|
| `RandomHoldoutSplit` | `RandomHoldoutSplit(valid_size=0.5, random_seed=None, stratify=False)` | sklearn-compatible splitter yielding exactly one `(train_index, valid_index)` pair. Intended for `GridSearchCV`, feature-selection CV, or quick holdout validation. `get_n_splits(...)` always returns `1`. `valid_size` is passed to sklearn's split routine and may be a fraction or count supported by sklearn. |
| `PredefinedHoldoutSplit` | `PredefinedHoldoutSplit(valid_indices)` | sklearn-compatible splitter yielding exactly one split where `valid_indices` are validation samples and all other sample positions are training samples. `get_n_splits(...)` returns `1`. Useful when the holdout set is fixed by time, subject, fold assignment, or an external protocol. |
| `GroupTimeSeriesSplit` | `GroupTimeSeriesSplit(test_size, train_size=None, n_splits=None, gap_size=0, shift_size=1, window_type='rolling')` | Group-aware time-series CV splitter. `split(X, y=None, groups=None)` yields index arrays and requires `groups`. At least one of `train_size` or `n_splits` must be supplied. `window_type` is `'rolling'` or `'expanding'`; expanding windows cannot specify `train_size`. Group labels must appear in consecutive blocks. Size arguments are in number of groups, not samples. |

## Interpretability helpers

| API | Signature | Returns and notes |
|---|---|---|
| `feature_importance_permutation` | `feature_importance_permutation(X, y, predict_method, metric, num_rounds=1, feature_groups=None, seed=None)` | `(mean_importance_vals, all_importance_vals)` NumPy arrays. `predict_method(X)` should return predictions shaped like `y`. `metric` is `'accuracy'`, `'r2'`, or a callable `metric(y_true, y_pred)`. Importance is baseline score minus score after shuffling. `all_importance_vals` has shape `(n_features_or_groups, num_rounds)`. Pass `feature_groups` such as `[0, 1, [2, 3]]` to permute grouped columns together. Use a copy of `X` if you cannot tolerate temporary in-place shuffling. |
| `create_counterfactual` | `create_counterfactual(x_reference, y_desired, model, X_dataset, y_desired_proba=None, lammbda=0.1, random_seed=None)` | 1D NumPy array counterfactual candidate with the same feature count as `x_reference`. The model must implement `predict`; if `y_desired_proba` is provided, it must also implement `predict_proba`. `X_dataset` seeds the optimizer and computes feature-wise median absolute deviation. The weighting parameter is spelled `lammbda` in the API. Optimization warnings may indicate no reliable counterfactual was found. |

## Common scorer-contract distinctions

- `paired_ttest_*` and `combined_ftest_5x2cv`: `scoring` string or callable follows sklearn scorer semantics: `scorer(estimator, X, y)`.
- `bootstrap_point632_score`: `scoring_func` follows prediction metric semantics: `scoring_func(y_true, y_pred)`.
- `feature_importance_permutation`: `metric` follows prediction metric semantics: `metric(y_true, y_pred)`, while `predict_method` is the estimator's prediction callable.
- `scoring` and `accuracy_score`: accept already computed label arrays; they do not fit estimators.
