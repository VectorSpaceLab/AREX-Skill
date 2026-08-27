---
name: data-preparation
description: "Prepare SDV demo data, local files, metadata, utilities, and logs
  before modeling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# SDV data-preparation router

Use this sub-skill when the task is to prepare SDV inputs before synthesis: load demo data, read or write local CSV/Excel data, build/edit/validate metadata, visualize or anonymize metadata, clean relational references, subset sequential rows, or inspect SDV logs.

## Route here for

- Loading SDV demo datasets and demo resource files.
- Loading local CSV folders or Excel workbooks into `dict[str, pandas.DataFrame]`.
- Detecting metadata from a single DataFrame, multiple DataFrames, CSV folders, or local file handlers.
- Editing metadata columns, primary/alternate/foreign keys, sequence keys/indexes, and column relationships.
- Running `metadata.validate()` plus `metadata.validate_data(data_dict)` for multi-table data or `metadata.validate_table(dataframe, table_name=...)` for one DataFrame before fitting a synthesizer.
- Saving, loading, anonymizing, visualizing, or upgrading metadata JSON.
- Using `drop_unknown_references`, `get_random_sequence_subset`, SDV logging helpers, or safe saved-synthesizer loading diagnostics.

## Route elsewhere

- Model fitting, sampling, conditional sampling, save/load as a modeling workflow: use the single-table, multi-table, or sequential synthesis sub-skill.
- Constraint class design, custom constraints, and constraint serialization: use the constraints sub-skill.
- Quality reports, diagnostics, and plot comparison of real vs synthetic data: use the evaluation sub-skill.

## Operating sequence

1. Identify the data modality: single-table `DataFrame`, multi-table `dict` of DataFrames, or sequential single-table data.
2. Load or create data using the narrowest I/O tool: demo API, `load_csvs`/`save_csvs`, `CSVHandler`, or `ExcelHandler`.
3. Build `Metadata` first when possible; only use legacy `SingleTableMetadata` or `MultiTableMetadata` when a downstream API specifically requires them.
4. Edit sdtypes and keys explicitly after auto-detection; do not assume inferred primary/foreign keys are correct.
5. Run `metadata.validate()` and then validate data: `metadata.validate_data(data_dict)` for multi-table input or `metadata.validate_table(dataframe, table_name=...)` for one DataFrame before routing to a synthesizer.
6. For relational data, repair unknown foreign-key references with `drop_unknown_references` only after confirming the rows are safe to discard.
7. Save stable metadata JSON and keep task-specific outputs outside the skill tree.

## References

- [API reference](references/api-reference.md) for signatures, return types, and important API boundaries.
- [Workflows](references/workflows.md) for compact end-to-end recipes.
- [Troubleshooting](references/troubleshooting.md) for failure symptoms, causes, and fixes.
