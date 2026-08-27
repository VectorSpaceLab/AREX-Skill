---
name: inference-providers
description: "Operate the TaskingAI inference microservice provider/model
  catalog, credential validation, chat completion, text embedding, rerank,
  provider icons, custom/local providers, proxy safety, and provider
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TaskingAI Inference Providers

Use this sub-skill when a task is about TaskingAI's inference microservice: provider and model schema discovery, provider credentials, credential verification, chat completion, text embedding, rerank, provider icons, OpenAI-compatible/custom hosts, local model providers, proxy/URL blacklist behavior, or provider-specific failure diagnosis.

## Load this first

1. For provider/model selection, credential fields, wildcard schemas, local/custom-host choices, and catalog counts, read [references/provider-catalog.md](references/provider-catalog.md).
2. For HTTP route contracts, request/response bodies, validation order, streaming, fallbacks, proxy/custom-header behavior, and icon routes, read [references/api-reference.md](references/api-reference.md).
3. For source-backed native-test behavior, credential-sensitive checks, and safe skip criteria, read [references/native-testing.md](references/native-testing.md).
4. For symptoms, likely causes, and recovery steps, especially `PROVIDER_ERROR` versus `REQUEST_VALIDATION_ERROR`, read [references/troubleshooting.md](references/troubleshooting.md).
5. To inspect a user-supplied TaskingAI source tree without network calls or credentials, use [scripts/inspect_inference_catalog.py](scripts/inspect_inference_catalog.py).

## Source-backed facts to preserve

- The verified inference catalog snapshot contains 35 provider directories.
- Model schema types are exactly `chat_completion`, `text_embedding`, `rerank`, and `wildcard`.
- Provider and model metadata are loaded from bundled YAML resources into runtime caches before route handlers use them.
- Static import probes passed in Python 3.10 for `APIRouter`, `Provider`, and `DebugChatCompletionModel`.
- Credential verification can be schema-only at provider level or can call a default chat, embedding, or rerank model depending on provider metadata.

## Quick routing

- Backend object lifecycle, model-instance APIs exposed by the main backend, backend proxy endpoints, authentication, and database/API object semantics belong to `../backend-api/`.
- Deployment variables, container startup, service URLs, image tags, port wiring, `TASKINGAI_INFERENCE_URL`, global outbound proxy setup, and storage configuration belong to `../deployment-configuration/`.
- Plugin tool bundles, plugin vision/tool schemas, plugin execution, and plugin image generation belong to `../plugin-bundles/`.
- Stay here for provider catalog semantics, inference route payloads, credentials, `custom_host`, Ollama/LM Studio/LocalAI, provider icons, and provider-specific troubleshooting.

## Operating workflow

1. **Classify the requested model capability.** Use `chat_completion`, `text_embedding`, `rerank`, or `wildcard`; do not assume a wildcard schema has enough information without `provider_model_id`, `model_type`, and any required `properties`.
2. **Choose the provider path.** Use [provider selection guidance](references/provider-catalog.md#provider-selection-guidance) for hosted providers, hosted OpenAI-compatible routers, `custom_host`, and local OpenAI-compatible servers.
3. **Validate credentials before invocation.** Compare the request to the provider `credentials_schema`; pass either plaintext `credentials` or `encrypted_credentials`, never both. Use [credential validation semantics](references/api-reference.md#credential-validation-routes) when the user needs encrypted credentials for later reuse.
4. **Build the inference payload.** Use [chat completion](references/api-reference.md#post-v1chat_completion), [text embedding](references/api-reference.md#post-v1text_embedding), or [rerank](references/api-reference.md#post-v1rerank) contracts. Check model properties and configs before provider calls.
5. **Handle proxy and URL safety deliberately.** Request-level `proxy` values must be HTTPS and are rejected if they contain a configured provider URL blacklist entry. `custom_host` endpoint URLs are checked against the same blacklist before a provider call.
6. **Diagnose by error class.** Treat schema/model/property/proxy failures as request validation first. Treat upstream HTTP/API/auth/quota failures as provider failures. Use [troubleshooting](references/troubleshooting.md) before retrying with new credentials.

## Hard usability cases covered here

- Choose between `custom_host`, Ollama/LM Studio/LocalAI, OpenRouter, and a named hosted provider for an OpenAI-compatible user task while preserving the difference between actual provider model IDs and TaskingAI model schema IDs.
- Diagnose `PROVIDER_ERROR` versus `REQUEST_VALIDATION_ERROR` during credential validation by separating local schema/model/proxy checks from upstream provider responses.
