---
name: observability-and-hooks
description: "Guides agents configuring CrewAI telemetry, tracing, observability
  integrations, event listeners, execution hooks, kickoff hooks, output logs,
  task outputs, and security fingerprints."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# CrewAI Observability and Hooks

Use this sub-skill when a task involves CrewAI tracing, anonymous telemetry, observability providers, event listeners, LLM/tool execution hooks, before/after kickoff hooks, output logs, latest task outputs, or component fingerprints.

## Route by Intent

- Need Crew/Flow tracing enablement, telemetry disable switches, privacy boundaries, output logs, latest task outputs, or replay-observability data? Read [Tracing reference](references/tracing-reference.md).
- Need `@before_kickoff`, `@after_kickoff`, LLM hooks, tool hooks, hook registration/cleanup, event listener setup, callback signatures, or hook ordering? Read [Hooks reference](references/hooks-reference.md).
- Need OpenTelemetry exporter patterns, OpenLIT, Datadog, Langfuse, LangDB, Phoenix, Portkey, Weave, Opik, MLflow, Patronus, or other provider integration boundaries? Read [Integrations](references/integrations.md).
- Need to debug duplicate/missing traces, env override confusion, endpoint/protocol mismatches, callback signature errors, hooks overriding each other, log/task-output gaps, or fingerprint changes? Read [Troubleshooting](references/troubleshooting.md).
- Need a safe read-only snapshot of tracing-related env vars and installed observability packages? Run [check_tracing_config.py](scripts/check_tracing_config.py) with `--help` first.

## Boundaries

- Stay here for tracing, telemetry, event listeners used for monitoring, execution hooks, kickoff hooks, output logs, task output audit data, and fingerprints.
- Use [flows-and-events](../flows-and-events/SKILL.md) for `Flow`, `@start`, `@listen`, `@router`, flow graph mechanics, route labels, plotting, and flow persistence semantics.
- Use [cli-and-projects](../cli-and-projects/SKILL.md) for exact `crewai` command syntax, project scaffolding, `crewai traces`, `crewai log-tasks-outputs`, replay flags, and deployment commands.
- Use [core-runtime](../core-runtime/SKILL.md) for `Agent`, `Task`, `Crew`, `Process`, `CrewOutput`, `TaskOutput`, guardrails, callbacks outside observability, and core kickoff behavior.
- Use [tools-and-mcp](../tools-and-mcp/SKILL.md) for tool implementation, official tool classes, MCP adapters, and tool publishing beyond hook interception.
- Return to the [CrewAI root skill](../../SKILL.md) when a request spans multiple CrewAI capability areas and needs root routing context.

## Safe Defaults

- Prefer read-only inspection first: env/package checks, config review, and hook registration review before running a crew, flow, tool, LLM, or external exporter.
- Treat hosted trace dashboards and third-party observability providers as credential-bound: document required env vars, but do not send traces or initialize SDKs without approval.
- Use `tracing=False` on a specific Crew/Flow when a run must not emit CrewAI built-in traces; use telemetry disable env vars for OpenTelemetry-style anonymous telemetry spans.
- Keep hooks small and deterministic; avoid network calls, destructive tools, blocking prompts, or secret-printing inside global hooks unless the user explicitly approves the side effect.
- Clear or unregister global hooks in tests, notebooks, and long-lived workers to prevent duplicate behavior across repeated imports or `@CrewBase` instantiations.
