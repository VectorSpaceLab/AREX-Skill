# Tabular Workflows

Use these distilled recipes instead of original examples. They avoid downloads and source-checkout dependencies, and they keep result export/gating separate from validation.

## Common setup

```python
import pandas as pd
from deepchecks.tabular import Dataset

feature_cols = ["age", "income", "segment"]
cat_cols = ["segment"]
label_col = "target"

train_ds = Dataset(
    train_df,
    label=label_col,
    features=feature_cols,
    cat_features=cat_cols,
    index_name="customer_id",          # omit if no stable unique id column exists
    datetime_name="event_time",        # omit if no meaningful time column exists
    label_type="binary",               # or "multiclass" / "regression"
    dataset_name="Train",
)

test_ds = Dataset(
    test_df,
    label=label_col,
    features=feature_cols,
    cat_features=cat_cols,
    index_name="customer_id",
    datetime_name="event_time",
    label_type="binary",
    dataset_name="Test",
)
```

Preflight before calling Deepchecks:

```python
assert train_df.columns.is_unique
assert test_df.columns.is_unique
assert set(feature_cols).issubset(train_df.columns)
assert set(feature_cols).issubset(test_df.columns)
assert label_col in train_df.columns and label_col in test_df.columns
assert set(train_ds.features) == set(test_ds.features)
assert set(train_ds.cat_features) == set(test_ds.cat_features)
print(train_ds.columns_info)
```

If data arrives as numpy arrays:

```python
from deepchecks.tabular import Dataset

train_ds = Dataset.from_numpy(
    X_train,
    y_train,
    columns=["f1", "f2", "f3"],
    label_name="target",
    cat_features=[],
    label_type="regression",
    dataset_name="Train",
)
```

## Data integrity: single dataset quality

Use this before modeling, when only one table is available, or as a first check on each split.

```python
from deepchecks.tabular.suites import data_integrity

suite = data_integrity(
    n_samples=10_000,
    random_state=42,
)
result = suite.run(train_dataset=train_ds, with_display=False)

print("passed:", result.passed())
print("not ran:", [failure.get_header() for failure in result.get_not_ran_checks()])
```

Narrow to business-critical columns:

```python
suite = data_integrity(columns=["age", "income", "segment"], n_samples=10_000)
result = suite.run(train_ds, with_display=False)
```

Debug a specific data quality issue with one check:

```python
from deepchecks.tabular.checks import DataDuplicates, PercentOfNulls

result = DataDuplicates().run(train_ds, with_display=False)
duplicate_ratio = result.value

null_check = PercentOfNulls().add_condition_percent_of_nulls_not_greater_than(0.05)
null_result = null_check.run(train_ds, with_display=False)
```

## Train-test validation: split, drift, leakage

Use this after splitting or when comparing a reference/train table to a candidate/test table.

```python
from deepchecks.tabular.suites import train_test_validation

suite = train_test_validation(
    n_samples=10_000,
    random_state=42,
)
result = suite.run(
    train_dataset=train_ds,
    test_dataset=test_ds,
    with_display=False,
)

print("suite passed:", result.passed(fail_if_check_not_run=False))
print("not-ran count:", len(result.get_not_ran_checks()))
```

If date/index leakage checks are irrelevant, omit `datetime_name` and/or `index_name`; Deepchecks will mark date/index-specific checks unsupported rather than silently inventing metadata.

If the suite reports incompatible train/test metadata, rebuild both Datasets from the same `features`, `cat_features`, `label`, `index_name`, and `datetime_name` definitions.

## Model evaluation with a fitted sklearn-style model

Use this when a local model object can predict on `Dataset.features_columns`.

```python
from deepchecks.tabular.suites import model_evaluation

model.fit(train_ds.features_columns, train_ds.label_col)

result = model_evaluation(n_samples=10_000).run(
    train_dataset=train_ds,
    test_dataset=test_ds,
    model=model,
    with_display=False,
    feature_importance_timeout=0,  # avoid slow permutation importance in automation
)
```

If the model exposes `feature_importances_` or `coef_`, Deepchecks can use it. Otherwise pass explicit feature importance when checks need it:

```python
feature_importance = pd.Series(
    {"age": 0.45, "income": 0.45, "segment": 0.10},
    dtype=float,
)

result = model_evaluation().run(
    train_ds,
    test_ds,
    model=model,
    feature_importance=feature_importance,
    with_display=False,
)
```

## Model evaluation with predictions/probabilities and no model object

Use this when the model is served remotely, unavailable in the runtime, or too expensive to run inside the agent.

