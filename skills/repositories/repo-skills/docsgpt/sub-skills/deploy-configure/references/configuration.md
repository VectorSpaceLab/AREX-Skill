# Configuration

DocsGPT settings are environment-driven through Pydantic. Use a root `.env` for development and platform secrets/config in production. Restart processes after changing startup configuration.

## Core groups

| Concern | Main settings | Notes |
|---|---|---|
| LLM | `LLM_PROVIDER`, `LLM_NAME`, `API_KEY`, provider-specific keys, `OPENAI_BASE_URL` | provider-specific keys allow multiple providers; model catalog resolves capabilities |
| embeddings | `EMBEDDINGS_NAME`, `EMBEDDINGS_BASE_URL`, `EMBEDDINGS_KEY`, `EMBEDDINGS_MAX_INPUT_TOKENS` | setting a remote base URL avoids loading a local sentence-transformer |
| model catalog | `MODELS_CONFIG_DIR` | operator YAMLs load after built-ins; later duplicate model id wins |
| data | `POSTGRES_URI`, `AUTO_CREATE_DB`, `AUTO_MIGRATE` | canonical user-data store |
| Redis/Celery | `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, visibility/prefetch/recycle settings | keep web and worker values aligned |
| vector store | `VECTOR_STORE` plus backend-specific settings | supported keys: `faiss`, `elasticsearch`, `mongodb`, `qdrant`, `milvus`, `pgvector` |
| retrieval | `RETRIEVERS_ENABLED`, `PER_SOURCE_RETRIEVAL_ENABLED`, GraphRAG settings | source config can narrow behavior; instance allow-list still applies |
| auth | `AUTH_TYPE`, `JWT_SECRET_KEY`, OIDC/SCIM/RBAC settings | `LOCAL_MODE_ADMIN` is only safe in local no-auth mode |
| storage | `STORAGE_TYPE`, `S3_*`, `URL_STRATEGY` | `backend` proxies files; `s3` can expose direct object URLs |
| speech | `STT_PROVIDER`, `OPENAI_STT_MODEL`, limits/language; `TTS_PROVIDER`, ElevenLabs key | `faster_whisper` is optional |
| realtime | `ENABLE_SSE_PUSH`, replay limits, keepalive, concurrency budgets | Redis and proxy behavior matter |
| sandbox | `SANDBOX_BACKEND`, `SANDBOX_*`, `DAYTONA_*`, artifact quotas | runner is external to web app |

## Model catalog schema

A custom OpenAI-compatible provider needs one YAML per logical endpoint:

```yaml
provider: openai_compatible
display_provider: example
api_key_env: EXAMPLE_API_KEY
base_url: https://api.example.com/v1
defaults:
  supports_tools: true
  supports_structured_output: true
  supports_streaming: true
  context_window: 128000
models:
  - id: example-large
    display_name: Example Large
```

Important rules:

- `id` is the persisted registry key. Do not rename an id in use.
- `upstream_model_id` can point several registry ids at one provider model.
- `api_flavor` is `chat_completions` or `responses`.
- `reasoning_effort` accepts `none`, `minimal`, `low`, `medium`, `high`, or `xhigh`, but a model may support only a subset.
- attachments can use aliases `image`, `pdf`, `audio` or raw MIME types.
- unknown top-level keys, missing ids, unknown aliases, or unregistered provider values fail strict startup validation.
- a missing `MODELS_CONFIG_DIR` logs a warning and falls back to built-ins; malformed YAML in an existing directory fails startup.

Use `scripts/validate_model_catalog.py` before mounting a directory. Provider connectivity and model entitlement still require a live test through the application.

## Local OpenAI-compatible model example

```env
LLM_PROVIDER=openai
LLM_NAME=local-model
OPENAI_BASE_URL=http://host.docker.internal:11434/v1
API_KEY=None
```

The hostname differs between host, container, and Kubernetes networks. Prove connectivity from the web and worker processes, not only from the developer shell.

## Configuration safety

- Never print `Settings.model_dump()` unredacted in production.
- Keep `INTERNAL_KEY`, encryption/JWT secrets, provider keys, OAuth secrets, SCIM token, S3 credentials, and sandbox tokens out of logs.
- `ENCRYPTION_SECRET_KEY` must not remain at an insecure default on a real deployment.
- Validate lists/booleans as Pydantic expects; environment parsers may require JSON-like list syntax rather than comma-separated text for list fields.
- Use public browser URLs for redirects and endpoint references, internal service URLs for east-west traffic.
