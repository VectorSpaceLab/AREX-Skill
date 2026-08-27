---
name: client-and-api
description: "Use Xinference sync and async Python clients, model handles, and
  HTTP/OpenAI-compatible APIs safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Client and API

Use this sub-skill when a task is about calling a running Xinference service from
Python, cURL, the OpenAI SDK, or another HTTP client. It assumes the target model
has already been launched and identified by a model UID.

## Use this for

- `Client`, `AsyncClient`, `RESTfulClient`, and `AsyncRESTfulClient` usage.
- `launch_model`, `register_model`, `list_models`, `get_model`, and
  `terminate_model` client signatures.
- Model handles for chat, text generation, embeddings, rerank, images, audio,
  video, and flexible model requests.
- Service-root versus `/v1` OpenAI-compatible base URL selection.
- Streaming response iterators and async iterator handoffs.
- API key headers and endpoint placeholders in examples.
- Request-shape validation, including strict system-message ordering and
  integer-like replica validation.

## Route away when needed

- Service startup, model lifecycle CLI commands, and supervisor/worker cluster
  orchestration: `serving-and-cli`.
- Model family, engine, format, quantization, optional extras, LoRA, or custom
  model JSON decisions: `models-and-backends`.
- Auth database bootstrap, OIDC, admin policy, audit logs, metrics, Web UI, or
  deployment hardening: `operations-and-security`.

## Working pattern

1. Confirm the service endpoint root, for example `http://<host>:9997`.
2. Confirm the model UID returned by launch/list operations.
3. Pick the API surface:
   - Xinference Python client: endpoint root.
   - OpenAI-compatible SDK/cURL: endpoint root plus `/v1`.
   - Direct HTTP family endpoints: use the family-specific reference.
4. Add `Authorization: Bearer <token-or-api-key>` only when auth is enabled.
5. Keep examples placeholder-only until the user supplies a real endpoint,
   model UID, and API key policy.
6. If a request fails, classify the failure as endpoint/base-url, auth,
   model-UID, request-shape, streaming, or backend/model-readiness before
   changing code.

## Core rules

- A launched model UID is required for every request family.
- The OpenAI-compatible base URL should end in `/v1`; the Xinference `Client`
  constructor uses the service root.
- `RESTfulClient` is a compatibility alias for `Client`; `AsyncRESTfulClient` is
  an alias for `AsyncClient`.
- In this inspected build, the sync `Client.launch_model` exposes virtual-env
  launch knobs that the async launch signature does not mirror exactly. Check
  `references/api-reference.md` before assuming parity.
- Treat rerank as a Xinference HTTP/client workflow, not a universal OpenAI SDK
  helper.
- Do not make live network calls from bundled helper scripts; they render
  snippets only.

## References

- [API reference](references/api-reference.md) for verified signatures and model
  handle method notes.
- [OpenAI-compatible API](references/openai-compatible-api.md) for `/v1` base
  URL shape and request-family templates.
- [Client workflows](references/client-workflows.md) for sync/async launch,
  list/get, model handle, streaming, and registration flows.
- [Troubleshooting](references/troubleshooting.md) for 401/403, 404, strict
  message order, replica, streaming, and OCR response issues.

## Snippet helper

- [make_openai_client_snippets.py](scripts/make_openai_client_snippets.py)
  renders Python and cURL snippets for chat, generate, embedding, and rerank
  without contacting a server.
