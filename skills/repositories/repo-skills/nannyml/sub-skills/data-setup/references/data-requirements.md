# NannyML Data Requirements

NannyML operates on tabular data split into a reference period and an analysis period.

## Data periods

| Period | Purpose | Typical contents |
| --- | --- | --- |
| Reference | Baseline for expected model behavior and alert thresholds | Features, model outputs, timestamps when available, and targets when required by the selected workflow |
| Analysis | Monitored data to compare against the reference baseline | Features and model outputs; targets only when calculating realized performance or target drift |

Do not use model training data as the reference period when it would create over-optimistic performance expectations. Use a stable validation/test or known-good production window.

## Column roles

| Role | Meaning | Required by |
| --- | --- | --- |
| `timestamp` | Time of prediction/event; any pandas-parseable timestamp format | Optional for most workflows, required for period-based chunking and helpful for time-based plots |
| Features | Model input columns, categorical or continuous | Regression DLE; feature drift; multivariate drift; data-quality/summary checks |
| `y_pred_proba` | Predicted probability/score column(s) | CBPE classification and classification realized-performance metrics needing probabilities; output drift on scores |
| `y_pred` | Predicted label or regression prediction | Most classification metrics, all multiclass workflows, regression DLE and realized performance, output drift |
| `y_true` | Actual target/outcome | Reference for performance estimation; reference and analysis for realized performance and target drift |
| Join key | Identifier for joining analysis targets to analysis data | Required only when targets arrive separately |

Column names must be consistent between reference and analysis data for the same semantic role.

## Workflow-specific requirements

| Workflow | Reference data | Analysis data |
| --- | --- | --- |
| CBPE binary classification | `y_true`, one `y_pred_proba`, `y_pred` unless using only `roc_auc`/`average_precision` | `y_pred_proba`, `y_pred` if configured |
| CBPE multiclass classification | `y_true`, `y_pred`, one probability column per class | `y_pred`, same class probability columns |
| DLE regression | feature columns, `y_pred`, `y_true` | feature columns, `y_pred` |
| Realized performance | `y_true`, predictions/probabilities required by metrics | `y_true`, predictions/probabilities required by metrics |
| Feature drift | monitored feature columns | same monitored feature columns |
| Output drift | prediction labels and/or probability/score columns | same output columns |
| Target drift | target column | target column |
| Data-quality checks | selected data-quality columns | same selected columns |
| Summary statistics | selected continuous columns for avg/median/std/sum; any rows for row count | same selected columns |

## Joining analysis targets

If targets are delivered separately, join them before realized performance or target drift:

```python
analysis_with_targets = analysis.merge(analysis_targets, on='id')
# or, when the target frame is aligned by index:
analysis_with_targets = analysis.join(analysis_targets)
```

Then pass `analysis_with_targets` into `PerformanceCalculator.calculate` or target-drift `calculate`.

## Multiclass probability mapping

Multiclass workflows need a dictionary mapping class labels to probability columns:

```python
y_pred_proba = {
    'prepaid_card': 'y_pred_proba_prepaid_card',
    'highstreet_card': 'y_pred_proba_highstreet_card',
    'upmarket_card': 'y_pred_proba_upmarket_card',
}
```

All probability columns must exist in both reference and analysis data.

## Choosing feature lists

When building feature lists for drift, DLE, data quality, or summary statistics, usually exclude:

- identifiers such as `id`
- timestamp columns
- target columns
- model prediction labels
- prediction probability/score columns, unless intentionally monitoring output drift
- period/debug columns

Example:

```python
excluded = {'id', 'timestamp', 'y_true', 'y_pred', 'y_pred_proba', 'period'}
features = [column for column in reference.columns if column not in excluded]
```

## Built-in datasets

Use [../../../references/datasets.md](../../../references/datasets.md) for dataset-specific columns and recommended workflow pairings.

## Validation checklist

- Reference and analysis frames are non-empty.
- Reference and analysis share every selected monitored column.
- Targets are present in reference for performance estimation.
- Analysis targets are present only when required, and are joined with the correct key or index.
- Multiclass probability mappings cover all class probability columns.
- Timestamp columns parse with pandas before period chunking.
- Categorical columns have appropriate pandas dtypes or are passed through explicit type overrides in the owning workflow.
