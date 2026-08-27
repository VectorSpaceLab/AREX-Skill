---
name: question-answering
description: "Routes KAG solver, query, trace, and reasoner workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Question Answering

Use this sub-skill when the user already has a KAG project and wants to ask questions, inspect traces, or understand which solver pipeline is active.

## Triggers

Common requests include:

- run or debug a KAG query pipeline
- choose between `index_pipeline`, `kag_static_pipeline`, `kag_iterative_pipeline`, `naive_rag_pipeline`, `naive_generation_pipeline`, `self_cognition_pipeline`, or `mcp_pipeline`
- use `knext reasoner execute` or `knext thinker execute`
- diagnose `UNKNOWN` answers, missing references, or planner/executor confusion
- inspect solver-side config before a live query run

## Start here

1. Read `references/workflows.md` for the query flow and CLI usage.
2. Use `scripts/inspect_solver_config.py` to summarize the active solver config.
3. Read `references/api-reference.md` when you need signatures, pipeline names, or the `main_solver.py` call shape.
4. Read `references/troubleshooting.md` when answers are empty, traces are missing, or the wrong pipeline is selected.

## What belongs here

This sub-skill owns the tasks that turn a built KAG project into answers and traces:

- `SolverMain.invoke` and `SolverMain.ainvoke`
- query-time pipeline selection
- `knext reasoner execute` with either `--dsl` or `--file`
- `knext thinker execute`
- solver config inspection and answer-trace troubleshooting

## What does not belong here

- Project creation, schema commit, or builder configuration goes to `knowledge-construction`.
- MCP server launch, distributed submission, and benchmark planning go to `mcp-and-automation`.
- Cross-cutting install/import issues go to the root troubleshooting files.

## Bundled helper

- `scripts/inspect_solver_config.py` — prints a redacted summary of the solver and retrieval config.

## Working rule

If the query workflow depends on a builder problem, check the builder/index state before trying to fix the solver.
If the question is citation-sensitive, prefer a route that can emit references instead of a generation-only path.

## Common decisions

- If the answer is `UNKNOWN`, check retrieval coverage before changing the generator.
- If the trace has no references, verify that the chosen pipeline is an evidence-backed one.
- If `knext reasoner execute` is being used, confirm that exactly one of `--dsl` or `--file` is supplied.
- If the config has multiple pipeline selectors, confirm which key actually wins in that project.
- If a query depends on MCP tools, validate the tool config before treating the solver as broken.

## What a good answer should include

- the active pipeline and why it matches the user's question
- the query-time config keys that control the route
- whether the missing evidence comes from the builder side or the solver side
- the next safe command or config edit to try
- any conditions that would make the query path unsuitable without rebuilding the project

## Stop conditions

Stop and ask for confirmation when the fix would:

- require a new project build or schema commit
- need an external server or model service that is not available
- change the query route in a way that could alter expected citations
- rely on a custom component that has not been imported into the project

## Bundled helper
