---
name: inference
description: "Use qdrant-client inference with FastEmbed local embeddings or
  Qdrant Cloud remote inference for Document, Image, dense, sparse, and hybrid
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Inference

Use this sub-skill when a task involves qdrant-client inference inputs or model helpers: `models.Document`, `models.Image`, `models.InferenceObject`, local FastEmbed inference, Qdrant Cloud remote inference, dense/sparse/hybrid setup, `get_embedding_size`, vector parameter helpers, supported-model catalogs, schema inspection, or diagnosing optional inference dependencies.

## Start Here

- Read `references/inference-workflows.md` for local FastEmbed and remote Cloud inference recipes, `Document`/`Image` examples, dense/sparse/hybrid collection setup, and deprecated `add`, `query`, and `query_batch` notes.
- Read `references/model-and-schema-reference.md` for `list_*_models`, `get_embedding_size`, `get_fastembed_vector_params`, `get_fastembed_sparse_vector_params`, `get_vector_field_name`, `get_sparse_vector_field_name`, and inference schema parser behavior.
- Read `references/troubleshooting.md` when FastEmbed is missing, a sparse model has no fixed dense size, a model is unsupported, GPU extras conflict, CUDA/providers options conflict, remote images fail, or model downloads/cache access fail.
- Run `scripts/check_inference_optional_deps.py` to report whether `fastembed` is importable and to list supported model catalogs when listing is available without downloading model weights.

## Boundaries

- Use this sub-skill for inference-specific setup, model input objects, embedding helper methods, local-vs-remote inference behavior, and optional dependency diagnosis.
- Use `../client-operations/SKILL.md` for core `create_collection`, `upsert`, `upload_collection`, `query_points`, `query_batch_points`, filters, payloads, and result handling after the inference input objects are chosen.
- Use `../connection-and-transport/SKILL.md` for Qdrant Cloud `url`, `api_key`, TLS, REST/gRPC transport, headers, timeouts, and authentication. This sub-skill only covers `cloud_inference=True` semantics.
- Use `../async-client/SKILL.md` for `AsyncQdrantClient` parity and awaitable methods; the same inference input objects and helper concepts apply there.
- Use `../models-and-conversions/SKILL.md` for general generated model basics, REST/gRPC conversion, and low-level schema typing not specific to inference.
- Use `../migration-and-upload/SKILL.md` for bulk ingestion tuning once vectors or inference objects are ready for upload.

## Safe Defaults

- Prefer regular methods with inference objects, such as `upsert`, `upload_collection`, `query_points`, and `query_batch_points`; treat `add`, `query`, and `query_batch` as deprecated compatibility helpers.
- For local inference, install exactly one FastEmbed extra: `qdrant-client[fastembed]` for CPU or `qdrant-client[fastembed-gpu]` for GPU.
- Do not trigger model downloads unless the user explicitly asks to run local inference; catalog listing and code construction can be done without embedding data.
- For no-credential examples, use `QdrantClient(":memory:")` and make clear that embedding calls require FastEmbed and may download model weights.
- For Cloud inference, set `cloud_inference=True` on a remote Qdrant Cloud client; local `:memory:` mode cannot use Cloud inference.
- For image inputs sent to Cloud inference, pass image URLs or base64 strings, not local filesystem paths.

## Minimal Patterns

Local dense text inference with regular methods:

```python
from qdrant_client import QdrantClient, models

client = QdrantClient(":memory:")
model_name = "sentence-transformers/all-MiniLM-L6-v2"
client.create_collection(
    "docs",
    vectors_config=models.VectorParams(
        size=client.get_embedding_size(model_name),
        distance=models.Distance.COSINE,
    ),
)
client.upsert(
    "docs",
    points=[
        models.PointStruct(
            id=1,
            vector=models.Document(text="Qdrant supports local inference", model=model_name),
            payload={"source": "note"},
        )
    ],
)
hits = client.query_points(
    "docs",
    query=models.Document(text="local embedding search", model=model_name),
    limit=1,
).points
```

Remote Cloud inference uses the same `models.Document` and `models.Image` inputs after the client is constructed with `cloud_inference=True`.

## Acceptance Checks

- Inference examples identify whether they require local FastEmbed, remote Qdrant Cloud, credentials, or model downloads.
- Collection vector configs match the selected model dimensions and vector names, or explicitly use `get_fastembed_vector_params()` and `get_fastembed_sparse_vector_params()`.
- Sparse-only models are never passed to `get_embedding_size()` as if they had fixed dense vector dimensions.
- Deprecated helper usage is labeled as legacy and paired with the regular-method replacement.
- Troubleshooting distinguishes missing optional extras from unsupported model names and remote Cloud-inference configuration errors.
