# Inference API Reference

This reference summarizes the inference microservice routes and validation behavior. Backend-side model-instance proxy/object APIs are out of scope here and should route to `../backend-api/`.

## Route prefixes and response envelope

- Inference/catalog/manage/verification routes are mounted under `/v1`.
- Provider icon routes are mounted under `/images`.
- Success responses use `status: "success"`; data-bearing routes return `data` and sometimes `usage` or `fallback_index`.
- Application errors use an error object with a code such as `REQUEST_VALIDATION_ERROR`, `PROVIDER_ERROR`, `CREDENTIALS_VALIDATION_ERROR`, or `OBJECT_NOT_FOUND`.

## Catalog and management routes

| Route | Purpose | Key inputs | Normal output |
|---|---|---|---|
| `GET /v1/providers` | List loaded providers. | Optional `lang`, default `en`. | List of provider dictionaries with credential schema, resources, proxy/header flags, and icon URL. |
| `GET /v1/providers/get` | Get one provider. Hidden from OpenAPI schema. | `provider_id`, optional `lang`. | Single provider in a one-element `data` list; unknown provider returns `OBJECT_NOT_FOUND`. |
| `GET /v1/model_schemas` | List model schemas. | Optional `provider_id`, `type`, `lang`. | List of model schema dictionaries; provider filter is validated against loaded providers. |
| `GET /v1/model_schemas/get` | Get one model schema. Hidden from OpenAPI schema. | `model_schema_id`, optional `lang`. | Single model schema in a one-element `data` list; unknown schema returns `OBJECT_NOT_FOUND`. |
| `GET /v1/model_property_schemas/{model_type}` | Return property schema for `chat_completion` or `text_embedding`. Hidden from OpenAPI schema. | `model_type`. | Simplified property schema; unsupported type returns `OBJECT_NOT_FOUND`. |
| `GET /v1/caches` | Debug cache dump. Hidden from OpenAPI schema. | None. | Provider cache, model schema cache, and i18n cache. |
| `GET /v1/cache_checksums` | Cache checksum values. Hidden from OpenAPI schema. | None. | Provider/model/i18n checksums. |
| `GET /v1/health_check` | Service health probe. Hidden from OpenAPI schema. | None. | Empty success response. |
| `GET /v1/version` | Service version. Hidden from OpenAPI schema. | None. | Version string. |

## Provider icon route

`GET /images/providers/icons/{provider_id}.svg` returns the provider SVG icon as `image/svg+xml` after confirming the provider exists in the loaded provider cache. Unknown provider ids return `OBJECT_NOT_FOUND`.

The `icon_svg_url` field returned by provider catalog endpoints is built from the image URL prefix and this icon route. Deployment-level host/base-URL issues belong to `../deployment-configuration/`; provider existence and icon id issues stay here.

## POST /v1/chat_completion

Use for chat-completion inference, with optional streaming, function/tool calls, vision messages, proxy, custom headers, and fallback models.

### Request fields

| Field | Required | Meaning |
|---|---|---|
| `model_schema_id` | Yes | TaskingAI model schema id, such as `openai/gpt-4o` or `ollama/wildcard`. |
| `provider_model_id` | Sometimes | Required when the schema does not declare a fixed provider model id, especially wildcard schemas. |
| `messages` | Yes | List of system/user/assistant/function messages. User content may be text or multimodal text/image-url content. |
| `stream` | No | `false` by default; `true` returns Server-Sent Events. |
| `credentials` | No | Plaintext provider credentials. Mutually exclusive with `encrypted_credentials`. |
| `encrypted_credentials` | No | Encrypted credentials from validation routes. Mutually exclusive with `credentials`. |
| `properties` | Sometimes | Custom model properties when the schema lacks fixed properties, especially wildcard/custom-host validation. |
| `configs` | No | Chat model configuration. Known config ids include `temperature`, `top_p`, `top_k`, `max_tokens`, `stop`, `presence_penalty`, `frequency_penalty`, `response_format`, and `seed`; each model schema may allow only a subset. |
| `proxy` | No | Request-level provider URL override. Must start with `https://` and must not contain a blacklisted provider URL substring. |
| `custom_headers` | No | Up to 16 headers, key length under 64 and value length under 512. Merged into provider request headers by supported adapters. |
| `fallbacks` | No | Ordered fallback models with `model_schema_id` and optional `provider_model_id`. |
| `function_call` | No | `auto` by default after validation when functions are present; `none`, `auto`, or a specific function name. |
| `functions` | No | OpenAI-style function schemas. |

