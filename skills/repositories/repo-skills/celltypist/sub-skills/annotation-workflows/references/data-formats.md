# Annotation Data Formats

CellTypist annotation accepts raw-count tables, Matrix Market files, `.h5ad`, and in-memory `AnnData`. The most common failures come from orientation, missing `.mtx` sidecar names, non-gene-symbol features, or supplying raw counts where normalized AnnData is expected.

## Count tables: `.csv`, `.txt`, `.tsv`, `.tab`

Expected layout:

- Cell-by-gene is the desired layout: rows are cells and columns are genes.
- The first column/index should identify cells when using CSV/TSV-style tables.
- Column names should be gene symbols that overlap the chosen CellTypist model.
- Values should be raw UMI/read counts. CellTypist normalizes to 10,000 counts per cell and log1p-transforms internally.
- Include non-expressed genes when they are genuinely absent, because zero expression can contribute negative evidence relative to model signatures.

If the user has gene-by-cell data, set `transpose_input=True` in Python or `--transpose-input` in CLI. CellTypist also warns and auto-transposes if it detects a likely gene-by-cell table, including very large feature counts, long first variable names, or common gene symbols among observation names.

Python:

```python
result = celltypist.annotate(
    "query_counts.csv",
    model="local_model.pkl",
    transpose_input=False,
)
```

CLI:

```bash
celltypist --indata query_counts.csv --model local_model.pkl --outdir results --quiet
```

## Matrix Market: `.mtx`, `.mtx.gz`

Matrix Market inputs require explicit sidecar files:

- `gene_file`: one gene symbol per line, matching matrix variables after orientation is resolved.
- `cell_file`: one cell name per line, matching matrix observations after orientation is resolved.
- For gene-by-cell Matrix Market input, pass `transpose_input=True` or `--transpose-input` so that the final `AnnData` is cell-by-gene before sidecar lengths are checked.

Python:

```python
result = celltypist.annotate(
    "query.mtx",
    model="local_model.pkl",
    gene_file="genes.txt",
    cell_file="cells.txt",
)
```

CLI:

```bash
celltypist \
  --indata query.mtx \
  --model local_model.pkl \
  --gene-file genes.txt \
  --cell-file cells.txt \
  --outdir results \
  --quiet
```

Preflight checks for `.mtx`:

- If the input is cell-by-gene, `len(genes.txt)` must equal the number of matrix columns and `len(cells.txt)` must equal the number of matrix rows.
- If the input is gene-by-cell and you pass transpose, `len(genes.txt)` must equal the number of matrix rows before transpose and final `n_vars` after transpose; `len(cells.txt)` must equal the number of matrix columns before transpose and final `n_obs` after transpose.
- If CellTypist reports a gene or cell count mismatch, verify orientation first, then verify the exact line counts and order in the sidecar files.

## `.h5ad` and in-memory `AnnData`

For `.h5ad` or loaded `AnnData`, CellTypist does not treat the input as raw counts. It expects log1p-normalized expression to 10,000 counts per cell:

- `.X` is checked first.
- If `.X` has negative values or values above the expected log1p range and `.raw.X` exists, `.raw.X` is checked and may be used instead.
- If both `.X` and `.raw.X` are invalid, annotation raises an error.
- If values look valid but `expm1(first_cell).sum()` is not close to 10,000, CellTypist warns that the matrix may not be normalized with all genes.
- Preserve all genes where possible. Normalizing all genes and then subsetting before annotation can make the normalization check less meaningful and can reduce model feature overlap.

Python with a file:

```python
result = celltypist.annotate("query.h5ad", model="local_model.pkl")
```

Python with an in-memory object:

```python
result = celltypist.annotate(adata, model="local_model.pkl")
```

For probability and label insertion into the same object:

```python
adata_out = result.to_adata(
    insert_labels=True,
    insert_conf=True,
    insert_prob=True,
    prefix="ct_",
)
```

## Model-feature overlap

Prediction only uses genes that overlap `model.classifier.features`. If no input genes overlap the model, CellTypist raises `No features overlap with the model. Please provide gene symbols`.

Before running expensive annotation, check:

```python
model_genes = set(model.features)
input_genes = set(adata.var_names)
overlap = model_genes & input_genes
```

Low or zero overlap usually means the input uses Ensembl IDs, symbols from the wrong species, non-unique feature names, a transposed matrix, or a model trained on a different gene naming convention. Route model conversion/gene-ID mapping decisions to `../model-management/SKILL.md`.

## Cache and network implications

Annotation itself can run offline when the `model` argument is a local `.pkl` path or a loaded `Model` object. If a built-in model name or no model is supplied, CellTypist may inspect its model cache under the `CELLTYPIST_FOLDER` location and can attempt model-index/model downloads when cache files are absent. For offline workflows, set `CELLTYPIST_FOLDER` to an already populated cache or pass an explicit local model file.
