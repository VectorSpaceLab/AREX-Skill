# Training API Reference

This reference records the training and downsampling APIs verified for CellTypist 1.7.1.

## `celltypist.train`

Verified signature:

```python
celltypist.train(
    X=None,
    labels=None,
    genes=None,
    transpose_input=False,
    with_mean=True,
    check_expression=True,
    C=1.0,
    solver=None,
    max_iter=None,
    n_jobs=None,
    use_SGD=False,
    alpha=0.0001,
    use_GPU=False,
    mini_batch=False,
    batch_number=100,
    batch_size=1000,
    epochs=10,
    balance_cell_type=False,
    feature_selection=False,
    top_genes=300,
    date='',
    details='',
    url='',
    source='',
    version='',
    **kwargs,
) -> celltypist.models.Model
```

### Inputs

- `X`: expression input as an `AnnData` object, `.h5ad`, raw count table path (`.csv`, `.txt`, `.tsv`, `.tab`, `.mtx`, `.mtx.gz`), `DataFrame`, dense array, sparse matrix, or other array-like object accepted by CellTypist.
- `labels`: cell-type labels, either a one-label-per-cell file/list-like object or, for `AnnData`, an `.obs` column name.
- `genes`: one gene per input feature. Omit only when CellTypist can infer genes from an `AnnData`, table file, or `DataFrame`; array-like and `.mtx` inputs must provide genes.
- `transpose_input`: use `True` only when the expression matrix is gene-by-cell rather than cell-by-gene.

CellTypist expects cell-by-gene training data. For `AnnData` and in-memory array-like inputs, expression should already be `log1p` normalized to 10,000 counts per cell unless `check_expression=False` is an intentional bypass. Raw count table paths are normalized and log-transformed internally.

### Logistic Regression Defaults

- `use_SGD=False` selects traditional logistic regression.
- If `solver=None`, CellTypist picks `sag` for more than 50,000 cells and `lbfgs` otherwise.
- Valid CPU solvers are `liblinear`, `lbfgs`, `newton-cg`, `sag`, and `saga`.
- `C` is the inverse L2 regularization strength for traditional logistic regression.
- `max_iter` defaults by cell count when omitted: 1000 for fewer than 50,000 cells, 500 for 50,000 to fewer than 500,000 cells, and 200 for 500,000 or more cells.
- `n_jobs` controls CPU parallelism for traditional logistic regression and SGD, but not mini-batch training.

Use this mode for small to intermediate references, especially when more stable probability scores matter.

### SGD Training

- Set `use_SGD=True` for stochastic-gradient logistic regression.
- `alpha` is the SGD L2 regularization strength.
- `solver` and `C` are ignored when `use_SGD=True`.
- Extra keyword arguments are passed to `sklearn.linear_model.SGDClassifier`.

Use SGD when the expression matrix is too large for comfortable traditional logistic regression or when runtime matters more than default probability calibration.

### Mini-Batch SGD

- Mini-batch training requires both `use_SGD=True` and `mini_batch=True`.
- `batch_size` controls cells per batch, `batch_number` caps batches per epoch, and `epochs` controls repeated passes.
- The default `batch_number=100`, `batch_size=1000`, and `epochs=10` can observe up to about 1,000,000 sampled cells across epochs.
- CellTypist raises an error when the number of cells is less than or equal to `batch_size`.
- CellTypist warns when mini-batch training is requested for fewer than 10,000 cells.
- `balance_cell_type=True` samples rare labels with higher probability during mini-batch selection.

Use mini-batch SGD for very large references, not for tiny fixtures or modest atlases.

### Sparse and Memory Options

- `with_mean=True` on sparse input causes CellTypist to convert the matrix to dense before scaling.
- Set `with_mean=False` to preserve sparse storage during scaling and reduce RAM use, accepting a possible model-quality trade-off.
- CellTypist may still densify sparse matrices with 64-bit sparse indices because the downstream sklearn path cannot handle very large sparse index types.
- Downsample cells or restrict genes, such as highly variable genes, when large cell-by-gene matrices trigger runtime warnings.

### Expression Checks

- With `check_expression=True`, CellTypist checks the first row and expects `expm1(row).sum()` to be close to 10,000.
- HVG-only or otherwise subsetted matrices can fail this check even when derived from correctly normalized data because the subset no longer sums to 10,000.
- Use `check_expression=False` only when the user intentionally supplies such a subset, or when another validated preprocessing path guarantees the intended scale.

### GPU Caveat

- `use_GPU=True` applies only to non-SGD logistic regression.
- GPU training requires `cuml` to import successfully before calling `train`.
- If `use_GPU=True`, `use_SGD=False`, and `cuml` is absent, CellTypist logs a warning and returns `None` instead of a trained model.
- The GPU solver must be `qn` when specified.

Always check that the returned value is a `Model` before writing it.

### Feature Selection

- `feature_selection=True` performs a first SGD training pass, selects top genes per class from absolute coefficients, unions selected genes, and retrains on the reduced feature set.
- `top_genes` defaults to 300 per class before unioning.
- CellTypist raises an error when the total gene count is less than or equal to `top_genes`.
- Feature selection adds runtime; prefer precomputed HVGs when the user already has a trusted feature-selection workflow.

### Model Metadata and Output

- `date`, `details`, `url`, `source`, and `version` populate the returned model description.
- The return value is a `celltypist.models.Model` with `.write(file)` for persistence.
- After writing a model, use it in annotation by passing either the loaded `Model` object or the saved model path to `celltypist.annotate`; route annotation details to `../annotation-workflows/`.

## `celltypist.samples.downsample_adata`

Verified signature:

```python
celltypist.samples.downsample_adata(
    adata,
    mode='total',
    n_cells=None,
    by=None,
    balance_cell_type=False,
    random_state=0,
    return_index=True,
) -> Union[anndata.AnnData, numpy.ndarray]
```

### Parameters and Behavior

- `adata`: input `AnnData`.
- `mode='total'`: sample `n_cells` from all observations.
- `mode='each'`: sample up to `n_cells` from each cell type in `adata.obs[by]`.
- `n_cells` is required for all modes.
- `by` is required for `mode='each'` and for `mode='total', balance_cell_type=True`.
- `balance_cell_type=True` in total mode weights rare classes more heavily.
- `return_index=True` returns sampled observation indices; `False` returns an `AnnData` subset copy.
- `random_state` seeds the NumPy sampling path for reproducible downsampling.

### Downsampling Constraints

- In total mode, `n_cells` must be fewer than `adata.n_obs`.
- In each mode, cell types with fewer than `n_cells` observations contribute all available cells.
- Valid modes are only `total` and `each`.

Use downsampling to shrink training runs, then feed the subsetted `AnnData` into `celltypist.train` with the same label column and compatible preprocessing assumptions.
