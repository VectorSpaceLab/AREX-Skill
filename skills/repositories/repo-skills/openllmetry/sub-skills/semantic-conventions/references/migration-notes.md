# Migration notes

This reference explains how to move from legacy `LLM_*` naming to the current `GEN_AI_*` / upstream OpenTelemetry GenAI naming model without breaking compatibility.

## The short version

- New code should prefer `GEN_AI_*` names from `SpanAttributes` when the repo owns the attribute.
- New provider-facing code should prefer upstream `GenAIAttributes` constants such as `GEN_AI_PROVIDER_NAME`, `GEN_AI_INPUT_MESSAGES`, `GEN_AI_OUTPUT_MESSAGES`, and `GEN_AI_RESPONSE_FINISH_REASONS`.
- Do not assume every `LLM_*` name is obsolete at runtime. The package still retains compatibility aliases, and their string values are not all the same.
- Do not use `gen_ai.system` on new spans. Emit `gen_ai.provider.name` instead.

## Provider name migration

The provider name on spans is the current semantic-convention anchor.

| Old habit | New habit |
| --- | --- |
| Set `gen_ai.system` on a span | Set `gen_ai.provider.name` on the span. |
| Compare against display names like `OpenAI` | Compare against normalized provider values like `openai`, `anthropic`, `cohere`, or the provider's canonical upstream value. |
| Assume `GenAISystem` mirrors every upstream enum value | Treat `GenAISystem` as the repo's curated subset, and use upstream `GenAiSystemValues` when you need the full OpenTelemetry vocabulary. |

### Why this matters

Provider-specific tests in this repository check for `gen_ai.provider.name` and fail if a span still exposes the deprecated `gen_ai.system` field.

## Alias categories

The legacy aliases fall into three useful buckets.

| Bucket | Example | Migration rule |
| --- | --- | --- |
| Old Python name, old string value | `SpanAttributes.LLM_USAGE_TOTAL_TOKENS = "llm.usage.total_tokens"` | Replace with `SpanAttributes.GEN_AI_USAGE_TOTAL_TOKENS` in new code. The alias stays only for compatibility. |
| Old Python name, current string value | `SpanAttributes.LLM_PROMPTS = "gen_ai.prompt"` | Use the current `GEN_AI_*` name in new code, but note that the alias already carries the modern namespace. |
| New Python name, vendor-specific string | `SpanAttributes.GEN_AI_WATSONX_DECODING_METHOD = "llm.watsonx.decoding_method"` | Keep the new Python name. The `llm.watsonx.*` string is intentional vendor-qualified telemetry. |

## Before / after: total tokens

```python
# Before: legacy alias
from opentelemetry.semconv_ai import SpanAttributes

span.set_attribute(SpanAttributes.LLM_USAGE_TOTAL_TOKENS, total_tokens)

# After: current compatibility name
from opentelemetry.semconv_ai import SpanAttributes

span.set_attribute(SpanAttributes.GEN_AI_USAGE_TOTAL_TOKENS, total_tokens)
```

### Important warning

`SpanAttributes.LLM_USAGE_TOTAL_TOKENS` is intentionally retained for older packages that still import it. It is not the preferred spelling for new code, but removing it would break compatibility for older instrumentations.

## When to import upstream instead

Some names are better imported from the upstream OpenTelemetry GenAI module than from the local compatibility layer.

| Need | Prefer |
| --- | --- |
| Provider name on spans | `GenAIAttributes.GEN_AI_PROVIDER_NAME` |
| Message payloads | `GenAIAttributes.GEN_AI_INPUT_MESSAGES`, `GenAIAttributes.GEN_AI_OUTPUT_MESSAGES` |
| Tool definitions | `GenAIAttributes.GEN_AI_TOOL_DEFINITIONS` |
| Top-level finish metadata | `GenAIAttributes.GEN_AI_RESPONSE_FINISH_REASONS` |
| Operation name | `GenAIAttributes.GEN_AI_OPERATION_NAME` |
| Usage counts | `GenAIAttributes.GEN_AI_USAGE_INPUT_TOKENS`, `GenAIAttributes.GEN_AI_USAGE_OUTPUT_TOKENS` |

## Finish-reason migration

Be careful with finish reason naming:

- Local compatibility: `SpanAttributes.GEN_AI_RESPONSE_FINISH_REASON` and `SpanAttributes.LLM_RESPONSE_FINISH_REASON`.
- Upstream provider-span contract: `GenAIAttributes.GEN_AI_RESPONSE_FINISH_REASONS`.

The plural upstream field is the one provider tests expect on emitted spans. Keep it even when content tracing is disabled, because it is response metadata rather than prompt/output content.

## Request-type migration

`LLMRequestTypeValues` is a legacy compatibility enum.

| Old enum | What to use now |
| --- | --- |
| `LLMRequestTypeValues.CHAT` | `GenAiOperationNameValues.CHAT` for upstream operation names. |
| `LLMRequestTypeValues.COMPLETION` | `GenAiOperationNameValues.TEXT_COMPLETION` or `GENERATE_CONTENT`, depending on the provider surface. |
| `LLMRequestTypeValues.EMBEDDING` | `GenAiOperationNameValues.EMBEDDINGS`. |
| `LLMRequestTypeValues.RERANK` | `GenAiOperationNameValues.RETRIEVAL` or provider-specific rerank handling, depending on the wrapper. |

Use the compatibility enum only when you are preserving old local semantics.

## Cache-token alias caution

The cache-token aliases are unusual because the Python name is legacy, but the value is already the modern `gen_ai.usage.cache_*` spelling.

- `SpanAttributes.LLM_USAGE_CACHE_CREATION_INPUT_TOKENS`
- `SpanAttributes.LLM_USAGE_CACHE_READ_INPUT_TOKENS`

Do not rewrite these based on the `LLM_` prefix alone; the value is already current.

## Practical migration guidance

1. Prefer the current `GEN_AI_*` spellings for new repository code.
2. Keep legacy aliases only when you need backward compatibility with existing packages or tests.
3. When migrating provider code, check both the span attribute name and the JSON payload shape.
4. For provider name and finish-reason work, validate against the upstream OTel semantic-convention layer, not just the local compatibility alias.
