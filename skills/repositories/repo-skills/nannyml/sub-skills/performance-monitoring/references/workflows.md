# Performance Monitoring Workflows

## Workflow 1: binary classification performance estimation with CBPE

Use this when the model emits one probability score column and analysis targets are delayed or unavailable.

```python
import nannyml as nml

reference, analysis, _ = nml.load_synthetic_car_loan_dataset()

estimator = nml.CBPE(
    metrics=['roc_auc', 'f1', 'precision', 'recall', 'specificity', 'accuracy'],
    y_pred_proba='y_pred_proba',
    y_pred='y_pred',
    y_true='repaid',
    problem_type='classification_binary',
    timestamp_column_name='timestamp',
    chunk_size=5000,
)
estimated = estimator.fit(reference).estimate(analysis)
analysis_df = estimated.filter(period='analysis').to_df(multilevel=False)
figure = estimated.filter(period='analysis', metrics=['roc_auc']).plot()
```

If the user only needs `roc_auc` or `average_precision`, `y_pred` can be omitted. If they ask for F1, precision, recall, specificity, accuracy, confusion matrix, or business value, keep `y_pred`.

## Workflow 2: multiclass classification CBPE

Use a dict for probability columns. The dict keys are class labels and values are DataFrame column names.

```python
import nannyml as nml

reference, analysis, _ = nml.load_synthetic_multiclass_classification_dataset()

estimator = nml.CBPE(
    metrics=['roc_auc', 'f1', 'precision', 'recall', 'specificity', 'accuracy'],
    y_pred_proba={
        'prepaid_card': 'y_pred_proba_prepaid_card',
        'highstreet_card': 'y_pred_proba_highstreet_card',
        'upmarket_card': 'y_pred_proba_upmarket_card',
    },
    y_pred='y_pred',
    y_true='y_true',
    problem_type='classification_multiclass',
    timestamp_column_name='timestamp',
    chunk_size=6000,
)
estimated = estimator.fit(reference).estimate(analysis)
print(estimated.filter(period='analysis', metrics=['f1']).to_df(multilevel=False).head())
```

Multiclass workflows require `y_pred` and a probability column for each class used by the monitored model.

## Workflow 3: regression performance estimation with DLE

Use DLE when the model emits point predictions for a regression target and analysis targets are unavailable.

```python
import pandas as pd
import nannyml as nml

# NannyML 0.13.1 can hit ArrowStringArray issues under pandas 3 string inference.
if hasattr(pd.options, 'future') and hasattr(pd.options.future, 'infer_string'):
    pd.options.future.infer_string = False

reference, analysis, _ = nml.load_synthetic_car_price_dataset()
features = ['car_age', 'km_driven', 'price_new', 'accident_count', 'door_count', 'fuel', 'transmission']

# Keep string-like categorical columns as object/category before fitting.
for column in ['fuel', 'transmission']:
    reference[column] = reference[column].astype('object')
    analysis[column] = analysis[column].astype('object')

estimator = nml.DLE(
    feature_column_names=features,
    y_pred='y_pred',
    y_true='y_true',
    metrics=['mae', 'rmse', 'rmsle'],
    timestamp_column_name='timestamp',
    chunk_size=6000,
    tune_hyperparameters=False,
)
estimated = estimator.fit(reference).estimate(analysis)
print(estimated.filter(period='analysis', metrics=['rmse']).to_df(multilevel=False).head())
```

For smoke runs, keep `tune_hyperparameters=False`. If the user requests tuning, pass a bounded `hyperparameter_tuning_config`, especially `time_budget`.

## Workflow 4: realized performance when targets arrive

Join or append analysis targets before calling `PerformanceCalculator.calculate`.

```python
import nannyml as nml

reference, analysis, analysis_targets = nml.load_synthetic_car_loan_dataset()
analysis_with_targets = analysis.merge(analysis_targets, on='id')

calculator = nml.PerformanceCalculator(
    metrics=['roc_auc', 'f1'],
    y_true='repaid',
    y_pred='y_pred',
    y_pred_proba='y_pred_proba',
    problem_type='classification_binary',
    timestamp_column_name='timestamp',
    chunk_size=5000,
)
realized = calculator.fit(reference).calculate(analysis_with_targets)
print(realized.filter(period='analysis').to_df(multilevel=False).head())
```

