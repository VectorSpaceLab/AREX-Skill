---
name: model-backends
description: "Guide for resolving and extending lmms-eval model backends,
  registry aliases, chat-versus-simple dispatch, media handling, and decode
  backend troubleshooting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# model-backends

Use this route when the user is adding, fixing, or choosing a model backend, or when a backend behaves differently from what the task/model combination expects.
It is the right place for registry resolution, alias lookup, chat-versus-simple dispatch, multimodal message handling, and video decode backend selection.

## Read first

- `../../references/model-backends.md`
- `../../references/api-reference.md`
- `../../references/troubleshooting.md`

## What this route covers

- Model registry behavior through `ModelRegistryV2`, `list_available_models()`, and alias resolution.
- The `is_simple` split between chat-style and legacy simple backends.
- `ChatMessages` media extraction and message serialization.
- Backend-specific `model_args` such as checkpoint ids, message formats, and generation settings.
- Optional backend families such as API wrappers, local HF-style backends, vLLM, SGLang, and video-capable decoders.
- Throughput and timing-oriented model metrics.

## Typical workflow

1. Identify whether the user is asking about a named model id, an alias, or a backend class.
2. Check the registry first with `lmms-eval models --aliases` or the bundled registry smoke.
3. Decide whether the backend should resolve as chat or simple.
4. Verify `model_args` and optional extras before touching the implementation.
5. If video or other media decoding is involved, confirm the decode backend and optional dependencies.
6. Use `video_decode_smoke.py` for backend selection questions and `model_registry_smoke.py` for alias / class-path questions.

## Helpful commands

```bash
lmms-eval models --aliases
python -m lmms_eval --help
```

## Bundled scripts

- `../../scripts/model_registry_smoke.py` — inspect canonical models, aliases, and a concrete resolution.
- `../../scripts/video_decode_smoke.py` — inspect video decode backends and optionally decode a local clip.

## Cross-route handoff

- Send task YAML request-shape questions to `task-authoring`.
- Send CLI argument and cache/reasoning flows to `cli-and-workflows`.
- Send HTTP server/client/MCP/TUI behavior to `service-ops`.

## Common failure modes

- `is_simple` does not match the resolved backend type.
- A `model_args` string points to the wrong checkpoint or provider format.
- Optional backend packages such as `torchcodec`, `decord`, `vllm`, or `sglang` are missing.
- Video decode falls back to the wrong backend or an unavailable environment variable setting.
- Throughput metrics are absent because the backend does not emit them.

Use the registry smoke before changing model code, and use the troubleshooting reference when a failure looks like a missing backend rather than a code bug.
