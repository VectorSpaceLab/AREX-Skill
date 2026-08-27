---
name: model-io-and-hub
description: "Save, load, inspect, minify, and share scvi-tools model artifacts
  locally or through Hugging Face Hub metadata."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# model-io-and-hub

Use this sub-skill when the task is about scvi-tools model persistence: `model.save()`, `ModelClass.load()`, saved registry inspection, matching an `AnnData`/`MuData` to a saved model, minified data artifacts, `scvi.hub.HubModel`, Hub metadata/model cards, or version compatibility checks.

Do not use this sub-skill for choosing model classes, training schedules, callbacks, GPU strategy, inference outputs, or general installation. Route those to the root skill, data setup, core model, multimodal/spatial, and training/inference sub-skills as appropriate.

## Fast Path

1. Save trained models to a directory with `model.save(dir_path, overwrite=False, save_anndata=False, prefix=None)`; use `save_anndata=True` only when the training data is small and shareable.
2. Load with the exact model class, for example `scvi.model.SCVI.load(dir_path, adata=adata, accelerator="auto", device="auto", prefix=None)`.
3. If `adata` is omitted, scvi-tools tries to load `adata.h5ad` or `mdata.h5mu` saved next to `model.pt`; if none exists, the model loads without data only when the workflow does not immediately need data-bound methods.
4. Inspect saved setup before loading new data with `ModelClass.view_setup_args(dir_path)`, `ModelClass.load_registry(dir_path)`, and `scripts/check_saved_model.py`.
5. For Hub workflows, create local `HubMetadata` and `HubModelCardHelper` first, instantiate `HubModel(local_dir, metadata=..., model_card=...)`, call `hub_model.save(overwrite=True)`, and only then push when credentials/network are available.

## Internal References

- Read [save/load](references/save-load.md) for signatures, saved files, registry compatibility, minified data, and legacy conversion.
- Read [hub](references/hub.md) for `HubMetadata`, `HubModelCardHelper`, `HubModel`, Hugging Face/S3 flows, and credential caveats.
- Read [troubleshooting](references/troubleshooting.md) for missing AnnData, mismatched genes, minified-data failures, missing extras, and Hub upload/download errors.
- Run `scripts/check_saved_model.py --help` to inspect a saved local model directory without importing private repository paths.