```python
feature_importance = pd.Series(
    [0.45, 0.45, 0.10],
    index=train_ds.features,
)

result = model_evaluation().run(
    train_dataset=train_ds,
    test_dataset=test_ds,
    y_pred_train=train_predictions,
    y_pred_test=test_predictions,
    y_proba_train=train_probabilities,
    y_proba_test=test_probabilities,
    model_classes=[0, 1],  # sorted in the exact probability-column order
    feature_importance=feature_importance,
    with_display=False,
)
```

Shape checklist:

```python
assert len(train_predictions) == train_ds.n_samples
assert len(test_predictions) == test_ds.n_samples
assert train_probabilities.shape == (train_ds.n_samples, len(model_classes))
assert test_probabilities.shape == (test_ds.n_samples, len(model_classes))
```

If only predicted labels are available, omit `y_proba_*`; ROC/AUC/calibration checks that need probabilities may not run, but label-based performance checks can still be useful.

## Custom scorers

Use scorer strings for common metrics and sklearn scorers for custom metrics.

```python
from sklearn.metrics import make_scorer, fbeta_score, cohen_kappa_score
from deepchecks.tabular.suites import model_evaluation

custom_scorers = {
    "F0.5": make_scorer(fbeta_score, beta=0.5, average="binary"),
    "Cohen kappa": make_scorer(cohen_kappa_score),
    "Accuracy": "accuracy",
}

suite = model_evaluation(scorers=custom_scorers)
result = suite.run(train_ds, test_ds, model, with_display=False)
```

For regression gates, prefer greater-is-better strings:

```python
suite = model_evaluation(scorers={"Neg RMSE": "neg_rmse", "R2": "r2"})
```

Avoid lower-is-better scorers like raw `mae` or `rmse` for pass/fail thresholds unless you intentionally handle the warning and condition semantics.

## Custom checks, conditions, and suites

Create focused suites when built-in suites are too broad.

```python
from deepchecks.tabular import Suite
from deepchecks.tabular.checks import DataDuplicates, FeatureDrift, TrainTestPerformance

focused_suite = Suite(
    "Focused tabular gate",
    DataDuplicates().add_condition_ratio_less_or_equal(max_ratio=0.0),
    FeatureDrift().add_condition_drift_score_less_than(
        max_allowed_categorical_score=0.2,
        max_allowed_numeric_score=0.2,
    ),
    TrainTestPerformance(scorers=["accuracy", "precision"]),
)

result = focused_suite.run(train_ds, test_ds, model=model, with_display=False)
```

Add a custom condition to a check after inspecting `result.value`:

```python
from deepchecks.tabular.checks import DataDuplicates

check = DataDuplicates()
probe = check.run(train_ds, with_display=False)
print(probe.value)  # float duplicate ratio

check.add_condition("duplicate ratio is exactly zero", lambda ratio: ratio == 0.0)
result = check.run(train_ds, with_display=False)
```

Remove or clear conditions from a suite:

```python
suite = data_integrity()
print(suite)          # inspect check and condition indexes
suite[5].remove_condition(0)
suite[5].clean_conditions()
suite.remove(5)       # remove the whole check from the suite
```

## Result handoff

After validation, use the sibling integration guidance for persistence and gates:

- HTML/JSON saving: [results-and-integrations](../../results-and-integrations/SKILL.md)
- CI/pytest condition gates: [results-and-integrations](../../results-and-integrations/SKILL.md)
- Package-wide display/import problems: [root troubleshooting](../../../references/troubleshooting.md)

Minimal status extraction before handoff:

```python
failed_to_run = result.get_not_ran_checks()
not_passed = result.get_not_passed_checks(fail_if_warning=True)
summary = {
    "passed": result.passed(fail_if_warning=True, fail_if_check_not_run=False),
    "not_ran": [item.get_header() for item in failed_to_run],
    "not_passed": [item.get_header() for item in not_passed],
}
```

## Bundled smoke helper

Run the bundled smoke script to verify that the tabular API can construct Datasets and optionally execute small suites:

```bash
python <tabular-validation-sub-skill>/scripts/deepchecks_tabular_smoke.py --help
python <tabular-validation-sub-skill>/scripts/deepchecks_tabular_smoke.py --skip-run
python <tabular-validation-sub-skill>/scripts/deepchecks_tabular_smoke.py --suite model-evaluation
```

Resolve `<tabular-validation-sub-skill>` to the directory containing this sub-skill's `SKILL.md`. Use `--predictions-only` to exercise the precomputed prediction path. Use `--html-out some-report.html` only when an explicit local output path is desired; the script writes no report by default.
