# MCP server troubleshooting

## Startup failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Graphiti service not initialized` | Config parsing, backend connection, or provider setup failed during startup. | Inspect startup logs, then verify config file path, provider keys, and backend settings. |
| Server exits when launched by a desktop client | Stdio command or environment variables are wrong. | Use an absolute command in the client config and pass `OPENAI_API_KEY` plus backend vars in the client environment. |
| HTTP client cannot connect | Server transport/port mismatch. | Start with `--transport http --host 0.0.0.0 --port <port>` and connect to the same port. |
| SSE client cannot connect | SSE is deprecated or endpoint mismatch. | Prefer streamable HTTP unless the client explicitly requires SSE. |
| `--destroy-graph` erased data | Destructive startup flag used outside a disposable environment. | Do not use this flag in shared graphs; restore from backup if needed. |

## Backend and provider failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `get_status` reports database connection failed | Backend is unreachable or credentials are wrong. | Fix `database.provider` and matching Neo4j/FalkorDB settings, then restart. |
| FalkorDB tools fail immediately | FalkorDB package/extra or endpoint is missing. | Install the Falkor dependency path and verify the Redis/FalkorDB endpoint. |
| Provider API errors during `add_memory` | Missing API key, invalid model, or provider rate limit. | Set the correct provider credentials and lower `SEMAPHORE_LIMIT` if rate-limited. |
| Local reranker dependency error | No provider reranker and local BGE fallback dependency missing. | Install the provider/reranker extra or configure a provider reranker. |

## Tool-call behavior

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `add_memory` succeeds but searches are empty | Ingest is queued and has not finished. | Poll `get_episodes` before searching. |
| `search_nodes` returns no nodes | Wrong group, no ingested data, or restrictive filters. | Search the same `group_id` used by `add_memory`; relax type filters. |
| `search_memory_facts` rejects date filters | Invalid ISO-8601 date string. | Use full ISO strings and ensure timezone-naive values should be interpreted as UTC. |
| `clear_graph` says no group IDs specified | Neither argument nor default config group is available. | Pass `group_ids` explicitly. |
| Custom type extraction fails | Invalid labels/types or config schema mismatch. | Validate `entity_types`, `edge_types`, and `edge_type_map`; keep names graph-safe. |

## Smoke order

1. `python ../../scripts/check_graphiti_install.py`
2. `python scripts/mcp_smoke.py --transport stdio --list-only`
3. Full `python scripts/mcp_smoke.py` once backend and model credentials are ready
4. If HTTP is required, start the server separately and run `python scripts/mcp_smoke.py --transport http`

If the list-only smoke fails, do not debug Graphiti extraction yet. Fix transport
startup and tool registration first.
