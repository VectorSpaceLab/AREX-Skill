---
name: observability
description: "Use this sub-skill for EverOS logging, Prometheus metrics,
  OpenTelemetry and Langfuse tracing, recall scores, and observability
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# EverOS Observability

Use this sub-skill when a task asks about structured logs, request IDs, Prometheus metrics, OpenTelemetry/OTLP export, Langfuse traces/scores, privacy controls, or tracing demo workflows.

## Read/run map

- Read [observability](references/observability.md) for logging, `/metrics`, OTel configuration, trace lifecycle, and privacy settings.
- Read [Langfuse](references/langfuse.md) for Langfuse-specific endpoint/key mapping, recall scores, demo/replay choices, and credential boundaries.
- Read [troubleshooting](references/troubleshooting.md) for missing extras, rejected keys, no spans, score issues, content capture surprises, and noisy logs.
- Run [trace_demo_driver.py](scripts/trace_demo_driver.py) against a running server. It defaults to health/config guidance; use `--run-flow` only when you intentionally want a tiny memory write/search to generate traces.

## Key facts

- Structlog and stdlib logging are configured into one console-rendered format.
- Every request gets a request ID before handlers run.
- `/metrics` exposes the Prometheus registry.
- OpenTelemetry is optional and no-op-safe when disabled or the `otel` extra is absent.
- Langfuse integration uses native OTLP/HTTP plus optional Langfuse scores; EverOS does not require a Langfuse SDK.
- `capture_content=false` by default; set it true only after considering privacy.
