---
name: evaluation
description: "Route SDV quality, diagnostic, and visualization workflows for
  real versus synthetic data."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# SDV evaluation router

Use this sub-skill when the task is to score synthetic data quality, run diagnostic checks, or build real-vs-synthetic plots after SDV sampling. It owns the SDV evaluation functions and their interaction with `sdmetrics` report/visualization objects.

## Route here for

- Natural requests such as "evaluate SDV synthetic data", "quality report", "diagnostic report", `evaluate_quality`, `run_diagnostic`, `get_column_plot`, `get_column_pair_plot`, or `get_cardinality_plot`.
- Single-table `DataFrame` evaluation and multi-table `dict[str, DataFrame]` evaluation through the unified `sdv.evaluation` functions.
- Plot selection for one column, two columns, and multi-table relationship cardinality.
- Interpreting report scores/properties and debugging type, metadata, column, table, or sdtype errors in evaluation calls.

## Route elsewhere

- Loading data or constructing metadata: use the data-preparation sub-skill.
- Fitting or sampling data with SDV models: use single-table, multi-table, or sequential sub-skills.
- Constraint validation and constraint-specific failures: use the constraints sub-skill.
- Metadata graph visualization, not synthetic-vs-real comparison: use data-preparation.

## Operating path

1. Confirm `real_data` and `synthetic_data` use the same data shape: both pandas DataFrames for single-table workflows or both dictionaries for multi-table workflows.
2. Confirm metadata is valid and describes the real/synthetic data columns. If not, route to data-preparation before scoring.
3. Use `evaluate_quality` for distribution/trend similarity and `run_diagnostic` for data-validity/data-structure checks.
4. Use plot helpers only after confirming the target table/column names and sdtypes are supported, or provide an explicit `plot_type`.
5. Treat report scores as diagnostic evidence, not proof that the synthetic data is safe or private. Capture the result object and inspect its properties/details when the task needs explanations.

## References

- [API reference](references/api-reference.md) for function signatures, accepted data shapes, and return objects.
- [Workflows](references/workflows.md) for single-table, multi-table, and plot recipes.
- [Troubleshooting](references/troubleshooting.md) for common report and visualization failures.
