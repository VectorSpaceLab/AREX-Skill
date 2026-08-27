# Backend troubleshooting

## Engine alias not recognized

**Symptoms**
- `FuguePluginsRegistrationError: Fugue execution engine is not recognized`
- `make_execution_engine(...)` cannot resolve a backend string or object

**Likely cause**
- The backend package was not installed or not imported, so its registration side effects never ran.

**Fix**
- Install the matching Fugue extra.
- Import the backend package before resolving the alias.
- If you are using a custom type, register it with `register_execution_engine(...)`.

## Dask SQL or partition behavior is inconsistent

**Symptoms**
- A Dask query works in some shapes but not others
- HAVING or related SQL shapes behave oddly

**Likely cause**
- The Dask SQL stack can have version-specific limitations.

**Fix**
- Prefer a DuckDB or Native fallback for the query shape if the Dask SQL path fails.
- Keep the Dask extra pinned to a verified combination when the workflow needs it.

## Spark Connect limitations

**Symptoms**
- RDD operations are unavailable
- Some repartitioning shapes fail or are skipped

**Likely cause**
- Spark Connect intentionally omits some Spark local-mode features, and the repo's own tests skip those branches.

**Fix**
- Use local Spark when you need RDD-heavy or even-repartition behavior.
- Treat Spark Connect as a separate service-backed environment.
- Treat the upstream Spark Connect launcher as reference-only; this generated skill does not bundle or invoke it because it downloads Spark and starts a server.

## DuckDB extension and config issues

**Symptoms**
- DuckDB extension loading fails
- A pragma config string is rejected

**Likely cause**
- The DuckDB-specific config or extension list is malformed, or the extension requires network/download access.

**Fix**
- Simplify the DuckDB config first and remove extension rows until the base engine works.
- Re-add extension settings one by one.

## Ibis or Polars object confusion

**Symptoms**
- A Polars dataframe or Ibis object is not recognized the way you expected

**Likely cause**
- Polars is primarily a dataframe integration layer, and the actual SQL execution path may still be DuckDB-backed.

**Fix**
- Choose the engine explicitly when the query path matters.
- Confirm which package owns the dataframe conversion versus the SQL backend.

## Ray remote configuration surprises

**Symptoms**
- A Ray engine starts with the wrong level of parallelism or remote behavior

**Likely cause**
- The Ray config keys were not set on the execution engine.

**Fix**
- Pass the `fugue.ray.remote.*` and `fugue.ray.shuffle.*` settings through the engine config.
