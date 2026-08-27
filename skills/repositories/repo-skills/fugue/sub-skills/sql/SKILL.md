---
name: sql
description: "Translate FugueSQL strings into workflows, manage YIELD and PRINT
  statements, and run SQL-oriented dataframe tasks."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# sql

Use this sub-skill for FugueSQL strings and workflow translation.

## Covers

- `fugue_sql(...)` for the single-result SQL helper
- `fsql(...)`, `fugue_sql_flow(...)`, and `FugueSQLWorkflow` for full multi-output SQL workflows
- `raw_sql(...)` for direct `SELECT` statements on the execution engine
- SQL workflow syntax such as `CREATE`, `SELECT`, `TRANSFORM USING`, `OUTPUT USING`, `PRINT`, and `YIELD`
- templated SQL variables, implicit dataframe lookup, and case/dialect knobs

## Excludes

- Workflow DAG mechanics that do not require FugueSQL text, which belong in `../workflow/`
- Backend alias selection and registration, which belong in `../backends/`
- Notebook cell magics and `%%fsql`, which belong in `../notebook/`

## Read these files

- `references/sql-reference.md` for syntax, helper signatures, and query-shape examples
- `references/troubleshooting.md` for parser, import, and workflow translation failures
- `scripts/sql_smoke.py` for a tiny runnable smoke check

## Typical user prompts

- "How do I write a FugueSQL query that calls a Python transform?"
- "How do I use `fsql`, YIELD, or PRINT in FugueSQL?"
- "Why does my FugueSQL query work in one backend but not another?"
- "How do I pass external dataframes or variables into FugueSQL?"

If the request is about engine registration, notebook execution, or plain workflow DAGs without FugueSQL text, route to the sibling sub-skill instead of expanding this one.
