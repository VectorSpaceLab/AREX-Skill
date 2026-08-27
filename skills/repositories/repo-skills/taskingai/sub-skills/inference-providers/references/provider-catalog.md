# Provider and Model Catalog

This reference distills TaskingAI inference provider/model schema behavior for future operating use. It is self-contained; if a user supplies a newer TaskingAI source tree, compare it with the bundled static helper rather than reading or running source scripts.

## Catalog loading model

- Provider directories are discovered by provider id, using lowercase alphanumeric/underscore ids that do not start with `template`.
- Provider metadata comes from each provider's `provider.yml`: `provider_id`, localized name/description keys, `credentials_schema`, documentation/resource URLs, proxy/header flags, token-usage flags, and credential-verification defaults.
- Model schemas come from provider model YAML files. Each schema has `model_schema_id`, `provider_model_id` when the concrete provider model is fixed, `type`, optional `properties`, config schema ids, pricing, and deprecation state.
- The inference service builds in-memory provider and model-schema caches at startup. Catalog endpoints return serialized cache data, not live provider API discovery.
- `ALLOWED_PROVIDERS` can restrict loaded providers, and the debug provider is omitted in production mode. Full deployment/env behavior is owned by `../deployment-configuration/`.
- Provider icon URLs are generated from the image URL prefix and served through the inference image route; icon file serving details are in [api-reference.md](api-reference.md#provider-icon-route).

## Verified catalog snapshot

The verified static snapshot contains 35 providers and 196 model schema files:

| Model type | Count | Use |
|---|---:|---|
| `chat_completion` | 131 | Chat messages, streaming, function/tool calls, optional vision inputs. |
| `text_embedding` | 39 | Text embeddings; routes normalize output vectors and enforce fallback embedding-size equality. |
| `rerank` | 9 | Query/document reranking; source catalog includes Cohere and Jina rerank models. |
| `wildcard` | 17 | Provider-compatible schemas where callers must supply `provider_model_id` and often `model_type`/`properties`. |

The only valid `ModelType` values are `chat_completion`, `text_embedding`, `rerank`, and `wildcard`.

## Provider summary table

`schema counts` are `chat / embed / rerank / wildcard`. `provider-level check` means `verify_provider_credentials` returns encrypted credentials after schema loading instead of making a provider call.

| Provider | Schema counts | Required credential keys | Provider-level check | Default verification when model call is required | Notes |
|---|---:|---|---|---|---|
| `ai21` | 1 / 1 / 0 / 0 | `AI21_API_KEY` | No | `chat_completion` `j2-ultra` | Hosted chat and embedding. |
| `anthropic` | 7 / 0 / 0 / 1 | `ANTHROPIC_API_KEY` | No | `chat_completion` `claude-3-sonnet` | Proxy/custom headers enabled; token usage returned. |
| `aws_bedrock` | 11 / 2 / 0 / 0 | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` | No | `chat_completion` `anthropic/claude-v2.1` | Provider model ids include Bedrock-style provider/model names. |
| `azure_openai` | 8 / 1 / 0 / 0 | `AZURE_OPENAI_RESOURCE_NAME`, `AZURE_OPENAI_DEPLOYMENT_ID`, `AZURE_OPENAI_API_KEY` | No | `chat_completion` `gpt-3.5-turbo` | Proxy/custom headers enabled; deployment id is credential-level. |
| `baichuan` | 5 / 1 / 0 / 0 | `BAICHUAN_API_KEY` | No | `chat_completion` `baichuan3-turbo` | Hosted chat and embedding. |
| `cohere` | 6 / 6 / 4 / 0 | `COHERE_API_KEY` | No | `chat_completion` `command` | Covers all three non-wildcard model types. |
| `custom_host` | 2 / 1 / 0 / 0 | `CUSTOM_HOST_ENDPOINT_URL`, `CUSTOM_HOST_MODEL_ID`, `CUSTOM_HOST_API_KEY` | No | `chat_completion` `openai-function-call` | Arbitrary OpenAI-compatible endpoint; endpoint URL and actual model id are credentials. |
| `debug` | 5 / 6 / 0 / 1 | `DEBUG_API_KEY` | No | `chat_completion` `debug-chat-completion` | Development/testing provider; omitted in production mode. |
| `deepseek` | 2 / 0 / 0 / 0 | `DEEPSEEK_API_KEY` | No | `chat_completion` `deepseek-chat` | Hosted chat provider. |
| `fireworks` | 0 / 2 / 0 / 1 | `FIREWORKS_API_KEY` | No | `text_embedding` `gte-base` | Embedding plus wildcard provider. |
| `google_gemini` | 5 / 1 / 0 / 1 | `GOOGLE_GEMINI_API_KEY` | No | `chat_completion` `gemini-1.0-pro` | Proxy/custom headers enabled; chat, vision-era schemas, embedding, wildcard. |
| `groq` | 6 / 0 / 0 / 1 | `GROQ_API_KEY` | No | `chat_completion` `gemma-7b` | Proxy/custom headers enabled; hosted OpenAI-compatible chat. |
| `hugging_face` | 0 / 0 / 0 / 1 | `HUGGING_FACE_API_KEY` | Yes | None | Wildcard provider; provider-level verification is schema-only. |
| `hugging_face_inference_endpoint` | 0 / 0 / 0 / 1 | `HUGGING_FACE_API_KEY`, `HUGGING_INFERENCE_ENDPOINT_URL` | Yes | None | Wildcard endpoint URL credential. |
| `jina` | 0 / 8 / 5 / 0 | `JINA_API_KEY` | No | `rerank` `jina-reranker-v1-base-en` | Embedding and rerank; no chat schemas. |
| `leptonai` | 11 / 0 / 0 / 0 | `LEPTONAI_API_KEY` | No | `chat_completion` `gemma-7b` | Hosted chat models. |
| `llama_api` | 0 / 0 / 0 / 1 | `LLAMA_API_API_KEY` | Yes | None | Hosted wildcard provider. |
| `lm_studio` | 0 / 0 / 0 / 1 | `LM_STUDIO_HOST` | Yes | None | Local OpenAI-compatible server; host credential, caller supplies model id. |
| `localai` | 0 / 0 / 0 / 1 | `LOCALAI_HOST` | Yes | None | Local OpenAI-compatible server; host credential, caller supplies model id. |
| `minimax` | 6 / 0 / 0 / 0 | `MINIMAX_API_KEY` | No | `chat_completion` `abab5.5-chat` | Hosted chat provider. |
| `mistralai` | 8 / 1 / 0 / 1 | `MISTRAL_API_KEY` | No | `chat_completion` `open-mistral-7b` | Hosted chat, embedding, wildcard. |
| `moonshot` | 3 / 0 / 0 / 0 | `MOONSHOT_API_KEY` | No | `chat_completion` `moonshot-v1-8k` | Hosted chat provider. |
| `ollama` | 0 / 0 / 0 / 1 | `OLLAMA_HOST` | Yes | None | Local OpenAI-compatible server; host credential, caller supplies model id. |
| `openai` | 7 / 5 / 0 / 1 | `OPENAI_API_KEY` | No | `chat_completion` `gpt-4o-mini` | Named OpenAI schemas plus wildcard; proxy/custom headers enabled. |
| `openrouter` | 0 / 0 / 0 / 1 | `OPENROUTER_API_KEY` | Yes | None | Hosted router wildcard; provider-level verification is schema-only. |
| `reka` | 3 / 0 / 0 / 0 | `REKA_API_KEY` | No | `chat_completion` `reka-flash` | Hosted chat provider. |
| `replicate` | 0 / 0 / 0 / 1 | `REPLICATE_API_KEY` | Yes | None | Hosted wildcard provider. |
| `sensetime` | 6 / 1 / 0 / 0 | `SENSETIME_ACCESS_KEY_ID`, `SENSETIME_SECRET_ACCESS_KEY` | No | `chat_completion` `sensechat` | Hosted chat and embedding. |
| `siliconcloud` | 0 / 0 / 0 / 1 | `SILICONCLOUD_API_KEY` | Yes | None | Hosted wildcard provider. |
| `togetherai` | 4 / 0 / 0 / 1 | `TOGETHERAI_API_KEY` | No | `chat_completion` `meta-llama/Llama-2-70b-chat-hf` | Proxy/custom headers enabled; one source filename contains a space but schema id is normal. |
| `tongyi` | 5 / 2 / 0 / 0 | `TONGYI_API_KEY` | No | `chat_completion` `qwen-turbo` | Hosted chat and embedding. |
| `volcengine` | 6 / 0 / 0 / 0 | `VOLCENGINE_API_KEY`, `VOLCENGINE_ENDPOINT_ID` | No | `chat_completion` `doubao-lite-4k` | Endpoint id is required credential. |
| `wenxin` | 4 / 0 / 0 / 0 | `WENXIN_API_KEY`, `WENXIN_SECRET_KEY` | No | `chat_completion` `ernie-bot` | Hosted chat provider. |
| `yi` | 7 / 0 / 0 / 0 | `YI_API_KEY` | No | `chat_completion` `yi-spark` | Hosted chat provider. |
| `zhipu` | 3 / 1 / 0 / 0 | `ZHIPU_API_KEY` | No | `chat_completion` `glm-3-turbo` | Hosted chat and embedding. |

## Provider selection guidance

### Named hosted provider

Choose the named provider when the model belongs to a TaskingAI schema already present in the catalog, when credentials are provider-specific, or when provider adapters translate TaskingAI messages/configs to non-OpenAI APIs. Examples include Anthropic, AWS Bedrock, Google Gemini, Cohere, Jina, Tongyi, and Zhipu.

### Hosted OpenAI-compatible provider or router

Use an existing hosted OpenAI-compatible provider when the catalog has a provider adapter or wildcard that matches the user's account and routing expectations:

- `openai`: named OpenAI schemas plus `openai/wildcard`.
- `groq`, `deepseek`, `moonshot`, and similar named providers: prefer them when TaskingAI has provider-specific credentials and schema ids.
- `openrouter`, `llama_api`, `siliconcloud`, `replicate`, `fireworks/wildcard`, `mistralai/wildcard`, or `togetherai/wildcard`: use when the provider's router owns the actual model id and the caller can supply `provider_model_id`.

### `custom_host`

Use `custom_host` for an arbitrary OpenAI-compatible HTTP endpoint that is not better represented by a named provider. Important distinctions:

- TaskingAI model schema ids are `custom_host/openai-function-call`, `custom_host/openai-tool-calls`, and `custom_host/openai-text-embedding`.
- The actual provider model name is credential field `CUSTOM_HOST_MODEL_ID`, not the TaskingAI `provider_model_id`.
- `CUSTOM_HOST_ENDPOINT_URL` is the exact provider API endpoint; for chat it must point at the compatible chat-completions endpoint, and for embeddings it must point at the compatible embeddings endpoint.
- The endpoint URL is checked against the provider URL blacklist. Text embedding also requires the endpoint to start with `http://` or `https://`; proxy override still must be HTTPS.
- Use `openai-tool-calls` for providers that support modern OpenAI `tools`; use `openai-function-call` for legacy OpenAI-style function-call payloads.

### Ollama, LM Studio, and LocalAI

Use `ollama`, `lm_studio`, or `localai` when the user is running a local OpenAI-compatible server and wants TaskingAI to call it directly.

- These are wildcard schemas with provider-level credential checks, so `verify_provider_credentials` only validates/encrypts host credentials.
- Required credential is only the host (`OLLAMA_HOST`, `LM_STUDIO_HOST`, or `LOCALAI_HOST`). The caller supplies the actual local model name as `provider_model_id`.
- Chat adapters append the OpenAI-compatible route path to the host. Embedding adapters use the corresponding embeddings path when implemented.
- Prefer these over `custom_host` when the local runtime matches one of these supported providers and host-only configuration is enough. Prefer `custom_host` when the endpoint path, API key, or function-call flavor must be controlled explicitly.

## Wildcard schema rules

Wildcard schemas are flexible but require more caller responsibility:

- `model_schema_id` names the wildcard schema, such as `openai/wildcard` or `ollama/wildcard`.
- `provider_model_id` must be supplied unless the schema itself maps to a concrete provider model.
- `model_type` is required during validation when the wildcard schema cannot infer it.
- Text embedding wildcard calls need `properties.embedding_size`; otherwise model-info validation raises `REQUEST_VALIDATION_ERROR`.
- For chat wildcard/custom-host verification, properties such as `streaming`, `function_call`, and `vision` determine which validation prompt is used and whether streaming/function-call checks are expected.

## Credential semantics

- Credential fields are exactly the keys declared in the provider `credentials_schema`.
- Each request accepts either plaintext `credentials` or `encrypted_credentials`, not both.
- Missing required credential fields produce request-validation failures before provider calls.
- Encrypted credentials are decrypted locally; invalid encrypted values produce request-validation failures.
- Provider-level credential verification is schema-only when `pass_provider_level_credential_check` is true. This is common for local/wildcard/router providers where there is no safe default provider call.
- When provider-level verification is not schema-only, provider metadata chooses a default model type and default provider model id for a lightweight real call.

## Static catalog inspection helper

Use [../scripts/inspect_inference_catalog.py](../scripts/inspect_inference_catalog.py) when a user supplies a TaskingAI source tree and you need a no-network, no-credential catalog diff. The helper reports provider count, model type counts, required credential keys, wildcard schemas, duplicate ids, missing icons, and route decorator facts without importing provider code or calling providers.
