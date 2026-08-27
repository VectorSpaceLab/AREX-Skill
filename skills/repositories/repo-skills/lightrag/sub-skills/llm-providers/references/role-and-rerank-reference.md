# Role and Rerank Reference

LightRAG routes LLM work through role-specific wrappers, even when every role uses the same base provider. Rerank has a separate function, timeout, and queue from LLM roles.

## Role Registry

| Role id | Env prefix | Main responsibility | Recommended model shape |
| --- | --- | --- | --- |
| `extract` | `EXTRACT` | Ingestion-stage entity/relation extraction and summarization. | Capable model with enough context for source chunks and extraction prompts. |
| `keyword` | `KEYWORD` | Query-stage high/low-level keyword extraction before retrieval. | Cheap, low-latency model with reliable structured output. |
| `query` | `QUERY` | Final answer generation from retrieved context. | Strongest answer-quality model; tune context and reasoning as needed. |
| `vlm` | `VLM` | Image analysis during multimodal ingestion. | Vision-capable model when VLM processing is enabled. |

If a role has no dedicated configuration, it inherits base LLM behavior. Role wrappers are independent and have separate queues/concurrency limits.

## Embedded Role Configuration

Use `RoleLLMConfig` for embedded Python code:

```python
from lightrag import LightRAG, RoleLLMConfig

rag = LightRAG(
    llm_model_func=base_llm,
    embedding_func=embedding_func,
    role_llm_configs={
        "keyword": RoleLLMConfig(func=fast_llm, kwargs={"temperature": 0.0}, max_async=8, timeout=60),
        "query": RoleLLMConfig(func=strong_llm, kwargs={"temperature": 0.2}, max_async=2, timeout=240),
    },
)
```

Dict form is accepted and normalized to `RoleLLMConfig`. Unknown role keys raise `ValueError`; common typo failures include `qurey` instead of `query`.

`RoleLLMConfig` fields:

| Field | Meaning |
| --- | --- |
| `func` | Raw async callable for the role. If unset, inherits base `llm_model_func`. |
| `kwargs` | Role-specific kwargs injected by the wrapper. If `None`, inherits base `llm_model_kwargs` unless metadata marks the role as cross-provider. |
| `max_async` | Role queue concurrency. If unset, inherits base `llm_model_max_async` or role env defaults in API/server usage. |
| `timeout` | Role timeout. If unset, inherits `default_llm_timeout`. |
| `metadata` | Non-call provider identity and builder context such as binding, model, host, provider options, and cross-provider state. Secrets are stripped from public snapshots/logs. |

## API/Server Role Overrides

Each role may override provider, model, host, API key, concurrency, timeout, and provider options:

```env
QUERY_LLM_BINDING=openai
QUERY_LLM_MODEL=<strong-chat-model>
QUERY_LLM_BINDING_HOST=<openai-compatible-base-url>
QUERY_LLM_BINDING_API_KEY=<secret>
QUERY_MAX_ASYNC_LLM=2
QUERY_LLM_TIMEOUT=240
QUERY_OPENAI_LLM_REASONING_EFFORT=medium
```

Variable pattern:

| Variable | Effect |
| --- | --- |
| `{ROLE}_LLM_BINDING` | Role provider override. |
| `{ROLE}_LLM_MODEL` | Role model/deployment name. |
| `{ROLE}_LLM_BINDING_HOST` | Role endpoint/base URL. |
| `{ROLE}_LLM_BINDING_API_KEY` | Role API key for non-Bedrock providers. |
| `{ROLE}_MAX_ASYNC_LLM` | Role queue concurrency. |
| `{ROLE}_LLM_TIMEOUT` | Role request timeout. |
| `{ROLE}_{PROVIDER_PREFIX}_{FIELD}` | Provider-specific option override. |
| `{ROLE}_AWS_REGION`, `{ROLE}_AWS_ACCESS_KEY_ID`, `{ROLE}_AWS_SECRET_ACCESS_KEY`, `{ROLE}_AWS_SESSION_TOKEN` | Role-level Bedrock SigV4 settings. |

### Same-Provider Overrides

When a role's binding is unset or equals the base `LLM_BINDING`:

- Role model inherits `LLM_MODEL` when unset.
- Role host inherits `LLM_BINDING_HOST` when unset.
- Role API key inherits `LLM_BINDING_API_KEY` when unset.
- Role timeout inherits `LLM_TIMEOUT` when unset.
- Role max async inherits `MAX_ASYNC_LLM` when unset.
- Provider options start from base provider options and then overlay role-specific provider options.

