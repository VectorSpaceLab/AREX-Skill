# Inference and model troubleshooting

Use this guide when `/vectorise`, `/models`, model-management load/unload, Triton, CUDA, or model downloads fail.

## Start with safe checks

1. If you only need backend facts, run the bundled probe with no network side effects:

   ```bash
   python scripts/check_model_backends.py
   ```

2. Only when the task explicitly needs a live Triton readiness check, pass a URL:

   ```bash
   python scripts/check_model_backends.py --triton-url http://localhost:8000
   ```

3. If a model-dependent request fails, retry the same request shape with `random/small` and explicit random `modelProperties`. If random works, the failure is likely in model download, Triton, CUDA, or family-specific properties rather than MessagePack/request shape.

## `/vectorise` request failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| 415 with `Unsupported Content-Type` | Request was not sent as `application/msgpack`. | Set both `Content-Type` and usually `Accept` to `application/msgpack`; pack the body with MessagePack. |
| 400 with `Invalid MessagePack format` | Body is not valid MessagePack. | Repack the dict with `msgpack.packb(..., use_bin_type=True)`. |
| 422 validation error | Missing or mismatched request fields. | Check `modality`, `contents`, `embeddingModelConfig`, and `preprocessingConfig`; aliases are camelCase. |
| 400 service error during vectorisation | Model or preprocessing layer raised a service error. | Check family-specific model properties, media download settings, and Triton/model-management health. |
| 500 internal error | Unhandled exception, often missing `modelProperties` on a direct call or backend failure. | Include full `modelProperties`, then isolate with `random/small`. |

Direct `/vectorise` does not resolve a registry name by itself. If `embeddingModelConfig.modelProperties` is missing, the loader has no `type` and no `dimensions` to select a pipeline.

## Model-name and property failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Unsupported model name | Name is not in the default registry and no custom properties were supplied. | Use a registry name from `model-registry.md` or provide explicit `modelProperties`. |
| `Unsupported model type` | `modelProperties.type` is not `random`, `hf`, or `open_clip`. | Correct the `type` field. |
| `dimensions` validation error | Missing, non-integer, zero, or negative dimensions. | Set a positive integer matching the encoder output width. |
| OpenCLIP cannot load model | Effective name does not start with `hf-hub:` or `open_clip/`, or tokenizer/preprocessor settings are wrong. | Use a supported name prefix or set `tritonModelName` to the backend identifier. |
| HF property validation error | Missing `poolingMethod` or wrong encoder input/output names. | Use `poolingMethod: mean|cls`; inputs must be `input_ids`, `attention_mask`, `token_type_ids`; output must be `last_hidden_state`. |
| Triton model-property validation error | Bad `maxBatchSize`, missing tensors, or invalid source basenames. | Keep `maxBatchSize` in 1..128; sources must end in `model.onnx` or `model.onnx.data*`; check tensor names and dims. |

## S3, HF, and auth failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Default registry model cannot download ONNX files | `MARQO_DEFAULT_MODELS_S3_BUCKET` is wrong, inaccessible, or empty. | Use a reachable S3 bucket prefix or the default public bucket; do not leave the variable empty. |
| Model-management reports missing AWS credentials | S3 source requires credentials unavailable to the model-management runtime. | Configure AWS credentials in the runtime or switch sources to reachable public URLs. |
| Source file not found | The URI is wrong or the runtime cannot access it. | Verify every source URI and ensure the final basename is `model.onnx` or `model.onnx.data*`. |
| Private HF model fails to load tokenizer/model assets | HF credentials are not available to the runtime, or the direct orchestrator route lacks auth context. | For higher-level Marqo API requests, supply a `modelAuth` object with exactly one auth method. For direct `/vectorise`, prefer accessible sources or preconfigured runtime credentials. |
| Auth validation says missing or too many auth objects | `modelAuth` is empty or includes both S3 and HF auth. | Supply exactly one supported auth object. |

Never paste tokens into logs or bundled skill files. Treat auth as runtime configuration.

## OpenCLIP and HF download/cache failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| OpenCLIP import or tokenizer load fails | `open_clip` or its dependencies are missing or incompatible. | Run `check_model_backends.py`; install/repair the runtime package set before retrying. |
| Transformers tokenizer load fails | `transformers` is missing, cannot reach HF, or cache is invalid. | Verify import status, network/auth, and that the model cache directory is writable. |
| Download repeats or partially fails | Cache directory is not writable, full, or contains partial files. | Make cache storage writable and large enough; remove corrupt partial artifacts if needed. |
| Shape mismatch after encode | Encoder output dims do not match `dimensions`, or tensor specs do not match the ONNX model. | Align `dimensions`, `input`, and `output` specs with the actual ONNX encoder. |

