# Data Setup Troubleshooting

## Missing obs or layer key

Symptom: setup raises a key error for `batch_key`, `labels_key`, `size_factor_key`, covariate keys, or `layer`.

Fix:

```python
print(adata.obs.columns.tolist())
print(adata.layers.keys())
print(adata.obsm.keys())
assert "batch" in adata.obs
assert "counts" in adata.layers
```

Then either rename the data field or pass the correct setup argument. Do not pass legacy names such as `batch="batch"`; current setup methods use `batch_key="batch"`.

## Non-count data warning

Symptom: setup warns that `adata.X` or `adata.layers[...]` does not contain unnormalized count data.

Fix:

- Point `layer` to raw counts, not log-normalized or scaled values.
- Rebuild `adata.layers["counts"]` from raw integer input when available.
- Keep normalized matrices in separate layers such as `log1p` and never pass those layers to count-likelihood models.
- For `poisson_gene_selection`, non-negative integers are mandatory and invalid data raises `ValueError`.

## SCANVI unlabeled category mismatch

Symptom: `SCANVI.setup_anndata` fails or downstream labels look wrong.

Fix:

```python
labels = adata.obs["labels"].astype("category")
print(labels.cat.categories.tolist())
```

Pass `unlabeled_category` exactly as stored, for example `"Unknown"`, or add missing unlabeled entries before setup. Avoid mixing `None`, `nan`, and string labels.

## TOTALVI protein field missing

Symptom: `TOTALVI.setup_anndata` fails because `protein_expression_obsm_key` is absent or protein names are missing.

Fix:

```python
assert "protein_expression" in adata.obsm
assert adata.obsm["protein_expression"].shape[0] == adata.n_obs
adata.uns["protein_names"] = [f"protein_{i}" for i in range(adata.obsm["protein_expression"].shape[1])]
scvi.model.TOTALVI.setup_anndata(
    adata,
    protein_expression_obsm_key="protein_expression",
    protein_names_uns_key="protein_names",
    batch_key="batch",
)
```

If proteins are in a separate AnnData object, build a `MuData` object and use `TOTALVI.setup_mudata` instead of forcing arrays into `obsm`.

## Missing protein modality in MuData

Symptom: `TOTALVI.setup_mudata` or `MULTIVI.setup_mudata` fails with missing modality or mapped role errors.

Fix:

```python
print(mdata.mod.keys())
scvi.model.TOTALVI.setup_mudata(
    mdata,
    modalities={"rna_layer": "rna", "protein_layer": "protein_expression", "batch_key": "rna"},
)
```

The values in `modalities` must be existing `mdata.mod` keys. For `MULTIVI`, map `"atac_layer"` to the accessibility modality and omit `"protein_layer"` only if the intended model run truly has no proteins.

## MuData not fully paired

Symptom: `AnnDataManager` validation fails for MuData pairing.

Fix:

- Check that modalities share the same observation names in the same order: `mdata.mod["rna"].obs_names.equals(mdata.mod["accessibility"].obs_names)`.
- Subset and reorder modalities to common cells before constructing `MuData`.
- Call `mdata.update()` after modifying modalities.

## Registry changed after another setup call

Symptom: a data object was set up for one model, then another setup call overwrote manager UUIDs and the first model behaves unexpectedly.

Fix:

- Prefer separate `adata.copy()` objects when comparing model families.
- Re-run the desired model's setup method immediately before constructing that model.
- Inspect `model.adata_manager.validate()` and `model.adata_manager.registry` if reusing objects across workflows.

## Transfer or query data has different variables

Symptom: transfer/setup for target data fails with a variable count mismatch.

Fix:

```python
adata_target = adata_target[:, adata_source.var_names].copy()
```

The registered `LayerField` records source variable names and count; target data must match for registry transfer and many reference workflows.

## Difficult Recovery Cases

- Broken obs key/layer recovery: a dataset has raw counts in `adata.layers["raw_counts"]`, normalized values in `adata.X`, and a batch column named `sample`; recover with `layer="raw_counts"` and `batch_key="sample"`, then confirm the registry points to `layers/raw_counts`.
- Multimodal fixture with missing protein obsm: an AnnData CITE-seq example lacks `adata.obsm["protein_expression"]`; detect the missing field, add a correctly shaped protein matrix plus `adata.uns["protein_names"]`, or switch to `MuData` and call `setup_mudata`.
