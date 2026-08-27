# Evaluation workflows

Use these recipes after synthetic data has been sampled. For fitting/sampling, route to the relevant synthesis sub-skill first.

## 1. Evaluate single-table synthetic data

```python
from sdv.evaluation import evaluate_quality, run_diagnostic

quality = evaluate_quality(real_data, synthetic_data, metadata, verbose=True)
diagnostic = run_diagnostic(real_data, synthetic_data, metadata, verbose=True)

quality_score = quality.get_score()
diagnostic_score = diagnostic.get_score()
quality_properties = quality.get_properties()
diagnostic_properties = diagnostic.get_properties()
```

Interpretation pattern:

- `run_diagnostic` should be the first gate after sampling. Low diagnostic scores usually mean invalid data structure, metadata mismatch, or constraint/key failures.
- `evaluate_quality` measures statistical similarity, not privacy or task utility.
- Inspect `get_properties()` before requesting details by property name, because exact report property names come from the installed `sdmetrics` version.

## 2. Evaluate multi-table synthetic data

```python
from sdv.evaluation import evaluate_quality, run_diagnostic

quality = evaluate_quality(real_tables, synthetic_tables, metadata, verbose=False)
diagnostic = run_diagnostic(real_tables, synthetic_tables, metadata, verbose=False)

print(quality.get_score())
print(diagnostic.get_properties())
```

Multi-table inputs must both be dictionaries with the same table names. Validate relational data first:

```python
metadata.validate()
metadata.validate_data(real_tables)
metadata.validate_data(synthetic_tables)
```

If diagnostic scores are poor, route back to multi-table synthesis or data-preparation to fix relationships and sdtypes before interpreting quality.

## 3. Plot one single-table column

```python
from sdv.evaluation.single_table import get_column_plot

fig = get_column_plot(
    real_data=real_data,
    synthetic_data=synthetic_data,
    metadata=metadata,
    column_name='amount',
)
fig.show()
```

Override the automatic plot type when needed:

```python
fig = get_column_plot(
    real_data=real_data,
    synthetic_data=synthetic_data,
    metadata=metadata,
    column_name='region',
    plot_type='bar',
)
```

## 4. Plot a pair of single-table columns

```python
from sdv.evaluation.single_table import get_column_pair_plot

fig = get_column_pair_plot(
    real_data=real_data,
    synthetic_data=synthetic_data,
    metadata=metadata,
    column_names=['amount', 'region'],
    plot_type='box',
    sample_size=500,
)
```

Use `sample_size` for large datasets to keep figures interactive. Do not reduce the underlying report inputs just because plots are sampled.

## 5. Plot multi-table columns and cardinality

```python
from sdv.evaluation.multi_table import (
    get_column_plot,
    get_column_pair_plot,
    get_cardinality_plot,
)

fig_amount = get_column_plot(
    real_data=real_tables,
    synthetic_data=synthetic_tables,
    metadata=metadata,
    table_name='orders',
    column_name='amount',
)

fig_pair = get_column_pair_plot(
    real_data=real_tables,
    synthetic_data=synthetic_tables,
    metadata=metadata,
    table_name='orders',
    column_names=['amount', 'status'],
    sample_size=500,
)

fig_cardinality = get_cardinality_plot(
    real_data=real_tables,
    synthetic_data=synthetic_tables,
    child_table_name='orders',
    parent_table_name='customers',
    child_foreign_key='customer_id',
    metadata=metadata,
    plot_type='bar',
)
```

Cardinality plots use metadata's parent primary key; ensure the relationship and table names are correct before plotting.

## 6. Use reports to decide next action

| Finding | Likely next route |
| --- | --- |
| Diagnostic data-structure failures | data-preparation for metadata/data mismatch, or synthesis sub-skill for model output issues. |
| Diagnostic data-validity failures | constraints for business-rule failures, or data-preparation for sdtype/key mismatch. |
| Low column-shape quality | model-selection and transformer tuning in single-table/multi-table/sequential sub-skills. |
| Low column-pair trend quality | try different model family, add constraints, or improve metadata sdtypes. |
| Poor cardinality or relationship quality | multi-table synthesis and relationship metadata checks. |
| Unsupported plot type/sdtype errors | evaluation troubleshooting and metadata sdtype correction. |

## 7. Keep evaluation separate from privacy validation

SDV quality and diagnostic reports describe similarity and validity. They do not prove privacy, fairness, downstream utility, or compliance. If the task asks for privacy metrics or model utility, treat SDV reports as one diagnostic component and add external task-specific checks.
