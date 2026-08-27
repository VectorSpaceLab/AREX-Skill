# Inference Provider Troubleshooting

Use this reference to turn inference symptoms into likely causes and recovery steps. For exact route fields, see [api-reference.md](api-reference.md). For provider/model choices, see [provider-catalog.md](provider-catalog.md).

## First triage checklist

1. Identify the surface: catalog, provider icon, credential validation, chat completion, text embedding, rerank, streaming, local provider, or custom host.
2. Capture the error code and HTTP status, if present. Do not treat all validation failures as provider failures.
3. Confirm the selected `model_schema_id`, `provider_model_id`, `model_type`, `properties`, and credential keys.
4. Check whether the task is actually a backend object/proxy API issue; if yes, route to `../backend-api/`.
5. Check whether service startup, container networking, global outbound proxy, ports, or environment variables are the root issue; if yes, route to `../deployment-configuration/`.
6. Avoid retrying paid provider calls until local request validation and credential field names are correct.

## `REQUEST_VALIDATION_ERROR` versus `PROVIDER_ERROR`

| Error class | What it usually means | Recovery priority |
|---|---|---|
| `REQUEST_VALIDATION_ERROR` | TaskingAI rejected the request before, or while shaping, the provider call. Common causes: missing required credential field, both plaintext and encrypted credentials, invalid encrypted credentials, unknown model schema, missing wildcard `provider_model_id`, missing wildcard embedding `properties.embedding_size`, model type mismatch, unsupported function/vision/stream/config, invalid proxy scheme, provider URL blacklist match, malformed `custom_host` endpoint. | Fix local payload/schema/config first. Do not rotate provider keys until request shape is valid. |
| `PROVIDER_ERROR` | The request shape reached a provider adapter and the upstream provider rejected or returned invalid data. Common causes: bad API key, quota/rate limit, content filter, provider outage, unsupported model id at provider, empty/malformed provider response. | Verify provider account/model/quota/region and credentials. Retry only when provider-side conditions are addressed. |
| `CREDENTIALS_VALIDATION_ERROR` | Verification-specific response did not satisfy expected content/function-call/embedding-size checks, or a generic verification exception occurred. | Read the detailed message. If it wraps a provider/request validation message, follow that more specific class. |

### Difficult credential-validation example

For `custom_host/openai-text-embedding`:

- Endpoint URL `12345678` should be diagnosed as `REQUEST_VALIDATION_ERROR` because the endpoint does not start with `http://` or `https://`; no provider credential rotation is useful.
- A valid embeddings endpoint with a fake API key should be diagnosed as likely `PROVIDER_ERROR` because local URL shape is valid and the upstream endpoint rejects the request.
- Missing `properties.embedding_size` for wildcard/custom-host embeddings should be diagnosed as `REQUEST_VALIDATION_ERROR` even if credentials are correct.

## Symptom matrix

