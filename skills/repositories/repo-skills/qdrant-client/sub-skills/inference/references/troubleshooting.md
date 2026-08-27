# Inference Troubleshooting

Use this guide for qdrant-client inference failures involving FastEmbed, Cloud inference, `models.Document`, `models.Image`, `models.InferenceObject`, vector helper schemas, model catalogs, and model downloads.

## `ImportError: fastembed is not installed`

Cause:

- A local inference path saw `models.Document`, `models.Image`, or `models.InferenceObject` while `cloud_inference=False`, but the optional FastEmbed package was not installed.
- Deprecated helpers such as `add()`, `query()`, `query_batch()`, `set_model()`, `set_sparse_model()`, or `get_embedding_size()` tried to access FastEmbed catalogs/models.

Fix:

```bash
pip install "qdrant-client[fastembed]"
```

For GPU FastEmbed, use a clean environment and install:

```bash
pip install "qdrant-client[fastembed-gpu]"
```

Do not install both extras together. If the user only wants to construct Cloud inference requests, avoid calling local helper methods that require FastEmbed.

## `cloud_inference=True` with Local Mode

Cause:

- `QdrantClient(":memory:", cloud_inference=True)` or `QdrantClient(path=..., cloud_inference=True)` was requested.

Fix:

- Use local FastEmbed by leaving `cloud_inference=False`, or connect to a remote Qdrant Cloud cluster that supports inference.
- Route URL, API key, TLS, headers, and transport setup to `connection-and-transport`.

## Sparse Model Passed to `get_embedding_size()`

Symptom:

- `ValueError` meaning sparse embeddings do not return fixed embedding size and distance type.

Cause:

- Sparse models such as `Qdrant/bm25` produce sparse vectors, not fixed dense vectors.

Fix:

- Use `sparse_vectors_config={"name": models.SparseVectorParams(...)}` for sparse vectors.
- Use `get_fastembed_sparse_vector_params()` only after `set_sparse_model(...)` when following the helper workflow.
- Use `get_embedding_size()` only for dense text, dense image, late-interaction text, or late-interaction multimodal models that have fixed dimensions in the local FastEmbed catalog.

## Unsupported Model Name

Symptoms:

- `ValueError: Unsupported embedding model: ...`
- `ValueError: ... is not found among supported models. Check if cloud_inference is set to True or fastembed is installed (for local inference)?`
- `ValueError: ... is not among supported models`

Causes:

- The model name is misspelled or belongs to a provider/catalog unavailable in the current mode.
- Local FastEmbed is not installed, so local catalog methods are empty.
- A Cloud-only model was used with local FastEmbed helpers.
- A local FastEmbed model was used with Cloud inference but the Cloud plan/provider does not expose that model.

Fix:

- For local inference, run `scripts/check_inference_optional_deps.py` and inspect `QdrantClient.list_text_models()`, `list_image_models()`, `list_sparse_models()`, and late-interaction catalogs.
- For Cloud inference, check Cloud model availability for the target cluster and plan.
- Keep local and Cloud model dimensions/catalogs separate when creating collections.

## GPU Extra or CUDA Problems

Symptoms:

- Import errors from ONNX Runtime or FastEmbed.
- Provider initialization failures.
- CUDA unavailable or device selection failures.

Causes:

- `fastembed` and `fastembed-gpu` were installed together or swapped in the same environment.
- `models.Document(..., options={"cuda": True})` was used without the GPU extra and compatible runtime.
- `cuda`, `device_ids`, and `providers` were combined in a way unsupported by FastEmbed/ONNX Runtime.

Fix:

- Use one clean environment with either `qdrant-client[fastembed]` or `qdrant-client[fastembed-gpu]`.
- Use `options={"cuda": True}` only when the GPU extra and CUDA runtime are ready.
- Do not mix `providers` with `cuda`/`device_ids` unless the selected FastEmbed model and ONNX Runtime provider configuration explicitly supports it.
- For CPU fallback, remove GPU options and use the CPU extra.

## Model Download or Cache Failures

Symptoms:

- First embedding call fails with network, permission, cache, or local-files-only errors.
- Catalog listing works, but `upsert`, `query_points`, `add`, or `set_model` fails when the model is initialized.

Causes:

