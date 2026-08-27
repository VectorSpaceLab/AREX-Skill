# Hub and Local Model Metadata

scvi-tools provides `scvi.hub` helpers for packaging a saved local model with metadata and a model card, then optionally pushing or pulling from Hugging Face Hub or S3. Importing `scvi.hub` requires the optional `huggingface_hub` dependency.

## Local Hub package

Create the model artifact first:

```python
model.save("hub_ready_model", overwrite=True, save_anndata=True)
```

Build required metadata from the saved directory:

```python
import anndata
from scvi.hub import HubMetadata, HubModel, HubModelCardHelper

metadata = HubMetadata.from_dir(
    "hub_ready_model",
    anndata_version=anndata.__version__,
)
card = HubModelCardHelper.from_dir(
    "hub_ready_model",
    license_info="cc-by-4.0",
    anndata_version=anndata.__version__,
    data_modalities=["rna"],
    data_is_annotated=False,
    description="Short description of the model and training data.",
)
hub_model = HubModel("hub_ready_model", metadata=metadata, model_card=card)
hub_model.save(overwrite=True)
```

A complete local Hub package contains:

- `model.pt`: saved scvi-tools model weights and registry.
- `adata.h5ad` or `mdata.h5mu`: optional attached data.
- `_scvi_required_metadata.json`: required `HubMetadata` JSON.
- `README.md`: Hugging Face model card generated or supplied through `HubModelCardHelper`/`ModelCard`.

## Metadata fields

`HubMetadata` requires:

- `scvi_version`: version used to train/save the model.
- `anndata_version`: AnnData version used with the artifact.
- `model_cls_name`: class name such as `SCVI` or `TOTALVI`.
- `training_data_url`: optional data URL when data is too large to upload; cellxgene URLs must be public portal sessions, not self-hosted sessions.
- `model_parent_module`: defaults to `scvi.model`; set it for custom model classes.

`HubMetadata.from_dir(local_dir, anndata_version=...)` reads `model.pt` and fills `scvi_version` plus `model_cls_name` from the saved registry.

## Model card fields

`HubModelCardHelper.from_dir()` extracts model init params, setup args, summary stats, data registry, and minified-data status when a local `adata.h5ad` is present. Supply human fields explicitly:

```python
card = HubModelCardHelper.from_dir(
    local_dir,
    license_info="cc-by-4.0",
    anndata_version=anndata.__version__,
    data_modalities=["rna"],
    tissues=["blood"],
    data_is_annotated=True,
    data_is_minified=False,
    training_data_url=None,
    training_code_url="https://example.org/training-code",
    description="What the model was trained to represent.",
    references="Relevant publications or dataset references.",
)
```

The generated card tags include `library_name: scvi-tools`, `model_cls_name:<class>`, `scvi_version:<version>`, `anndata_version:<version>`, and optional modality/tissue/annotation tags.

## Loading Hub packages

For a local package:

```python
hub_model = HubModel("hub_ready_model")
model = hub_model.model
adata = hub_model.adata
```

If no local `adata.h5ad`/`mdata.h5mu` exists, load with a compatible object:

```python
hub_model = HubModel("hub_ready_model")
hub_model.load_model(adata=adata, accelerator="auto", device="auto")
```

If neither local data nor a valid `training_data_url` is available, `HubModel.load_model()` raises an error because it cannot attach data to the saved registry.

## Hugging Face push and pull

Push only when credentials and network access are available:

```python
hub_model.push_to_huggingface_hub(
    repo_name="org/model-name",
    repo_token=None,
    repo_create=False,
    repo_create_kwargs=None,
    collection_name=None,
    push_anndata=True,
)
```

Operational notes:

- `repo_token=None` uses the token known to `huggingface_hub`, such as `HF_TOKEN` or the local Hugging Face cache.
- If `repo_token` is a file path, scvi-tools reads the token from that file.
- Use `repo_create=True` only if the token has permission to create repositories.
- Set `push_anndata=False` to avoid uploading `*.h5ad` and `*.h5mu` files.
- Hugging Face uploads reject associated data files at or above the scvi-tools 5 GB threshold; use a `training_data_url` and leave large data external.

Pull with:

```python
hub_model = HubModel.pull_from_huggingface_hub(
    repo_name="org/model-name",
    cache_dir=None,
    revision="main",
    pull_anndata=True,
)
```

Always pass a pinned `revision` for reproducible downstream work. If `pull_anndata=False` or the remote repo lacks data, provide `adata` to `hub_model.load_model(adata=...)` before data-bound inference.

## S3 support

`HubModel.push_to_s3()` and `HubModel.pull_from_s3()` require optional `boto3`. Use `unsigned=True` for public unsigned reads where appropriate, and pass normal `boto3.client()` kwargs for credentials or endpoint configuration.
