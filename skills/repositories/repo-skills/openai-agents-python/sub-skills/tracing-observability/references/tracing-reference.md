# Tracing & Observability Reference

This reference summarizes the OpenAI Agents Python tracing, usage, logging, and visualization surfaces verified from repository docs, source, examples, and tests.

## Configuration Surfaces

| Surface | Purpose | Notes |
| --- | --- | --- |
| `RunConfig.tracing_disabled` | Disable tracing for one run. | Leaves global tracing state unchanged. |
| `RunConfig.tracing` | Per-run tracing export config. | `TracingConfig` currently accepts `api_key`; do not log the value. |
| `RunConfig.trace_include_sensitive_data` | Include or exclude sensitive model/tool payloads in trace spans. | Defaults to `True` unless `OPENAI_AGENTS_TRACE_INCLUDE_SENSITIVE_DATA` is set to a false value. |
| `RunConfig.workflow_name` | Logical trace workflow name. | Defaults to `"Agent workflow"`; set a product/job-specific name in production. |
| `RunConfig.trace_id` | Override trace identifier. | If supplied manually, use the `trace_<32_hex_or_alnum>` format; `gen_trace_id()` creates valid IDs. |
| `RunConfig.group_id` | Link related traces. | Useful for chat threads, jobs, tenant-scoped batches, or prompt-cache grouping boundaries. |
| `RunConfig.trace_metadata` | Attach trace metadata. | Keep metadata low-cardinality and non-secret. |
| `trace(...)` | Create a higher-level trace context. | Wrap multiple `Runner.run` calls when they should appear under one trace. |
| `set_tracing_disabled(True)` | Disable tracing globally in process. | Manual setting takes precedence over the env-derived default. |
| `set_tracing_export_api_key(key)` | Set the default tracing exporter key. | Use when model traffic uses a different key/client than trace export. |
| `OPENAI_AGENTS_DISABLE_TRACING=1` | Disable tracing globally before first provider use. | Tests confirm the default provider reads the env flag lazily on first tracing use. |
| `OPENAI_AGENTS_TRACE_INCLUDE_SENSITIVE_DATA=0` | Change default sensitive trace payload capture. | Explicit `RunConfig(trace_include_sensitive_data=...)` wins. |
| `OPENAI_ORG_ID`, `OPENAI_PROJECT_ID` | Attribute default backend exports. | Read by the default backend exporter. |

The default OpenAI model key can also be used for tracing. When a custom model key/client should not be used for trace export, configure the model/provider with `use_for_tracing=False` and set tracing separately. See [../../models-providers/SKILL.md](../../models-providers/SKILL.md) for provider setup.

## Default Trace Shape

By default, `Runner.run`, `Runner.run_sync`, and `Runner.run_streamed` are wrapped in a trace. The SDK creates spans for agent execution, task/turn boundaries, model generation/response calls, function tools, guardrails, handoffs, MCP tool listing, and audio operations. Realtime and voice-specific audio tracing is routed to [../../realtime-voice/SKILL.md](../../realtime-voice/SKILL.md).

A trace records:

- `workflow_name`: logical workflow name.
- `trace_id`: generated unless supplied.
- `group_id`: optional grouping value.
- `metadata`: optional user metadata.
- `disabled`: whether a no-op trace is returned.

A span records:

- `trace_id` and optional `parent_id`.
- Start/end timestamps.
- Typed `span_data`, such as `AgentSpanData`, `GenerationSpanData`, `FunctionSpanData`, `GuardrailSpanData`, `HandoffSpanData`, `ResponseSpanData`, `TaskSpanData`, `TurnSpanData`, `MCPListToolsSpanData`, and audio span data.

## Span Helpers

Common helpers imported from `agents` or `agents.tracing` include:

| Helper | Use |
| --- | --- |
| `trace(workflow_name, trace_id=None, group_id=None, metadata=None, tracing=None, disabled=False)` | Create a trace context manager or manual trace. |
| `custom_span(name, data=None, span_id=None, parent=None, disabled=False)` | Add application-specific observability within an active trace. |
| `agent_span(...)`, `task_span(...)`, `turn_span(...)` | Instrument custom agent/task/turn boundaries. |
| `generation_span(...)`, `response_span(...)` | Instrument model calls or response IDs. |
| `function_span(name, input=None, output=None, ...)` | Instrument tool-like work; beware sensitive input/output. |
| `guardrail_span(...)`, `handoff_span(...)`, `mcp_tools_span(...)` | Instrument SDK-adjacent custom operations. |
| `get_current_trace()`, `get_current_span()` | Inspect active contextvars. |
| `gen_trace_id()`, `gen_span_id()` | Generate valid IDs. |
| `flush_traces()` | Force processor flush after a trace context closes. |

`trace()` and span helpers do not start automatically unless used as context managers. If manually starting or finishing, preserve current context with the helper arguments described in the API objects; prefer `with trace(...):` and `with custom_span(...):` for normal application code.

## Processors and Exporters

The default tracing setup is lazy:

