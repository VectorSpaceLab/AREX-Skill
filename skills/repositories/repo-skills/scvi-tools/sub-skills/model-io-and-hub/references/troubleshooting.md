# Troubleshooting Model IO and Hub Artifacts

## `Failed to load model file ... model.pt`

Likely causes:

- `dir_path` points to a file instead of the save directory.
- The model was saved with a `prefix`, but `load(..., prefix=...)` did not use the same prefix.
- The artifact uses the legacy pre-v0.15 format.

Fixes:

1. Confirm the directory contains `model.pt` or `{prefix}model.pt`.
2. Run `scripts/check_saved_model.py --model-dir <dir> --prefix <prefix>`.
3. For old files, run `ModelClass.convert_legacy_save(old_dir, converted_dir, overwrite=True)` and load the converted directory.

## Saved model has no matching AnnData

Symptoms include warnings about no saved AnnData, Hub `Could not find any dataset to load the model with`, or failures when calling data-bound methods.

Fixes:

- Load with a compatible object: `ModelClass.load(path, adata=adata)` or `hub_model.load_model(adata=adata)`.
- Do not rerun setup on that object manually; `load()` transfers the saved registry.
- Check `ModelClass.view_setup_args(path)` and ensure required `layer`, `batch_key`, label, protein, covariate, and modality keys exist.
- If the original data cannot be shared, provide a minified artifact or documented `training_data_url` rather than publishing weights alone.

## `var_names` mismatch warning

scvi-tools warns when saved feature names differ from the provided data.

Fixes:

- Reorder or subset query data to the saved reference feature order before load.
- For query mapping, prefer `prepare_query_anndata()` or `prepare_query_mudata()` when available for that model family.
- Do not ignore the warning for expression, latent, or differential analysis; feature mismatch invalidates results.

## Loading model from a different class

`ModelClass.load()` checks the saved registry model name.

Fixes:

- Use the class recorded in `load_registry(path)["model_name"]`.
- Use dedicated conversion constructors such as `SCANVI.from_scvi_model()` where documented.
- Reserve `allowed_classes_names_list` for deliberate compatibility work where the target class can safely consume the saved registry and state dict.

## Minified-data errors

Common failures:

- `The <model> model currently does not support minified data.`
- `Minification is not supported for models that do not use observed library size.`
- `It appears you are trying to load a non-minified model with minified adata`.
- Count-dependent methods such as ELBO, reconstruction error, marginal likelihood, training loss, or some transfer constructors fail after count-free minification.

Fixes:

- Confirm the model inherits minified-mode support before calling `minify_adata()` or `minify_mudata()`.
- Store latent posterior arrays before minifying and pass the matching keys: `use_latent_qzm_key` and `use_latent_qzv_key`.
- Use `minified_data_type="latent_posterior_parameters_with_counts"` when downstream operations need counts.
- If loading a non-minified saved model with a sparse-zero object that has latent params, load first and then call `minify_adata(use_latent_qzm_key="_scvi_latent_qzm", use_latent_qzv_key="_scvi_latent_qzv")`.
- Save minified models with `save_anndata=True` when the minified data is intended to travel with the weights.

## Hub import or optional dependency failure

`import scvi.hub` requires optional `huggingface_hub`; S3 helpers require `boto3`; DVC-backed large training-data fallback requires DVC support.

Fixes:

- Install the relevant optional packages in the runtime environment before using Hub/S3 workflows.
- Keep local save/load workflows independent from Hub if optional extras are unavailable.
- Avoid importing `scvi.hub` in simple local inspection scripts unless Hub metadata is explicitly requested.

## Hub upload fails without credentials or network

Publishing requires network access and a Hugging Face token with write permission.

Fixes:

- Use `hub_model.save(overwrite=True)` to validate local metadata/card generation offline.
- Authenticate with `HF_TOKEN`, `huggingface-cli login`, or `repo_token=...` only in secure environments.
- Use `repo_create=True` only when the token can create the target repo.
- Use `push_anndata=False` when data cannot be shared, and include a valid `training_data_url` or user instructions for providing compatible data.

## Hub package says `No metadata found` or `No model card found`

`HubModel(local_dir)` needs `_scvi_required_metadata.json` and `README.md` in the local directory.

Fixes:

```python
metadata = HubMetadata.from_dir(local_dir, anndata_version=anndata.__version__)
card = HubModelCardHelper.from_dir(local_dir, license_info="cc-by-4.0", anndata_version=anndata.__version__)
hub_model = HubModel(local_dir, metadata=metadata, model_card=card)
hub_model.save(overwrite=True)
```

Then retry `HubModel(local_dir)`.

## Version compatibility concerns

Saved registries record `scvi_version` and Hub metadata records both scvi-tools and AnnData versions.

Checks:

- Compare `scvi.__version__` to the saved registry before blaming data shape issues.
- Prefer loading and immediately re-saving with the current scvi-tools version only after a successful smoke test.
- For legacy artifacts, convert with the class-specific `convert_legacy_save()` rather than editing saved files manually.
