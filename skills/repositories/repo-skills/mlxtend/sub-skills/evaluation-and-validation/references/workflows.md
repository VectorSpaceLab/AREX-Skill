# Evaluation and validation workflows

Use these recipes to choose the smallest mlxtend evaluation workflow that answers the question. When the task is about building the estimator itself, route to [../../estimators-and-ensembles/SKILL.md](../../estimators-and-ensembles/SKILL.md). When the task is about feature engineering or plotting, route to the sibling sub-skill instead.

## 1) Choose the question first

### A. I only need a metric for one set of predictions
Use `accuracy_score`, `scoring`, `confusion_matrix`, `lift_score`, or `proportion_difference`.

- If you already have `y_true` and `y_pred`, use `accuracy_score` or `scoring`.
- If you need class-by-class error rates, `scoring(..., metric='average per-class accuracy')` or `accuracy_score(..., method='average')` is the best fit.
- If you need binary classification diagnostics, `scoring` provides precision, recall, specificity, F1, Matthews correlation coefficient, and related rates.
- If you need class association structure, use `confusion_matrix` first; derive extra summaries from the matrix.
- If you need a simple prevalence-like lift measure for binary labels or thresholded predictions, use `lift_score`.
- If you only need a rough independent-proportions comparison, `proportion_difference` returns a z statistic and normal p-value, but paired prediction comparisons should use McNemar or Cochran instead.

### B. I need a validation splitter for sklearn model selection
Use `RandomHoldoutSplit`, `PredefinedHoldoutSplit`, or `GroupTimeSeriesSplit`.

- Use `RandomHoldoutSplit` for one random holdout split in `GridSearchCV` or `cross_val_score`.
- Use `PredefinedHoldoutSplit` when the validation indices are fixed by an external protocol.
- Use `GroupTimeSeriesSplit` when groups are temporal blocks and leakage across time or subject groups must be avoided.

### C. I need uncertainty or resampling-based performance estimates
Use `bootstrap`, `BootstrapOutOfBag`, `bootstrap_point632_score`, `bias_variance_decomp`, or `permutation_test`.

- Use `bootstrap` when you already have a scalar statistic and want a bootstrap confidence interval.
- Use `BootstrapOutOfBag` when sklearn tooling expects a splitter and you want OOB validation folds.
- Use `bootstrap_point632_score` for classifier/regressor evaluation when you want the .632, .632+, or OOB bootstrap estimate.
- Use `bias_variance_decomp` when you want the expected loss, bias, and variance decomposition across bootstrap resamples.
- Use `permutation_test` for a nonparametric null distribution on a scalar statistic or a paired sample comparison.

### D. I need to compare two fitted models statistically
Choose the test by data structure and whether predictions are paired.

- Same test set, two classifiers, paired correctness: `mcnemar` on `mcnemar_table`.
- Same test set, two or more classifiers, paired correctness: `cochrans_q` for an omnibus comparison; follow with pairwise McNemar if needed.
- Prediction arrays on the same samples, more than two models: `ftest` for an overall comparison of classification accuracy patterns.
- Repeated resampling with fitted estimators: `paired_ttest_resampled`, `paired_ttest_kfold_cv`, or `paired_ttest_5x2cv`.
- Repeated 5x2cv with estimators: `combined_ftest_5x2cv` when you want the Alpaydin F-test variant instead of a t-test.

### E. I need feature importance or a counterfactual explanation
Use `feature_importance_permutation` or `create_counterfactual`.

- Use `feature_importance_permutation` when the model is already trained and you want drop-in performance degradation after shuffling features or feature groups.
- Use `create_counterfactual` when you need a nearby input that flips the model decision or pushes the probability toward a desired target.

## 2) Metric and scoring recipes

### Accuracy and scoring
1. Start from prediction arrays, not an estimator.
2. For overall correctness, use `accuracy_score(..., method='standard')` or `scoring(..., metric='accuracy')`.
3. For binary class-specific behavior, map a positive label with `scoring(..., positive_label=...)`.
4. For multiclass balance, use `accuracy_score(..., method='average')` or `scoring(..., metric='balanced accuracy')`.
5. For confusion-based diagnostics, compute `confusion_matrix` first and interpret counts before derived rates.

### Interpretation
- `accuracy_score(..., normalize=True)` returns a fraction in `[0, 1]`.
- `normalize=False` returns the count of correct predictions.
- `scoring(..., metric='error')` returns `1 - accuracy`.
- Binary metrics are undefined if the inputs contain more than two classes after conversion to numpy arrays.

### Cost controls
- For exploratory checks, use a tiny prediction vector and deterministic labels.
- Avoid computing both `confusion_matrix` and a derived metric when the metric alone already answers the question.

## 3) Holdout and time-series split recipes

### Random holdout
Use `RandomHoldoutSplit` when you want one validation split that behaves like a sklearn cross-validator.

