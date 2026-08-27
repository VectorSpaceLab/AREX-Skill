---
name: sql-backend
description: "Use Lux optional PostgreSQL SQL executor workflows with
  LuxSQLTable and JoinedSQLTable."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# sql-backend

Use this sub-skill when a user wants Lux to explore data that already lives in a PostgreSQL database through `LuxSQLTable`, `JoinedSQLTable`, and the SQL executor.

SQL support is optional and service-backed. Do not assume that a PostgreSQL service, database credentials, fixture tables, `psycopg2`, or SQLAlchemy are available. The required CPU Lux environment verifies base Pandas/visualization workflows only; SQL native behavior remains an optional backend until a user supplies a database service.

## Route map

- Start with [`references/sql-workflows.md`](references/sql-workflows.md) for connection setup, executor switching, table/view setup, `JoinedSQLTable`, query-template behavior, and safe schema notes.
- Use [`references/api-reference.md`](references/api-reference.md) when the task depends on exact APIs, signatures, executor behavior, generated SQL patterns, or class limitations.
- Use [`references/troubleshooting.md`](references/troubleshooting.md) for missing connector, missing table, PostgreSQL service, schema, permissions, expensive metadata, or unsupported Pandas/SQL operations.
- Use [`scripts/sql_table_probe.py`](scripts/sql_table_probe.py) before constructing a `LuxSQLTable` when credentials are available and the user wants a non-destructive connectivity/table probe.

## Minimal decision checklist

1. Confirm the user has PostgreSQL >= 9.5 and a table or view that already exists.
2. Confirm exactly one connector path: a `psycopg2` connection/DSN or a SQLAlchemy PostgreSQL engine/URL.
3. Configure Lux with `lux.config.set_SQL_connection(connection_or_engine)` and keep `lux.config.set_executor_type("SQL")` in mind when refreshing SQL executor state.
4. Bind the table with either `lux.LuxSQLTable(table_name="...")` or `sql_tbl.set_SQL_table("...")`.
5. Avoid ordinary Pandas manipulation on `LuxSQLTable`; if the user needs arbitrary transforms, perform them in SQL first or load a small result into Pandas and use Lux's Pandas workflow.
6. Treat joins as a special, permission-sensitive `JoinedSQLTable(joins=[...])` workflow, not as a normal SQL executor capability.

## Do not use this sub-skill for

- In-memory Pandas `DataFrame` recommendations and intents; route to the Pandas/intent sub-skill.
- `Clause`, `Vis`, `VisList`, and export-only questions that do not involve a SQL-backed table; route to the visualization/export sub-skill.
- Global Lux style, widget, or action configuration unless the issue is specific to SQL executor switching.