### Validation and execution order

1. Validate the primary model schema with requested `ModelType.CHAT_COMPLETION`.
2. Validate fallback model schemas in order, using the same requested chat type.
3. Validate credentials from the first loaded provider context; plaintext and encrypted credentials cannot both be present.
4. Validate message order and content: at most one system message, system message must be first, function messages must answer previous assistant function calls, and user/assistant text messages are merged when consecutive.
5. Detect multimodal user content and validate that the selected model allows vision input.
6. Validate streaming, function-call support, vision support, and model configs against model properties.
7. Reject request-level `proxy` if it contains a configured provider URL blacklist entry.
8. Call the provider adapter for the primary model; on failure, try fallback models sequentially. The first successful fallback response sets `fallback_index` to the zero-based fallback position.

### Response behavior

- Non-stream success returns `data.object: "ChatCompletion"`, `finish_reason`, assistant `message`, `created_timestamp`, `usage`, and optional `fallback_index`.
- Streaming success yields SSE frames of the form `data: <json>\n\n` and a final `data: [DONE]\n\n`.
- Streaming provider errors are converted into SSE error objects with `code: PROVIDER_ERROR`; unexpected streaming exceptions use `UNKNOWN_ERROR`. This means an HTTP connection can be successful while the stream body reports provider failure.

## POST /v1/text_embedding

Use for embedding one text or a list of texts.

### Request fields

| Field | Required | Meaning |
|---|---|---|
| `model_schema_id` | Yes | Embedding model schema id or wildcard schema. |
| `provider_model_id` | Sometimes | Required for wildcard schemas without a fixed provider model id. |
| `input` | Yes | A string or list of strings. |
| `fallbacks` | No | Ordered fallback embedding models. |
| `credentials` / `encrypted_credentials` | No | Same mutually-exclusive credential rule as chat completion. |
| `properties` | Sometimes | Required for wildcard text embeddings when schema lacks fixed `embedding_size`. |
| `configs` | No | Text-embedding config object; usually empty. |
| `input_type` | No | Optional embedding input type, such as `document` or `query`, when provider supports it. |
| `proxy` | No | Must be HTTPS and pass blacklist checks. |
| `custom_headers` | No | Optional provider request headers. |

### Validation and execution order

1. Validate primary and fallback schemas as `ModelType.TEXT_EMBEDDING`.
2. Validate credentials.
3. Reject non-embedding model types unless the selected schema is wildcard and resolves to text embedding.
4. Normalize single-string input into a list.
5. Reject fallback embedding models whose `embedding_size` differs from the primary model.
6. Reject blacklisted request-level proxy URLs.
7. Batch inputs using the model property's `max_batch_size`, run batches in chunks of up to 20 concurrent tasks, and merge outputs in order.
8. Normalize nonzero embedding vectors to unit length before returning them.

### Response behavior

Returns `status`, `data` as a list of `{index, embedding}`, `usage.input_tokens`, and optional `fallback_index`.

## POST /v1/rerank

Use for reranking documents against a query.

### Request fields

| Field | Required | Meaning |
|---|---|---|
| `model_schema_id` | Yes | Rerank model schema id. |
| `provider_model_id` | Sometimes | Required when schema does not fix a provider model id. |
| `query` | Yes | Query text. |
| `documents` | Yes | List of document strings. |
| `top_n` | Yes | Number of ranked results to return. |
| `credentials` / `encrypted_credentials` | No | Same mutually-exclusive credential rule as chat completion. |
| `proxy` | No | Must be HTTPS and pass blacklist checks. |
| `custom_headers` | No | Optional provider request headers. |

### Validation and execution order

