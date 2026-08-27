# Native Testing Notes and Safe Skip Criteria

This reference distills source-backed native-test behavior for the inference sub-skill. Do not depend on the original repository tests being available at runtime; use these notes to decide what kind of validation is safe for the user's environment. For static catalog checks, use the bundled [../scripts/inspect_inference_catalog.py](../scripts/inspect_inference_catalog.py).

## Source-backed native-test coverage

The source test suite covers these inference behaviors:

- Catalog/cache routes: provider list, provider get, provider icon fetch, model schema list/get, model property schema, cache dump, and cache checksums.
- Chat completion: normal responses, streaming SSE, length finish reason, function/tool calls, function result continuation, wildcard cases, and selected proxy/custom-header cases.
- Text embedding: normal embeddings, wildcard embeddings, embedding vector unit-normalization expectations, and embedding-size behavior.
- Rerank: normal rerank result shape and relevance-score ordering assumptions.
- Credential validation: provider-level validation, model-level validation, wildcard validation, bad credentials, bad custom-host endpoint URL, missing wildcard embedding properties, and provider URL blacklist rejection.
- Credential health checking: dynamically selects one non-wildcard model per provider when required credential environment variables are present, makes lightweight calls, and reports success/failure.

Verified static import facts: `APIRouter`, `Provider`, and `DebugChatCompletionModel` imported successfully under Python 3.10.

## What is safe without network or credentials

Safe static checks:

1. Run the bundled static helper against a user-supplied TaskingAI source tree to count providers/model schemas and detect catalog inconsistencies.
2. Inspect generated references for route coverage and error-code guidance.
3. Validate payload shape manually against [api-reference.md](api-reference.md), without contacting providers.
4. If a live inference service is already running, `GET /v1/health_check`, `GET /v1/providers`, `GET /v1/model_schemas`, and provider icon checks are generally low-risk; they do not require provider credentials but still depend on service availability and deployment routing.

Avoid provider-call validation unless the user explicitly allows external provider calls and supplies appropriate credentials or local provider hosts.

## Credential/network-sensitive checks

Provider-call tests can spend quota, hit rate limits, reveal credential mistakes, or depend on third-party service availability. Treat these checks as opt-in:

- `POST /v1/verify_provider_credentials` for providers whose metadata requires a real model call.
- `POST /v1/verify_credentials` for chat, embedding, rerank, wildcard, and `custom_host` cases.
- `POST /v1/chat_completion`, `/v1/text_embedding`, and `/v1/rerank` against hosted providers.
- Streaming SSE checks, which may succeed at the HTTP layer while returning stream-body error objects.
- External resource URL checks from provider documentation fields.
- Local providers (`ollama`, `lm_studio`, `localai`) unless the local server is already running and the user gives the host and model id.

## Safe skip criteria

Skip or downgrade native checks to static validation when any of these apply:

- No live TaskingAI inference service is available and the user did not authorize service startup.
- Required provider credentials are missing, expired, intentionally fake, or not allowed to be used.
- Network access to external providers is unavailable or disallowed.
- The check would call a paid provider, consume quota, or use credentials outside the user's stated budget.
- Local providers are requested but the local server/model is not running or not under the user's control.
- The task only needs catalog/schema reasoning and static payload construction.
- The provider is `debug` in production mode, where the service omits the debug provider.
- A provider service error is clearly transient or provider-side and not relevant to the user's payload/schema question.
- The expected result depends on deployment URL, container topology, or global outbound proxy wiring; route those issues to `../deployment-configuration/` first.

## Native success signals by surface

| Surface | Minimal success signal | Common safe alternative |
|---|---|---|
| Catalog | `/v1/providers` and `/v1/model_schemas` return `status: success` with non-empty data. | Static helper reports expected provider/model counts. |
| Provider icon | `/images/providers/icons/{provider_id}.svg` returns HTTP 200 for a listed provider. | Confirm provider is in catalog and icon files are not missing via static helper. |
| Provider credential validation | Returns encrypted credentials for the provider. | Schema-only field check for providers with `pass_provider_level_credential_check: true`. |
| Model credential validation | Returns resolved provider/model/type/properties and encrypted credentials. | Validate local request fields and explain that provider call is skipped for credentials/network. |
| Chat completion | Non-stream response has `status: success`, `data.object: ChatCompletion`, assistant message, finish reason, and usage. | Validate request shape and model capabilities; do not fabricate provider output. |
| Streaming chat | SSE frames include `ChatCompletionChunk` and final `ChatCompletion`, then `[DONE]`. | Explain stream-body error behavior and validate payload shape. |
| Text embedding | Response has ordered embeddings and usage; vector length matches expected embedding size. | Check model schema `properties.embedding_size`; for wildcard, require user-supplied `properties.embedding_size`. |
| Rerank | Response has ranked results with document index/text and relevance scores. | Check provider/model type is rerank and payload includes `query`, `documents`, `top_n`. |

## Source-backed skip/xfail patterns to preserve

The source tests intentionally skip or tolerate several provider realities:

- Timeouts around provider calls are skipped rather than treated as deterministic schema failures.
- Provider service errors can be skipped in broad provider sweeps because they often reflect provider availability rather than TaskingAI request construction.
- Some providers/models are excluded from function-call, streaming, length, or validation tests when source evidence showed unsupported behavior or unstable upstream responses.
- Bad-credential tests skip providers where provider-level verification is schema-only, because no upstream call is expected.
- `custom_host` bad endpoint URL is expected to produce `REQUEST_VALIDATION_ERROR`; `custom_host` good endpoint with bad API key is expected to produce `PROVIDER_ERROR`.
- Wildcard text embedding without `properties.embedding_size` is expected to produce `REQUEST_VALIDATION_ERROR`.
- Provider URL blacklist checks are expected to produce `REQUEST_VALIDATION_ERROR` before external provider calls.

## Suggested hard usability cases for verification planning

These cases go beyond simple happy-path tests and are suitable for downstream usability-test artifacts outside the runtime skill tree:

1. **Provider choice case:** A user has an OpenAI-compatible model available through a local Ollama server, LM Studio, OpenRouter, and an arbitrary private HTTPS endpoint. The expected answer should choose between `ollama`/`lm_studio`/`openrouter`/`custom_host`, identify which field is the actual model id, and list the minimum credentials/properties without calling the provider.
2. **Credential validation diagnosis case:** A `custom_host/openai-text-embedding` validation request fails once with endpoint `12345678` and once with a valid endpoint plus fake API key. The expected answer should classify the first as local `REQUEST_VALIDATION_ERROR` and the second as likely upstream `PROVIDER_ERROR`, with recovery steps from [troubleshooting.md](troubleshooting.md).
