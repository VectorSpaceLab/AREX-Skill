---
name: sdk-and-tracing
description: "Traceloop SDK initialization, decorator tracing, manual spans, and
  client-facing observability workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# sdk-and-tracing

Use this sub-skill for Traceloop SDK bootstrap, offline tracing, and user-app tracing workflows.

## Use it when
- you need to initialize `Traceloop`
- you need exporter or processor setup for local debugging or Traceloop/OTLP delivery
- you need decorator-based spans from `@workflow`, `@task`, `@agent`, `@tool`, or `@conversation`
- you need manual LLM spans via `track_llm_call`
- you need association properties or prompt context on spans
- you need the prompt, dataset, experiment, user-feedback, or guardrail surfaces at a high level

## Install choices
- Base SDK: `traceloop-sdk`
- Dataset helpers: `traceloop-sdk[datasets]` when you need CSV/DataFrame helpers
- Debug exporters: `InMemorySpanExporter` for assertions, `ConsoleSpanExporter` for inspection

## Route elsewhere
- [`../instrumentations/SKILL.md`](../instrumentations/SKILL.md) for provider/vector/framework wrapper specifics and target-library requirements
- [`../semantic-conventions/SKILL.md`](../semantic-conventions/SKILL.md) for exact GenAI/span-attribute tables and migration details
- [`../repo-development/SKILL.md`](../repo-development/SKILL.md) for uv/Nx, test commands, and VCR policy

## Read first
- [`references/sdk-api.md`](references/sdk-api.md)
- [`references/sdk-workflows.md`](references/sdk-workflows.md)
- [`references/troubleshooting.md`](references/troubleshooting.md)

## Runtime helpers
- [`scripts/offline_tracing_smoke.py`](scripts/offline_tracing_smoke.py)
- [`scripts/manual_span_smoke.py`](scripts/manual_span_smoke.py)

## Operating notes
- `use_attributes=True` is the current default; `use_legacy_attributes` is deprecated.
- `TRACELOOP_TRACE_CONTENT=false` intentionally hides decorated entity inputs/outputs and prompt content.
- If `Traceloop.init()` receives both `exporter` and `processor`, the exporter is ignored; wrap the exporter inside the processor instead.
- `Traceloop.init()` returns a client only when it is using the Traceloop endpoint path with an API key and no custom exporter or processor.
- Stay at SDK/bootstrap depth here; do not descend into provider wrapper internals or exact semantic-convention tables.
