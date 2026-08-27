---
name: workflow
description: "Build FugueWorkflow DAGs, dataframe utilities, UDF wrappers,
  partitions, checkpoints, and reusable modules."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# workflow

Use this sub-skill for Fugue workflow DAGs and the dataframe-oriented API surface.

## Covers

- `FugueWorkflow` DAG construction and execution
- `WorkflowDataFrame` operations such as `transform`, `process`, `output`, `select`, `join`, `zip`, `partition`, `save`, `checkpoint`, and `assert_eq`
- one-shot dataframe helpers such as `transform(...)`, `out_transform(...)`, `load(...)`, `save(...)`, `select(...)`, `join(...)`, `union(...)`, `aggregate(...)`, `persist(...)`, and `repartition(...)`
- workflow decorators: `creator`, `processor`, `transformer`, `outputter`, `cotransformer`, `output_transformer`, `output_cotransformer`, and `module`

## Excludes

- Full FugueSQL grammar, `YIELD`, `PRINT`, and SQL workflow translation, which belong in `../sql/`
- Engine alias selection, backend package registration, and backend-specific runtime issues, which belong in `../backends/`
- `%load_ext fugue_notebook` and `%%fsql`, which belong in `../notebook/`

## Read these files

- `references/workflow-reference.md` for the API map, workflow patterns, and function-shape conventions
- `references/troubleshooting.md` for common workflow failures and recovery steps
- `scripts/workflow_smoke.py` for a tiny runnable smoke check that exercises the core DAG API

## Typical user prompts

- "How do I build a Fugue workflow around a pandas function?"
- "How do I partition a dataframe before a transform?"
- "How do I checkpoint or save a workflow result?"
- "How do I turn a Python function into a reusable Fugue module?"

If the user is asking about SQL text, engine aliases, or notebook magics, route to the sibling sub-skill instead of expanding this one.
