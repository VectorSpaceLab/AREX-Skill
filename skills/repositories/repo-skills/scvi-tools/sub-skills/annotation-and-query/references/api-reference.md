# Annotation and Query API Reference

## Imports

```python
import scvi
from scvi.model import SCVI, SCANVI
from scvi.external import SOLO, CellAssign
```

`scvi.external` contains optional models. In a minimal install, imports may succeed while model-specific optional dependencies or accelerators are unavailable; prefer CPU-safe smoke tests before long runs.

## `scvi.model.SCANVI`

### Setup

```python
SCANVI.setup_anndata(
    adata,
    labels_key="cell_type",
    unlabeled_category="Unknown",
    layer=None,
    batch_key=None,
    size_factor_key=None,
    categorical_covariate_keys=None,
    continuous_covariate_keys=None,
    use_minified=True,
)
```

Key requirements:

- `labels_key` is required and must name a column in `adata.obs`.
- `unlabeled_category` is required and must exactly match the token used for unlabeled cells.
- Counts are read from `adata.X` unless `layer` is provided.
- `batch_key`, size factors, and covariates become part of the registry and must be compatible for later query data.

### Constructor

```python
SCANVI(
    adata,
    n_hidden=128,
    n_latent=10,
    n_layers=1,
    dropout_rate=0.1,
    dispersion="gene",
    gene_likelihood="zinb",
    use_observed_lib_size=True,
    linear_classifier=False,
)
```

Annotation-specific options:

- `linear_classifier=True` uses a single linear classifier head; useful for simpler decision boundaries and interpretability checks.
- `dispersion="gene-label"` can model label-specific dispersion, but only use it when labels are reliable enough.
- `gene_likelihood` should match count assumptions; `"zinb"` is the default.

### Initialize from SCVI

```python
scanvi = SCANVI.from_scvi_model(
    scvi_model,
    unlabeled_category="Unknown",
    labels_key="cell_type",
    adata=None,
    linear_classifier=False,
)
```

Behavior and validation:

- The source `scvi_model` must already be trained.
- If the source `SCVI` setup did not include a labels key, `labels_key` must be provided.
- If `adata` is supplied, it is validated against the source model registry.
- Minified latent-posterior-only data cannot initialize SCANVI unless counts were retained in the minification mode.
- Model architecture parameters already fixed by the source `SCVI` are not overridden by `scanvi_kwargs`.

### Prediction

Common pattern:

```python
hard = scanvi.predict()
adata.obs["scanvi_label"] = hard

soft = scanvi.predict(soft=True)
adata.obs["scanvi_confidence"] = soft.max(axis=1).to_numpy()
adata.obs["scanvi_margin"] = (
    soft.max(axis=1) - soft.apply(lambda row: row.nlargest(2).iloc[-1], axis=1)
).to_numpy()
```

Prediction checks:

- Hard predictions should be one label per observed cell.
- Soft predictions should have one column per registered labeled class, not a new column for every unknown query category.
- Low maximum probability or low top-two margin should trigger manual review.

## `scvi.external.SOLO`

### Create from SCVI

```python
solo = SOLO.from_scvi_model(
    scvi_model,
    adata=None,
    restrict_to_batch=None,
    doublet_ratio=2,
)
```

Requirements and behavior:

- The input `SCVI` model must be trained on count data.
- `SCVI` setup may include a `batch_key` and labels, but extra continuous and categorical covariates are unsupported for SOLO initialization.
- `restrict_to_batch` is only valid when the source `SCVI` was trained with multiple batch categories.
- If the source has multiple batches and `restrict_to_batch` is omitted, SOLO uses the first batch behavior and emits a warning; prefer explicit per-batch runs.
- `doublet_ratio` controls the number of simulated doublets relative to observed cells.

### Train and predict

```python
solo.train(
    max_epochs=400,
    lr=1e-3,
    train_size=0.9,
    validation_size=None,
    batch_size=128,
    early_stopping=True,
)

probs = solo.predict(soft=True, include_simulated_doublets=False, return_logits=False)
calls = solo.predict(soft=False)
```

Output details:

- With `soft=True`, `SOLO.predict(...)` returns a DataFrame indexed by cell barcode.
- Default soft outputs are probabilities in current scvi-tools; use `return_logits=True` only to reproduce older logit behavior.
- By default, simulated doublets are excluded from returned predictions.
- With `soft=False`, the output is the winning class label, usually `"singlet"` or `"doublet"`.

## `scvi.external.CellAssign`

### Setup

```python
CellAssign.setup_anndata(
    adata,
    size_factor_key="size_factor",
    layer=None,
    batch_key=None,
    categorical_covariate_keys=None,
    continuous_covariate_keys=None,
)
```

`size_factor_key` is central to CellAssign. A common approximation is total counts per cell divided by the mean total counts.

### Constructor

```python
model = CellAssign(adata, cell_type_markers)
```

`cell_type_markers` must be a `pandas.DataFrame` where:

- Index values are marker gene names.
- Columns are candidate cell type labels.
- Rows can be selected and ordered by `adata.var_names`.
- Row index values are unique.

The constructor internally reorders markers with `cell_type_markers.loc[adata.var_names]`. If any `adata.var_names` are missing from the marker matrix index, it raises a `KeyError` that the AnnData and marker matrix do not contain the same genes. Duplicate marker rows raise an `AssertionError`.

### Train and predict

```python
model.train(
    max_epochs=400,
    lr=3e-3,
    train_size=None,
    validation_size=None,
    batch_size=1024,
    early_stopping=True,
)

assignment_probs = model.predict()
hard = assignment_probs.idxmax(axis=1)
confidence = assignment_probs.max(axis=1)
```

Output details:

- `CellAssign.predict()` returns soft probabilities as a DataFrame with columns equal to `cell_type_markers.columns`.
- Hard labels are derived with `idxmax(axis=1)`; keep probabilities for uncertainty review.
- `get_normalized_expression(...)` is available through model mixins for expression inspection after fitting.

## Preflight validators

Use these checks before training annotation models:

```python
assert labels_key in adata.obs
assert adata.obs[labels_key].isna().sum() == 0
assert unlabeled_category in set(map(str, adata.obs[labels_key].astype(str)))
assert adata.var_names.is_unique
```

For CellAssign:

```python
assert marker_df.index.is_unique
missing = adata.var_names.difference(marker_df.index)
if len(missing):
    raise ValueError(f"marker matrix is missing {len(missing)} adata genes")
marker_df = marker_df.loc[adata.var_names]
empty_types = marker_df.columns[(marker_df.sum(axis=0) == 0).to_numpy()]
if len(empty_types):
    raise ValueError(f"cell types with no markers: {list(empty_types)}")
```

For query/reference SCANVI:

```python
if not query_adata.var_names.equals(reference_adata.var_names):
    query_adata = query_adata[:, reference_adata.var_names].copy()
query_adata.obs[labels_key] = query_adata.obs[labels_key].astype(str)
query_adata.obs.loc[:, labels_key] = query_adata.obs[labels_key].where(
    query_adata.obs[labels_key].isin(reference_adata.obs[labels_key].astype(str).unique()),
    unlabeled_category,
)
```
