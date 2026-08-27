# Evaluation API reference

This reference covers SDV's public evaluation helpers. It assumes real and synthetic data have already been generated and share the same metadata.

## Imports

```python
from sdv.evaluation import evaluate_quality, run_diagnostic
from sdv.evaluation.single_table import get_column_plot, get_column_pair_plot
from sdv.evaluation.multi_table import get_cardinality_plot
```

The unified `sdv.evaluation` functions work with both single-table DataFrames and multi-table dictionaries. The `sdv.evaluation.single_table` and `sdv.evaluation.multi_table` modules own plot helpers and still expose deprecated `evaluate_quality` / `run_diagnostic` aliases that emit `FutureWarning`; prefer unified imports for report generation.

## Unified report functions

| Function | Signature | Input contract | Return object |
| --- | --- | --- | --- |
| `evaluate_quality` | `evaluate_quality(real_data, synthetic_data, metadata, verbose=True)` | `real_data` and `synthetic_data` must both be pandas DataFrames or both be `dict[str, DataFrame]`. Metadata can be unified `Metadata`; legacy single-table metadata is converted internally for DataFrame inputs. | `sdmetrics.reports.QualityReport` generated from the metadata dict. |
| `run_diagnostic` | `run_diagnostic(real_data, synthetic_data, metadata, verbose=True)` | Same data-shape rules as `evaluate_quality`. | `sdmetrics.reports.DiagnosticReport`. |

Typical report methods from `sdmetrics` objects:

- `report.get_score()` returns an overall score.
- `report.get_properties()` returns a DataFrame of report property scores.
- `report.get_details(property_name)` returns a DataFrame with row-level or metric-level details when supported by that property.
- Report generation prints progress unless `verbose=False`.

## Single-table plot functions

| Function | Signature | Behavior |
| --- | --- | --- |
| `get_column_plot` | `get_column_plot(real_data, synthetic_data, metadata, column_name, plot_type=None)` | Returns a Plotly figure comparing one column. If `plot_type=None`, SDV chooses `distplot` for numerical/datetime columns and `bar` for categorical/boolean columns. |
| `get_column_pair_plot` | `get_column_pair_plot(real_data, synthetic_data, metadata, column_names, plot_type=None, sample_size=None)` | Returns a Plotly figure comparing two columns. With `plot_type=None`, SDV chooses `scatter` for numeric/datetime pairs, `heatmap` for categorical/boolean pairs, and `box` for mixed types. `sample_size` limits plotted points. |

Plot helpers can accept `real_data=None` or `synthetic_data=None` for one-sided visualization in some contexts, but score/report generation requires both datasets.

## Multi-table plot functions

| Function | Signature | Behavior |
| --- | --- | --- |
| `get_column_plot` | `get_column_plot(real_data, synthetic_data, metadata, table_name, column_name, plot_type=None)` | Delegates to single-table column plotting after selecting `table_name`. |
| `get_column_pair_plot` | `get_column_pair_plot(real_data, synthetic_data, metadata, table_name, column_names, plot_type=None, sample_size=None)` | Delegates to single-table pair plotting for one table. |
| `get_cardinality_plot` | `get_cardinality_plot(real_data, synthetic_data, child_table_name, parent_table_name, child_foreign_key, metadata, plot_type='bar')` | Compares cardinality of a parent-child relationship. Parent primary key is read from metadata. |

For multi-table reports, pass full dictionaries to `evaluate_quality` and `run_diagnostic`; do not call table plot helpers as a substitute for quality scoring.

## Metadata handling

- For single-table DataFrames with unified `Metadata`, SDV uses the metadata's single table name when available; otherwise it falls back to the default table name `table`.
- For legacy single-table metadata, SDV converts it into unified `Metadata` for report generation.
- For dictionaries, metadata must include all table names and relationships needed by the reports.
- Validation should happen before evaluation. Evaluation functions validate data type compatibility but assume metadata semantically describes the data.

## Plot type vocabulary

| Context | Supported values | Notes |
| --- | --- | --- |
| One column | `distplot`, `bar`, or `None` | Unsupported sdtypes require explicit `plot_type`; otherwise SDV raises `VisualizationUnavailableError`. |
| Column pair | `scatter`, `heatmap`, `box`, `violin`, or `None` | Mixed numerical/categorical pairs default to `box`; categorical pairs default to `heatmap`. |
| Cardinality | `bar` or `distplot` | Use `distplot` for high-cardinality numeric distributions; otherwise `bar` is often easier to read. |

## Return-object usage pattern

```python
quality_report = evaluate_quality(real_data, synthetic_data, metadata, verbose=False)
quality_score = quality_report.get_score()
quality_properties = quality_report.get_properties()

if 'Column Shapes' in set(quality_properties['Property']):
    column_details = quality_report.get_details('Column Shapes')
```

The exact property names and detail columns are owned by the installed `sdmetrics` version, so inspect `get_properties()` before requesting details by name.
