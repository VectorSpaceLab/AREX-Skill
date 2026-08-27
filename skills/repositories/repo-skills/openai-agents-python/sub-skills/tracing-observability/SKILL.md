---
name: tracing-observability
description: "Configure OpenAI Agents Python tracing, trace processors, spans,
  sensitive-data controls, logging, usage tracking, and agent visualization."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Tracing & Observability

Use this sub-skill when a task mentions `tracing`, `trace_include_sensitive_data`, `workflow_name`, `trace_id`, `group_id`, `trace_metadata`, `Span`, trace processors, `usage`, debug logs, visualization, Graphviz, or a tracing/export API key.

## Start Here

- Read [references/tracing-reference.md](references/tracing-reference.md) for verified tracing APIs, config fields, processors, spans, sensitive-data controls, usage, logging, and visualization surfaces.
- Use [references/workflows.md](references/workflows.md) for implementation patterns: enable/disable tracing, custom processors, trace metadata, usage collection, visualization generation, and safe logging.
- Use [references/troubleshooting.md](references/troubleshooting.md) for missing trace API keys, disabled tracing, sensitive payload leakage, processor/exporter failures, flush/shutdown behavior, and Graphviz optional dependency issues.
- Run [scripts/check_tracing_config.py](scripts/check_tracing_config.py) for a safe no-network import/config check that masks secret values and can emit JSON.

## Routing Boundaries

- Stay here for `RunConfig.tracing_disabled`, `RunConfig.tracing`, `RunConfig.trace_include_sensitive_data`, `workflow_name`, `trace_id`, `group_id`, `trace_metadata`, `trace()`, span helpers, `TracingProcessor`, `add_trace_processor()`, `set_trace_processors()`, `flush_traces()`, `Usage`, SDK loggers, and `draw_graph()`.
- Route model/provider API key selection, OpenAI-compatible endpoints, Responses websocket transport, and adapter-specific model setup to [../models-providers/SKILL.md](../models-providers/SKILL.md).
- Route core `Runner` call shapes, `RunResult`, streaming event interpretation, sessions, and `RunState` resume mechanics to [../core-runtime/SKILL.md](../core-runtime/SKILL.md).
- Route realtime and voice-specific tracing controls, including audio payload controls, to [../realtime-voice/SKILL.md](../realtime-voice/SKILL.md).

## Fast Decisions

- Tracing is enabled by default; disable it globally with `OPENAI_AGENTS_DISABLE_TRACING=1` or `set_tracing_disabled(True)`, and per run with `RunConfig(tracing_disabled=True)`.
- Set a logical `workflow_name` for every production workflow and use `group_id` to link traces from one conversation or job family.
- Set `trace_include_sensitive_data=False` for sensitive workloads; it redacts model/tool trace payloads but does not automatically sanitize application exceptions, logs, metadata, or custom processor output.
- Use `add_trace_processor()` to observe traces in addition to the default OpenAI exporter; use `set_trace_processors()` only when intentionally replacing default export behavior.
- Call `flush_traces()` after a trace context closes when a short-lived job or background task needs immediate export delivery.
- Use `result.context_wrapper.usage` for token/request accounting and `draw_graph()` for local topology visualization when the optional Graphviz package is available.

## Safety Notes

- Never print API key values, per-run `tracing={"api_key": ...}` values, or local machine paths in diagnostics.
- Keep custom processors non-blocking and defensive; processor/exporter exceptions are logged as non-fatal but can drop observability data.
- Treat verbose logs and exception chains as separate leakage channels from tracing payload controls.
