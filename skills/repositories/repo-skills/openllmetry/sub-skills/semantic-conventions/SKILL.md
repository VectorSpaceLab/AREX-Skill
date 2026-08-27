---
name: semantic-conventions
description: "Understand and validate OpenLLMetry's GenAI semantic-convention layer."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Semantic Conventions

Use this sub-skill when the task is about OpenLLMetry's semantic-convention contract rather than a provider wrapper or SDK decorator workflow.

## Route here for

- Importing or validating `opentelemetry.semconv_ai` symbols such as `SpanAttributes`, `GenAISystem`, `Meters`, `Events`, `EventAttributes`, `LLMRequestTypeValues`, and `TraceloopSpanKindValues`.
- Mapping upstream OpenTelemetry GenAI attributes such as `gen_ai.provider.name`, `gen_ai.input.messages`, `gen_ai.output.messages`, `gen_ai.tool.definitions`, and `gen_ai.response.finish_reasons`.
- Understanding Traceloop workflow/task/agent/tool span attributes and vector DB event attributes.
- Migrating legacy `LLM_*` names to current `GEN_AI_*` or upstream `GenAIAttributes` names without breaking compatibility aliases.
- Checking whether an installed environment exposes the expected constants and enums using `scripts/check_semconv_constants.py`.

## Use the bundled references

- `references/semantic-attributes.md` — import map, constant groups, message/tool/finish-reason validation rules, and compliance-helper expectations.
- `references/migration-notes.md` — legacy alias categories, provider-name migration, and safe before/after snippets.
- `references/troubleshooting.md` — version drift, deprecated `gen_ai.system`, content/event gating, JSON schemas, finish-reason placement, and alias confusion.
- `scripts/check_semconv_constants.py` — no-network helper for public constant/enumeration checks; supports `--json`.

## Route elsewhere

- Provider wrapper patch points, `.instrument()` behavior, optional target-library failures, and VCR/live-service provider behavior: `../instrumentations/SKILL.md`.
- Traceloop SDK initialization, decorators, manual spans, exporters/processors, and app-level content-tracing configuration: `../sdk-and-tracing/SKILL.md`.
- Checkout-level commands, package maintenance, lint/test selection, and VCR cassette policy: `../repo-development/SKILL.md`.

## Operating checks

When validating a semantic-convention change, keep these invariants visible:

1. New provider spans should use upstream `gen_ai.provider.name`; treat `gen_ai.system` as deprecated compatibility data.
2. Content-bearing message attributes must use the upstream JSON-array fields; finish-reason metadata must not be dropped solely because content tracing is disabled.
3. `SpanAttributes.LLM_*` names are intentionally retained for older packages, but new code should use current `GEN_AI_*` names or upstream `GenAIAttributes` constants.
4. The shared `_testing.py` helper is the source pattern for constant/enumeration compliance checks; use the bundled checker for a safe environment probe.
