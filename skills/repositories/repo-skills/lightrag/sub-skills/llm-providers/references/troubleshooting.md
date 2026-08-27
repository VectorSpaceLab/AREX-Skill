# LLM Provider Troubleshooting

Use this guide for LightRAG provider failures that do not require calling a live service. Do not run live LLM, embedding, VLM, or rerank calls unless the user explicitly supplies credentials/services and asks for that validation.

## Quick Triage

| Symptom | Likely area | First check | Route if outside this sub-skill |
| --- | --- | --- | --- |
| `401`, `403`, auth, or credential error | Provider auth | Correct provider-specific key source and role override inheritance. | API server env mechanics: `../../api-server/SKILL.md` |
| Connection refused, timeout, DNS, bad gateway | Service URL | `*_BINDING_HOST` or `RERANK_BINDING_HOST` points to the intended service and path. | Deployment/network setup: `../../api-server/SKILL.md` |
| Vector dimension mismatch | Embedding/storage contract | `EmbeddingFunc.embedding_dim`, provider output dimension, and stored vectors match. | Rebuild/clear vectors: `../../storage-backends/SKILL.md` |
| Prefix/asymmetric config error | Embedding semantics | `EMBEDDING_ASYMMETRIC`, provider mode, and prefix variables are compatible. | Storage rebuild planning: `../../storage-backends/SKILL.md` |
| VLM ignores images or fails payload validation | VLM image path | `VLM_PROCESS_ENABLE`, effective `vlm` role binding, and `image_inputs` shape. | Parser multimodal orchestration: `../../document-pipeline/SKILL.md` |
| Rerank has no effect | Rerank setup | `rerank_model_func` is configured and `QueryParam(enable_rerank=True)` is set. | Core query behavior: `../../core-rag/SKILL.md` |
| Old answers after provider tuning | Cache identity | Cache identity changed only for role/binding/model/host, not provider options. | Cache deletion/vector lifecycle: `../../storage-backends/SKILL.md` |

## Credentials and Service URLs

| Provider | Common mistake | Fix |
| --- | --- | --- |
| OpenAI-compatible | Base URL points at a chat endpoint instead of API root, or a proxy rejects unsupported OpenAI options. | Use a base URL expected by the SDK/proxy and remove incompatible provider options for that endpoint. |
| Azure OpenAI | OpenAI-style model name used where Azure deployment name is expected. | Use Azure deployment names and set the Azure API version through the supported process/config field. |
| Ollama | `LLM_BINDING_HOST` is unset for a non-default local service, or a cloud model needs bearer auth. | Set the explicit service URL and bearer key only when required by the service. |
| Gemini | AI Studio and Vertex AI modes are mixed. | Use API-key mode or Vertex process-level configuration consistently; `DEFAULT_GEMINI_ENDPOINT` lets the SDK choose. |
| Bedrock | Generic `LLM_BINDING_API_KEY`, `EMBEDDING_BINDING_API_KEY`, or role API key is set. | Use AWS SigV4 env fields or `AWS_BEARER_TOKEN_BEDROCK`; role Bedrock bindings cannot use `{ROLE}_LLM_BINDING_API_KEY`. |
| Jina/Cohere/Aliyun rerank | `RERANK_BINDING_API_KEY` is missing and provider-specific fallback env is unset. | Set the provider-specific key or `RERANK_BINDING_API_KEY`; keep the endpoint compatible with the chosen response format. |
| VoyageAI | Optional package or key is missing. | Install provider extras and provide `VOYAGE_API_KEY` or `VOYAGEAI_API_KEY`. |

Keep secrets out of reusable examples, logs, generated skills, and cache keys. Use placeholders such as `<secret>` in documentation.

## Role Override Pitfalls

- Unknown role ids fail early; valid role ids are `extract`, `keyword`, `query`, and `vlm`.
- Same-provider role overrides inherit base model, host, API key, timeout, max async, and provider options unless a role-specific value overrides them.
- Cross-provider role overrides require a role model and, for non-Bedrock providers, a role API key. They do not inherit base provider options.
- Bedrock roles use `{ROLE}_AWS_*` fields, global AWS fields, or process-level bearer token; setting `{ROLE}_LLM_BINDING_API_KEY` for Bedrock is invalid.
- `get_llm_role_config()` is safe for observability because it strips secret-like metadata keys; missing secrets there does not prove the runtime lacks credentials.

## Async Cleanup and Runtime Updates

| Situation | Recommendation |
| --- | --- |
| Updating role kwargs/function in a script | `update_llm_role_config()` is acceptable, but queued calls on the old wrapper may finish in the background. |
| Updating roles inside an async service | Prefer `await aupdate_llm_role_config(...)` so the retired queue drains or is force-cancelled deterministically. |
| Sync update called without a running loop | LightRAG logs that retired queue cleanup is skipped. Use async update if deterministic cleanup is required. |
| Updating binding/model/host/api key/provider options | Register a role LLM builder first, or pass `model_func` directly; otherwise metadata-only updates fail. |
| Failed runtime update | The previous wrapped function and metadata are restored. Inspect the raised exception rather than assuming a partial switch. |

