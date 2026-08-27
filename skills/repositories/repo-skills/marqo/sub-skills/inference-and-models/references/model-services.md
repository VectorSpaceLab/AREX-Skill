# Model services and Triton lifecycle

This reference covers Marqo's inference-service model cache, model-management API, and Triton load/unload behavior.

## Service map

```text
Marqo API layer
  ├─ InferenceClient -> inference orchestrator /vectorise
  └─ ModelManagerClient -> inference orchestrator /models

Inference orchestrator
  ├─ TritonInference -> Triton gRPC encode calls
  └─ ModelManagementClient -> model-management /v1/models/load|unload

Model-management service
  ├─ TritonModelDownloader -> prepares ONNX model repository files
  └─ TritonClient -> Triton REST /v2/repository/models/{name}/load|unload
```

Startup, compose, and container orchestration commands belong to the local-development sub-skill; this reference only describes the runtime contracts.

## Inference orchestrator model cache

The inference orchestrator keeps loaded model objects in memory.

- Cache key format: `modelName||hhhh`, where `hhhh` is the first four hex characters of a BLAKE3 hash over sorted `modelProperties` JSON.
- Loading the same `modelName` and semantically identical `modelProperties` reuses the cached model.
- `GET /models?detailed=false` returns `{"models": [{"modelName": "...||hhhh"}]}`.
- `GET /models?detailed=true` adds `modelProperties`; this value is a serialized JSON string from the model-properties object.
- `DELETE /models?model_name=<full-cache-key>` unloads the cached model object and returns success. Use the full cache key from `/models`, not just the public registry name.
- A delete for an absent cache key is effectively idempotent at the inference-orchestrator cache layer.

## Model loading by family

| Family | Loader requirements | Load behavior | Unload behavior |
| --- | --- | --- | --- |
| `random` | `name`, `dimensions`, `type: random` | No model-management or Triton calls; builds a deterministic local model object. | No-op. |
| `hf` | HF properties plus `tritonTextEncoderProperties` | Loads tokenizer with Transformers, asks model-management to load one text encoder into Triton, chooses mean/CLS pooling. | Unloads the text encoder through model-management. |
| `open_clip` | OpenCLIP properties plus text and image encoder properties | Loads OpenCLIP tokenizer/image preprocessor, asks model-management to load both text and image encoders into Triton. | Unloads both encoders through model-management. |

OpenCLIP loaders use CPU for tokenizer/preprocessor setup; actual encoder inference is handled by Triton. HF loaders tokenize locally and send token tensors to the Triton text encoder.

## Model-management routes

| Route | Method | Body/query | Success response | Notes |
| --- | --- | --- | --- | --- |
| `/v1/healthz` | `GET` | none | `{"status": "ok"}` | Liveness only; it does not prove Triton is ready. |
| `/v1/models/load` | `POST` | JSON `{"tritonModelProperties": {...}}` | `{"message": "Model '<name>' loaded successfully."}` | Validates schema, prepares repository files, and calls Triton REST load. |
| `/v1/models/{model_name}/unload` | `POST` | query `remove-files=false|true` | `{"message": "Model '<name>' unloaded successfully."}` | Calls Triton REST unload; optionally removes cached model files. |

Model-management errors are returned as RFC 7807 Problem+JSON with fields such as `title`, `status`, `detail`, `code`, `instance`, and `request_id`.

## Triton model properties

General `TritonModelProperties` fields:

| Field | Validation |
| --- | --- |
| `name` | Model repository name. |
| `maxBatchSize` | Integer from 1 through 128; default 8. |
| `sources` | 1 to 5 URI/path strings; each basename must be `model.onnx` or start with `model.onnx.data`. |
| `input` | List of input tensor definitions: `name`, `dims`, `dataType`. |
| `output` | Exactly one output tensor definition for embedding models. |

