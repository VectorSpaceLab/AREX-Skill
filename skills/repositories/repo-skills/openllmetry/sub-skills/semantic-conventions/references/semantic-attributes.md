# Semantic attributes

This reference captures the semantic-convention surface that the generated OpenLLMetry skill should treat as authoritative.

## Canonical imports

```python
from opentelemetry.semconv_ai import (
    SpanAttributes,
    GenAISystem,
    Meters,
    Events,
    EventAttributes,
    LLMRequestTypeValues,
    TraceloopSpanKindValues,
)

from opentelemetry.semconv._incubating.attributes import gen_ai_attributes as GenAIAttributes
```

Use `SpanAttributes` for the OpenLLMetry compatibility layer and `GenAIAttributes` for upstream OpenTelemetry GenAI names such as `gen_ai.provider.name`, `gen_ai.input.messages`, and `gen_ai.output.messages`.

## Public symbol groups

| Symbol | Kind | Purpose |
| --- | --- | --- |
| `SpanAttributes` | class of string constants | Current `GEN_AI_*` names, long-lived `LLM_*` aliases, workflow/task/vector DB attributes, and vendor-specific fields. |
| `GenAISystem` | enum | Local vendor/system identifiers. Values align with upstream where possible and add repo-specific vendor names where needed. |
| `Meters` | class of string constants | Metric instrument names for client, DB, and vendor-specific telemetry. |
| `Events` | enum | Vector DB query/search event names. |
| `EventAttributes` | enum | Event payload fields used by the vector DB event emitters. |
| `LLMRequestTypeValues` | enum | Legacy request-type classification values. |
| `TraceloopSpanKindValues` | enum | Workflow/task/agent/tool span-kind values used by SDK decorators and workflow spans. |
| `GenAICustomOperationName` | enum | Project-specific operation names that extend the upstream OTel set. |
| `GenAITaskStatus` | enum | Status values for `gen_ai.task.status`. |

## Upstream OpenTelemetry GenAI names to remember

The upstream OTel module exposes the canonical span-attribute constants for provider-facing message and operation data:

- `GEN_AI_PROVIDER_NAME` → `gen_ai.provider.name`
- `GEN_AI_SYSTEM` → `gen_ai.system` (deprecated upstream alias)
- `GEN_AI_INPUT_MESSAGES` → `gen_ai.input.messages`
- `GEN_AI_OUTPUT_MESSAGES` → `gen_ai.output.messages`
- `GEN_AI_TOOL_DEFINITIONS` → `gen_ai.tool.definitions`
- `GEN_AI_OPERATION_NAME` → `gen_ai.operation.name`
- `GEN_AI_RESPONSE_FINISH_REASONS` → `gen_ai.response.finish_reasons`
- `GEN_AI_USAGE_INPUT_TOKENS` / `GEN_AI_USAGE_OUTPUT_TOKENS`
- `GEN_AI_USAGE_CACHE_READ_INPUT_TOKENS` / `GEN_AI_USAGE_CACHE_CREATION_INPUT_TOKENS`

## Current span-attribute families

### 1) Current `GEN_AI_*` compatibility names

These are the names new code should prefer inside `SpanAttributes`.

