# REST service troubleshooting

## Startup failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Service fails before `/healthcheck` | `OPENAI_API_KEY` missing or backend config invalid | Set the key and verify `DB_BACKEND`, `NEO4J_*`, or `FALKORDB_*` values. |
| `Graphiti` initialization error for Neo4j | Neo4j host, user, or password is wrong | Verify the bolt URI and credentials, then retry startup. |
| `Graphiti` initialization error for FalkorDB | FalkorDB host, port, or database is wrong | Verify the Redis/FalkorDB endpoint and graph name. |
| `Graph not found: default_db` | FalkorDB database name mismatch | Use the configured FalkorDB database name consistently. |

## Queue and retrieval failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `/messages` returns `202` but `/search` is empty | The queue has not finished processing | Poll `/episodes/{group_id}` until the episode exists, then search again. |
| Duplicate or unexpected search data | Reused `group_id` from a previous run | Generate a unique group ID for smoke tests or delete the old group first. |
| Search returns 500 or backend errors | Graph backend is down or stale | Check the graph backend logs and confirm the service can connect to the database. |
| `/clear` wipes too much data | Destructive route used without scoping | Prefer `DELETE /group/{group_id}` for smoke cleanup. |

## Data-shape issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Message ingest fails on JSON content | `episode_body` was not escaped as a JSON string | Serialize the JSON before sending it to the service. |
| `role_type` validation errors | Invalid role name supplied to `Message` | Use `user`, `assistant`, or `system`. |
| Empty or malformed `group_id` | Missing or invalid group id | Supply a non-empty, safe group ID. |

## Smoke check order

When debugging the service, follow this order:

1. `python ../../scripts/check_graphiti_install.py`
2. `python scripts/graph_service_smoke.py --health-only`
3. Full smoke with ingest/search against the desired backend
4. If needed, inspect the service logs and backend logs together

If the health check fails, do not move on to ingest debugging until startup is
stable.
