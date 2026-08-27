# Annotation and Query Troubleshooting

## SCANVI reports that `labels_key` is required

Likely cause: `SCANVI.from_scvi_model(scvi_model, unlabeled_category=...)` was called after the source `SCVI` model was set up without labels.

Fix:

```python
scanvi = scvi.model.SCANVI.from_scvi_model(
    scvi_model,
    unlabeled_category="Unknown",
    labels_key="cell_type",
)
```

Also confirm `cell_type` exists in the `AnnData` used to initialize SCANVI and contains the `unlabeled_category` token.

## Unlabeled token mismatch creates wrong categories

Symptoms:

- Unlabeled query cells remain as a real class such as `"unknown"`, `"Unknown"`, `"UNK"`, or `nan` instead of being treated as the configured unlabeled category.
- Soft predictions include unexpected behavior or hard predictions appear overconfident for cells that should be unknown.

Fix:

```python
labels_key = "cell_type"
unlabeled_category = "Unknown"
adata.obs[labels_key] = adata.obs[labels_key].astype("string").fillna(unlabeled_category)
adata.obs.loc[adata.obs[labels_key].isin(["unknown", "UNK", "nan", "None"]), labels_key] = unlabeled_category
scvi.model.SCANVI.setup_anndata(
    adata,
    labels_key=labels_key,
    unlabeled_category=unlabeled_category,
    batch_key="batch",
)
```

Validation:

```python
values = set(adata.obs[labels_key].astype(str))
assert unlabeled_category in values
assert not {"unknown", "UNK", "nan", "None"}.intersection(values - {unlabeled_category})
```

## Query labels include unseen categories

SCANVI is not an open-set classifier by default. If query cells contain labels not present in the reference, those labels should usually be replaced by the unlabeled token before query mapping or SCANVI setup.

Fix:

```python
reference_labels = set(reference_adata.obs[labels_key].astype(str))
query_adata.obs[labels_key] = query_adata.obs[labels_key].astype(str)
unseen = ~query_adata.obs[labels_key].isin(reference_labels)
query_adata.obs.loc[unseen, labels_key] = unlabeled_category
```

Review:

- Record how many query cells were converted to `unlabeled_category`.
- If unseen classes are biologically expected, treat them as an open-set review group and do not force a final reference label without confidence checks.
- Inspect soft prediction entropy or top-two probability margins.

## `SCANVI.from_scvi_model` rejects the query AnnData

Likely causes:

- Query genes are missing, duplicated, or in a different order than the reference registry.
- The count layer used during reference setup is missing from query data.
- Batch or covariate columns are absent or contain incompatible categories.
- The source `SCVI` model was minified without retaining counts.

Fix checklist:

```python
assert query_adata.var_names.is_unique
query_adata = query_adata[:, reference_adata.var_names].copy()
assert query_adata.var_names.equals(reference_adata.var_names)
for key in ["batch", labels_key]:
    assert key in query_adata.obs
```

If the model was minified, use a model artifact that retained counts or retrain/load from non-minified data for SCANVI initialization.

## `SOLO.from_scvi_model` rejects covariates

SOLO supports `SCVI` models set up with count data and optionally `batch_key`, but it rejects registered continuous or categorical covariates.

Fix options:

- Train a separate `SCVI` model for SOLO using only counts and optional `batch_key`.
- Keep the covariate-rich model for downstream biological integration, not doublet detection.
- If batch effects matter, run `SOLO.from_scvi_model(scvi_model, restrict_to_batch="...")` separately per batch category.

## SOLO batch restriction errors

Symptoms:

- `restrict_to_batch` was provided but the `SCVI` model was not trained with multiple batches.
- The requested batch category is absent.
- Multiple batches exist but no batch restriction was provided, leading to warnings and first-batch behavior.

Fix:

```python
batch_key = "batch"
print(adata.obs[batch_key].astype("category").cat.categories)
solo = scvi.external.SOLO.from_scvi_model(scvi_model, restrict_to_batch="batch_0")
```

When the model has only one batch, omit `restrict_to_batch`.

## SOLO predictions look like logits

Current `SOLO.predict(soft=True)` returns probabilities by default and emits a warning describing the historical change. If values are not between 0 and 1, check whether `return_logits=True` was passed.

Fix:

```python
probs = solo.predict(soft=True, return_logits=False)
assert ((probs >= 0) & (probs <= 1)).all().all()
doublet_score = probs["doublet"]
```

## CellAssign marker rows do not match `adata.var_names`

Symptoms:

- `KeyError: Anndata and cell type markers do not contain the same genes.`
- Many marker genes are silently absent after subsetting.
- The marker matrix has duplicate row names.

Fix:

```python
assert adata.var_names.is_unique
assert marker_df.index.is_unique
shared = adata.var_names.intersection(marker_df.index)
if len(shared) == 0:
    raise ValueError("no overlap between adata.var_names and marker_df.index")
bdata = adata[:, shared].copy()
marker_df = marker_df.loc[bdata.var_names]
missing_after_subset = bdata.var_names.difference(marker_df.index)
assert len(missing_after_subset) == 0
```

If marker identifiers use gene symbols but `adata.var_names` uses Ensembl IDs, map identifiers before constructing `bdata`; do not rely on CellAssign to reconcile them.

## CellAssign has empty or uninformative marker columns

Symptoms:

- A cell type is never predicted.
- Assignment probabilities are diffuse across all classes.
- One cell type dominates despite weak biological support.

Fix:

```python
empty_types = marker_df.columns[marker_df.sum(axis=0) == 0]
if len(empty_types):
    raise ValueError(f"cell types with no marker genes: {list(empty_types)}")
rare_markers = marker_df.sum(axis=0).sort_values()
print(rare_markers)
```

Review marker specificity, remove broad housekeeping markers, and add discriminative markers for sibling lineages.

## CellAssign size factors are missing or invalid

Symptoms:

- Setup fails because `size_factor_key` is absent.
- Training is unstable or assignments track library size.

Fix:

```python
library_size = np.asarray(adata.X.sum(axis=1)).ravel()
if (library_size <= 0).any():
    raise ValueError("cells with zero library size cannot use this size factor")
adata.obs["size_factor"] = library_size / library_size.mean()
scvi.external.CellAssign.setup_anndata(adata, size_factor_key="size_factor", batch_key="batch")
```

## Annotation confidence is too low

Do not solve low confidence by lowering thresholds only. Check:

- Whether training labels contain inconsistent naming or batch-specific label imbalance.
- Whether query data has the same genes and count representation as the reference.
- Whether predicted probabilities have low maximum values or small top-two margins.
- Whether SOLO doublet scores are high for ambiguous cells.
- Whether CellAssign marker assignments agree with SCANVI for broad lineages.

Recommended output columns:

```python
adata.obs["annotation_label"] = hard_labels
adata.obs["annotation_confidence"] = max_probability
adata.obs["annotation_margin"] = top_probability - second_probability
adata.obs["annotation_status"] = np.where(
    (adata.obs["annotation_confidence"] < 0.7) | (adata.obs["annotation_margin"] < 0.2),
    "review",
    "accepted",
)
```
