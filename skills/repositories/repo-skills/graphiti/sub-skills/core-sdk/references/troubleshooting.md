# Core SDK troubleshooting

## Construction and backend setup

| Symptom | Cause | Fix |
| --- | --- | --- |
| `ValueError: uri must be provided when graph_driver is None` | `Graphiti()` was called without either Neo4j credentials or a `graph_driver`. | Pass `Graphiti(uri, user, password)` for Neo4j, or create `Neo4jDriver` / `FalkorDriver` and pass `graph_driver=...`. |
| `ModuleNotFoundError: falkordb` | The FalkorDB extra is missing. | Install `graphiti-core[falkordb]` before importing `FalkorDriver`. |
| Neo4j auth/connection errors | The database is down or credentials are wrong. | Verify `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, and that bolt port 7687 is reachable. |
| FalkorDB connection errors | Redis/FalkorDB is down or the wrong host/port/database is configured. | Verify `FALKORDB_HOST`, `FALKORDB_PORT`, `FALKORDB_DATABASE`, or the `FalkorDriver(...)` constructor. |
| `Graph not found: default_db` | Backend database name mismatch. | Neo4j defaults to `neo4j`; FalkorDB defaults to `default_db`. Pass the database explicitly when needed. |
| `Connection closed by server` on FalkorDB during hybrid search | FalkorDB can be sensitive to concurrent queries on one connection. | Prefer Neo4j for local hybrid-search debugging, or lower concurrency and simplify the query. |

## Ingestion issues

| Symptom | Cause | Fix |
| --- | --- | --- |
| JSON episodes fail or extract poorly | A Python object was passed without serialization, or the JSON has unclear fields. | Pass a JSON string with `json.dumps(...)` and add a useful `source_description`. |
| `Invalid excluded entity types` | `excluded_entity_types` names do not match configured types. | Use only `Entity` or keys present in `entity_types`. |
| `group_id ... must contain only alphanumeric characters, dashes, or underscores` | Invalid graph partition identifier. | Use a sanitized `group_id`; avoid spaces and punctuation. |
| `node_labels must start with a letter or underscore...` | A custom label is not a safe Cypher identifier. | Rename labels/types to letters, numbers, and underscores, with a valid first character. |
| Ingested data appears missing | Search is using a different `group_id` or backend database. | Keep `group_id` and backend settings stable between ingest and search. |

## Search issues

| Symptom | Cause | Fix |
| --- | --- | --- |
| `search()` returns no facts | Data may still be absent, scoped to another group, or not yet indexed. | Verify the `group_id`, run a node search with `search_()`, and inspect episodes. |
| `search_()` returns empty `nodes` | The selected `SearchConfig` may only search edges or episodes. | Use `NODE_HYBRID_SEARCH_RRF` or a config with `node_config`. |
| Cross-encoder/reranker failures | Missing provider key or missing local reranker dependency. | Use a provider-backed reranker or install `sentence-transformers` for local BGE fallback. |
| Search results are noisy | Query too broad or no type/date filters. | Use `SearchFilters`, stricter `group_ids`, recipe-specific limits, or node-centered reranking. |

## Provider and structured-output issues

| Symptom | Cause | Fix |
| --- | --- | --- |
| LLM returns malformed JSON | Small/local provider does not honor schema output. | Use a stronger model or `OpenAIGenericClient(..., structured_output_mode='json_object')`. |
| `429` rate-limit errors | Too much ingestion/search concurrency. | Lower `SEMAPHORE_LIMIT` or `Graphiti(max_coroutines=...)`. |
| Empty or truncated LLM responses | Provider flake, refusal, or context limit. | Retry with a more capable model and lower concurrency; shorten episode chunks when needed. |
| Azure deployment errors | Deployment names or endpoint format are wrong. | Use the Azure `/openai/v1/` endpoint format and ensure model/deployment names match Azure. |
| Local model extraction misses fields | Model is too small or lacks reliable JSON behavior. | Prefer capable local models, reduce concurrency, and use `json_object` mode. |

## Data-density and chunking

Graphiti uses density-aware content chunking. If large JSON or entity-dense text
causes bad extraction or context pressure, inspect these environment controls:

- `CHUNK_TOKEN_SIZE`
- `CHUNK_OVERLAP_TOKENS`
- `CHUNK_MIN_TOKENS`
- `CHUNK_DENSITY_THRESHOLD`

Do not tune them for normal prose until you have evidence that density-driven
chunking is the problem.

## Safe verification

Use these in order:

1. `python ../../scripts/check_graphiti_install.py`
2. `python scripts/quickstart_graphiti.py --backend neo4j`
3. `python scripts/quickstart_graphiti.py --backend falkordb`

The quickstart script needs a live backend and model credentials; the import
check does not prove end-to-end ingest/search.