Use this when only changing model strength or provider options:

```env
LLM_BINDING=openai
LLM_MODEL=<balanced-chat-model>
LLM_BINDING_HOST=<openai-compatible-base-url>
LLM_BINDING_API_KEY=<secret>
OPENAI_LLM_REASONING_EFFORT=minimal

KEYWORD_LLM_MODEL=<fast-keyword-model>
KEYWORD_MAX_ASYNC_LLM=8
KEYWORD_LLM_TIMEOUT=30
KEYWORD_OPENAI_LLM_REASONING_EFFORT=minimal

QUERY_LLM_MODEL=<strong-chat-model>
QUERY_MAX_ASYNC_LLM=2
QUERY_LLM_TIMEOUT=240
QUERY_OPENAI_LLM_REASONING_EFFORT=medium
```

### Cross-Provider Overrides

When `{ROLE}_LLM_BINDING` differs from base `LLM_BINDING`:

- `{ROLE}_LLM_MODEL` is required.
- Non-Bedrock roles require `{ROLE}_LLM_BINDING_API_KEY`.
- If role host is unset, LightRAG uses that provider's default host when available.
- Provider options do not inherit base provider options; only role-specific options are applied.

Example: local base/extraction with OpenAI-compatible final answers:

```env
LLM_BINDING=ollama
LLM_MODEL=<local-chat-model>
LLM_BINDING_HOST=<ollama-or-compatible-url>
OLLAMA_LLM_NUM_CTX=32768

QUERY_LLM_BINDING=openai
QUERY_LLM_MODEL=<answer-model>
QUERY_LLM_BINDING_HOST=<openai-compatible-base-url>
QUERY_LLM_BINDING_API_KEY=<secret>
QUERY_OPENAI_LLM_REASONING_EFFORT=minimal
```

## Bedrock Role Rules

Bedrock does not use generic LightRAG API-key fields:

- Do not set `LLM_BINDING_API_KEY` for Bedrock base auth.
- Do not set `{ROLE}_LLM_BINDING_API_KEY` for a Bedrock role.
- Use global AWS SigV4 env vars, role-specific `{ROLE}_AWS_*` env vars, or process-level `AWS_BEARER_TOKEN_BEDROCK`.
- `AWS_BEARER_TOKEN_BEDROCK` is process-level and cannot be overridden per role.
- `DEFAULT_BEDROCK_ENDPOINT`, empty endpoint, or `None` lets the AWS SDK select the default regional endpoint.

## Runtime Role Updates

`LightRAG` exposes runtime update APIs:

| Method | Behavior |
| --- | --- |
| `update_llm_role_config(role, ...)` | Rebuilds the role wrapper and schedules old queue cleanup if an event loop is running. If no running event loop exists, cleanup is skipped with a warning. |
| `aupdate_llm_role_config(role, ...)` | Rebuilds the role wrapper and awaits graceful shutdown of the retired queue, then force-cancels after the bounded queue-drain timeout. |
| `wait_for_retired_llm_queues()` | Waits for scheduled cleanup tasks from prior sync updates. |
| `register_role_llm_builder(builder)` | Required when runtime updates change provider metadata such as binding/model/host/api key unless `model_func` is supplied directly. |
| `set_role_llm_metadata(role, **metadata)` | Stores metadata used by future builder-driven updates. |
| `get_llm_role_config(role=None)` | Returns sanitized runtime role config snapshots. Secret-like fields are stripped. |
| `get_llm_queue_status(include_base=True)` | Returns queue status for each role; `include_base` is kept for compatibility and does not add a base entry. |
| `get_embedding_queue_status()` | Returns queue status for the wrapped embedding function. |
| `get_rerank_queue_status()` | Returns queue status for the wrapped rerank function. |

Use async updates in long-running async services when deterministic old-queue cleanup matters. Use sync updates for quick non-blocking switches and then call `wait_for_retired_llm_queues()` when it is safe to wait.

Runtime update validations include:

- Invalid role ids raise `ValueError`.
- Non-callable `model_func` raises `TypeError`.
- Metadata updates without a registered builder or direct `model_func` raise `ValueError`.
- Failed builder/update attempts roll back to the previous wrapped function and metadata.
- Cross-provider updates should not inherit base kwargs into the rebuilt role.

## Role Cache Identity