## Asymmetric Prefix Errors

Asymmetric embedding is disabled unless `EMBEDDING_ASYMMETRIC=true`.

| Configuration | Result |
| --- | --- |
| Prefix variables set while `EMBEDDING_ASYMMETRIC` is unset/false | Prefixes are ignored with a warning. |
| `EMBEDDING_ASYMMETRIC=true` with `jina`, `gemini`, or `voyageai` | Provider task/input-type parameters are used; prefix variables are ignored with a warning. |
| `EMBEDDING_ASYMMETRIC=true` with `openai`, `azure_openai`, or `ollama` and both prefix variables configured | Text prefix mode is used. |
| Prefix mode with only one prefix variable configured | Configuration error. Use `NO_PREFIX` for the intentionally empty side. |
| Prefix mode with both prefixes empty or both `NO_PREFIX` | Configuration error; at least one side must be non-empty. |
| `EMBEDDING_ASYMMETRIC=true` with unsupported bindings | Configuration error. |

Changing asymmetric mode, prefixes, provider task behavior, embedding model, or dimension changes vector semantics. Plan vector rebuilds with `../../storage-backends/SKILL.md`.

## Embedding Dimension and Cache Identity

- `EmbeddingFunc` validates that returned vectors can be reshaped by `embedding_dim` and that vector count matches input text count.
- Server `EMBEDDING_DIM` defaults to provider metadata when unset; dynamic-dimension providers can receive dimensions depending on binding and `EMBEDDING_SEND_DIM` behavior.
- Existing vector data is not automatically compatible with a new provider, model, dimension, or asymmetric configuration.
- LLM cache identity includes role, binding, model, and host. It excludes API keys and provider options to avoid secret leakage.
- Changing provider options such as temperature, reasoning effort, extra body, or timeout may reuse old cached answers if role/binding/model/host stay the same. Disable or clear relevant cache entries only through the storage/cache workflow.

## Optional Dependencies

Some providers import optional packages only when used, while others may fail at import time if optional extras are absent. Treat missing package errors as provider availability issues, not as proof the LightRAG core install is broken.

| Area | Typical optional dependency need |
| --- | --- |
| Local Hugging Face | Transformers/model/tokenizer stack and local model resources. |
| Gemini | Google GenAI package and credentials. |
| VoyageAI | `voyageai` package and key. |
| Bedrock | AWS SDK credentials/runtime support. |
| LlamaIndex | LlamaIndex objects and selected provider packages. |
| Observability | Optional tracing/export packages when enabled. |

Use the bundled `../scripts/check_llm_symbols.py` to distinguish missing public symbols from missing optional provider packages without contacting services.

## VLM Image Input and Cache Issues

- `image_inputs` may be raw base64 strings, data URLs, or dicts with `base64` plus optional metadata.
- Dict inputs without `base64`, invalid base64 strings, unsupported item types, or empty decoded bytes fail before provider calls.
- The normalizer derives MIME type, digest, byte count, and dimensions when possible. PNG, JPEG, GIF, and WebP dimensions are recognized when headers are available.
- Cache identity for VLM includes normalized image content metadata but deliberately excludes source identifiers such as file path/source id, so identical bytes can share cache across different sources.
- Do not store raw base64 in reusable docs or audit notes. Keep image payload checks synthetic and tiny.
- If the pipeline never invokes VLM, confirm `VLM_PROCESS_ENABLE=true` and the effective `vlm` role binding supports image inputs. Parser-side multimodal routing belongs to `../../document-pipeline/SKILL.md`.

## Rerank Pitfalls

- `QueryParam(enable_rerank=True)` does not create a rerank function; it only permits reranking when `rerank_model_func` is configured.
- `RERANK_BINDING=null` disables server rerank even if query params request it.
- Rerank functions should return `{ "index": int, "relevance_score": float }` entries pointing at original input documents.
- Cohere chunking aggregates chunk scores back to original document indices and applies `top_n` after aggregation.
- `min_rerank_score` can filter out chunks after scoring; low recall may be threshold-related rather than provider failure.
- Rerank endpoints differ by provider. Aliyun uses a different request/response envelope from Jina/Cohere.
- Rerank queue settings are independent from role LLM queue settings: use `MAX_ASYNC_RERANK` and `RERANK_TIMEOUT`.

## Safe Checks

Run from this sub-skill directory:

```bash
python scripts/check_llm_symbols.py
python scripts/check_llm_symbols.py --json
```

The script imports modules and inspects symbols only. It does not call provider services, read credentials, create storages, mutate vector data, or require external project files.
