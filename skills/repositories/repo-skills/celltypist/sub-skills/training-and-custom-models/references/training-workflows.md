# Training Workflows

Use these patterns to plan a custom CellTypist model training run without running an expensive job prematurely.

## Prepare Training Inputs

1. Confirm expression shape is cells by genes. If the user has genes by cells, set `transpose_input=True`.
2. Confirm labels have one value per cell. For `AnnData`, prefer an `.obs` column name; for matrices, use a label vector or one-label-per-line file.
3. Confirm genes have one value per feature. Gene names are inferred from `AnnData`, table files, or `DataFrame` columns; plain arrays, sparse matrices, and `.mtx` files need explicit genes.
4. Confirm expression scale. `AnnData`, dense arrays, sparse matrices, and `DataFrame` inputs should be `log1p` normalized to 10,000 counts per cell; raw table paths are normalized internally.
5. Run `scripts/training_data_check.py` on tiny CSV/label/gene fixtures when the user asks for a quick preflight before real training.

## One-Pass Logistic Regression

Use default `celltypist.train` for small or intermediate references, especially when the user cares about probability ranges and wants fewer tuning decisions.

```python
import celltypist

model = celltypist.train(
    X=expression_input,
    labels=label_input,
    genes=gene_input,
    n_jobs=8,
    max_iter=500,
    details="custom reference model",
)
model.write("custom_celltypist_model.pkl")
```

Planning notes:

- Omit `genes` when using `AnnData`, a table file, or a `DataFrame` with gene columns.
- Leave `solver=None` unless the user has a specific sklearn reason; CellTypist chooses by cell count.
- Use `solver='saga'` or another valid CPU solver only when it matches the user's sklearn tuning plan.
- If training appears slow on a very wide/large matrix, reduce genes, downsample cells, lower `max_iter`, or switch to SGD.

## SGD Training

Use `use_SGD=True` when the matrix is large and faster training matters more than default probability calibration.

```python
model = celltypist.train(
    X=expression_input,
    labels=label_input,
    genes=gene_input,
    use_SGD=True,
    alpha=0.0001,
    max_iter=1000,
    n_jobs=8,
)
model.write("custom_sgd_celltypist_model.pkl")
```

Planning notes:

- `C`, `solver`, and `use_GPU` do not affect SGD mode.
- Tune `alpha` and `max_iter` if probability scores will be interpreted downstream.
- Pass sklearn `SGDClassifier` keyword arguments through `celltypist.train(..., **kwargs)` only when the user understands the sklearn behavior.

## Mini-Batch SGD

Use mini-batch SGD only for large references where there are more cells than `batch_size`.

```python
model = celltypist.train(
    X=expression_input,
    labels=label_input,
    genes=gene_input,
    use_SGD=True,
    mini_batch=True,
    batch_size=1000,
    batch_number=100,
    epochs=10,
    balance_cell_type=True,
)
model.write("custom_minibatch_celltypist_model.pkl")
```

Planning notes:

- Mini-batch mode raises an error if `n_cells <= batch_size`.
- Mini-batch mode is not worthwhile for tiny examples; CellTypist warns below 10,000 cells.
- `balance_cell_type=True` helps rare cell types appear in batches, but it cannot sample more unique cells from a class than exist in the reference.
- `n_jobs` is not useful for mini-batch training.

## Sparse AnnData and HVG-Only Training

For sparse matrices, avoid accidental densification during scaling:

```python
model = celltypist.train(
    X=adata[:, adata.var["highly_variable"]],
    labels="cell_type",
    with_mean=False,
    check_expression=False,
    use_SGD=True,
)
```

Use `check_expression=False` only with an explanation: HVG-only matrices often fail the 10,000-count normalization check because excluded genes are no longer part of the row sum. Keep it `True` for full normalized matrices whenever possible.

## Two-Pass Feature Selection

Use built-in feature selection when the user wants CellTypist to select genes from model coefficients and can afford an extra training pass.

```python
model = celltypist.train(
    X=expression_input,
    labels=label_input,
    genes=gene_input,
    feature_selection=True,
    top_genes=300,
    max_iter=100,
)
model.write("custom_feature_selected_celltypist_model.pkl")
```

Variants:

```python
sgd_model = celltypist.train(
    X=expression_input,
    labels=label_input,
    genes=gene_input,
    use_SGD=True,
    feature_selection=True,
)

minibatch_model = celltypist.train(
    X=expression_input,
    labels=label_input,
    genes=gene_input,
    use_SGD=True,
    mini_batch=True,
    feature_selection=True,
    batch_size=1000,
)
```

Planning notes:

- `top_genes` must be smaller than the available gene count.
- Feature selection first trains with SGD regardless of the final classifier path.
- If the user already has trusted HVGs, subset externally and pass `check_expression=False` with the normalization rationale.

## Downsample Before Training

Use `celltypist.samples.downsample_adata` when an `AnnData` reference is too large for the chosen training path.

```python
from celltypist import samples

indices = samples.downsample_adata(
    adata,
    mode="total",
    n_cells=100000,
    by="cell_type",
    balance_cell_type=True,
    random_state=0,
)
reference = adata[indices].copy()
model = celltypist.train(reference, labels="cell_type", use_SGD=True, with_mean=False)
```

For equal per-type sampling:

```python
reference = samples.downsample_adata(
    adata,
    mode="each",
    n_cells=2000,
    by="cell_type",
    return_index=False,
)
model = celltypist.train(reference, labels="cell_type", use_SGD=True, with_mean=False)
```

Downsampling checks:

- Always provide `n_cells`.
- In total mode, `n_cells` must be less than `adata.n_obs`.
- Provide `by` when using per-type mode or balanced total sampling.
- Keep the label column present after subsetting.

## Save and Use a Custom Model

After `celltypist.train` returns a model, write it to a user-chosen path and use that path or the loaded model in annotation.

```python
model.write("custom_celltypist_model.pkl")

# Later, in an annotation workflow:
predictions = celltypist.annotate(query_adata, model="custom_celltypist_model.pkl")
```

If `use_GPU=True` returned `None` because `cuml` was unavailable, do not call `.write`; either install a compatible RAPIDS/cuML stack or rerun with CPU logistic regression/SGD.

## Preflight Command Examples

CSV matrix with labels and genes:

```bash
python scripts/training_data_check.py --matrix train.csv --labels labels.csv --genes genes.csv --check-expression
```

HVG-only sparse planning check without strict expression sum validation:

```bash
python scripts/training_data_check.py --matrix hvg_train.csv --labels labels.csv --genes hvg_genes.csv --mini-batch --batch-size 1000 --feature-selection --top-genes 300 --no-check-expression
```

Downsampling argument check:

```bash
python scripts/training_data_check.py --n-cells 50000 --downsample-mode total --adata-cells 200000 --downsample-by cell_type --balance-cell-type
```

The helper validates shape, label/gene lengths, expression scale expectations, mini-batch feasibility, feature-selection feasibility, and downsampling arguments; it does not train a model.