Workflow:
1. Provide `valid_size`.
2. Decide whether the split should be stratified.
3. Pass the splitter into `GridSearchCV`, `cross_val_score`, or a feature selector.

Notes:
- `get_n_splits()` always returns 1.
- Use a fixed `random_seed` for reproducibility.
- Keep the validation fraction large enough that every class is represented.

### Predefined holdout
Use `PredefinedHoldoutSplit` when an external rule already decides validation rows.

Workflow:
1. Compute or store the validation indices.
2. Pass them directly to the splitter.
3. Use the splitter in sklearn tooling as the `cv` argument.

Notes:
- This is the safest choice when train/validation membership must be identical across runs.
- It is also the easiest way to document exact validation composition in a workflow note.

### Group time series
Use `GroupTimeSeriesSplit` when group order matters and leakage across neighboring time blocks is unacceptable.

Workflow:
1. Build a 1D `groups` array with consecutive blocks for each group.
2. Choose `test_size` in groups, not rows.
3. Provide either `train_size` or `n_splits`.
4. If using `window_type='expanding'`, omit `train_size`.
5. Add `gap_size` when you need a buffer between train and test blocks.
6. Add `shift_size` when you want rolling windows to advance by more than one group.

Interpretation:
- Training and test windows are defined over group blocks, then expanded to row indices.
- A non-consecutive group array is invalid.
- A too-small group count raises a `ValueError` before any split is yielded.

Cost controls:
- Keep synthetic checks short by using few groups and one or two splits.
- Use rolling windows for bounded train sizes; use expanding windows when you need cumulative history.

## 4) Bootstrap, OOB, and .632 recipes

### Ordinary bootstrap on a scalar statistic
Use `bootstrap` when the statistic can be written as `func(x_sample)` and returns a scalar.

Workflow:
1. Convert the data to a NumPy array.
2. Write or choose a scalar-valued statistic such as mean or median.
3. Pick `num_rounds`.
4. Read the result as `(original, standard_error, (lower_ci, upper_ci))`.

Interpretation:
- `original` is the statistic on the original sample.
- `standard_error` is the standard deviation of the bootstrap replicates.
- The confidence interval is percentile-based.

Cost controls:
- Lower `num_rounds` for smoke checks.
- Choose a scalar statistic only; if your function returns a vector, fix that before running the bootstrap.

### OOB validation
Use `BootstrapOutOfBag` when you need sklearn-compatible bootstrap resampling.

Workflow:
1. Instantiate with `n_splits` and `random_seed`.
2. Feed it to sklearn tools that accept a `cv` object.
3. Remember that test folds are out-of-bag samples.

### .632 and .632+
Use `bootstrap_point632_score` when you want a direct model score estimate from bootstrap resamples.

Workflow:
1. Start with a fitted-capable sklearn estimator.
2. Choose `method='oob'`, `'.632'`, or `'.632+'`.
3. Provide a scoring function only when the default accuracy/MSE behavior is not enough.
4. Set `predict_proba=True` only when the scorer consumes probabilities.

Interpretation:
- `.632` blends training and OOB error.
- `.632+` adjusts that blend using the no-information rate.
- `oob` reports plain out-of-bag scores.
- The return value is one score per bootstrap split; average them for the headline estimate.

Cost controls:
- Reduce `n_splits` first.
- Use `clone_estimator=True` unless you deliberately want to reuse mutable model state.
- Prefer `oob` for quick exploration and `.632+` only when you need the correction.

### Bias-variance decomposition
Use `bias_variance_decomp` when you need expected loss plus bias and variance across bootstrap samples.

Workflow:
1. Split the data into train and test sets first.
2. Choose `loss='0-1_loss'` for classification or `loss='mse'` for regression.
3. Set `num_rounds`.
4. Read `(avg_expected_loss, avg_bias, avg_var)`.

Interpretation:
- For classification, `avg_bias` is the main-prediction misclassification rate.
- For regression, `avg_bias` is squared bias.
- Compare loss, bias, and variance together; do not interpret one in isolation.

## 5) Permutation test recipes

### Generic permutation test
Use `permutation_test` when you need a nonparametric p-value for a scalar statistic.

Workflow:
1. Decide whether the comparison is paired.
2. Choose a direction: two-sided (`'x_mean != y_mean'`) or one-sided.
3. Use `method='exact'` for tiny samples and `method='approximate'` when exact enumeration is too expensive.
4. Supply a custom statistic only if the built-in mean-difference forms do not fit.

Interpretation:
- The return value is a p-value under the null.
- Smaller p-values mean the observed statistic is more extreme than most permuted samples.
- Paired mode keeps observation pairing intact and only swaps paired values.

Cost controls:
- Exact mode grows combinatorially.
- Approximate mode is deterministic only when `seed` is fixed.

## 6) Paired model-comparison recipes

### When to use each test

