# Annotation Troubleshooting

Use this when `celltypist.annotate` or `celltypist --indata ...` fails or gives suspicious outputs.

## Missing Matrix Market sidecars

Symptom:

- `Missing gene_file and/or cell_file. Please provide both arguments together with the input mtx file`.

Cause:

- `.mtx` and `.mtx.gz` inputs do not carry gene and cell names, so CellTypist requires both sidecar files.

Recovery:

- Provide `gene_file="genes.txt"` and `cell_file="cells.txt"` in Python.
- Provide `--gene-file genes.txt --cell-file cells.txt` in CLI.
- Ensure each file has one name per line and no header unless the header is an actual gene/cell name.

## Matrix Market gene/cell length mismatch

Symptoms:

- `The number of genes in ... does not match the number of genes in ...`.
- `The number of cells in ... does not match the number of cells in ...`.

Cause:

- Sidecar line counts do not match the matrix dimensions after CellTypist's orientation handling.

Recovery:

- Determine whether the Matrix Market file is cell-by-gene or gene-by-cell.
- For gene-by-cell input, set `transpose_input=True` or `--transpose-input`.
- Recount lines in sidecars and verify their order matches the matrix rows/columns after transpose.
- Do not swap gene and cell sidecars to silence the error; doing so usually causes feature-overlap failure later.

## Transposed table or gene-by-cell warning

Symptoms:

- Warning that the input matrix is detected as gene-by-cell and will be transposed.
- Very low feature overlap or cell names that look like gene symbols.

Cause:

- CellTypist expects cell-by-gene tables, but the file may have genes as rows and cells as columns. It also auto-detects likely gene-by-cell layouts using large variable counts, long names, or common gene symbols in observation names.

Recovery:

- If you know the input is gene-by-cell, pass `transpose_input=True` or `--transpose-input` explicitly.
- Confirm that final variables are gene symbols and final observations are cells.
- If the data was already cell-by-gene but auto-transposed unexpectedly, inspect the first row/column names for unusually long cell identifiers or accidental gene symbols in cell names.

## AnnData normalization errors or warnings

Symptoms:

- `Invalid expression matrix in .X, expect log1p normalized expression to 10000 counts per cell`.
- `Invalid expression matrix in both .X and .raw.X`.
- Warning that an expression matrix is invalid and prediction may not be accurate.

Cause:

- `.h5ad` and in-memory `AnnData` inputs are expected to have log1p-normalized expression to 10,000 counts per cell in `.X`; `.raw.X` is used only when `.X` fails and `.raw.X` is valid.
- Negative scaled values, raw counts, or normalization after gene subsetting can violate expectations.

Recovery:

- Normalize all genes to 10,000 counts per cell and log1p-transform before annotation.
- Preserve `.raw` with valid normalized expression if `.X` stores scaled data.
- If the source is raw counts and a table workflow is acceptable, export a raw count table and let CellTypist normalize the table input internally.

## No model feature overlap

Symptom:

- `No features overlap with the model. Please provide gene symbols`.

Cause:

- Input genes do not overlap `model.classifier.features`. Common reasons include Ensembl IDs instead of symbols, wrong species, a transposed matrix, empty/incorrect sidecar files, or using a model trained with a different gene namespace.

Recovery:

- Verify orientation and sidecar files first.
- Compare a sample of `adata.var_names` or table columns with `model.features`.
- Convert gene IDs or species only when scientifically appropriate; route model conversion and cache/model decisions to `../model-management/SKILL.md`.
- Use an explicit local model trained on the same gene namespace when available.

## Output directory does not exist

Symptoms:

- CLI help failure saying output directory does not exist.
- `Output folder ... does not exist. Please provide a valid folder` from `to_table` or `to_plots`.

Cause:

- CellTypist does not create export folders for table or plot outputs.

Recovery:

- Run `mkdir -p results` before the CLI command.
- In Python, call `Path("results").mkdir(parents=True, exist_ok=True)` before `result.to_table(folder="results")`.

## Majority voting missing or skipped

Symptoms:

- `predicted_labels` exists, but `over_clustering` and `majority_voting` columns are absent.
- Downstream `to_adata(insert_conf_by="majority_voting")` raises that `majority_voting` is missing.

Cause:

- Majority voting was not requested, or the input has 50 or fewer cells. CellTypist skips majority voting for <=50 cells because over-clustering is not considered reliable.

Recovery:

- For small smoke tests, validate raw `predicted_labels`, `decision_matrix`, and `probability_matrix` instead of majority voting.
- For real majority voting, use more than 50 cells and pass `majority_voting=True`.
- Before using `insert_conf_by="majority_voting"`, check `"majority_voting" in result.predicted_labels.columns`.

## Over-clustering length mismatch

Symptom:

- `Length of over_clustering (...) does not match the number of input cells (...)`.

Cause:

- The vector/file supplied to `over_clustering` has one entry per cluster assignment, but its length does not match the final number of query cells.

Recovery:

- Verify the final cell count after any transpose.
- Ensure the over-clustering file has exactly one line per query cell, in the same order as the input cells.
- For `.h5ad`, prefer an existing `.obs` column name when cluster assignments are already aligned to cells.

## GPU over-clustering falls back to CPU

Symptom:

- Warning that `rapids_singlecell` is not installed and CellTypist will switch back to CPU.

Cause:

- `use_GPU=True` or `--use-GPU` was requested for automatic over-clustering, but optional RAPIDS support is unavailable.

Recovery:

- Accept CPU fallback for correctness.
- If GPU acceleration is required, install and validate `rapids_singlecell` in the active environment before running annotation.
- Use precomputed `over_clustering` to avoid automatic Leiden/neighbor-graph work when appropriate.

## Default model triggers cache or network surprises

Symptoms:

- Annotation with `model=None` or a built-in model name fails in an offline environment.
- Model listing or default-model resolution tries to consult remote model metadata.

Cause:

- CellTypist stores model files under the `CELLTYPIST_FOLDER` location. If cache files are missing, model discovery/download helpers may fetch model metadata or model files.

Recovery:

- For offline annotation, pass an explicit local `.pkl` model path or a loaded `Model` object.
- Set `CELLTYPIST_FOLDER` before Python imports CellTypist if you need a non-default populated cache.
- Route cache population, built-in model downloads, and model inventory to `../model-management/SKILL.md`.
