# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Import error for SQL support | Optional SQL packages are missing | Install the SQL extra or the needed SQLAlchemy driver, then rerun. |
| PostgreSQL install fails with `pg_config` errors | Native PostgreSQL headers are missing | Install platform PostgreSQL development libraries, or use `psycopg2-binary` when that is acceptable. |
| Import error for Neo4j or ArangoDB support | Optional graph packages are missing | Install the matching graph extra or driver package before constructing the agent. |
| `SQLChatAgent` says database information is missing | Neither `database_uri` nor `database_session` was provided | Supply a valid SQLAlchemy URI or a bound SQLAlchemy session. |
| SQL URI fails at startup | Malformed URI, missing driver, wrong credentials, or unavailable host | Validate the URI with SQLAlchemy outside the agent; use SQLite for local smoke checks. |
| Neo4j or Arango initialization raises a connection error | Service is not running, host/port is wrong, or credentials/database are invalid | Start the service and verify credentials before constructing the agent. |
| Query is rejected even though it looks intentional | Default safety policy blocks non-read or dangerous operations | Prefer a read-only rewrite. If writes are required, extend `allowed_statement_types`; avoid disabling all checks. |
| Graph read tool refuses to run before schema lookup | The agent has not called the graph schema tool yet | Use `graph_schema_tool` for Neo4j or `arango_schema_tool` for ArangoDB first. |
| No graph results despite data existing | Labels, collection names, properties, or relationship names are case-sensitive | Re-check the schema and use exact names. |
| Schema metadata is too large | Full SQL or graph schema does not fit in useful context | Use SQL schema tools, narrow SQL context descriptions, seed a smaller `kg_schema`, or ask Arango for specific collections/properties. |
| Arango schema output is trimmed | `max_schema_fields` was exceeded | Increase the limit only if context budget allows, or use `arango_schema_tool` with narrower `collections` / `properties` settings. |
| Result rows are missing or truncated | Result limits are active | Adjust `max_result_rows`, `max_num_results`, or split the query into pages. |
| Pandas expression is blocked | `full_eval=False` sanitization rejects unsafe or unsupported operations | Rewrite using allowed pandas operations. Use `full_eval=True` only for trusted input and a controlled runtime. |

## Quick local safety check

Run the bundled script with `--help` to see available local checks. It inspects
safety defaults and can validate SQL, Cypher, and AQL strings without connecting
to a database service or model provider.