| Constant | Value | Notes |
| --- | --- | --- |
| `GEN_AI_USAGE_TOTAL_TOKENS` | `gen_ai.usage.total_tokens` | Current total-token span attribute. |
| `GEN_AI_USAGE_TOKEN_TYPE` | `gen_ai.usage.token_type` | Token type classification. |
| `GEN_AI_USER` | `gen_ai.user` | Project-policy user identifier. |
| `GEN_AI_HEADERS` | `gen_ai.headers` | Project-policy request/response headers. |
| `GEN_AI_IS_STREAMING` | `gen_ai.is_streaming` | Streaming-mode marker. |
| `GEN_AI_REQUEST_REPETITION_PENALTY` | `gen_ai.request.repetition_penalty` | Request tuning field. |
| `GEN_AI_RESPONSE_FINISH_REASON` | `gen_ai.response.finish_reason` | Local compatibility name; upstream provider spans use plural `gen_ai.response.finish_reasons`. |
| `GEN_AI_RESPONSE_STOP_REASON` | `gen_ai.response.stop_reason` | Response termination metadata. |
| `GEN_AI_CONTENT_COMPLETION_CHUNK` | `gen_ai.content.completion.chunk` | Chunk content for streaming flows. |
| `GEN_AI_REQUEST_REASONING_EFFORT` | `gen_ai.request.reasoning_effort` | Reasoning request field. |
| `GEN_AI_USAGE_REASONING_TOKENS` | `gen_ai.usage.reasoning_tokens` | Reasoning token count. |
| `GEN_AI_REQUEST_N` | `gen_ai.request.n` | Sample count / candidate count. |
| `GEN_AI_REQUEST_MAX_COMPLETION_TOKENS` | `gen_ai.request.max_completion_tokens` | Completion cap. |
| `GEN_AI_REQUEST_STRUCTURED_OUTPUT_SCHEMA` | `gen_ai.request.structured_output_schema` | Structured-output schema payload. |
| `GEN_AI_REQUEST_REASONING_SUMMARY` | `gen_ai.request.reasoning_summary` | Reasoning summary request field. |
| `GEN_AI_RESPONSE_REASONING_EFFORT` | `gen_ai.response.reasoning_effort` | Response reasoning field. |
| `GEN_AI_OPENAI_API_BASE` | `gen_ai.openai.api_base` | OpenAI-specific metadata. |
| `GEN_AI_OPENAI_API_VERSION` | `gen_ai.openai.api_version` | OpenAI-specific metadata. |
| `GEN_AI_OPENAI_API_TYPE` | `gen_ai.openai.api_type` | OpenAI-specific metadata. |

### 2) Workflow / task / agent / tool surface

| Constant | Value | Notes |
| --- | --- | --- |
| `TRACELOOP_SPAN_KIND` | `traceloop.span.kind` | Workflow/task/agent/tool span-kind tag. |
| `TRACELOOP_WORKFLOW_NAME` | `traceloop.workflow.name` | Workflow-level naming. |
| `TRACELOOP_ENTITY_NAME` | `traceloop.entity.name` | Entity label. |
| `TRACELOOP_ENTITY_PATH` | `traceloop.entity.path` | Entity path. |
| `TRACELOOP_ENTITY_VERSION` | `traceloop.entity.version` | Entity version. |
| `TRACELOOP_ENTITY_INPUT` | `traceloop.entity.input` | Entity input payload. |
| `TRACELOOP_ENTITY_OUTPUT` | `traceloop.entity.output` | Entity output payload. |
| `TRACELOOP_ASSOCIATION_PROPERTIES` | `traceloop.association.properties` | Correlation / association metadata. |
| `TRACELOOP_PROMPT_MANAGED` | `traceloop.prompt.managed` | Prompt-registry marker. |
| `TRACELOOP_PROMPT_KEY` | `traceloop.prompt.key` | Prompt key. |
| `TRACELOOP_PROMPT_VERSION` | `traceloop.prompt.version` | Prompt version. |
| `TRACELOOP_PROMPT_VERSION_NAME` | `traceloop.prompt.version_name` | Prompt version name. |
| `TRACELOOP_PROMPT_VERSION_HASH` | `traceloop.prompt.version_hash` | Prompt version hash. |
| `TRACELOOP_PROMPT_TEMPLATE` | `traceloop.prompt.template` | Prompt template body. |
| `TRACELOOP_PROMPT_TEMPLATE_VARIABLES` | `traceloop.prompt.template_variables` | Prompt template variable payload. |
| `TRACELOOP_CORRELATION_ID` | `traceloop.correlation.id` | Deprecated correlation field retained for compatibility. |
| `GEN_AI_TASK_ID` | `gen_ai.task.id` | Task identifier. |
| `GEN_AI_TASK_NAME` | `gen_ai.task.name` | Task name. |
| `GEN_AI_TASK_PARENT_ID` | `gen_ai.task.parent.id` | Parent-task linkage. |
| `GEN_AI_TASK_INPUT` | `gen_ai.task.input` | Task input. |
| `GEN_AI_TASK_OUTPUT` | `gen_ai.task.output` | Task output. |
| `GEN_AI_TASK_STATUS` | `gen_ai.task.status` | Use `GenAITaskStatus` values. |
| `GEN_AI_TASK_KIND` | `gen_ai.task.kind` | Task kind. |
| `GEN_AI_WORKFLOW_NODES` | `gen_ai.workflow.nodes` | Workflow graph nodes. |
| `GEN_AI_WORKFLOW_EDGES` | `gen_ai.workflow.edges` | Workflow graph edges. |