Supported data types include `TYPE_FP64`, `TYPE_FP32`, `TYPE_FP16`, `TYPE_INT8`, `TYPE_INT16`, `TYPE_INT32`, `TYPE_INT64`, and `TYPE_BF16`.

Family-specific constraints:

- OpenCLIP encoder properties use exactly one input named `input` and exactly one output named `output`.
- HF encoder properties use exactly three inputs named `input_ids`, `attention_mask`, `token_type_ids`, and one output named `last_hidden_state`.

## Model-management load sequence

1. Validate `tritonModelProperties`.
2. Build a Triton model repository layout for the model and write a generated `config.pbtxt`.
3. Download or reuse each source file. Sources may be S3, HTTP(S), FTP, or local paths supported by the runtime filesystem layer.
4. Call Triton REST `POST /v2/repository/models/{model_name}/load`.
5. Return a success message or a Problem+JSON error.

The generated Triton config uses the ONNX Runtime backend, dynamic batching, and the input/output tensor specs from `tritonModelProperties`.

## Model-management unload sequence

1. Acquire the model-operation lock.
2. Call Triton REST `POST /v2/repository/models/{model_name}/unload`.
3. If `remove-files=true`, remove the prepared model repository files for that model.
4. Return a success message or a Problem+JSON error.

Load and unload operations are protected by a short lock. Concurrent load/unload bursts can become operation-conflict errors; retry after the active operation finishes.

## Service configuration knobs

| Runtime | Variable | Default/meaning |
| --- | --- | --- |
| Marqo API | `MARQO_REMOTE_INFERENCE_URL` | Base URL for `/vectorise` and `/models`. |
| Marqo API | `MARQO_INFERENCE_TIMEOUT` / `MARQO_INFERENCE_POOL_SIZE` | Remote inference client timeout and keepalive pool size. |
| Marqo API | `MARQO_API_INFERENCE_CACHE_SIZE` / `MARQO_API_INFERENCE_CACHE_TYPE` | API-side cache; size `0` disables it; type is `LRU` or `LFU`. |
| Inference orchestrator | `MARQO_TRITON_URL` | Triton gRPC endpoint; default points at port 8001. |
| Inference orchestrator | `MARQO_MODEL_MANAGEMENT_CONTAINER_URL` | Model-management HTTP endpoint; default points at port 8883. |
| Inference orchestrator | `MARQO_INFERENCE_CACHE_SIZE` / `MARQO_INFERENCE_CACHE_TYPE` | Orchestrator-side cache; size `0` disables it. |
| Inference orchestrator | `MARQO_MODELS_TO_PRELOAD` | JSON list of registry names or `{model, modelProperties}` objects to warm on startup. |
| Inference orchestrator | `MARQO_DEFAULT_MODELS_S3_BUCKET` | S3 prefix used when registry defaults point at Marqo-hosted ONNX files. |
| Model management | `MARQO_TRITON_REST_URL` | Triton REST endpoint; default points at port 8000. |
| Model management | `MARQO_MODEL_CACHE_PATH` | Writable model repository/cache root. |
| Model management | `MARQO_MODELS_TO_PRELOAD` | JSON array of up to three `TritonModelProperties` objects. |

## Triton clients

- The inference orchestrator uses a gRPC Triton client for actual `infer` calls. Its URL parser strips `http://` or `https://` before constructing the gRPC client.
- The model-management service uses a REST Triton client for repository load/unload routes.
- REST load/unload failures map to Triton communication or Triton model load errors.
- The model-management REST client does not implement a loaded-model listing; use the inference orchestrator `/models` route for loaded Marqo model cache entries.

## Safe backend inspection

Run the bundled script without a Triton URL to inspect optional Python packages and CUDA availability without model downloads or network calls:

```bash
python scripts/check_model_backends.py
```

Only pass `--triton-url` when a live Triton readiness probe is explicitly desired:

```bash
python scripts/check_model_backends.py --triton-url http://localhost:8000
```
