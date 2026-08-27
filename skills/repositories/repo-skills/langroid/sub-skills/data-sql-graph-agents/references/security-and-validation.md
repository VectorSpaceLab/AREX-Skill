# Security and validation

This sub-skill is built around default-off safety gates. Treat the prompt, the
schema text, and any data read back from the database as untrusted unless you
have explicitly constrained them.

## TableChatAgent / pandas evaluation

- `full_eval=False` by default.
- When `full_eval=False`, the pandas expression is sanitized before evaluation.
- Even with `full_eval=True`, the evaluator still runs with restricted builtins;
  that is a hardening layer, not a full sandbox.
- For mutations, prefer `df.assign(...)` and other expression-based rewrites
  that return a new dataframe.

## SQLChatAgent

Default policy:

- `allowed_statement_types` defaults to `['SELECT']`.
- `allow_dangerous_operations=False` by default.
- Queries are parsed with `sqlglot` and rejected before execution when the
  top-level statement type is not allowlisted.
- Multi-statement queries are checked statement by statement.
- Nested writes such as `WITH ... DELETE ... SELECT ...` and `SELECT ... INTO`
  are treated as writes and rejected when writes are not allowlisted.
- Dangerous SQL primitives are blocked by default, including patterns such as
  PostgreSQL `COPY ... PROGRAM`, `pg_read*`, `lo_import/export`, MySQL
  `INTO OUTFILE`, `LOAD_FILE`, `LOAD DATA`, SQLite `load_extension` and
  `ATTACH`, MSSQL `xp_cmdshell`, `sp_OACreate`, `OPENROWSET`, `BULK INSERT`,
  and stored-program or extension creation.
- If you need writes, extend `allowed_statement_types` explicitly.
- If you set `allow_dangerous_operations=True`, the safety checks are bypassed;
  use that only with a least-privilege database role and trusted prompts.

## Neo4jChatAgent and CSVGraphAgent

Default policy:

- `allow_dangerous_operations=False`.
- The retrieval path is read-only.
- The write path is allowed to write, but still rejects code-execution, file,
  and network primitives by default.
- The Cypher validator strips comments and string/backtick literals before
  checking for dangerous clauses.
- Blocked examples include `LOAD CSV`, `apoc.*`, `dbms.*`, and `CALL db.*`.
- `CSVGraphAgent` reuses the Neo4j Cypher validator before each row write, so a
  dangerous generated Cypher statement never reaches `write_query` when the
  gate is active.

## ArangoChatAgent

Default policy:

- `allow_dangerous_operations=False`.
- The retrieval path is read-only.
- The write path can create or modify graph data, but user-defined AQL function
  calls are blocked by default.
- The AQL validator strips comments and literal spans before checking for
  unsafe constructs.
- Blocked examples include `namespace::function(...)` UDF calls and write
  operations such as `INSERT`, `UPDATE`, `REPLACE`, `REMOVE`, and `UPSERT`
  on the read path.
- If you set `allow_dangerous_operations=True`, the safety checks are bypassed;
  use that only with a least-privilege ArangoDB role and trusted prompts.

## Result bounds and truncation

Safety also includes limiting how much data comes back:

- `SQLChatAgentConfig.max_result_rows` truncates SQL result sets.
- `SQLChatAgentConfig.max_retained_tokens` limits how much query-result text is
  kept in history.
- `ArangoChatAgentConfig.max_num_results` truncates AQL result sets.
- `ArangoChatAgentConfig.max_schema_fields` trims oversized schema responses.
- `AQLRetrievalTool` also caps result and retained tokens at the tool level.

## Good habits

- Use schema or schema tools before writing queries when the model does not know
  the shape of the data yet.
- Keep query strings small and explicit.
- Prefer least-privilege database roles.
- Treat `allow_dangerous_operations=True` as an opt-in escape hatch, not a
  convenience default.
