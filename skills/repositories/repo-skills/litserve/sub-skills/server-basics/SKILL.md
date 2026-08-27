---
name: server-basics
description: "Serve models and custom pipelines with LitServe LitAPI and
  LitServer, including batching, streaming, auth, callbacks, loggers,
  middleware, payloads, multi-endpoints, clients, Docker, and deployment."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# server-basics

Use this sub-skill when a task asks how to build, run, deploy, or debug a general
LitServe server. It covers the standard `LitAPI` + `LitServer` workflow and the
HTTP-serving surfaces around it.

## Use this for

- Serving a custom model or pipeline with `litserve.LitAPI` and `litserve.LitServer`.
- Choosing `accelerator`, `devices`, `workers_per_device`, `timeout`, `num_api_servers`,
  host, port, logging, and client-generation settings.
- Adding batching, streaming, async handlers, auth, callbacks, loggers, middleware,
  request tracking, payload limits, health/info/shutdown endpoints, and multiple API paths.
- Handling JSON, form data, multipart file uploads, and base64 image input/output.
- Generating a local Dockerfile with `litserve dockerize` or deploying through the
  Lightning CLI passthrough.

## Route elsewhere

- OpenAI-compatible chat completions or embeddings belong in
  [`../openai-specs/SKILL.md`](../openai-specs/SKILL.md).
- MCP tool exposure and MCP server mounting belong in [`../mcp/SKILL.md`](../mcp/SKILL.md).
- Torch/CUDA benchmark harnesses, FastAPI parity tests, throughput benchmark scripts,
  and transformer/vision benchmark reproduction are intentionally out of scope.
- Start from the root LitServe router when the user request spans multiple sub-skills:
  [`../../SKILL.md`](../../SKILL.md).

## Reference map

Read these bundled references instead of opening the source repository:

- [`references/api-reference.md`](references/api-reference.md): constructor defaults,
  hooks, endpoint registration, auth, callbacks, loggers, middleware, client generation,
  and Docker/deployment knobs.
- [`references/workflows.md`](references/workflows.md): task recipes for serving,
  batching, streaming, async, files, images, auth, multi-endpoints, client generation,
  Docker, and deployment.
- [`references/data-formats.md`](references/data-formats.md): JSON, form, multipart,
  Pydantic, image, and streaming payload contracts.
- [`references/troubleshooting.md`](references/troubleshooting.md): common validation
  errors, readiness issues, auth mismatches, client/Docker problems, and excluded paths.

## Bundled examples

- [`scripts/minimal_server.py`](scripts/minimal_server.py): safe CPU square server with
  port, host, accelerator, batching, workers, and client-generation options.
- [`scripts/file_upload_server.py`](scripts/file_upload_server.py): multipart file and
  form-data server with an optional payload-size limit.
- [`scripts/image_roundtrip_server.py`](scripts/image_roundtrip_server.py): base64 image
  request/response server using `ImageInput` and `ImageOutput`.

## Operating notes

- Prefer putting `max_batch_size`, `batch_timeout`, `api_path`, `stream`, `loop`, `spec`,
  `mcp`, and `enable_async` on the `LitAPI` constructor. The same settings on
  `LitServer` are deprecated compatibility paths.
- Load heavy model state in `setup(device)`, not in `__init__`.
- For local development use `host="127.0.0.1"`; for containers and remote deployment use
  `host="0.0.0.0"`.
- Do not use this sub-skill to implement OpenAI or MCP specs directly; route those to the
  sibling sub-skills so their endpoint contracts remain precise.