For regression, omit `y_pred_proba` and set `problem_type='regression'`:

```python
reference, analysis, analysis_targets = nml.load_synthetic_car_price_dataset()
analysis_with_targets = analysis.merge(analysis_targets, on='id')

calculator = nml.PerformanceCalculator(
    metrics=['mae', 'rmse'],
    y_true='y_true',
    y_pred='y_pred',
    problem_type='regression',
    timestamp_column_name='timestamp',
    chunk_size=6000,
)
realized = calculator.fit(reference).calculate(analysis_with_targets)
```

## Workflow 5: compare estimated and realized performance

Use this when targets arrive later and the user wants to validate estimation quality.

```python
import nannyml as nml

reference, analysis, analysis_targets = nml.load_synthetic_car_loan_dataset()
analysis_with_targets = analysis.merge(analysis_targets, on='id')

estimated = nml.CBPE(
    metrics=['roc_auc'],
    y_pred_proba='y_pred_proba',
    y_pred='y_pred',
    y_true='repaid',
    problem_type='classification_binary',
    timestamp_column_name='timestamp',
    chunk_size=5000,
).fit(reference).estimate(analysis)

realized = nml.PerformanceCalculator(
    metrics=['roc_auc'],
    y_true='repaid',
    y_pred='y_pred',
    y_pred_proba='y_pred_proba',
    problem_type='classification_binary',
    timestamp_column_name='timestamp',
    chunk_size=5000,
).fit(reference).calculate(analysis_with_targets)

figure = estimated.filter(metrics=['roc_auc']).compare(realized.filter(metrics=['roc_auc'])).plot()
```

`compare` requires one metric/key per side. If the user wants many metrics, loop over them and compare one at a time.

## Workflow 6: business value and confusion matrix

For binary classification:

```python
estimator = nml.CBPE(
    metrics=['confusion_matrix', 'business_value'],
    y_pred_proba='y_pred_proba',
    y_pred='y_pred',
    y_true='repaid',
    problem_type='classification_binary',
    business_value_matrix=[[2, -5], [-10, 10]],
    normalize_confusion_matrix='all',
    normalize_business_value='per_prediction',
    chunk_size=5000,
)
```

Use the same options on `PerformanceCalculator` for realized confusion matrix or business value. The business-value matrix orientation is tied to confusion matrix cells; keep it square and verify matrix shape before running a long job.

## Workflow 7: tune DLE only when requested

DLE uses internal LightGBM models. Hyperparameter tuning is optional and can be expensive. A bounded example:

```python
estimator = nml.DLE(
    feature_column_names=features,
    y_pred='y_pred',
    y_true='y_true',
    metrics=['rmse'],
    tune_hyperparameters=True,
    hyperparameter_tuning_config={
        'time_budget': 10,
        'metric': 'mse',
        'estimator_list': ['lgbm'],
        'eval_method': 'cv',
        'hpo_method': 'cfo',
        'n_splits': 5,
        'task': 'regression',
        'seed': 1,
        'verbose': 0,
    },
)
```

Use a fixed seed and small budget for reproducible diagnostics; increase the budget only when the user accepts the runtime tradeoff.

## Validation checklist

Before running a performance workflow, check:

- The `problem_type` matches the model family.
- Reference data has targets for every selected performance estimator/calculator.
- Analysis targets are present only when calculating realized performance.
- Classification probability columns match the binary string or multiclass dict shape.
- `y_pred` is present unless the workflow is binary-only and uses only `roc_auc` or `average_precision`.
- Chunking is intentionally selected and produces enough chunks.
- Metric names are valid for the problem type.
- Log-based regression metrics are appropriate for the data.
- Result comparisons are filtered to one metric/key per side.