1. `get_trace_provider()` creates a `DefaultTraceProvider` on first use.
2. The provider registers the default `BatchTraceProcessor`.
3. The batch processor sends traces/spans through `BackendSpanExporter` to the OpenAI traces ingest endpoint.

Processor APIs:

| API | Effect |
| --- | --- |
| `add_trace_processor(processor)` | Adds an additional processor alongside existing processors and the default exporter. |
| `set_trace_processors([processor, ...])` | Replaces all processors. Use this for local-only tests or alternate exporters. |
| `set_trace_provider(provider)` | Replaces the global provider. Use only for advanced framework integration or tests. |
| `TracingProcessor` | Interface with `on_trace_start`, `on_trace_end`, `on_span_start`, `on_span_end`, `shutdown`, and `force_flush`. |
| `TracingExporter` | Interface with `export(items)`. |
| `BatchTraceProcessor(exporter, max_queue_size=8192, max_batch_size=128, schedule_delay=5.0, export_trigger_ratio=0.7)` | Queues trace start events and span end events, exports periodically or at queue threshold, and flushes on shutdown. |
| `BackendSpanExporter(api_key=None, organization=None, project=None, endpoint=..., max_retries=3, base_delay=1.0, max_delay=30.0)` | Default HTTP exporter; reads `OPENAI_API_KEY`, `OPENAI_ORG_ID`, and `OPENAI_PROJECT_ID` when not provided. |
| `ConsoleSpanExporter()` | Prints exported trace/span data locally; use cautiously because it may print payloads. |

Tests verify that processor and exporter failures are logged as non-fatal. This prevents agent execution from crashing, but failed batches can be dropped. Custom processors should still catch their own errors, avoid long blocking calls, and implement `force_flush()` / `shutdown()`.

## Sensitive-Data Controls

`RunConfig.trace_include_sensitive_data=False` keeps spans for sensitive operations while excluding model generation and function-tool input/output payload details from trace data. The default is `True` unless `OPENAI_AGENTS_TRACE_INCLUDE_SENSITIVE_DATA` sets a different default before constructing `RunConfig`.

This setting does not automatically sanitize:

- Values that application code puts in `trace_metadata`.
- Values that custom processors copy out of spans before redaction or add from side channels.
- Exception objects, exception chains, tracebacks, or logs emitted by application code.
- Tool error messages intentionally returned to the model.
- Values printed by `ConsoleSpanExporter` or custom logging handlers.

The logging-specific defaults are separate. `OPENAI_AGENTS_DONT_LOG_MODEL_DATA=1` and `OPENAI_AGENTS_DONT_LOG_TOOL_DATA=1` are the default protections; setting either to `0` or `false` can include data in debug logs.

## Usage Tracking

`Usage` is aggregated on the run context and can be read from `result.context_wrapper.usage`. It tracks:

| Field | Meaning |
| --- | --- |
| `requests` | Number of model API requests. |
| `input_tokens` | Total input tokens. |
| `output_tokens` | Total output tokens. |
| `total_tokens` | Input plus output tokens. |
| `input_tokens_details.cached_tokens` | Cached input token count when provider reports it. |
| `output_tokens_details.reasoning_tokens` | Reasoning token count when provider reports it. |
| `request_usage_entries` | Per-request `RequestUsage` entries with input/output/total token breakdowns. |

Usage is per run, even when a `Session` persists conversation history. Subsequent session turns may include previous messages and therefore can have higher input token counts. Third-party adapters depend on upstream usage reporting; streamed Chat Completions and some LiteLLM providers may need `ModelSettings(include_usage=True)`. Route adapter setup to [../../models-providers/SKILL.md](../../models-providers/SKILL.md).

## Logging and Debug

The SDK uses Python logging and does not attach handlers by default. The primary logger is `openai.agents`; tracing internals also use the tracing logger path. `enable_verbose_stdout_logging()` sets the `openai.agents` logger to `DEBUG` and attaches a stdout stream handler.

For production logging:

- Prefer application-owned handlers/formatters over calling `enable_verbose_stdout_logging()` globally.
- Keep `OPENAI_AGENTS_DONT_LOG_MODEL_DATA` and `OPENAI_AGENTS_DONT_LOG_TOOL_DATA` at their default protective values unless debugging in a safe environment.
- Add filters that redact API keys, bearer tokens, user payloads, and tool outputs before logs leave the process.
- Remember that `trace_include_sensitive_data=False` and logging redaction are independent controls.

## Visualization

`agents.extensions.visualization.draw_graph(agent, filename=None)` returns a `graphviz.Source` object and can render a PNG when `filename` is supplied. Optional dependency installation is required for `graphviz` Python package and a system Graphviz executable may be needed for rendering.

The graph includes:

- `__start__` and `__end__` nodes.
- Agents as yellow boxes.
- Function tools as green ellipses.
- MCP servers as grey boxes.
- Handoff edges as solid arrows.
- Tool edges as dotted arrows.
- MCP edges as dashed arrows.

Tests cover real `Agent` objects, `handoff(...)` objects, MCP server nodes, agents with no handoffs, and handoff cycles. For topology inspection without rendering, use the returned `graph.source` DOT string or `get_main_graph(agent)`.
