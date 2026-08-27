# Evals and Graph Troubleshooting

## Evals vs Unit Tests

- Symptom: an eval is used as the only guard for deterministic code behavior.
- Cause: confusing quality measurement with regression testing.
- Fix: keep fast `pytest` unit tests for exact contracts and use evals for datasets, model/application behavior, scorer comparison, repeated runs, and qualitative metrics. For agent unit tests, route to `../agent-core/SKILL.md` and use `TestModel` or `FunctionModel`.

## Missing Ground Truth

- Symptom: `EqualsExpected()` records no assertion, custom evaluators see `ctx.expected_output is None`, or report evaluators cannot compute expected labels.
- Cause: cases lack `expected_output` or required `metadata` keys.
- Fix: include `expected_output` for expected-vs-actual checks and add typed `metadata` for auxiliary labels, thresholds, rubrics, or required terms. In custom evaluators, handle missing metadata explicitly and return an `EvaluationReason` with a useful reason.

## Invalid Evaluator Return Types

- Symptom: evaluator execution fails or report fields do not contain expected values.
- Cause: `Evaluator.evaluate()` returned an unsupported object, nested dict, Pydantic model, list, or non-finite float.
- Fix: return `bool`, finite `float`, `int`, `str`, `EvaluationReason`, or `dict[str, scalar | EvaluationReason]`. Use booleans for assertions, numeric values for scores, and strings for labels. Keep result names stable when report evaluators read them.

## Evaluator Name Drift

- Symptom: report evaluators cannot find a score, label, or assertion key after a refactor.
- Cause: evaluator result names changed or a mapping key differs from `score_key`, `positive_key`, `predicted_key`, or `expected_key`.
- Fix: override `get_default_evaluation_name()` for single-output evaluators, keep mapping keys explicit, and bump `get_evaluator_version()` when behavior changes enough that old scores should remain distinguishable.

## Serialized Dataset Load Errors

- Symptom: `Dataset.from_file()` raises validation errors or cannot load custom evaluators.
- Cause: wrong `Dataset[...]` generic parameters, invalid YAML/JSON shape, missing custom evaluator registry, or stale schema.
- Fix: load with matching `Dataset[InputsT, OutputT, MetadataT]`, pass `custom_evaluator_types` and `custom_report_evaluator_types`, regenerate the schema with `to_file()`, and prefer YAML for human-edited datasets.

## Flaky LLM-as-Judge Results

- Symptom: pass rates swing between runs or failures cluster around judge calls.
- Cause: stochastic judge model, rate limits, rubric ambiguity, or unbounded concurrency.
- Fix: start with deterministic evaluators, make rubrics narrow, set `max_concurrency`, use `repeat` to measure variability, configure `retry_evaluators` only for transient exceptions, and route judge model/provider setup to `../models-and-providers/SKILL.md`.

## Logfire Optional Dependency or Trace Gaps

- Symptom: `import logfire` fails, eval traces are missing, or `ctx.span_tree` raises a span-recording error.
- Cause: `logfire` optional dependency is not installed, tracing was configured too late, or the OpenTelemetry provider is incompatible.
- Fix: keep Logfire optional in reusable scripts, configure it before running/instrumenting tasks, use `send_to_logfire='if-token-present'` for credential-safe scripts, and avoid depending on `ctx.span_tree` unless tracing setup is part of the task.

## Concurrency Hides Failures

- Symptom: errors are hard to read, external resources are overwhelmed, or result ordering surprises assertions.
- Cause: evals and graph maps run cases/paths concurrently by default.
- Fix: set `Dataset.evaluate_sync(..., max_concurrency=1, progress=False)` while debugging. In graph tests, sort joined lists when order is not meaningful, or use reducers/data structures that preserve the semantics you need.

## Graph Generic Typing Mistakes

- Symptom: type checkers complain, graph building fails, or `ctx.state`, `ctx.deps`, or `ctx.inputs` has an unexpected type.
- Cause: `GraphBuilder` type parameters do not match `StepContext`, `BaseNode`, or `GraphRunContext` annotations.
- Fix: align generics in order: state, deps, input for `StepContext`; state, deps, run-end type for `BaseNode`; state, deps for `GraphRunContext`. Use `None` as a placeholder when a later generic slot is needed.

## Legacy `Graph` Deprecation Warning

- Symptom: importing `Graph` from `pydantic_graph` emits `PydanticGraphDeprecationWarning`.
- Cause: the original `BaseNode`-based runner is deprecated at the top-level namespace.
- Fix: use `GraphBuilder` for new code. For existing `BaseNode` classes, integrate them with builder `g.node(NodeType)` and keep `BaseNode`, `End`, and `GraphRunContext` imports.

## Diagram Edges Do Not Match Type Hints

- Symptom: Mermaid output misses an edge, shows an unexpected edge, or has unlabeled decision/fork paths.
- Cause: missing return annotations, unresolved forward references, an edge path was not passed to `g.add(...)`, or a decision branch/fork was not wired to a destination.
- Fix: add explicit return hints to every step and `BaseNode.run()`, use `from __future__ import annotations` when classes reference each other, add every `g.edge_from(...).to(...)` path, and use `.label(...)` or `g.decision(note=...)` for diagram clarity.

## Empty Map Never Reaches Join

- Symptom: a graph mapping an empty iterable hangs or skips expected aggregation behavior.
- Cause: the map fork has no downstream item tasks and no join target to receive the initial value.
- Fix: create the join first and pass `downstream_join_id=collect.id` to `.map(...)` or `add_mapping_edge(...)` when empty iterables are valid inputs.

## Mutable Join Initial Values Leak State

- Symptom: results from different runs share accumulated list/dict values.
- Cause: a mutable object was supplied as `initial` and reused.
- Fix: prefer `initial_factory=list[T]`, `initial_factory=dict[K, V]`, or another factory for mutable reducer state. Reserve `initial=0` or similar immutable values for numeric reducers.

## Decision Branch Does Not Match

- Symptom: graph fails at a decision node for an apparently valid value.
- Cause: branch order, a missing catch-all branch, using a union or `Literal` without `TypeExpression`, or a predicate that returns false.
- Fix: order branches from most specific to broadest, use `TypeExpression[Literal['value']]` or `TypeExpression[int | float]` for complex type expressions, add `matches=` predicates carefully, and include `g.match(object)` only when a default branch is intended.
