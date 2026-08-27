# Logging, Tracing, Token Accounting, and Streaming

## Configuration Surface

mcp-agent uses two related observability sections in `mcp_agent.config.yaml`:

```yaml
logger:
  transports: [console, file]
  level: info
  progress_display: true
  path: "logs/mcp-agent.jsonl"
  path_settings:
    path_pattern: "logs/mcp-agent-{unique_id}.jsonl"
    unique_id: "timestamp"       # timestamp or session_id
    timestamp_format: "%Y%m%d_%H%M%S"
  batch_size: 100
  flush_interval: 2.0
  max_queue_size: 2048

otel:
  enabled: true
  service_name: "mcp-agent"
  service_version: "1.0.0"
  sample_rate: 1.0
  exporters:
    - console
    - file:
        path: "traces/mcp-agent-trace.jsonl"
    - otlp:
        endpoint: "http://collector:4318/v1/traces"
        headers:
          Authorization: "Bearer ${OTEL_TOKEN}"
```

Supported logger transports are `console`, `file`, `http`, and `none`. Supported OTEL exporters are `console`, `file`, and `otlp`. Exporter entries may be plain strings or keyed mappings; prefer keyed mappings when an exporter needs a path, endpoint, or headers.

## Logger Behavior

The developer-facing logger emits structured `Event` objects through an async event bus:

- `app.logger` is suitable for startup and tool-level messages.
- `running_app.context.logger` is request-aware inside `async with app.run() as running_app:`.
- `agent.logger` is available when an `Agent` is active.
- Events carry `type`, `name`, `namespace`, `message`, `timestamp`, `data`, optional `context`, and trace IDs when a span is active.
- `logger.info("message", name="event.name", key="value")` stores custom keyword data under the event payload.
- `event_context(...)` and `async_event_context(...)` time sync/async blocks and emit duration metadata.

File transport writes compact JSON Lines with fields such as `level`, `timestamp`, `namespace`, `message`, and optional `data`. HTTP transport batches events and posts JSON to `logger.http_endpoint` with optional headers and timeout.

## MCP Upstream Logging

When an app is served as an MCP server, the upstream logging listener can forward matched events to connected clients. The logger binds the active request context, sets the request-scoped session id, and attaches the upstream session to the event. Session log levels map `debug`, `info`/`notice`, `warning`/`warn`, and `error`/`critical`/`alert`/`emergency` to mcp-agent event levels.

Use this only as application instrumentation guidance. For MCP server auth, transport setup, or upstream session lifecycle internals, route to `../mcp-server-integration/SKILL.md`.

## OpenTelemetry Setup

`otel.enabled: true` configures a tracer provider with resource attributes:

- `service.name` from `otel.service_name`.
- `service.instance.id` from `otel.service_instance_id` or the current session id.
- `service.version` from `otel.service_version` or package metadata when available.
- `session.id` from the runtime session.

`otel.sample_rate` is clamped to `0.0..1.0` and applied through parent-based trace-id-ratio sampling when explicitly set. OTEL uses W3C trace context propagation.

Exporter notes:

- `console` emits spans to stdout; use for local debugging.
- `file` writes spans to a JSONL file; use `path` or `path_settings` for per-run trace files.
- `otlp` requires `endpoint`; if missing, mcp-agent logs an error instead of exporting.
- Headers may contain secret references, but never print resolved secrets in diagnostics or reports.

## Tracing Helpers

Use `mcp_agent.tracing.telemetry` helpers inside tools, workflows, and support functions:

```python
from mcp_agent.tracing.telemetry import get_tracer, get_meter, record_attributes, telemetry

tracer = get_tracer(context)
with tracer.start_as_current_span("workflow.plan") as span:
    record_attributes(span, {"step_count": len(steps)}, prefix="plan")

meter = get_meter(context)
requests = meter.create_counter("agent_requests_total")
requests.add(1, {"agent": "planner"})

@telemetry.traced("custom.helper")
async def helper(payload):
    ...
```

`record_attribute` and `record_attributes` flatten dictionaries, sequences, callables, and non-primitive values into OpenTelemetry-safe span attributes. Tool result helpers can mark failed MCP tool calls as span errors.

## Provider Autoinstrumentation

When tracing is configured, mcp-agent attempts to initialize Anthropic and OpenAI OpenTelemetry instrumentors. The base package includes the OpenTelemetry instrumentation packages, but the provider SDK packages themselves are optional extras. If a provider SDK is missing, imports of provider-specific AugmentedLLM modules can fail before credentials are checked.

## Token Accounting

AugmentedLLM methods are wrapped with token tracking. Token usage is recorded into a hierarchy of app, workflow, agent, and LLM nodes when a runtime context has a token counter and execution is not in Temporal replay.

Useful operations:

- `await app.get_token_summary()` or context token-counter methods for total usage, cost, model breakdowns, and usage tree data.
- `await token_counter.record_usage(input_tokens=..., output_tokens=..., model_name=..., provider=...)` for custom usage insertion.
- `await token_counter.watch(callback=..., node_type="llm", threshold=1000, include_subtree=True)` for real-time usage notifications.
- `await token_counter.unwatch(watch_id)` to avoid leaking callbacks.

Cost estimates depend on known model metadata; unknown model/provider pairs still track tokens but may use default or zero-cost estimates.

## Progress Displays

`logger.progress_display: true` adds a Rich progress listener. It converts structured log payloads that include `data.progress_action` into progress rows and can also show token totals when a token counter is available.

Operational cautions:

- Use progress display for interactive CLI sessions.
- Disable or ignore progress display in non-TTY, CI, notebook, and log-only environments.
- Progress conversion expects nested `data` payloads; plain log messages still emit normally but do not become progress rows.
- Do not replay event logs interactively in automated validation; use `scripts/summarize_event_log.py` instead.

## Streaming Events

Use streaming when a UI or monitor needs incremental output:

```python
from mcp_agent.workflows.llm.streaming_events import StreamEventType

async for event in agent.llm.generate_stream("Investigate this repo"):
    if event.type == StreamEventType.TEXT_DELTA:
        print(event.content, end="", flush=True)
    elif event.type == StreamEventType.TOOL_USE_START:
        logger.info("tool.started", data={"tool": event.content.get("name")})
    elif event.type == StreamEventType.ITERATION_END:
        logger.info("iteration.usage", data={"usage": event.usage})
    elif event.type == StreamEventType.ERROR:
        logger.error("stream.error", data=event.content or {})
        break
```

`generate_str_stream()` yields text chunks only and hides tool/iteration metadata. Prefer `generate_stream()` for observability, progress, or debugging.

Current streaming support is provider-specific. Anthropic and Bedrock have native streaming paths in the repository evidence; OpenAI-compatible streaming support can differ by wrapper and version. Always handle `ERROR` events and outer exceptions.

## Event Log Inspection

Use `scripts/summarize_event_log.py` to inspect JSONL produced by file logging. It accepts compact file transport lines and common event-shaped records, validates timestamps when present, redacts sensitive keys, and reports malformed lines without crashing by default.

Example:

```bash
python scripts/summarize_event_log.py logs/mcp-agent.jsonl --limit 100
python scripts/summarize_event_log.py logs/mcp-agent.jsonl --json --strict
```

Use `--strict` only when malformed JSON should fail the run.