| Symptom | Likely cause | Recovery steps |
|---|---|---|
| `Provider <id> not found` | Provider not loaded, filtered by allowed provider settings, debug provider omitted in production, or typo in `provider_id`. | List providers from the catalog endpoint or static helper; correct id; if deployment filtering is intended, route env/startup changes to `../deployment-configuration/`. |
| `Model schema <id> not found` | Wrong `model_schema_id`, provider filtered out, stale client catalog, or using provider model id where TaskingAI schema id is expected. | Use `/v1/model_schemas` or [provider-catalog.md](provider-catalog.md); distinguish `model_schema_id` from `provider_model_id`. |
| `provider_model_id is required` | Wildcard schema or schema with no fixed provider model id. | Supply the actual provider model id. For local providers, this is the local model name. For `custom_host`, the actual model is usually `CUSTOM_HOST_MODEL_ID` and the TaskingAI schema chooses function/tool/embedding flavor. |
| `model_type is required` or `model_type ... is invalid` | Wildcard schema cannot infer type, or caller requested chat/embedding/rerank mismatched with schema. | Set `model_type` to one of `chat_completion`, `text_embedding`, or `rerank`; choose a schema with the matching type. |
| Text embedding validation says `embedding_size` is required | Wildcard or custom embedding schema lacks fixed properties. | Add `properties: {"embedding_size": <expected_dimension>}`; confirm provider model's actual dimension. |
| Fallback embedding rejected for size mismatch | Primary and fallback embeddings have different dimensions. | Choose fallback embedding model with identical `embedding_size`, or remove fallback. |
| Chat rejects vision input | Selected model properties do not allow vision, or wildcard properties omitted `vision: true`. | Choose a vision-capable schema or set accurate wildcard properties; verify image content shape. Plugin vision/tool bundles route to `../plugin-bundles/`. |
| Chat rejects function/tool calls | Model properties do not allow function calls, wrong `function_call`/`functions` combination, or message history has unmatched function call ids. | Use a function-capable schema; validate function message sequence; for `custom_host`, choose `openai-tool-calls` or `openai-function-call` according to provider protocol. |
| Streaming request fails but non-stream works | Model properties do not allow streaming, provider stream endpoint differs, provider emitted stream-body error, or adapter does not return expected chunks. | Confirm `streaming` property; read SSE frames for error objects; retry non-stream only if streaming is not required. |
| Stream returns `[DONE]` after an error object | The route catches streaming exceptions and emits an SSE error object before final `[DONE]`. | Inspect error object code/message inside the stream body; do not rely on connection status alone. |
| `Invalid proxy URL. Must start with https://` | Request-level provider `proxy` is not HTTPS. | Use an HTTPS provider URL override or remove `proxy`. Deployment-level outbound proxy is separate and belongs to `../deployment-configuration/`. |
| `Invalid provider url: <url>` | Request-level `proxy` or `custom_host` endpoint contains a configured blacklist substring. | Remove or change the blacklisted URL; if the blacklist/env is wrong, route deployment config changes to `../deployment-configuration/`. |
| `custom_host` rejects provider model id | Chat custom host only supports TaskingAI provider model ids `openai-function-call` and `openai-tool-calls` for chat. | Use `custom_host/openai-function-call` or `custom_host/openai-tool-calls`; put the actual upstream model name in `CUSTOM_HOST_MODEL_ID`. |
| `custom_host` embedding endpoint returns malformed response | Endpoint is not an OpenAI-compatible embeddings route, API key is invalid, or provider returns embeddings with unexpected data shape. | Confirm endpoint path, `CUSTOM_HOST_MODEL_ID`, API key, and expected embedding dimension. |
| Local Ollama/LM Studio/LocalAI provider cannot connect | Host credential wrong, local server not running, model not pulled/loaded, or container cannot reach host. | Confirm host URL from the inference service network, local model name as `provider_model_id`, and server health. Route container networking to `../deployment-configuration/`. |
| Provider icon 404/`OBJECT_NOT_FOUND` | Provider id is unknown or filtered; icon route validates provider before serving SVG. | Confirm provider appears in catalog. Static helper can detect missing icon files for a source tree. |
| Provider list/model schema list empty | Service did not load catalog, allowed providers filtered everything, or service startup failed before cache population. | Check health/version, deployment logs/env through `../deployment-configuration/`; use static helper to confirm the source tree has provider resources. |
| Bad credentials test returns success for local/router provider | Provider has schema-only provider-level credential verification. | Use model-level validation or an actual inference call if the user authorizes it; do not expect provider-level validation to contact the upstream service. |
| Hosted provider returns content filter error | Adapter surfaced provider refusal/content filtering as `PROVIDER_ERROR`. | Change prompt/content, verify provider policy, and avoid treating it as TaskingAI schema failure. |
| Rate limit/quota/auth provider errors | Upstream account problem, invalid key, missing region/deployment id, or quota exhausted. | Verify provider console/account, credential keys, region/deployment-specific fields, and budget before retry. |

## Custom-host recovery flow

1. Decide the OpenAI-compatible flavor:
   - Chat with modern tools: `custom_host/openai-tool-calls`.
   - Chat with legacy functions: `custom_host/openai-function-call`.
   - Embedding: `custom_host/openai-text-embedding`.
2. Put the actual model name in `CUSTOM_HOST_MODEL_ID`.
3. Put the exact provider API endpoint in `CUSTOM_HOST_ENDPOINT_URL`.
4. For embeddings, set `properties.embedding_size` to the model's real output dimension.
5. Ensure the endpoint is not blacklisted and starts with `http://` or `https://` where required.
6. If local validation passes but provider returns an error, treat the remaining issue as upstream auth/model/quota/protocol compatibility.

## Local provider recovery flow

Use this for `ollama`, `lm_studio`, and `localai`.

1. Confirm the local server is already running and reachable from the inference service process or container.
2. Use the provider's host credential field: `OLLAMA_HOST`, `LM_STUDIO_HOST`, or `LOCALAI_HOST`.
3. Use the local model name as `provider_model_id` with the provider wildcard schema.
4. For embeddings, provide `model_type: text_embedding` and `properties.embedding_size` when the wildcard schema cannot infer dimensions.
5. If running inside containers, validate host networking from the inference service network; route Docker/network fixes to `../deployment-configuration/`.
6. Remember provider-level credential validation is schema-only for these providers; use model-level validation or an actual inference call when authorized.

## Fallback recovery flow

- Chat completion fallbacks are tried sequentially after provider-adapter errors; the first successful fallback returns `fallback_index`.
- Text embedding fallbacks must match the primary embedding size before any provider call is useful.
- Rerank has no fallback list in the source-backed route.
- Credential loading uses the provider associated with the resolved model info. Prefer same-provider fallbacks unless you have confirmed credential coverage for the target provider set.

## When to stop and ask the user

Ask for clarification instead of guessing when:

- The user says "OpenAI-compatible" but does not specify hosted router, local server, or arbitrary endpoint.
- A wildcard schema is requested without `provider_model_id` or `model_type`.
- A text embedding wildcard/custom-host request lacks expected embedding dimension.
- Provider calls would spend quota or use credentials and the user has not authorized them.
- The error could be deployment reachability rather than inference payload semantics.
