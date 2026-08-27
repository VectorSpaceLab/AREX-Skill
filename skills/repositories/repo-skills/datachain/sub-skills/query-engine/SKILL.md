---
name: query-engine
description: "Guides DataChain query operations, SQL-style function expressions,
  schema mapping, vector search, and backend-sensitive behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Query Engine

Use this sub-skill when the user asks about DataChain's native Query Engine:
SQL-style chain operations, `datachain.func` expressions, `Column` / `ColumnExpr`,
nested signal resolution, schema flattening, vector distance search, or a query
bug that may depend on the active warehouse backend.

## Trigger Phrases

Load this sub-skill for prompts containing or implying:

- `mutate` vs `map`, native SQL expression, `datachain.func`, `dc.C`,
  `Column`, `ColumnExpr`, alias, label, or expression type inference;
- `filter`, `select`, `select_except`, `order_by`, `distinct`, `group_by`,
  `merge`, `union`, `subtract`, `diff`, `file_diff`, `limit`, `offset`,
  `shuffle`, `sample`, `count`, `sum`, `avg`, `min`, or `max`;
- aggregate, array, conditional, numeric, string, path, random, or window
  functions;
- vector search, cosine/euclidean distance, embedding columns, or
  `similarity_search`;
- nested fields, flattened column names, `SignalSchema`, SQL type conversion,
  nullability, backend divergence, or behavior that passes locally but fails in
  Studio / ClickHouse.

## First Decision

1. **Choosing an operation or expression pattern** → read
   [operations-and-functions](references/operations-and-functions.md). Prefer
   native Query Engine operations when the logic can be expressed with columns
   and `dc.func`; reroute Python callables or file-content processing to
   sibling sub-skill `sdk-pipelines`.
2. **Nested fields, schema flattening, SQL type conversion, or backend parity**
   → read [schema-and-backends](references/schema-and-backends.md) before
   proposing a fix or claiming a backend result generalizes.
3. **Vector nearest-neighbor / embedding ranking** → read the vector sections in
   [operations-and-functions](references/operations-and-functions.md) and the
   backend notes in [schema-and-backends](references/schema-and-backends.md).
4. **A broken query, missing column, alias conflict, delta error, or backend-only
   failure** → read [troubleshooting](references/troubleshooting.md), then use
   [schema_probe.py](scripts/schema_probe.py) or [query_smoke.py](scripts/query_smoke.py)
   only as small local diagnostics.

## Boundaries and Reroutes

- This sub-skill owns native chain operations, SQL functions, query expression
  semantics, schema flattening/resolution, SQL type conversion, and
  backend-sensitive query behavior.
- For raw data ingestion, UDFs (`map`, `gen`, `agg`), checkpoint/delta pipeline
  recipes, exports, LLM calls, or file download/upload workflows, reroute to
  sibling sub-skill `sdk-pipelines`.
- For command-line, Studio auth/job/pipeline, or CLI parser questions, reroute
  to sibling sub-skill `cli-and-studio`.
- For DataChain's packaged agent skills or knowledge-base generation, reroute to
  sibling sub-skill `agent-harness`.
- For contributor test policy, nox, packaging, or source-maintenance decisions,
  reroute to sibling sub-skill `repo-development`.

## Safety Rules

- Keep query guidance self-contained; do not require future agents to open the
  source checkout, repository docs, or repository tests to use this sub-skill.
- Do not say a CPU/local SQLite smoke proves ClickHouse, BigQuery, Snowflake, or
  Postgres behavior. Treat backend parity as a matrix claim that needs backend
  evidence.
- Do not materialize a large chain with `to_pandas()`, `to_list()`, or Python
  loops just to filter, project, group, aggregate, rank, or compute SQL
  distances; use native Query Engine operations when possible.
- Use `map` only for Python callables, file-content reads, model/API calls, or
  logic that cannot be expressed as a SQL-style expression.
- Every chain operation returns a new chain. Never assume `filter`, `mutate`,
  `select`, `merge`, or `union` changed the receiver in place.
