# Troubleshooting

Use this reference for cross-cutting Graphiti failures. Sub-skills own their
workflow-specific troubleshooting, but the symptoms below show up across the repo.

## Import and install problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'openai'` | Graphiti dependencies were not installed in the active environment. | Reinstall `graphiti-core` in the target environment and rerun the import check. |
| `ModuleNotFoundError` for `graphiti_core.driver.falkordb_driver` | The FalkorDB extra is missing. | Install `graphiti-core[falkordb]` before using the Falkor path. |
| `ImportError` for optional provider clients | The relevant provider extra was not installed. | Install only the provider extra for the workflow you actually need. |
| `No provider reranker available, using local BGERerankerClient` | No OpenAI/Gemini reranker is configured. | Accept the fallback, or install `sentence-transformers` if you want the local BGE fallback. |
| `No provider reranker is available ... Install the MCP server's 'providers' extra` | The local BGE fallback was selected but `sentence-transformers` is missing. | Install the extra the error message names, or provide a provider reranker. |

## Graph and driver issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `uri must be provided when graph_driver is None` | `Graphiti` was constructed without a driver or URI. | Pass either `graph_driver=...` or `uri/user/password`. |
| `Graph not found: default_db` | The driver is pointed at the wrong database name. | Use the backend's default database name or pass the explicit database value when the driver supports it. |
| FalkorDB query/connection failures during concurrent search | FalkorDB can drop the connection under concurrent query pressure. | Prefer Neo4j for local hybrid-search work or reduce concurrency. |
| `group_id "..." must contain only alphanumeric characters, dashes, or underscores` | Invalid partition ID. | Sanitize the `group_id` before ingest/search. |
| `node_labels must start with a letter or underscore...` | Unsafe custom node labels were provided. | Use safe Cypher identifiers for labels. |
| `Invalid excluded entity types` | `excluded_entity_types` includes names that are not in the configured entity types. | Compare the exclusion list against the configured entity types and remove the invalid entries. |
| `edge ... not found` / `node ... not found` | UUID lookup failed. | Recheck the ID or search by name/query first. |

## LLM and structured-output problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `OPENAI_API_KEY` missing or empty | Default clients were used without credentials. | Set the key or inject custom clients. |
| JSON parse / schema validation failures on OpenAI-compatible providers | The provider accepts `json_schema` but does not enforce it, or a small model produced malformed JSON. | Use a stronger model, switch to `OpenAIGenericClient(..., structured_output_mode='json_object')`, and reduce concurrency. |
| `429` rate-limit errors | Too many concurrent LLM operations. | Lower `SEMAPHORE_LIMIT` and rerun. |
| `EmptyResponseError` / empty LLM body | The provider returned an empty or truncated completion. | Retry with a stronger model or a lower-concurrency configuration. |

## Service and transport issues

| Surface | Symptom | Recovery |
| --- | --- | --- |
| REST service | Startup fails because a backend cannot connect | Check `NEO4J_*` or `FALKORDB_*` variables and ensure the target DB is running. |
| REST service | `/messages` returns 202 but search is empty | The queue has not finished processing yet. Poll `/episodes/{group_id}` or wait before searching. |
| MCP server | `Graphiti service not initialized` | The server failed during config or backend setup. Inspect the startup logs and config file. |
| MCP server | Tool returns an `ErrorResponse` about the database | The configured backend is unreachable. Fix the database settings or start the database. |
| MCP server | HTTP/stdio mismatch in a client | Use the same transport the server was started with and the endpoint that transport expects. |

## Operational reminders

- `GRAPHITI_TELEMETRY_ENABLED=false` keeps local checks quiet and avoids telemetry noise.
- Kuzu is deprecated; do not spend time debugging new workflows around it unless a
  task explicitly requires Kuzu compatibility.
- Neptune is supported in code and docs, but it is not part of the minimum skill
  verification path here.
- If a workflow depends on a real backend or API key, a successful import check is
  not enough; run the workflow-specific smoke or native test.
