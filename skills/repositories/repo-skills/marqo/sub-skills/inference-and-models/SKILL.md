---
name: inference-and-models
description: "Marqo model registry, inference request shaping, preprocessing,
  model backends, cache behavior, and Triton/model-management troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# inference-and-models

Use this sub-skill for Marqo model-registry facts, inference request shaping, preprocessing, model backends, cache behavior, and Triton/model-management troubleshooting.

## Route here when the task involves
- translating a registry model name into runtime `modelProperties`
- deciding between random, HF, and OpenCLIP pipelines
- building or repairing `/vectorise` requests
- inspecting or clearing loaded models
- probing CUDA, Triton, or download/cache readiness
- diagnosing model load, unload, auth, or preprocessing failures

## Route away when the task is about
- search query construction or ranking fusion
- index schema or Vespa layout
- service startup, compose, or container orchestration

## Bundled references
- `references/model-registry.md`
- `references/inference-api.md`
- `references/model-services.md`
- `references/troubleshooting.md`
- `scripts/check_model_backends.py`

## Working rules
1. Prefer `random/*` for no-download smoke checks and shape debugging.
2. For direct `/vectorise`, always send a complete `embeddingModelConfig.modelProperties` object; the direct inference route does not resolve registry names for you.
3. Keep `/vectorise` requests and responses on `application/msgpack`.
4. Use the bundled backend probe before touching live Triton or model-download paths.
5. When a model is already loaded, inspect the full cache key returned by `/models` before trying `DELETE /models`.
6. Never trigger model downloads or Triton calls just to inspect support; use the bundled script and the `random` family first.

## Fast selection guide
| Need | Start with |
| --- | --- |
| No-download smoke test | `random/small` or `random/medium` |
| Text embeddings | `hf/*` |
| Text + image embeddings | `open_clip/*` or `hf-hub:*` |
| Load/unload or Triton errors | `references/model-services.md` |
| Bad request or preprocessing validation | `references/inference-api.md` + `references/troubleshooting.md` |
| Backend/cuda sanity check | `scripts/check_model_backends.py` |

## Typical flow
1. Identify the model family and whether the request is meant for the direct inference service or the Marqo API client.
2. Use `references/model-registry.md` to obtain the correct property shape and any family-specific fields.
3. Use `references/inference-api.md` to build the request body and expected response shape.
4. Use `references/model-services.md` for load/unload, Triton, and cache-key behavior.
5. Use `references/troubleshooting.md` and the probe script when a backend or auth dependency fails.

## Output expectations
- This sub-skill should help produce corrected request payloads, cache-key-aware diagnostics, and backend triage steps.
- It should not broaden into search or index advice.
- It should not assume external downloads are safe unless the user explicitly wants that path.