### 3) Vector DB, MCP, and LangGraph surface

| Constant family | Examples | Notes |
| --- | --- | --- |
| Vector DB generic | `VECTOR_DB_VENDOR`, `VECTOR_DB_OPERATION`, `VECTOR_DB_QUERY_TOP_K`, `VECTOR_DB_QUERY_EMBEDDINGS_COUNT`, `VECTOR_DB_QUERY_RESULT_COUNT`, `VECTOR_DB_QUERY_TOP_SCORE`, `VECTOR_DB_QUERY_TOP_DISTANCE` | Generic vector-store telemetry. |
| Pinecone | `PINECONE_USAGE_READ_UNITS`, `PINECONE_USAGE_WRITE_UNITS`, `PINECONE_QUERY_*`, `PINECONE_QUERY_*` | Pinecone-specific query and usage names. |
| Chroma | `CHROMADB_*` | Chroma collection/query/update/upsert telemetry. |
| Milvus | `MILVUS_*` | Milvus collection/query/search/upsert telemetry. |
| Qdrant | `QDRANT_*` | Qdrant query/upload/upsert telemetry. |
| Marqo | `MARQO_*` | Marqo query/delete telemetry. |
| MCP | `MCP_METHOD_NAME`, `MCP_REQUEST_ARGUMENT`, `MCP_REQUEST_ID`, `MCP_SESSION_INIT_OPTIONS`, `MCP_RESPONSE_VALUE` | MCP request/response telemetry. |
| LangGraph | `LANGGRAPH_COMMAND_SOURCE_NODE`, `LANGGRAPH_COMMAND_GOTO_NODE`, `LANGGRAPH_COMMAND_GOTO_NODES` | LangGraph vendor namespace. |

### 4) Legacy `LLM_*` aliases

The module still exposes compatibility aliases. Some keep the old `llm.*` string, some already point at `gen_ai.*`, and some are intentionally renamed in Python while keeping a vendor-specific string.

Use the alias category, not the prefix alone, to decide migration behavior.

| Alias pattern | Example | Current meaning |
| --- | --- | --- |
| Old name, old value | `LLM_USAGE_TOTAL_TOKENS = "llm.usage.total_tokens"` | Legacy compatibility only; migrate new code to `GEN_AI_USAGE_TOTAL_TOKENS`. |
| Old name, new value | `LLM_PROMPTS = "gen_ai.prompt"` | Legacy Python name, current namespace string. |
| New name, old vendor string | `GEN_AI_WATSONX_DECODING_METHOD = "llm.watsonx.decoding_method"` | Current Python name for a vendor-specific namespace. |
| Cache-token aliases | `LLM_USAGE_CACHE_CREATION_INPUT_TOKENS`, `LLM_USAGE_CACHE_READ_INPUT_TOKENS` | Legacy Python names that already carry the `gen_ai.usage.cache_*` string form. |

## Enum values and validation expectations

### `GenAISystem`

The local enum is a curated subset used by the repo. It aligns with upstream where possible and adds project-specific vendors where needed.

