# Fairness guide

This guide covers fairness-aware `supervised.AutoML` usage for binary classification, multiclass classification, and regression. It assumes generic training choices such as algorithms, validation, and time limits have already been selected; route those decisions to `../../training-core/` when needed.

## Activate fairness-aware training

Fairness behavior is activated at fit time by passing `sensitive_features`:

```python
from supervised import AutoML

automl = AutoML(
    ml_task="binary_classification",
    fairness_metric="demographic_parity_ratio",
    fairness_threshold=0.8,
    privileged_groups=[{"gender": "male"}],
    underprivileged_groups=[{"gender": "female"}],
)
automl.fit(X_train, y_train, sensitive_features=S_train)
```

Fairness-related constructor arguments:

- `fairness_metric`: metric used to judge whether a model is fair. Use `"auto"` for task-specific defaults.
- `fairness_threshold`: cutoff used for the fair/unfair decision. Use `"auto"` when a documented default exists.
- `privileged_groups`: list of dictionaries identifying privileged group values, or `"auto"` to infer them.
- `underprivileged_groups`: list of dictionaries identifying underprivileged group values, or `"auto"` to infer them.

Relevant `fit()` argument:

- `sensitive_features`: a pandas `Series`, pandas `DataFrame`, or NumPy array with the same row count and order as `X` and `y` after any train/test split. Use a DataFrame when you need stable feature names for group declarations.

## Sensitive-feature preparation

Prefer a pandas `DataFrame` for sensitive columns:

```python
S = X[["sex", "age_bucket"]].copy()
automl.fit(X_train, y_train, sensitive_features=S_train)
```

Rules and caveats:

- Split `X`, `y`, and `sensitive_features` together so their row order stays aligned.
- A single `Series` is accepted, but a `DataFrame` is clearer and safer when group declarations are used.
- Multiple sensitive columns are supported. AutoML reports fairness for each column and uses intersections of sensitive values when computing fairness-optimization weights.
- Numeric sensitive columns are automatically converted into two equal-size categorical bins. If the group boundary matters for policy, pre-bin the column yourself and use explicit labels.
- If `sensitive_features` is a NumPy array, AutoML assigns generated names. Use a DataFrame instead when you want group names such as `{"sex": "Male"}`.

## Binary classification recipe

Use classification fairness metrics with a binary target. A common default is demographic parity ratio with a threshold of `0.8`:

```python
automl = AutoML(
    ml_task="binary_classification",
    fairness_metric="demographic_parity_ratio",
    fairness_threshold=0.8,
    privileged_groups=[{"gender": "male"}],
    underprivileged_groups=[{"gender": "female"}],
    train_ensemble=False,
)
automl.fit(X_train, y_train, sensitive_features=S_train)
```

If groups are omitted or set to `"auto"`, AutoML infers the privileged/underprivileged values from the fairness metric. For parity metrics it uses the highest and lowest selection rates. For equalized-odds metrics it uses the groups with the strongest true-positive-rate or false-positive-rate separation.

## Multiclass classification recipe

Use the same classification fairness metric names. AutoML evaluates the metric one class at a time, using a one-vs-rest view of each class. A single sensitive column named `gender` with target classes such as `A`, `B`, and `C` can appear in reports as feature keys like `gender__A`, `gender__B`, and `gender__C`.

```python
automl = AutoML(
    ml_task="multiclass_classification",
    fairness_metric="demographic_parity_ratio",
    fairness_threshold=0.8,
    train_ensemble=True,
)
automl.fit(X_train, y_train, sensitive_features=S_train)
```

When reviewing results, check every reported class-specific sensitive-feature key, not only the aggregate best-model score.

## Regression recipe

Use regression fairness metrics with a continuous target. The default is `group_loss_ratio`, which compares the model loss/score across sensitive groups using the model's regression evaluation metric.

```python
automl = AutoML(
    ml_task="regression",
    eval_metric="rmse",
    fairness_metric="group_loss_ratio",
    fairness_threshold=0.8,
)
automl.fit(X_train, y_train, sensitive_features=S_train)
```

For `group_loss_difference`, choose a threshold in the units of the underlying evaluation metric. AutoML cannot choose a safe default because a difference of `1.0` can be tiny for one target scale and huge for another.

```python
automl = AutoML(
    ml_task="regression",
    eval_metric="mae",
    fairness_metric="group_loss_difference",
    fairness_threshold=250.0,
)
```

## Bias mitigation and model selection behavior

When `sensitive_features` is supplied, AutoML computes fairness metrics in addition to performance metrics and changes model selection:

- Fairness information is added to model reports and to `report_structured()` output.
- The leaderboard includes `fairness_metric`, one or more `fairness_<feature>` columns, and `is_fair` when fairness is active.
- AutoML prefers the best-performing model among fair models.
- If no model satisfies the fairness threshold, AutoML selects the most fair valid model: highest fairness value for ratio metrics, lowest fairness value for difference metrics.
- Bias mitigation is handled by sample weighting and an internal smart-grid style search over sample weights.
- Ensembling can participate in fairness-aware training. Stacking is limited to fair base models; when no fair base model exists, stacking can be skipped.

Expect a performance/fairness tradeoff. Tight fairness thresholds can make a slower or less accurate model win, or can leave no model marked fair.

## Report and structured-report outputs

After a fairness-aware `fit()`:

```python
leaderboard = automl.get_leaderboard()
summary = automl.report_structured(format="dict")
model_details = automl.report_structured(format="dict", model_name="1_Xgboost")
```

Useful signals:

- Leaderboard: `fairness_metric`, `fairness_<feature>` or `fairness_<feature>__<class>`, and `is_fair`.
- Top-level structured report: `fairness_summary` when fairness is active, plus fairness columns in the compact leaderboard.
- `fairness_summary`: configured fairness metric, threshold, whether the best model is fair, worst/best fairness, sensitive feature scores, and fairness certificate fields when a fair model has enough information.
- Selected-model structured report: `selected_model.fairness` plus `selected_model.metrics.fairness_metrics_details` for per-group metric tables and privileged/underprivileged values.
- Markdown report: Fairness Summary, fairness group metrics, and certificate sections can be included when fairness is active.

If `report_structured()` has no fairness section, verify that `fit()` received `sensitive_features`; setting fairness constructor arguments alone is not enough.

## Distilled reference-only dataset patterns

These patterns are useful for adapting a user-provided local dataset, but should not be treated as bundled runnable checks:

- Adult-style binary classification: derive `sensitive_features` from `sex`, declare `Male` and `Female` groups manually, and use `demographic_parity_ratio >= 0.8` as a common starting point.
- Drug-style multiclass classification: convert the target into a few class labels, use a sensitive column such as gender, and inspect one fairness result per target class.
- Housing/ACS/Crime/LawSchool-style regression: derive a categorical sensitive feature from a demographic or thresholded numeric variable, use `group_loss_ratio` first, and only use `group_loss_difference` after selecting a scale-aware threshold.

For a self-contained runtime check, use `../scripts/fairness_smoke.py`; it generates synthetic data and does not fetch network datasets or read local CSVs.