The LLM cache identity is role-aware. For each role, LightRAG partitions cache entries by:

```text
role + binding + model + host
```

API keys and provider options are excluded from cache identity to avoid secret leakage. Changing provider options without changing model/host can reuse prior cached answers; decide whether this is acceptable. Changing role binding/model/host should naturally produce a different cache partition.

## Rerank Configuration

Reranking is independent from role LLM configuration.

### Constructor/API Fields

| Field | Meaning |
| --- | --- |
| `rerank_model_func` | Async function called with `query`, `documents`, and `top_n`. |
| `rerank_model_max_async` | Rerank queue concurrency. |
| `default_rerank_timeout` | Rerank timeout. |
| `min_rerank_score` | Post-rerank threshold for retrieved chunks. |
| `QueryParam(enable_rerank=True)` | Query-level toggle. Defaults to enabled, but no rerank occurs if no function is configured. |
| `QueryParam(chunk_top_k=...)` | Number of text chunks to keep after reranking. |

If `enable_rerank=True` but no rerank function is configured, LightRAG logs a warning and returns the original retrieved docs.

### Server Env Fields

```env
RERANK_BINDING=cohere
RERANK_MODEL=<rerank-model>
RERANK_BINDING_HOST=<rerank-endpoint-url>
RERANK_BINDING_API_KEY=<secret>
MAX_ASYNC_RERANK=4
RERANK_TIMEOUT=30
MIN_RERANK_SCORE=0.0
```

Supported server bindings:

| Binding | Function | Default model | Default endpoint | Credential fallback |
| --- | --- | --- | --- | --- |
| `cohere` | `cohere_rerank` | `rerank-v3.5` | `https://api.cohere.com/v2/rerank` | `COHERE_API_KEY` then `RERANK_BINDING_API_KEY`. |
| `jina` | `jina_rerank` | `jina-reranker-v2-base-multilingual` | `https://api.jina.ai/v1/rerank` | `JINA_API_KEY` then `RERANK_BINDING_API_KEY`. |
| `aliyun` | `ali_rerank` | `gte-rerank-v2` | DashScope rerank endpoint | `DASHSCOPE_API_KEY` then `RERANK_BINDING_API_KEY`. |
| `null` | None | None | None | No rerank function configured. |

Cohere rerank can chunk long documents when configured:

```env
RERANK_ENABLE_CHUNKING=true
RERANK_MAX_TOKENS_PER_DOC=480
```

When chunking is enabled, chunk-level scores are aggregated back to original documents, and `top_n` is applied after aggregation.

## Rerank Result Contract

Preferred rerank function output:

```python
[
    {"index": 0, "relevance_score": 0.91},
    {"index": 2, "relevance_score": 0.83},
]
```

LightRAG copies the original retrieved documents by index and adds `rerank_score`. Legacy rerank functions that return already-reranked documents are still tolerated and truncated to `top_n` when present.

## Practical Pattern: Cheap Keyword, Strong Query

Use this when query latency matters but final answer quality needs a stronger model:

```env
LLM_BINDING=openai
LLM_MODEL=<balanced-chat-model>
LLM_BINDING_HOST=<openai-compatible-base-url>
LLM_BINDING_API_KEY=<secret>
OPENAI_LLM_REASONING_EFFORT=minimal

KEYWORD_LLM_MODEL=<fast-keyword-model>
KEYWORD_MAX_ASYNC_LLM=8
KEYWORD_LLM_TIMEOUT=30
KEYWORD_OPENAI_LLM_REASONING_EFFORT=minimal

QUERY_LLM_MODEL=<strong-chat-model>
QUERY_MAX_ASYNC_LLM=2
QUERY_LLM_TIMEOUT=240
QUERY_OPENAI_LLM_REASONING_EFFORT=medium
```

If `KEYWORD` points to an OpenAI-compatible local service that does not understand OpenAI reasoning fields, avoid incompatible global `OPENAI_LLM_*` options; set provider options only on roles that support them.

## Observability Checklist

When a configured role behaves unexpectedly:

1. Inspect sanitized `get_llm_role_config()` output or API health status.
2. Confirm role id and env prefix are correct.
3. Confirm same-provider versus cross-provider inheritance rules.
4. Confirm provider options are valid for the endpoint actually serving that role.
5. Confirm per-role queue status and max async values.
6. Confirm cache identity changed if the role should stop reusing old cached answers.
7. For runtime updates, await old queue cleanup when deterministic shutdown matters.