| Member | Value | Upstream relation |
| --- | --- | --- |
| `OPENAI` | `openai` | Upstream-aligned. |
| `ANTHROPIC` | `anthropic` | Upstream-aligned. |
| `COHERE` | `cohere` | Upstream-aligned. |
| `MISTRALAI` | `mistral_ai` | Upstream-aligned as `MISTRAL_AI`. |
| `OLLAMA` | `ollama` | Project-specific. |
| `GROQ` | `groq` | Upstream-aligned. |
| `ALEPH_ALPHA` | `aleph_alpha` | Project-specific. |
| `REPLICATE` | `replicate` | Project-specific. |
| `TOGETHER_AI` | `together_ai` | Project-specific. |
| `WATSONX` | `ibm.watsonx.ai` | Upstream-aligned as `IBM_WATSONX_AI`. |
| `HUGGINGFACE` | `hugging_face` | Project-specific. |
| `FIREWORKS` | `fireworks` | Project-specific. |
| `AZURE` | `az.ai.openai` | Upstream-aligned as `AZ_AI_OPENAI`. |
| `AWS` | `aws.bedrock` | Upstream-aligned as `AWS_BEDROCK`. |
| `GOOGLE` | `gcp.gen_ai` | Upstream-aligned as `GCP_GEN_AI`. |
| `OPENROUTER` | `openrouter` | Project-specific. |
| `LANGCHAIN` | `langchain` | Project-specific. |
| `CREWAI` | `crewai` | Project-specific. |

Validation rule: values should remain lowercase, dot-separated where the upstream spec uses dots, and underscore-separated only where the repo intentionally uses underscores.

### `LLMRequestTypeValues`

| Member | Value |
| --- | --- |
| `COMPLETION` | `completion` |
| `CHAT` | `chat` |
| `RERANK` | `rerank` |
| `EMBEDDING` | `embedding` |
| `UNKNOWN` | `unknown` |

Treat this as a compatibility enum, not the upstream operation-name taxonomy.

### `TraceloopSpanKindValues`

| Member | Value |
| --- | --- |
| `WORKFLOW` | `workflow` |
| `TASK` | `task` |
| `AGENT` | `agent` |
| `TOOL` | `tool` |
| `UNKNOWN` | `unknown` |

These values are used by SDK decorators and workflow/task spans.

### `Events` and `EventAttributes`

| Event | Typical payload fields |
| --- | --- |
| `DB_QUERY_EMBEDDINGS` | `DB_QUERY_EMBEDDINGS_VECTOR` |
| `DB_QUERY_RESULT` | `DB_QUERY_RESULT_ID`, `DB_QUERY_RESULT_SCORE`, `DB_QUERY_RESULT_DISTANCE`, `DB_QUERY_RESULT_METADATA`, `DB_QUERY_RESULT_VECTOR`, `DB_QUERY_RESULT_DOCUMENT` |
| `DB_SEARCH_EMBEDDINGS` | `DB_SEARCH_EMBEDDINGS_VECTOR` |
| `DB_SEARCH_RESULT` | `DB_SEARCH_RESULT_QUERY_ID`, `DB_SEARCH_RESULT_ID`, `DB_SEARCH_RESULT_SCORE`, `DB_SEARCH_RESULT_DISTANCE`, `DB_SEARCH_RESULT_ENTITY` |

Event payloads should be treated as structured data for vector DB traces, not as generic string blobs.

## Validation expectations

1. `gen_ai.provider.name` is the current provider identifier on spans. Treat `gen_ai.system` as deprecated compatibility data.
2. `gen_ai.input.messages`, `gen_ai.output.messages`, and `gen_ai.tool.definitions` are JSON strings, not Python objects.
3. `gen_ai.response.finish_reasons` is span metadata. It should remain available even when content tracing suppresses message bodies.
4. Provider-specific wrappers may differ in how aggressively they gate tool definitions when content tracing is off. Validate against the provider's semconv tests, not a generic assumption.
5. The bundled `scripts/check_semconv_constants.py` helper should be able to import the package, confirm the expected values, and fail cleanly when a constant drifts.
6. Provider test suites in this repository reuse the shared `_testing.py` module from `opentelemetry-semantic-conventions-ai`; update that source of truth when the compliance contract changes.
