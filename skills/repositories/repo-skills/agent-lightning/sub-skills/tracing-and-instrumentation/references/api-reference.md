# Tracing API reference

## Purpose

Use this for verified tracing, emitter, and adapter signatures.

## Tracers

```python
OtelTracer()
AgentOpsTracer(*, agentops_managed=True, instrument_managed=True, daemon=True)
OtelTracer.trace_context(self, name=None, *, store=None, rollout_id=None, attempt_id=None) -> AsyncGenerator
Tracer.get_last_trace(self) -> list[Span]
Tracer.create_span(self, name, attributes=None, timestamp=None, status=None) -> SpanCoreFields
Tracer.operation_context(self, name, attributes=None, start_time=None, end_time=None)
```

`Tracer.lifespan(store=None)` initializes and tears down a tracer for local debug snippets.

## Emitters

Verified signatures:

```python
emit_reward(reward: float | dict, *, primary_key: str | None = None, attributes: dict | None = None, propagate: bool = True) -> SpanCoreFields
emit_message(message: str, attributes: dict | None = None, propagate: bool = True) -> None
emit_object(object: Any, attributes: dict | None = None, propagate: bool = True) -> SpanCoreFields
operation(fn=None, *, propagate: bool = True, name: str | None = None, **additional_attributes)
```

Important behavior:

- `emit_reward(1.0)` creates a primary reward dimension.
- `emit_reward({"score": 0.8}, primary_key="score")` requires `primary_key`.
- Non-numeric reward values raise `TypeError` or `ValueError`.
- `emit_message` requires a string.
- `emit_object` requires JSON-serializable objects except supported scalar/bytes literals.
- With `propagate=True`, there must be an active tracer.
- With `propagate=False`, a dummy tracer creates local `SpanCoreFields` without exporting.

## Reward readers

```python
find_reward_spans(spans) -> list[SpanLike]
find_final_reward(spans) -> float | None
get_reward_value(span) -> float | None
get_rewards_from_span(span) -> list[RewardPydanticModel]
is_reward_span(span) -> bool
```

`find_final_reward` returns the last non-null reward it can extract from the span list. It understands current Agent Lightning annotation spans and older AgentOps reward payloads.

## Tag/link helpers

```python
make_tag_attributes(tags: list[str]) -> dict[str, Any]
extract_tags_from_attributes(attributes: dict[str, Any]) -> list[str]
make_link_attributes(links: dict[str, str]) -> dict[str, Any]
extract_links_from_attributes(attributes: dict[str, Any]) -> list[LinkPydanticModel]
query_linked_spans(spans, links) -> list[SpanLike]
```

`make_link_attributes` requires string values. Use it to connect rewards to LLM response IDs, span IDs, or workflow-specific identifiers.

## Adapters

Verified signatures:

```python
TraceToMessages()
TraceToMessages.adapt(self, source: Sequence[Span]) -> list[OpenAIMessages]
TracerTraceToTriplet(
    repair_hierarchy=True,
    llm_call_match='openai\\.chat\\.completion',
    agent_match=None,
    exclude_llm_call_in_reward=True,
    reward_match=RewardMatchPolicy.FIRST_OCCURRENCE,
    _skip_empty_token_spans=False,
)
TracerTraceToTriplet.adapt(self, source: Sequence[Span] | Sequence[ReadableSpan]) -> list[Triplet]
LlmProxyTraceToTriplet()
LlmProxyTraceToTriplet.adapt(self, source: Sequence[Span]) -> list[Triplet]
```

Use `TracerTraceToTriplet` for normal tracer spans. Use `LlmProxyTraceToTriplet` for proxy spans. Use `TraceToMessages` for chat-message-oriented algorithms such as prompt optimization.

## Span model reminders

`Span` records:

- `rollout_id`, `attempt_id`, `sequence_id`,
- `trace_id`, `span_id`, `parent_id`,
- `name`, `status`, timestamps,
- flattened `attributes`, `events`, `links`, and OpenTelemetry resource metadata.

Sequence IDs are monotonic per rollout attempt so adapters can reconstruct chronological order even when spans come from distributed workers.