1. Validate model schema as `ModelType.RERANK`.
2. Validate credentials.
3. Reject non-rerank model types unless wildcard resolution produced rerank.
4. Reject blacklisted proxy URLs.
5. Obtain the provider rerank adapter and call it with query, documents, `top_n`, credentials, proxy, and custom headers.
6. Compute token usage from query, documents, and returned document texts.

Rerank has no fallback-list behavior in the source-backed route.

## Credential validation routes

### POST /v1/verify_provider_credentials

Hidden from OpenAPI schema. Use when validating provider-level credentials and returning encrypted credentials for later storage.

Input: `provider_id`, optional `credentials`, optional `encrypted_credentials`.

Behavior:

1. Load provider metadata by `provider_id`.
2. If `pass_provider_level_credential_check` is true, only validate required/allowed credential fields, encrypt them, and return `{provider_id, encrypted_credentials}`. No provider API call is made.
3. Otherwise, build a default `model_schema_id` from provider id and the provider's default credential verification model id/type.
4. Validate model info and credentials.
5. Make a lightweight provider call according to default type:
   - chat: prompt `Only say your name` with `max_tokens=10`;
   - embedding: embed `Hello`;
   - rerank: query `skin` against one document.
6. Encrypt credentials and return provider id, model schema id, provider model id, model type, properties, and encrypted credentials.

### POST /v1/verify_credentials

Hidden from OpenAPI schema. Use when validating a specific model/schema/credential combination.

Input: `model_schema_id`, optional `provider_model_id`, optional `properties`, optional `configs`, optional `model_type`, optional `credentials`, optional `encrypted_credentials`, optional `proxy`, optional `custom_headers`.

Behavior:

1. Validate model info and resolve wildcard schemas to a concrete model type.
2. Validate credentials.
3. Reject blacklisted proxy URLs.
4. Run a model-type-specific lightweight provider call:
   - chat: validate stream/function/vision/config support, then call with `Only say your name` or a function-call prompt when function-call behavior must be tested;
   - text embedding: embed `Hello` and require returned vector length to match `properties.embedding_size`;
   - rerank: query `skin` against one document.
5. Encrypt credentials and return resolved provider/model/type/properties and encrypted credentials.

## Proxy, custom headers, and URL blacklist

- Request-level `proxy` is a provider API URL override in provider adapters, not the deployment's global outbound proxy. Deployment-level outbound proxy configuration belongs to `../deployment-configuration/`.
- Request-level `proxy` must start with `https://` in provider adapters.
- The route layer rejects request-level `proxy` values that contain a configured provider URL blacklist substring.
- `custom_host` also checks its credential endpoint URL against the same blacklist before calling the endpoint.
- Text embedding for `custom_host` additionally requires the endpoint URL to start with `http://` or `https://`.
- `custom_headers` are merged into provider request headers by adapters that accept them. Catalog flags `enable_custom_headers` and `enable_proxy` guide clients/UI, but route schemas expose these fields broadly.

## Error code decision points

| Error code | Typical status | Common inference causes |
|---|---:|---|
| `REQUEST_VALIDATION_ERROR` | 422 | Unknown/missing provider model id, missing required credentials, both plaintext and encrypted credentials, invalid encrypted credential format, wildcard embedding missing `embedding_size`, model type mismatch, invalid/blacklisted proxy or custom-host URL, unsupported function/vision/stream/config choice. |
| `PROVIDER_ERROR` | 400 | Upstream provider rejects credentials, quota/rate-limit/content-filter error surfaced by adapter, invalid API key at provider, provider response is malformed/empty after a valid local request shape. |
| `CREDENTIALS_VALIDATION_ERROR` | 401 | Verification-specific generic failure or a verification response that does not contain the expected chat content/function call or embedding size. Source routes preserve many provider/request validation errors instead of converting them to this code. |
| `OBJECT_NOT_FOUND` | 404 | Unknown provider id, model schema id, or unsupported model property schema type. |
| `INTERNAL_SERVER_ERROR` / `UNKNOWN_ERROR` | 500 | Missing model info, unhandled provider adapter exception, or unexpected streaming failure. |

For diagnosis steps, use [troubleshooting.md](troubleshooting.md).
