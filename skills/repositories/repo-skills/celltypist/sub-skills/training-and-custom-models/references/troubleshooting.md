# Training Troubleshooting

Use this guide to turn common CellTypist training failures into concrete parameter or data fixes.

## Missing Training Inputs

Symptoms:

- `Missing training data and/or training labels`
- `Missing genes`
- Invalid input extension for `X`

Fixes:

- Provide both `X` and `labels`.
- For array-like or sparse matrix `X`, provide `genes` with one gene per column.
- For `.mtx` or `.mtx.gz`, provide `genes`; CellTypist cannot infer them from the matrix alone.
- For `AnnData`, pass `labels` as an existing `.obs` column name or a vector with one entry per observation.
- Use `transpose_input=True` only when the matrix is gene by cell.

## Label or Gene Length Mismatch

Symptoms:

- `Length of training labels (...) does not match the number of input cells`
- `The number of genes (...) provided does not match the number of genes in the training data`

Fixes:

- Confirm shape is cells by genes before training.
- If the matrix is genes by cells, set `transpose_input=True` and recheck expected lengths.
- Regenerate labels after any cell downsampling so labels still correspond to the final cell order.
- Regenerate genes after any HVG or feature subset so genes still correspond to final columns.
- Run `scripts/training_data_check.py --matrix ... --labels ... --genes ...` on a small fixture to catch mismatches before a full run.

## Expression Validation Failure

Symptoms:

- `Invalid expression matrix, expect log1p normalized expression to 10000 counts per cell`
- Full normalized data passes, but an HVG-only subset fails.

Fixes:

- For `AnnData`, dense arrays, sparse matrices, and `DataFrame` inputs, provide `log1p` normalized expression to 10,000 counts per cell.
- For raw count table paths (`.csv`, `.txt`, `.tsv`, `.tab`, `.mtx`, `.mtx.gz`), let CellTypist normalize internally.
- If the user intentionally trains on HVGs or another gene subset derived from normalized data, use `check_expression=False` and document that the subset no longer sums to 10,000 because excluded genes were removed.
- Do not use `check_expression=False` to hide unknown preprocessing; confirm the source scale first.

## Sparse Matrix Memory Blow-Up

Symptoms:

- Training starts but memory spikes.
- Sparse input unexpectedly becomes dense.
- The user trains from sparse `AnnData` with many cells/genes.

Fixes:

- Set `with_mean=False` so scaling does not subtract means and densify sparse data.
- Prefer `use_SGD=True` for large sparse references.
- Downsample cells or subset genes before training.
- Be aware that CellTypist may still densify sparse matrices with 64-bit sparse index arrays for sklearn compatibility.

## Invalid Solver or GPU Solver

Symptoms:

- `Invalid solver` for CPU logistic regression.
- `Invalid solver, should be 'qn' to run on GPU`.

Fixes:

- For CPU logistic regression, use one of `liblinear`, `lbfgs`, `newton-cg`, `sag`, or `saga`.
- Leave `solver=None` when possible so CellTypist chooses `lbfgs` or `sag` by cell count.
- For GPU logistic regression, use `solver='qn'` or omit `solver`.
- Remember `solver` is ignored when `use_SGD=True`.

## Long Runtime or Non-Convergence

Symptoms:

- Training takes too long.
- Warnings about large datasets and many genes.
- Logistic regression does not converge within the expected time.

Fixes:

- For default logistic regression, reduce `max_iter` to cap runtime if the user accepts possible suboptimality.
- Use `n_jobs=-1` or an explicit CPU count for non-mini-batch CPU paths.
- Switch to `use_SGD=True` for large matrices.
- Downsample cells with `celltypist.samples.downsample_adata`.
- Restrict genes to HVGs or use `feature_selection=True` when enough genes are available.

## GPU Training Returns No Model

Symptoms:

- A warning says `to run logistic regression on GPU, please first install cuml`.
- `model.write(...)` fails because `model` is `None`.

Fixes:

- Treat `use_GPU=True` as optional acceleration only for non-SGD logistic regression.
- Confirm `cuml` imports before planning GPU training.
- If `cuml` is unavailable, rerun with `use_GPU=False` or `use_SGD=True`.
- Always check the training return value before writing: `if model is None: ...`.

## Mini-Batch on Too Few Cells

Symptoms:

- `Number of cells (...) is fewer than the batch size (...)`.
- Warning that fewer than 10,000 cells are not enough for proper mini-batch training.

Fixes:

- Set `mini_batch=False` and keep `use_SGD=True` for small or medium references.
- Lower `batch_size` so it is strictly less than the number of cells.
- Use standard SGD or logistic regression for tiny fixtures and smoke tests.
- Use `scripts/training_data_check.py --mini-batch --batch-size ...` before starting a long job.

## Feature Selection Top-Gene Failure

Symptoms:

- `The number of genes (...) is fewer than the top_genes (...)`.

Fixes:

- Set `top_genes` to a value strictly smaller than the available gene count.
- Disable `feature_selection=True` when the matrix already has very few genes.
- If the user already selected HVGs externally, train on that subset with `check_expression=False` when the normalization rationale is sound.

## Downsampling Argument Failure

Symptoms:

- `Please provide n_cells`.
- `n_cells (...) should be fewer than the total number of cells (...)`.
- `Please specify the cell type column`.
- `Unrecognized mode value`.

Fixes:

- Always pass `n_cells`.
- For `mode='total'`, choose `n_cells < adata.n_obs`.
- For `mode='each'`, provide `by` as a valid `adata.obs` label column.
- For `mode='total', balance_cell_type=True`, also provide `by`.
- Use only `mode='total'` or `mode='each'`.
- Use `return_index=True` when you want indices and `return_index=False` when you want a subset `AnnData` copy.