Use `random/small` to verify the request path before spending time on OpenCLIP/HF downloads.

## CUDA and memory failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `torch.cuda.is_available()` is false | CPU-only torch build, no visible GPU, or missing driver/runtime. | Use CPU-safe random checks; route service startup/GPU runtime setup to local-development. |
| CUDA out of memory | Triton/GPU model batch or model size exceeds available memory. | Reduce model `maxBatchSize`, unload unused models, use a smaller model, or use random/HF-small for debugging. |
| Probe shows no CUDA but random request works | Request stack is fine; GPU backend is unavailable. | Do not treat no-CUDA as a `/vectorise` schema failure. |
| Probe import of torch fails | Torch is not installed or incompatible with the Python runtime. | Repair the environment before selecting real HF/OpenCLIP pipelines. |

The inference liveness route returning `{"status": "ok"}` is not a CUDA capability proof.

## Triton and model-management failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Triton is unavailable` or timeout | Wrong Triton URL/port, service down, network blocked, or REST vs gRPC endpoint confusion. | Check `MARQO_TRITON_URL` for gRPC encode calls and `MARQO_TRITON_REST_URL` for model-management load/unload. Use `--triton-url` only for an explicit REST readiness probe. |
| `Model management container is unavailable` | Inference orchestrator cannot reach model-management service. | Check `MARQO_MODEL_MANAGEMENT_CONTAINER_URL` and service health. |
| Load/unload returns Problem+JSON 400 | Invalid model properties or source download failure. | Inspect `detail`; repair schema or source access. |
| Load/unload returns Problem+JSON 409 | Another model operation is in progress. | Retry after the active load/unload finishes. |
| Load/unload returns 502/timeout-style dependency error | Triton failed or timed out during repository operation. | Probe Triton readiness, verify model repository files, and inspect Triton-side error text. |
| `DELETE /models` does not remove expected model | Used public model name instead of full cache key. | Call `GET /models?detailed=false` and use the returned `modelName` value including `||hhhh`. |

Remember that model-management load/unload talks to Triton REST repository routes, while inference encoding talks to Triton gRPC inference routes.

## Preprocessing and media failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Modality/config mismatch | `modality` differs from `preprocessingConfig.modality`. | Use `language` with text config and `image` with image config. |
| Text chunking validation error | `shouldChunk=true` without `chunkConfig`, or `chunkConfig` present while chunking is false. | Add/remove `chunkConfig` according to `shouldChunk`. |
| `split_length must be greater than split_overlap` | Invalid text chunk overlap. | Keep `splitLength > splitOverlap >= 0`. |
| Invalid split method | Split method is not one of the supported values. | Use `character`, `word`, `sentence`, or `passage`. |
| Image chunking validation error | `shouldChunk=true` without `patchMethod`, or `patchMethod` present while chunking is false. | Add/remove `patchMethod`; valid values are `simple`, `frcnn`, `dino-v1`, `dino-v2`, `marqo-yolo`. |
| Image URL download fails | Bad URL, auth header missing, timeout too low, unsupported content type, or image decoder error. | Set `downloadHeader`, raise `downloadTimeoutMs`, or use a reachable image/base64 data URL. |
| Per-item media errors appear in results | `returnIndividualError=true`. | This is expected; set false if the whole batch should fail on the first media error. |

## Inference cache pitfalls

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Cache never used | Cache size is zero, `useInferenceCache=false`, or skip rule applies. | Set a positive cache size and `useInferenceCache=true`; avoid `device`, non-text/image modalities, and chunking. |
| Invalid cache startup error | Bad cache size or type. | Size must be a positive integer when enabled; type must be `LRU` or `LFU`. |
| Chunked requests do not cache | Cache is per content, not per chunk. | Disable chunking for cache tests or accept bypass behavior. |
| URL images are not cached | Only base64 image data URLs are cached; URL images are skipped. | Use base64 data URLs if image cache behavior is the test target. |
| Errors are not cached | Error entries are intentionally skipped. | Reproduce with a valid content if testing cache hits. |

## Random-model fallback

Random models are the safest way to separate request/schema issues from backend issues:

- They require explicit `modelProperties` just like real direct `/vectorise` calls.
- They support text and image request shapes without downloads.
- They produce deterministic vectors for the same input string and configured dimension.
- They do not validate semantic quality, OpenCLIP/HF tokenizer behavior, Triton repository setup, or real CUDA performance.

If `random/small` succeeds but HF/OpenCLIP fails, focus on model properties, package imports, download/auth/cache, Triton, or CUDA instead of the base `/vectorise` route.
