# Evaluation troubleshooting

## Report input errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `real_data must be a pandas DataFrame or dictionary` or same for `synthetic_data`. | A list, NumPy array, file path, or other object was passed. | Load data into a pandas DataFrame for single-table or `dict[str, DataFrame]` for multi-table before evaluation. |
| `real_data and synthetic_data must have the same type`. | One input is a DataFrame and the other is a dict. | Use both DataFrames for single-table workflows or both dictionaries for multi-table workflows. |
| Report generation fails with metadata table/column errors. | Metadata does not describe the data being evaluated. | Route to data-preparation: validate metadata and both datasets before scoring. |
| Multi-table report fails because table names differ. | Real and synthetic dict keys are not identical or metadata uses different table names. | Align dictionary keys and metadata table names before calling `evaluate_quality` or `run_diagnostic`. |
| Report emits many warnings or slow progress. | Large data, many columns, many table relationships, or verbose progress output. | Use `verbose=False` for quiet runs; downsample only for exploratory plots, not for final report scoring unless the task explicitly accepts sampled evaluation. |

## Diagnostic and quality interpretation

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Diagnostic score is low. | Synthetic data violates metadata structure, sdtypes, keys, or relationships. | Fix validity first. Route to data-preparation, constraints, or the relevant synthesizer before interpreting quality. |
| Quality score is low but diagnostic is high. | Data is structurally valid but model did not capture distributions/trends well. | Tune model family/parameters/transformers, add constraints, or improve metadata sdtypes. Use synthesis sub-skills. |
| `get_details('...')` fails for a property name. | The installed `sdmetrics` report does not expose that property name. | Inspect `report.get_properties()` and use the exact property string returned. |
| Users ask whether a high score proves privacy. | SDV quality reports are not privacy guarantees. | State the limitation and add privacy-specific analysis outside this repo skill if required. |

## Single-table plots

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `VisualizationUnavailableError` says a column sdtype is unsupported. | Automatic plot selection only supports numerical/datetime and categorical/boolean sdtypes. | Provide explicit `plot_type` if visualization makes sense, or correct metadata sdtype in data-preparation. |
| Plot function cannot find `column_name`. | Column is absent from real/synthetic data or metadata. | Check the column exists in both datasets and metadata. Rebuild metadata if columns changed after sampling. |
| Pair plot rejects `column_names`. | Not exactly two valid columns, or one is missing. | Pass a two-item list of existing columns. |
| Plot is too large or slow. | Too many rows are being rendered. | Use `sample_size` for column-pair plots and consider plotting a representative subset for one-column plots. |
| Automatic plot type looks wrong. | Metadata sdtype does not match the desired visualization. | Override with `plot_type`, or fix metadata sdtype and re-run. |

## Multi-table plots

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Plot helper says table is missing. | `table_name`, `parent_table_name`, or `child_table_name` does not match metadata/data dict keys. | Use exact table names from `metadata.tables.keys()` and data dict keys. |
| Cardinality plot fails or looks nonsensical. | Relationship names or `child_foreign_key` do not match metadata, or data violates relationship integrity. | Validate metadata relationships and both real/synthetic dictionaries before plotting. |
| `get_cardinality_plot` uses the wrong parent key. | Metadata primary key for the parent table is incorrect. | Fix parent primary key in metadata, revalidate, and regenerate the plot. |
| Multi-table column plot succeeds but report fails. | Table-level plot only needs one table, while reports need the entire relational dict and metadata. | Use plots for local diagnosis; fix full dict/metadata before report generation. |

## Deprecated imports and sdmetrics warnings

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `FutureWarning: The evaluation functions are now accessible via the 'sdv.evaluation' module.` | Code imports `evaluate_quality` or `run_diagnostic` from `sdv.evaluation.single_table` or `.multi_table`. | Import report functions from `sdv.evaluation`. Keep plot helpers from modality modules. |
| `sdmetrics` multi-table report deprecation warnings appear during imports. | The installed `sdmetrics` version still exposes legacy multi-table report modules. | Warnings do not block SDV evaluation. Prefer unified SDV evaluation functions and record the installed versions if reproducibility matters. |
| Plotly figure does not display in the current environment. | Running in a headless terminal, notebook renderer not configured, or frontend cannot display Plotly. | Save or serialize the figure with Plotly tooling, configure a renderer, or inspect `fig.data`/`fig.layout` programmatically. |
