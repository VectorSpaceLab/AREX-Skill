# Cross-Cutting Troubleshooting

Use this before drilling into a sub-skill when a symptom could come from several services.

## Triage sequence

1. **Identify the surface**: source import, ASGI route, worker task, database write, vector search, LLM call, tool call, or client stream.
2. **Check configuration without secrets**: selected provider/store/auth mode, base URLs, feature flags, queue names, and service reachability.
3. **Separate enqueue from completion**: record task/run id, terminal state, and persisted output.
4. **Reproduce narrowly**: health/config endpoint, one tiny source, one query, one tool action, or one client frame.
5. **Preserve evidence**: HTTP status, response body, correlation/task id, sanitized logs, and exact component versions.

## Symptom matrix

| Symptom | Likely cause | Next action |
|---|---|---|
| `/mcp` or `GET /api/messages/<id>/events` returns 404 while chat works | WSGI Flask app was started instead of the ASGI composition | start `application.asgi:asgi_app`; verify reverse proxy forwards those paths |
| app imports but requests fail with database errors | `POSTGRES_URI` absent/invalid, database missing, schema not migrated, or pool/network issue | normalize the URI, check reachability, inspect migration state; never point tests at production |
| background task remains pending | Redis/Celery unavailable, wrong queue, worker not consuming, or task result backend mismatch | inspect broker/result URLs and worker queues; a bare worker consumes all configured queues |
| upload succeeds but source is empty | parsing failed, unsupported/corrupt input, worker unavailable, embedding/vector write failed | poll task status and inspect parser/worker error; retry with a tiny supported file |
| retrieval returns no context | wrong source ownership/id, chunks absent, embedding mismatch, score threshold too strict, or approximate index/filter issue | verify source status and chunk count; remove unsupported threshold assumptions; check pgvector index guidance |
| provider/model is absent | key missing, custom catalog directory missing, invalid YAML, model disabled, or persisted model id renamed | validate model catalog and environment variable name; restore stable model id |
| stream disconnects or duplicates work | client does not buffer SSE frames/reconnect correctly, proxy buffering/timeouts, or retry lacks idempotency | use the API sub-skill; distinguish native reconnect from `/v1` idempotency |
| tool selected but fails | missing credentials, malformed action schema, SSRF block, disabled tool, approval policy, or missing optional service | validate offline first; inspect sanitized tool result; do not weaken URL controls |
| code/artifact tool always fails | sandbox backend is not running/configured or render libraries are missing | verify backend and image; keep these tools out of defaults until the runner works |
| login loop or 401/403 | auth mode mismatch, issuer/redirect/cookie/proxy issue, group allowlist, revoked session, or team/RBAC denial | inspect `/api/config`, OIDC discovery/redirect, claims, and authorization separately |

## Stop conditions

Stop and request operator action instead of guessing when recovery requires production credentials, schema/data mutation, destructive re-ingestion, external provider changes, firewall/DNS changes, identity-provider reconfiguration, bucket policy changes, or execution of untrusted code. Provide a sanitized preflight and rollback plan first.

## Focused references

- Installation, models, auth, storage and services: [deploy troubleshooting](../sub-skills/deploy-configure/references/troubleshooting.md)
- Parsing, connectors and worker ingestion: [ingestion troubleshooting](../sub-skills/ingest-sources/references/troubleshooting.md)
- Embeddings, stores and ranking: [retrieval troubleshooting](../sub-skills/retrieval-vectorstores/references/troubleshooting.md)
- Agent/workflow graphs and schedules: [agent troubleshooting](../sub-skills/agents-workflows/references/troubleshooting.md)
- Tool, sandbox, MCP and device failures: [tool troubleshooting](../sub-skills/tools-integrations/references/troubleshooting.md)
- Request, streaming and client behavior: [API troubleshooting](../sub-skills/api-client-operations/references/troubleshooting.md)
