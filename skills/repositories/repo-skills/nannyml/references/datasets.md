# Built-in Dataset Catalog

NannyML bundles small tabular datasets that are useful for examples, smoke tests, and usability checks. Each loader returns a tuple:

```python
reference_df, analysis_df, analysis_targets_df = loader()
```

The reference DataFrame contains the baseline period. The analysis DataFrame contains monitored records. The third DataFrame contains analysis targets and must be joined only for realized performance or target-drift workflows.

## Loaders and best-fit workflows

| Loader | Problem type / purpose | Typical target | Best-fit routes |
| --- | --- | --- | --- |
| `load_synthetic_binary_classification_dataset()` | Binary classification sample for work-from-home prediction | `work_home_actual` | CBPE, realized performance, univariate drift, result comparison |
| `load_synthetic_car_loan_dataset()` | Binary classification sample for loan repayment | `repaid` | CBPE, realized performance, multivariate drift, ranking, CLI config examples |
| `load_synthetic_multiclass_classification_dataset()` | Multiclass classification sample with three probability columns | `y_true` | Multiclass CBPE and realized performance |
| `load_synthetic_car_price_dataset()` | Regression sample for used-car price prediction | `y_true` | DLE, regression realized performance, regression output/target drift, summary stats |
| `load_synthetic_car_loan_data_quality_dataset()` | Binary car-loan sample with quality issues | `repaid` | Missing values, unseen values, numerical range, summary stats |
| `load_modified_california_housing_dataset()` | Modified real-world-style binary classification sample | dataset-specific target columns | Longer example workflows and performance/drift demonstrations |
| `load_titanic_dataset()` | Binary survival sample | dataset-specific target columns | Lightweight classification examples |
| `load_us_census_ma_employment_data()` | Real-world binary employment monitoring sample | employment target data | End-to-end performance estimation plus drift comparison |

## Quick inspection snippet

```python
import nannyml as nml

for loader in [
    nml.load_synthetic_binary_classification_dataset,
    nml.load_synthetic_car_loan_dataset,
    nml.load_synthetic_multiclass_classification_dataset,
    nml.load_synthetic_car_price_dataset,
    nml.load_synthetic_car_loan_data_quality_dataset,
]:
    reference, analysis, analysis_targets = loader()
    print(loader.__name__, reference.shape, analysis.shape, analysis_targets.shape)
    print(reference.columns.tolist())
```

## Column conventions in common loaders

### Binary work-from-home dataset

- Join analysis targets on `id`.
- Prediction score: `y_pred_proba`.
- Prediction label: `y_pred`.
- Target: `work_home_actual`.
- Timestamp: `timestamp`.
- Common features: `distance_from_office`, `salary_range`, `gas_price_per_litre`, `public_transportation_cost`, `wfh_prev_workday`, `workday`, `tenure`.

### Binary car-loan dataset

- Join analysis targets on `id` or index depending on the existing analysis frame.
- Prediction score: `y_pred_proba`.
- Prediction label: `y_pred`.
- Target: `repaid`.
- Timestamp: `timestamp`.
- Common features: `car_value`, `salary_range`, `debt_to_income_ratio`, `loan_length`, `repaid_loan_on_prev_car`, `size_of_downpayment`, `driver_tenure`.

### Multiclass dataset

- Join analysis targets on `id` or index depending on the target frame in use.
- Prediction label: `y_pred`.
- Target: `y_true`.
- Timestamp: `timestamp`.
- Class probability mapping:

```python
y_pred_proba = {
    'prepaid_card': 'y_pred_proba_prepaid_card',
    'highstreet_card': 'y_pred_proba_highstreet_card',
    'upmarket_card': 'y_pred_proba_upmarket_card',
}
```

### Regression car-price dataset

- Join analysis targets on `id` or by index when appropriate.
- Prediction column: `y_pred`.
- Target: `y_true`.
- Timestamp: `timestamp`.
- Common features: `car_age`, `km_driven`, `price_new`, `accident_count`, `door_count`, `fuel`, `transmission`.
- Remove rows with negative predictions before using logarithmic metrics such as `msle` or `rmsle` if the data or model can produce negative values.
- If DLE hits an Arrow-backed string reshape issue in your pandas/pyarrow environment, set `pd.options.future.infer_string = False` before loading the data or use `pandas<3`, then keep `fuel` and `transmission` as `object` or `category` before fitting.

## Dataset selection tips

- Use car-loan data when you need a compact binary classification workflow with both performance and drift.
- Use multiclass data when testing dictionary-style probability mappings.
- Use car-price data when testing DLE or regression performance calculation.
- Use car-loan data-quality data when testing missing, unseen, and range calculators.
- Use the US Census MA employment data for a richer example that naturally combines estimated performance, univariate drift, ranking, and comparisons.

## Safety notes

These loaders read packaged CSV or Parquet files from the installed package. They should not require network access or credentials. If a loader fails, first confirm that package data files were included in the installation and that `pandas`, `pyarrow`, and CSV/Parquet dependencies import cleanly.
