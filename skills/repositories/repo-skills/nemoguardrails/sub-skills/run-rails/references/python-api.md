# Python API

## Choose the engine

| Surface | Use when | Key behavior |
| --- | --- | --- |
| `Guardrails` | You want one facade that auto-selects the fastest supported engine. | Uses `IORails` when possible, otherwise falls back to `LLMRails` unless `require_iorails=True`. |
| `LLMRails` | You need the full Colang runtime, explicit state handling, or event processing. | Always uses the full runtime. |
| `IORails` | The config is limited to Colang 1.0 input/output/tool rails and no custom `llm`. | Stateless and intentionally narrow. |

If `llm` is passed to `Guardrails(..., use_iorails=True, ...)`, the wrapper skips `IORails` and falls back to `LLMRails`.
`Guardrails` forwards engine-specific keyword arguments, so stateful calls still reach the active engine when that engine supports them.

> Compatibility note: in environments that set `NEMO_GUARDRAILS_IORAILS_ENGINE`, the top-level `LLMRails` import can alias the wrapper.

## Verified signatures

```python
RailsConfig.from_path(config_path: str)
RailsConfig.from_content(
    colang_content: str | None = None,
    yaml_content: str | None = None,
    config: dict | None = None,
)

Guardrails(
    config: RailsConfig,
    llm: Optional[LLMModel] = None,
    verbose: bool = False,
    *,
    use_iorails: bool = True,
    require_iorails: bool = False,
)
LLMRails(config: RailsConfig, llm: Optional[LLMModel] = None, verbose: bool = False)

Guardrails.generate(prompt: str | None = None, messages: list[dict] | None = None, options: dict | GenerationOptions | None = None, **kwargs)
Guardrails.generate_async(prompt: str | None = None, messages: list[dict] | None = None, options: dict | GenerationOptions | None = None, **kwargs)
Guardrails.stream_async(prompt: str | None = None, messages: list[dict] | None = None, **kwargs)
Guardrails.check(messages: list[dict], rail_types: list[RailType] | None = None)
Guardrails.check_async(messages: list[dict], rail_types: list[RailType] | None = None)
Guardrails.generate_events(events: list[dict])
Guardrails.generate_events_async(events: list[dict])

LLMRails.generate(prompt: str | None = None, messages: list[dict] | None = None, options: dict | GenerationOptions | None = None, state: dict | None = None)
LLMRails.generate_async(prompt: str | None = None, messages: list[dict] | None = None, options: dict | GenerationOptions | None = None, state: dict | State | None = None, streaming_handler: StreamingHandler | None = None)
LLMRails.stream_async(prompt: str | None = None, messages: list[dict] | None = None, options: dict | GenerationOptions | None = None, state: dict | State | None = None, include_metadata: bool = False, generator: AsyncIterator[str] | None = None, include_generation_metadata: bool | None = None)
LLMRails.check(messages: list[dict], rail_types: list[RailType] | None = None)
LLMRails.check_async(messages: list[dict], rail_types: list[RailType] | None = None)
LLMRails.generate_events(events: list[dict])
LLMRails.generate_events_async(events: list[dict])
LLMRails.process_events(events: list[dict], state: dict | State | None = None, blocking: bool = False)
LLMRails.process_events_async(events: list[dict], state: dict | State | None = None, blocking: bool = False)
```

## Message, event, and state shapes

- `messages` is a list of dicts with at least `role` and `content`.
- `context` messages use `{"role": "context", "content": {...}}`.
- Assistant messages can carry `tool_calls` when the model/tool flow needs them.
- `prompt` is a convenience for a single user turn.
- `events` is a list of event dicts for `generate_events` and `process_events`.

### State rules

- Public `state` for `generate` / `generate_async` is only accepted as a Colang 1.0 transcript dict: `{"events": [...]}`.
- Colang 2.0 public dict state is rejected. Use `process_events_async(events, state)` with a live `State` object for trusted in-process continuation.
- On the HTTP server, caller-supplied dict state is rejected for Colang 2.0 as well.

## Return shapes

| API | Normal shape | Notes |
| --- | --- | --- |
| `generate` / `generate_async` | String or assistant message dict | When `options` or `state` ask for structured output, the engine returns `GenerationResponse`. |
| `check` / `check_async` | `RailsResult` | `status` is `passed`, `modified`, or `blocked`. |
| `stream_async` | Async iterator of strings or dict chunks | `include_metadata=True` yields dict chunks with `text` and optional `metadata`. |
| `generate_events` / `generate_events_async` | List of event dicts | LLMRails only; the wrapper raises on an IORails-backed instance. |
| `process_events` / `process_events_async` | `(output_events, output_state)` | LLMRails only; use for trusted stateful Colang 2.x execution. |

`GenerationResponse` carries `response`, `state`, `output_data`, `log`, `tool_calls`, `reasoning_content`, and `llm_metadata` when those values are available.

## Generation options

`GenerationOptions` accepts:

- `rails`: either a list of enabled rail categories or a nested boolean/list object for `input`, `dialog`, `retrieval`, `output`, `tool_input`, and `tool_output`.
- `llm_params`: extra parameters forwarded to the LLM call.
- `output_vars`: request selected context values or the full context.
- `llm_output`: include the raw LLM output when the engine can provide it.
- `log`: request `activated_rails`, `llm_calls`, `internal_events`, or `colang_history`.

## Check API behavior

- `check_async` auto-detects rails from message roles when `rail_types` is omitted.
- user-only messages run input rails; assistant-only messages run output rails; mixed user/assistant messages run both.
- `rail_types=[RailType.INPUT]` or `[RailType.OUTPUT]` overrides the automatic detection.

## Streaming rules

- Output rails need `rails.output.streaming.enabled` before `stream_async` can be used.
- `include_generation_metadata` is deprecated; use `include_metadata`.
- An external `generator=` bypasses the internal LLM but still lets output rails process streamed text.
- Sync wrappers called from a running event loop raise `RuntimeError`; use the async method instead.
- When the wrapper is backed by `IORails`, unsupported streaming kwargs are ignored except for `options` and `include_metadata`.

## Quick choice guide

- Use `Guardrails` when you want a safe default that can fall back.
- Use `LLMRails` when you need Colang runtime features, events, or explicit state control.
- Use `check_async` when you only need validation and not generation.
- Use `stream_async` when you need token streaming; use the bundled smoke script first if you want to avoid live provider calls.
