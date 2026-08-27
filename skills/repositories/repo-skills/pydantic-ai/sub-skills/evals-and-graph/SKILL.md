---
name: evals-and-graph
description: "Guides agents building Pydantic Evals datasets, evaluators,
  reports, Logfire evals, and pydantic-graph GraphBuilder state-machine
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Evals and Graph

Use this sub-skill when a task involves `pydantic_evals` datasets, cases, evaluators, reports, experiment runs, Logfire-backed eval analysis, or `pydantic_graph` state machines built with `GraphBuilder`.

## Read First

- Read [references/evals-workflows.md](references/evals-workflows.md) when creating `Dataset`/`Case` objects, custom evaluators, report evaluators, serialized YAML/JSON datasets, concurrency/retry settings, lifecycle hooks, or agent-eval integrations.
- Read [references/graph-workflows.md](references/graph-workflows.md) when designing a graph with `GraphBuilder`, `StepContext`, typed state/deps, `BaseNode` interop, decisions, joins, maps, broadcasts, or Mermaid diagrams.
- Read [references/troubleshooting.md](references/troubleshooting.md) when eval outputs, evaluator return types, optional Logfire tracing, graph typing, legacy `Graph`, joins, or rendered edges behave unexpectedly.
- Run [scripts/evals_graph_smoke.py](scripts/evals_graph_smoke.py) after installing `pydantic-evals` and `pydantic-graph` to verify a no-network eval plus a builder graph run.

## Routing

- Use evals for repeatable system-quality measurement over cases; keep ordinary unit tests for deterministic API contracts, regressions, and fast local assertions.
- Start eval work with typed `Dataset[InputsT, OutputT, MetadataT]`, named `Case(...)` rows, deterministic code evaluators, and `evaluate_sync(..., progress=False, max_concurrency=1)` while debugging.
- Add `LLMJudge` only when deterministic checks cannot express the quality target; route judge model/provider selection to `../models-and-providers/SKILL.md`.
- Evaluate Pydantic AI agents by wrapping `agent.run_sync()` or `agent.run()` as the dataset task; route agent construction, `TestModel`, `FunctionModel`, and `Agent.override(...)` details to `../agent-core/SKILL.md`.
- Use `GraphBuilder` for new graph workflows; import the legacy `Graph` runner only to maintain existing code and expect a deprecation warning when imported from `pydantic_graph`.

## Boundaries

- For core `Agent` construction, deterministic `TestModel` tests, run methods, dependencies, streaming, and message history, read `../agent-core/SKILL.md`.
- For LLM judge provider strings, optional provider extras, model settings, fallback, and auth diagnostics, read `../models-and-providers/SKILL.md`.
- For function tools, toolsets, approvals, deferred calls, and `ModelRetry`, read `../tools-and-toolsets/SKILL.md`.
- For structured output/message serialization used by evaluated agents, read `../outputs-and-messages/SKILL.md`.
- For maintainer VCR/cassette, native repo test selection, and CI workflow mechanics, read `../repo-development/SKILL.md` when that sub-skill exists.

## Non-Negotiables

- Keep bundled eval examples deterministic and no-network unless the user explicitly asks for live provider judging or Logfire upload.
- Give every eval case a useful `name`; include `expected_output` or metadata whenever evaluators need ground truth.
- Return evaluator scalars, `EvaluationReason`, or mappings of those values; do not return arbitrary models or nested dicts from `Evaluator.evaluate()`.
- Use builder-first graph APIs: `GraphBuilder(...)`, `@g.step`, `g.edge_from(...).to(...)`, `g.decision()`, `g.join(...)`, `.map()`, and `graph.run(...)`.
- Keep graph state and deps types consistent across `GraphBuilder`, `StepContext`, `BaseNode[...]`, and `GraphRunContext[...]` annotations.