| Situation | Recommended test |
|---|---|
| Two classifiers, same test set, paired correct/incorrect outcomes | `mcnemar` on `mcnemar_table` |
| Two or more classifiers, same test set, paired correct/incorrect outcomes | `cochrans_q` for omnibus comparison |
| Two or more classifiers or regressors, repeated resampling | `paired_ttest_resampled` |
| Two or more classifiers or regressors, repeated k-fold CV | `paired_ttest_kfold_cv` |
| Two or more classifiers or regressors, Dietterich 5x2 CV | `paired_ttest_5x2cv` |
| Two classifiers or regressors, Alpaydin 5x2 CV combined F-test | `combined_ftest_5x2cv` |
| Prediction arrays for two or more models on the same samples | `ftest` |

### Paired t-tests
Use these when you need a difference-of-scores test based on repeated resampling.

Workflow:
1. Pass two sklearn estimators.
2. Use a scoring string or callable compatible with sklearn `scorer(estimator, X, y)`.
3. Inspect `t` and `p`.
4. If `p < alpha`, reject the null of equal mean performance under the chosen resampling scheme.

Interpretation:
- The sign of `t` indicates the average direction of score differences under the procedure.
- The p-value is two-tailed.
- These tests compare fitted estimators, so they fit models repeatedly.

Cost controls:
- Start with `paired_ttest_5x2cv` for a standard balanced comparison.
- Use fewer rounds or folds for smoke checks.
- Reuse the same scorer across both estimators.

### F tests
Use `ftest` or `combined_ftest_5x2cv` when you want an omnibus F-type model comparison rather than a t-statistic.

Interpretation:
- `ftest` and `cochrans_q`/`mcnemar` are not ranking tools; they answer whether a difference exists.
- After a significant omnibus result, do pairwise follow-up tests if you need the source of the difference.
- `combined_ftest_5x2cv` expects fitted estimators and a scorer, just like the paired t-tests.

### McNemar and Cochran
Use these when you already have predicted labels and want to compare correctness on the same samples.

Workflow:
1. Build the contingency table with `mcnemar_table` or `mcnemar_tables`.
2. Use `mcnemar(..., exact=True)` when discordant counts are small.
3. Use `cochrans_q` when you have more than two classifiers.

Interpretation:
- For McNemar, the off-diagonal entries drive the statistic.
- Exact mode is safer for tiny discordant counts.
- For Cochran, a small p-value says at least one model differs, but not which one.

Cost controls:
- Contingency-table methods are cheaper than estimator refits when you already have predictions.
- Use them before more expensive resampling comparisons if you only need a quick paired check.

## 7) Permutation feature importance

Use `feature_importance_permutation` when the model already exists and you want a drop in score after shuffling one feature or feature group at a time.

Workflow:
1. Fit the model first.
2. Pass `predict_method` such as `model.predict`.
3. Choose `metric='accuracy'`, `metric='r2'`, or a custom `metric(y_true, y_pred)`.
4. Decide whether individual columns or grouped columns should be shuffled together.
5. Set `num_rounds`.
6. Read the returned mean and per-round importance arrays.

Interpretation:
- Higher importance means a larger performance drop after shuffling.
- Grouped features are most useful for one-hot encoded or otherwise linked columns.
- If a feature has near-zero importance, the model may not rely on it or the baseline metric may already be saturated.

Cost controls:
- Start with `num_rounds=1` for smoke checks.
- Use a copy of `X` when you do not want temporary in-place shuffling to touch your original array.
- If you only care about ranking, inspect the mean array and keep the per-round matrix only when variance matters.

## 8) Counterfactual explanation

Use `create_counterfactual` when you need an input close to `x_reference` that pushes the model toward `y_desired`.

Workflow:
1. Fit a model with `predict`, and optionally `predict_proba`.
2. Choose a reference example and a desired target label.
3. Provide the training dataset used to seed the optimizer.
4. If probability-based targeting is required, set `y_desired_proba` and make sure the model implements `predict_proba`.
5. Tune `lammbda` to balance target achievement against distance from the reference example.

Interpretation:
- Smaller `lammbda` emphasizes staying close to the original example.
- Larger `lammbda` emphasizes achieving the target prediction or target probability.
- The returned counterfactual is a single optimized feature vector, not an explanation plot.

Cost controls:
- Start with a small dataset slice and a modest `lammbda`.
- Use a deterministic `random_seed` so the initial optimizer seed is reproducible.
- If the optimization warns or stalls, simplify the target or increase the starting pool diversity.

## 9) Minimal sklearn expectations by workflow

- Metrics helpers: accept arrays; no fitting required.
- Splitters: implement sklearn cross-validator semantics and may be used directly in `cross_val_score`, `GridSearchCV`, or feature selectors.
- Paired t-tests and combined F tests: require two fitted-capable estimators and a sklearn scorer or compatible callable.
- Bootstrap .632: requires an estimator with `fit` and `predict`, plus `predict_proba` if probability scoring is requested.
- Feature importance: requires a fitted model and a prediction method, not a full sklearn scorer.
- Counterfactuals: require a model that can predict on a single-row array.
