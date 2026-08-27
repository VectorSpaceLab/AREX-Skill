# Inference API and preprocessing reference

This reference covers the direct inference-orchestrator HTTP API, Marqo core inference client wrappers, request schemas, preprocessing rules, and pipeline dispatch.

## Verified route surface

| Route | Method | Service | Request/response notes |
| --- | --- | --- | --- |
| `/` | `GET` | inference orchestrator | Basic service message and version. |
| `/healthz` | `GET` | inference orchestrator | Liveness response: `{"status": "ok"}`. It does not prove a model is loaded. |
| `/vectorise` | `POST` | inference orchestrator | Requires `Content-Type: application/msgpack`; returns MessagePack with numpy-compatible arrays. |
| `/models` | `GET` | inference orchestrator | Query `detailed=true|false`; returns loaded in-memory model cache entries. |
| `/models` | `DELETE` | inference orchestrator | Query `model_name=<full-cache-key>`; ejects a cached model entry. |

Model-management routes are covered in `model-services.md`.

## Direct `/vectorise` contract

The direct route expects a MessagePack-encoded `InferenceRequest` and responds with a MessagePack-encoded `InferenceResult`.

Important details:

- `Content-Type` must be exactly `application/msgpack`; otherwise the route returns 415.
- `Accept: application/msgpack` keeps error responses in the same media type.
- The direct inference service accepts text and image preprocessing configs. Marqo core client models also define audio/video preprocessing configs, but those are broader than the direct inference-orchestrator request discriminator.
- Direct callers should include `embeddingModelConfig.modelProperties`; otherwise model loading has no family/type information.

### Request schema

| Field | Type | Notes |
| --- | --- | --- |
| `modality` | `language` or `image` | Must match `preprocessingConfig.modality`. |
| `contents` | non-empty list of strings | Text strings, image URLs, image local paths visible to the service, or base64 image data URLs depending on modality. |
| `embeddingModelConfig` | object | See table below. |
| `preprocessingConfig` | text or image config | Discriminated by `modality`. |
| `useInferenceCache` | bool, default `false` | Uses cache only if service was configured with a positive cache size and skip rules do not apply. |
| `returnIndividualError` | bool, default `true` | If true, per-content media/preprocessing failures can be returned alongside successes. |

`embeddingModelConfig`:

| Field | Notes |
| --- | --- |
| `modelName` | Public or custom model name. Direct `/vectorise` still needs `modelProperties`. |
| `modelProperties` | Full registry/custom model properties, including `type` and `dimensions`. |
| `normalizeEmbeddings` | Defaults to true; controls vector normalization in random, HF, and OpenCLIP encoders. |

Marqo core inference request objects add two fields that are not part of the direct orchestrator schema:

- `device`, mainly for debugging and cache-bypass behavior.
- `modelAuth`, a higher-level auth object for private S3/HF model sources. Exactly one of the supported auth methods should be supplied when auth is required.

### Text preprocessing config

| Field | Notes |
| --- | --- |
| `modality` | Must be `language`. |
| `shouldChunk` | If true, `chunkConfig` is required. If false, `chunkConfig` must be absent. |
| `textPrefix` | Optional prefix applied after splitting and before model preprocessing. |
| `chunkConfig.splitMethod` | One of `character`, `word`, `sentence`, `passage`. |
| `chunkConfig.splitLength` | Must be greater than zero. |
| `chunkConfig.splitOverlap` | Must be non-negative and less than `splitLength`. |

### Image preprocessing config

| Field | Notes |
| --- | --- |
| `modality` | Must be `image`. |
| `shouldChunk` | If true, `patchMethod` is required. If false, `patchMethod` must be absent. |
| `downloadTimeoutMs` | Default 3000 ms. |
| `downloadThreadCount` | Optional per-request download worker count. |
| `downloadHeader` | Optional HTTP headers for protected image URLs. |
| `patchMethod` | One of `simple`, `frcnn`, `dino-v1`, `dino-v2`, `marqo-yolo`; only valid when chunking is enabled. |

