---
name: backend-api
description: "Operate TaskingAI backend REST/OpenAI-compatible APIs, object
  lifecycle, assistant generation, retrieval objects, auth, files, and backend
  service troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# backend-api

Use this sub-skill when the task is to work with TaskingAI's backend API/web service semantics: REST objects, lifecycle order, assistant/chat/message generation, retrieval collections/records/chunks, models, actions, bundle instances as backend tool references, OpenAI-compatible endpoints, authentication, file/image uploads, backend dependencies, or backend-native test prerequisites.

## Load this first

1. For route prefixes, auth mode, object lifecycle, request shapes, generation order, retrieval order, and OpenAI-compatible mappings, read [API and object model](references/api-and-object-model.md).
2. Before proposing or interpreting backend tests, read [native testing](references/native-testing.md) for Python-version constraints, DB/Redis/service prerequisites, and safe skip criteria.
3. When a backend service, import, generation, retrieval, auth, file, or storage symptom appears, use [troubleshooting](references/troubleshooting.md).

## Source-backed facts to preserve

- Backend package version evidence is `v0.3.0`.
- The backend builds a FastAPI app with an `APIRouter`; API mode uses `/v1`, while web-console mode uses `/api/v1`.
- Verified backend imports require Python 3.10. Python 3.11 backend import fails because `aioredis==2.0.1` defines a duplicate `TimeoutError` base class under Python 3.11.
- Verified model type values are `chat_completion`, `text_embedding`, `rerank`, and `wildcard`.
- Verified retrieval splitting includes `TextSplitter` with `token` and `separator` modes.

## Quick routing

- Starting containers, selecting Docker/Compose topology, setting environment variables, ports, storage mode, and service URL wiring belong to `../deployment-configuration/`.
- Provider-specific model schema catalogs, credentials, inference-provider behavior, and provider execution failures belong to `../inference-providers/`.
- Plugin bundle catalog internals, plugin schemas, and plugin-service execution internals belong to `../plugin-bundles/`.
- Backend-created action objects, bundle instances as backend tool references, assistant tool wiring, and tool execution from an assistant generation flow stay here; return to plugin/provider sub-skills only for the provider or bundle-specific payload details.

## Operating workflow

1. **Identify service purpose and auth.** API mode expects API-key bearer auth and `/v1` routes. Web mode expects admin bearer auth and `/api/v1` routes. Do not mix route prefixes with the wrong auth mode.
2. **Plan object order before calling generation.** For assistant + retrieval + tools, create or select required models first, then retrieval collections/records/chunks, actions or bundle instances, assistant, chat, user message, and finally generation. The exact order and constraints are in [API and object model](references/api-and-object-model.md#integrated-assistant--retrieval--tool-order).
3. **Validate IDs and model capabilities.** Backend route validation uses path IDs, object parents, model types, and model properties. Chat models must be `chat_completion`; retrieval collection models must be `text_embedding`; rerank is optional for query reranking; function-call tools require a chat model that supports function calling.
4. **Treat generation as orchestration.** Stateful generation loads chat memory, retrievals, tools, and model settings, then may run retrieval/tool function-call rounds before creating the assistant message.
5. **Check backend dependencies early.** DB/Redis/object storage/inference/plugin service availability affects imports, app startup, object writes, retrieval embedding, file/image uploads, and generation. Use [native testing](references/native-testing.md) and [troubleshooting](references/troubleshooting.md) to decide whether a failure is an app bug, missing service, wrong Python, or unavailable external dependency.

## Hard cases this sub-skill covers

- Mapping a request like "assistant with RAG over one document and a tool call" into the required model → collection → record/chunk → action/bundle-instance → assistant → chat → user message → generation sequence, with the validation points that can fail at each step.
- Explaining why backend import or inspection under Python 3.11 fails and choosing Python 3.10 for backend inspection/development instead of debugging unrelated FastAPI or Pydantic code.