- The model weights are not cached and the environment cannot reach the model source.
- The cache directory is not writable.
- `local_files_only` or equivalent options require a model already present in the cache.

Fix:

- Ask the user before triggering downloads.
- Pass a writable `cache_dir` through `models.Document(..., options={"cache_dir": "..."})`, `models.Image(..., options={"cache_dir": "..."})`, `set_model(cache_dir=...)`, or `set_sparse_model(cache_dir=...)`.
- For offline runs, pre-populate the FastEmbed cache and pass `options={"local_files_only": True}` only when the model is already cached.
- Use the no-download dependency check script before any embedding smoke test.

## Remote Image Inference Fails

Symptoms:

- Cloud inference rejects `models.Image` input.
- Request works locally but fails remotely.

Causes:

- Cloud inference requires image input as a URL or base64-encoded string.
- A local filesystem path or unsupported object type was sent to Cloud inference.
- The image URL is inaccessible to the Cloud inference service.

Fix:

```python
from qdrant_client.embed.utils import read_base64
from qdrant_client import models

image = models.Image(
    image=read_base64("image.png"),
    model="Qdrant/clip-ViT-B-32-vision",
)
```

Alternatively, host the image at an HTTPS URL accessible from Qdrant Cloud. Do not send private local paths to Cloud inference.

## Collection Vector Mismatch

Symptoms:

- Dimension mismatch on upsert or query.
- Query returns errors about vector name or missing sparse vector field.
- Deprecated `add()` asserts incompatible vector params.

Causes:

- The collection was created with a different model dimension than the `Document` or `Image` model now used.
- A named vector query omitted the `using` field.
- Helper-generated field names changed after `set_model()` or `set_sparse_model()` changed models.
- IDF sparse models were used without `models.Modifier.IDF`.

Fix:

- Recreate or migrate the collection with vector params matching the chosen model dimensions.
- Use stable explicit vector names such as `dense`, `sparse`, and `image` for production schemas.
- Pass `using="dense"` or `using="sparse"` in named-vector queries and prefetches.
- Use `models.SparseVectorParams(modifier=models.Modifier.IDF)` for known IDF sparse models such as `Qdrant/bm25`.

## Deprecated Helper Confusion

Symptoms:

- Warnings from `add`, `query`, or `query_batch`.
- Return objects have `document`, `metadata`, `embedding`, `sparse_embedding`, and `score` instead of standard `ScoredPoint` fields.
- A collection is created with unexpected vector names like `fast-all-minilm-l6-v2`.

Cause:

- The deprecated helper API was used instead of regular Qdrant methods.

Fix:

- Replace `add()` with `upsert()` or `upload_collection()` using `models.Document`/`models.Image` vectors.
- Replace `query()` with `query_points(query=models.Document(...))`.
- Replace `query_batch()` with `query_batch_points()` and `models.QueryRequest` objects.
- If keeping helpers for legacy code, keep `set_model()`, `set_sparse_model()`, helper-generated vector params, and helper field names consistent.

## `InferenceObject` Cannot Resolve

Symptoms:

- `ValueError` that a model does not support `InferenceObject` interface.
- `ValueError` that a model is not among supported models.

Causes:

- The generic `InferenceObject` was used for a model family that requires `Document` or `Image` explicitly.
- A late-interaction multimodal model does not support the generic object interface in local inference.
- The model is unavailable in local FastEmbed catalogs.

Fix:

- Prefer `models.Document` for text and sparse text models.
- Prefer `models.Image` for image models.
- Use `InferenceObject` only when a provider-specific interface is expected and supported by the selected inference mode.

## Async Inference Surprises

Symptoms:

- Inference examples are copied to async code but methods are not awaited.
- Client resources remain open.

Fix:

- Use the same `Document`, `Image`, helper, and Cloud inference concepts, but route lifecycle and awaited method details to `async-client`.
- Close async clients with `await client.close()`.

## Safe Diagnostic Order

1. Run `python sub-skills/inference/scripts/check_inference_optional_deps.py` to confirm qdrant-client and FastEmbed visibility without downloads.
2. Decide local FastEmbed versus Cloud inference.
3. Verify the model appears in the correct local or Cloud catalog.
4. Confirm collection vector names, dimensions, and sparse modifiers.
5. Only after user approval, run a small embedding smoke test that may initialize/download the selected model.