## Response schema

`InferenceResult.result` is aligned with the input `contents` order. Each entry is either:

- an `InferenceErrorModel` with `statusCode`, `errorCode`, and `errorMessage`; or
- a list of `(chunk_key, embedding)` tuples.

For unchunked text and most no-download random checks, each successful content has one tuple. Chunked text produces multiple tuples per original content. Embeddings are numpy arrays over MessagePack; after generic unpacking they may appear as array-like values.

## Safe no-download `/vectorise` payload

Use this shape to verify request formatting without model downloads or Triton traffic. The example body must still be MessagePack encoded before POSTing.

```python
payload = {
    "modality": "language",
    "contents": ["hello world"],
    "embeddingModelConfig": {
        "modelName": "random/small",
        "modelProperties": {
            "name": "random/small",
            "dimensions": 32,
            "tokens": 128,
            "type": "random",
            "notes": ""
        },
        "normalizeEmbeddings": True,
    },
    "preprocessingConfig": {
        "modality": "language",
        "shouldChunk": False,
    },
    "useInferenceCache": False,
    "returnIndividualError": True,
}
# body = msgpack.packb(payload, use_bin_type=True)
```

Expected unpacked result shape:

```json
{
  "result": [
    [["hello world", "<embedding array with 32 floats>"]]
  ]
}
```

## Pipeline dispatch

The inference service loads a model from `embeddingModelConfig.modelProperties.type` and dispatches as follows:

| `type` | Pipeline | Behavior |
| --- | --- | --- |
| `random` | `RandomModelInferencePipeline` | Text goes through split/prefix preprocessing; image contents pass through as strings; embeddings are deterministic and batch size is capped at 128. |
| `hf` | `HuggingFaceModelInferencePipeline` | Text is split/prefixed, tokenized, encoded through a Triton text encoder, pooled with mean or CLS pooling, and optionally normalized. |
| `open_clip` | `OpenCLIPModelInferencePipeline` | Text is split/prefixed; images are downloaded/preprocessed; text and image batches use the family-specific Triton encoder max batch sizes. |

Unsupported `type` values raise an invalid-model-properties error during loading. Unsupported modality for a model family is an internal inference error; do not route image requests to HF unless the higher-level caller intentionally treats URLs as text.

## Core client wrappers

| Client | Method | What it does | Failure behavior |
| --- | --- | --- | --- |
| `InferenceClient` | `vectorise(request)` | Packs the request by alias with MessagePack, POSTs to `/vectorise`, unpacks MessagePack response into `InferenceResult`. | HTTP errors and bad response MessagePack become `InferenceError`. |
| `ModelManagerClient` | `get_loaded_models(detailed=False)` | GET `/models?detailed=true|false` on the inference service. | 400 becomes `ModelError`; other HTTP errors propagate. |
| `ModelManagerClient` | `eject_model(model_name)` | DELETE `/models?model_name=<full-cache-key>` on the inference service. | 400 becomes `ModelError`; other HTTP errors propagate. |

## Inference cache behavior

Two cache locations exist depending on runtime mode:

- Marqo API mode can wrap the remote `InferenceClient` with an API-side cache.
- Inference-orchestrator mode can wrap the Triton-backed inference object with an orchestrator-side cache.

Shared cache rules:

- Cache size `0` disables the wrapper.
- Valid cache strategies are `LRU` and `LFU`.
- Cache is skipped when `useInferenceCache` is false, `device` is set, modality is not text/image, or chunking is enabled.
- Text is cached by original content string.
- Base64 image data URLs are cached by a `blake3:` hash key; image URLs are not cached.
- Per-content inference errors are not cached.
- Chunked results are not cached; if a multi-chunk result reaches a cache write path, it is treated as an unsupported cache case.
