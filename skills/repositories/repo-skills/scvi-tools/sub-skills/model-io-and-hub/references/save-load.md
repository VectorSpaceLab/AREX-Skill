# Save, Load, Inspect, and Minify Models

## Local save contract

All standard scvi-tools models inherit the same persistence shape from `BaseModelClass`:

```python
model.save(
    dir_path,
    prefix=None,
    overwrite=False,
    save_anndata=False,
    save_kwargs=None,
    legacy_mudata_format=False,
    **anndata_write_kwargs,
)
```

Key behavior:

- `dir_path` is a directory, not a single `.pt` filename. The core weight/registry file is `model.pt` or `{prefix}model.pt`.
- `overwrite=False` protects existing directories; pass `overwrite=True` only when replacement is intended.
- `save_anndata=True` writes `adata.h5ad` for `AnnData` or `mdata.h5mu` for `MuData` next to `model.pt`.
- Optimizer state and trainer history are not saved. Plan to continue with model weights, registry, and user attributes only.
- For MuData models, keep the default `legacy_mudata_format=False` unless an older consumer requires flat concatenated variable names.

Minimal pattern:

```python
model.train(max_epochs=20)
model.save("trained_scvi", overwrite=True, save_anndata=False)
loaded = scvi.model.SCVI.load("trained_scvi", adata=adata, accelerator="auto", device="auto")
```

## Local load contract

Use the same model class unless intentionally using a supported class conversion API:

```python
loaded = scvi.model.SCVI.load(
    dir_path,
    adata=None,
    accelerator="auto",
    device="auto",
    prefix=None,
    backup_url=None,
    allowed_classes_names_list=None,
)
```

Important checks:

- If `adata` is provided, it must be organized the same way as training data. Do not rerun `setup_anndata()` first; `load()` transfers the saved setup registry to the new object.
- The saved registry `model_name` must match the class being loaded unless `allowed_classes_names_list` is deliberately used by an advanced compatibility workflow.
- Saved `var_names` are compared with the provided data. A mismatch emits a warning; treat it as invalid for biological interpretation unless the task is explicitly repairing feature order.
- `prefix` must match the prefix used at save time, otherwise `model.pt` cannot be found.
- `backup_url` can retrieve `model.pt` when it is missing locally, but local `adata.h5ad`/`mdata.h5mu` handling still follows the saved-data rules.

## Inspect before loading

Use these before attaching a new dataset or diagnosing a downloaded artifact:

```python
scvi.model.SCVI.view_setup_args("trained_scvi")
registry = scvi.model.SCVI.load_registry("trained_scvi")
```

Useful registry fields include:

- `registry["model_name"]`: expected class name such as `SCVI`, `SCANVI`, `TOTALVI`, or `MULTIVI`.
- `registry["scvi_version"]`: scvi-tools version used to save the model.
- `registry["setup_method_name"]`: usually `setup_anndata`, `setup_mudata`, or experimental `setup_datamodule`.
- `registry["setup_args"]`: original setup keyword arguments, such as `layer`, `batch_key`, labels, covariates, protein keys, or modality mappings.
- `registry["field_registries"]`: concrete AnnData/MuData locations used by the model.

The bundled `scripts/check_saved_model.py` summarizes these fields without loading model weights into a model instance.

## Loading without saved AnnData

If `save_anndata=False`, load with a compatible object when you need model methods that validate data:

```python
adata = anndata.read_h5ad("query_or_training_like_data.h5ad")
loaded = scvi.model.SCVI.load("trained_scvi", adata=adata)
```

If the saved directory has no data and `adata` is omitted, scvi-tools warns or returns a model without attached data depending on the path. Data-bound methods such as normalized expression, latent representation, query transfer, or registry validation generally require a compatible `adata`/`mdata`.

## Minified data

Minification reduces saved data size for supported models by replacing count matrices with latent posterior summaries:

```python
qzm, qzv = model.get_latent_representation(return_dist=True, give_mean=False)
model.adata.obsm["X_latent_qzm"] = qzm
model.adata.obsm["X_latent_qzv"] = qzv
model.minify_adata(
    minified_data_type="latent_posterior_parameters",
    use_latent_qzm_key="X_latent_qzm",
    use_latent_qzv_key="X_latent_qzv",
)
model.save("minified_scvi", overwrite=True, save_anndata=True)
```

Rules and caveats:

- `BaseMinifiedModeModelClass.minify_adata()` applies to AnnData-backed models that support minified mode, such as SCVI/SCANVI-style RNA models.
- `BaseMudataMinifiedModeModelClass.minify_mudata()` applies to supported MuData-backed models registered with `setup_mudata`.
- Supported `minified_data_type` values are `"latent_posterior_parameters"` and `"latent_posterior_parameters_with_counts"`.
- Default minification stores latent posterior mean/variance and observed library size, removes raw count data, and sets the minify type in `.uns`.
- Use `"latent_posterior_parameters_with_counts"` when later workflows need count-dependent operations or `SCANVI.from_scvi_model()`.
- A non-minified saved model cannot be loaded with an actually minified sparse-zero `adata` unless the object carries latent parameters under `_scvi_latent_qzm` and `_scvi_latent_qzv` and is then properly minified after load.

## Reference mapping note

For scArches-style query mapping, use model-family APIs that wrap the same saved registry:

```python
scvi.model.SCVI.prepare_query_anndata(adata, reference_model="trained_scvi")
query_model = scvi.model.SCVI.load_query_data(adata, reference_model="trained_scvi")
```

Use `inplace_subset_query_vars=True` only when mutating query features to match reference feature order is acceptable.

## Legacy saves

For models saved before the modern single-`model.pt` format, convert first:

```python
scvi.model.SCVI.convert_legacy_save("old_save", "converted_save", overwrite=True)
```

`view_setup_args()` and `load_registry()` do not support pre-v0.15 setup dictionaries until conversion succeeds.
