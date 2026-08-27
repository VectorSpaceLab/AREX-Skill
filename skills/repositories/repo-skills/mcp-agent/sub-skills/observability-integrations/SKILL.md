---
name: observability-integrations
description: "Configure mcp-agent logging, OpenTelemetry tracing, token
  accounting, streaming, provider extras, local OpenAI-compatible providers, and
  LangChain/CrewAI tool adapters."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# observability-integrations

Use this sub-skill when a task involves mcp-agent observability or optional ecosystem integrations: structured logger transports, OpenTelemetry exporters, usage telemetry, token counters, progress displays, streaming callbacks, provider-specific extras, local OpenAI-compatible endpoints, LangChain tools, or CrewAI tools.

## Start Here

1. Read `references/logging-and-tracing.md` for logger transport configuration, OTEL exporter syntax, trace helpers, token accounting, progress displays, streaming events, and safe event-log inspection.
2. Read `references/provider-integrations.md` for optional provider extras, import-vs-credential failures, model selector knobs, LM Studio/local OpenAI-compatible endpoints, and LangChain/CrewAI wrappers.
3. Read `references/troubleshooting.md` when config validation, OTEL export, JSONL logs, token counters, progress output, streaming, provider imports, adapters, or local model endpoints fail.
4. Run `python scripts/check_observability_config.py --help` before editing config; use `--config mcp_agent.config.yaml --secrets mcp_agent.secrets.yaml --json` for credential-redacted diagnostics.
5. Run `python scripts/summarize_event_log.py --help` and then point it at a small JSONL event log to validate file transport output without replaying interactive progress UI.

## Core Workflows

- Enable structured logging with `logger.transports`, `logger.level`, `logger.progress_display`, and optional file/HTTP settings; prefer `file` plus `console` for local debugging and add HTTP only when an endpoint is intentionally configured.
- Enable tracing with `otel.enabled: true`, `otel.service_name`, `otel.sample_rate`, and one or more exporters: `console`, `file`, or `otlp` with endpoint and optional headers.
- Correlate logs and traces by running inside `MCPApp.run()` and using `app.logger`, `running_app.context.logger`, or `agent.logger`; active spans inject `trace_id` and `span_id` into events.
- Inspect token usage through the app or agent context token counter after AugmentedLLM calls; use progress display only for interactive TTY runs and use logs or summaries in CI.
- Treat provider SDKs and tool ecosystems as optional extras: import the relevant AugmentedLLM/tool adapter only after installing the matching extra and configuring non-secret model defaults.
- For streaming, consume `generate_stream()` events by type and keep callbacks non-blocking; use `generate_str_stream()` only when text deltas are enough.

## Route Elsewhere

- Use `../core-sdk/SKILL.md` for MCPApp, Agent, Settings, config/secrets basics, RequestParams fundamentals, local tool decorators, and normal provider setup.
- Use `../cli-cloud-operations/SKILL.md` for cloud log tailing, cloud logger commands, deployment diagnostics, app/server status, and CLI authentication.
- Use `../mcp-server-integration/SKILL.md` for MCP auth internals, server creation, transport semantics, upstream session lifecycle, and app-as-server behavior.
- Use `../workflow-patterns/SKILL.md` for routers, orchestrators, parallel workflows, evaluator loops, and durable workflow composition.

## Bundled Helpers

```bash
python scripts/check_observability_config.py --config mcp_agent.config.yaml --json
python scripts/summarize_event_log.py logs/mcp-agent.jsonl --limit 50 --json
```

Both helpers are self-contained and credential-safe. They do not import provider SDKs, contact external collectors, replay interactive displays, or require the original source repository.
