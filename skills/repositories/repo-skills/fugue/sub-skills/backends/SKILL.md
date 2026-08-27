---
name: backends
description: "Select, register, and troubleshoot Fugue execution backends and
  plugin packages."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# backends

Use this sub-skill for execution-engine and backend-package questions.

## Covers

- `make_execution_engine(...)`, `engine_context(...)`, and engine resolution rules
- `register_execution_engine(...)`, `register_sql_engine(...)`, and the default-engine registration helpers
- backend plugin packages and aliases for Native, DuckDB, Dask, Spark, Ray, Ibis, and Polars
- backend import side effects, object inference, and config-specific runtime failures

## Excludes

- Workflow DAG mechanics and dataframe transformations, which belong in `../workflow/`
- FugueSQL syntax, `YIELD`, and `PRINT`, which belong in `../sql/`
- Notebook extension setup and `%%fsql`, which belong in `../notebook/`

## Read these files

- `references/backend-reference.md` for the backend matrix, alias map, and resolution order
- `references/troubleshooting.md` for optional backend failures and service-specific issues
- `scripts/smoke_backends.py` for a safe import-and-registration smoke check

## Typical user prompts

- "Why does Fugue not recognize my Spark/Dask/Ray object?"
- "How do I select a DuckDB or Spark execution engine?"
- "How do I register a custom execution engine with Fugue?"
- "Which Fugue extra do I need for notebook, DuckDB, or Polars support?"

If the task is mainly about writing the dataframe workflow or FugueSQL text that happens to run on a backend, open the workflow or SQL sub-skill first and only come here for engine selection details.
