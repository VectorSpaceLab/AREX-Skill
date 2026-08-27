# SQL safety and metadata

This package can inspect database metadata without an LLM and can ask an LLM-backed `SQLDatabaseAgent` to generate a query. The important safety boundary is that generated SQL is still model output: use a read-only database role and keep `safe_mode=True` by default.

## What `_validate_sql` enforces

With `safe_mode=True`, `_validate_sql(sql_text, safe_mode=True)` returns `None` only when all of these checks pass:

1. The SQL text is non-empty.
2. The stripped, lower-cased SQL starts with `select`.
3. The lower-cased SQL text does not contain any of these substrings anywhere: `insert`, `update`, `delete`, `drop`, `alter`, `truncate`, `create`, `replace`.

When a check fails, `_validate_sql` returns an error string such as:

- `SQL generation failed: empty query.`
- `Only read-only SELECT queries are allowed (safe_mode=True).`
- `Write operations are not allowed; ensure the query is read-only (safe_mode=True).`

With `safe_mode=False`, the helper returns `None` without checking. Do not use `safe_mode=False` unless a human explicitly accepts the risk and the database connection itself cannot modify production data.

## Consequences of the validator design

The validator is intentionally conservative and string-based. This makes it easy to smoke test, but it is not a complete SQL parser.

| Case | Result | Operating implication |
| --- | --- | --- |
| `SELECT col FROM table` | accepted when no blocked substrings appear | Normal path. |
| `WITH ... SELECT ...` | rejected because it does not start with `select` | Ask for a plain `SELECT` query or manually review before using any bypass. |
| `SHOW TABLES`, `DESCRIBE table`, `EXPLAIN SELECT ...` | rejected because they do not start with `select` | Use SQLAlchemy metadata inspection instead of DB-specific metadata commands. |
| `SELECT last_update FROM orders` | can be rejected because `update` appears inside an identifier | This is a conservative false positive. Use a read-only account and manual review if bypass is truly needed. |
| SQL with a forbidden word in a string literal or comment | can be rejected | Remove comments/literals from the generated query when possible or manually review. |
| SQL obfuscated to avoid keyword matching | may not be fully understood by the string check | Do not rely on the helper alone for adversarial SQL; use read-only DB privileges. |

## Defense-in-depth checklist

Before executing model-generated SQL:

- Use a database role with only the minimum read permissions required for the task.
- Prefer replicas, snapshots, or disposable copies for exploratory work.
- Avoid passing full connection URLs or authentication details to model prompts, logs, or user-facing reports.
- Keep `safe_mode=True` for the agent.
- Inspect `agent.get_sql_query_code()` after execution and before handing results downstream.
- Check `agent.get_response().get("sql_database_error")`; do not treat `None` data as a valid empty result until errors are checked.
- If `log=True`, make sure the log directory is intended for generated code and does not leak local machine paths in final reports.

## Metadata collection behavior

`get_database_metadata(connection, n_samples=10)` accepts a SQLAlchemy `Engine` or `Connection` and returns a dictionary with:

- `dialect`: SQLAlchemy dialect name.
- `driver`: SQLAlchemy driver name.
- `connection_url`: rendered with password hiding when SQLAlchemy supports it. This can still reveal host, user, or database names; redact before sharing.
- `schemas`: list of schema objects.
- Each schema object includes `schema_name` and `tables`.
- Each table object includes `table_name`, `columns`, `primary_key`, `foreign_keys`, and `indexes`.
- Each column object includes `name`, `type`, and `sample_values`.

The metadata helper uses SQLAlchemy inspection and the dialect identifier preparer to quote schema, table, and column names during sample queries. This is important for identifiers containing spaces, mixed case, or reserved words.

## Sampling behavior by dialect

`build_query(col_name_quoted, table_name_quoted, n, dialect_name)` generates sampling SQL for each column:

| Dialect match | Sample query shape |
| --- | --- |
| PostgreSQL | `SELECT column FROM table ORDER BY RANDOM() LIMIT n` |
| MySQL | `SELECT column FROM table ORDER BY RAND() LIMIT n` |
| SQLite | `SELECT column FROM table ORDER BY RANDOM() LIMIT n` |
| Microsoft SQL Server | `SELECT TOP n column FROM table ORDER BY NEWID()` |
| Fallback / Oracle-style | `SELECT column FROM table WHERE ROWNUM <= n` |

Sampling is read-only, but it can still be expensive on large tables because random ordering may scan data. Keep `n_samples` low, scope the visible schema, or use a database copy/replica for large production databases.

## Metadata privacy notes

- Sample values can contain personal or sensitive data. If the user only needs table and column names, redact or remove `sample_values` before reporting.
- The connection URL hides passwords but can still disclose hosts or database names. Omit it from user-facing summaries unless explicitly needed.
- Primary and foreign keys may disclose business structure. Share only the minimum metadata necessary for the task.

## Bundled smoke coverage

Run `scripts/smoke_sql_safety.py` from this sub-skill to check the installed package's SQL helper behavior without LLM calls, external services, downloads, training, app launches, or destructive writes. The script creates an in-memory SQLite database, inspects metadata, verifies dialect-specific sample-query generation, and asserts that unsafe SQL is rejected by `_validate_sql`.
