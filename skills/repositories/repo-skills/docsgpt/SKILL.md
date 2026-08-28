---
name: docsgpt
description: "Routes DocsGPT deployment, source ingestion, retrieval, agent workflows, tools, integrations, and native or OpenAI-compatible API operations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DocsGPT

Use this operating graph for DocsGPT 0.18-era administration, integration, and extension tasks. It is a task router, not a replacement for the focused references below.

## Start here

1. Identify whether the task targets a source checkout, a running DocsGPT deployment, or an external client.
2. Choose the owning sub-skill from the routing table.
3. Establish prerequisites before changing state: Postgres for user data, Redis for cache/Celery/events, an LLM and embeddings path, and any optional vector-store, connector, or sandbox service.
4. Prefer read-only checks and dry-run/plan endpoints before migrations, re-ingestion, imports, schedules, or state-mutating tools.
5. Validate the result at the narrowest useful layer, then check the integrated API or UI path.

## Route by task

| Task signal | Read |
|---|---|
| install, local development, Docker, Kubernetes, environment variables, model providers, OIDC/SCIM/RBAC, Postgres, Redis, S3, observability, upgrades | [deploy-configure](sub-skills/deploy-configure/SKILL.md) |
| upload, parse, OCR, audio, URL/sitemap/crawler, GitHub/Reddit/S3 source, Google Drive, SharePoint, Confluence, chunking, ingestion worker, re-ingestion | [ingest-sources](sub-skills/ingest-sources/SKILL.md) |
| embeddings, FAISS, pgvector, Qdrant, Milvus, MongoDB Atlas, Elasticsearch, classic/hybrid RAG, pre-screening, GraphRAG, retrieval quality | [retrieval-vectorstores](sub-skills/retrieval-vectorstores/SKILL.md) |
| classic/agentic/research/workflow agent, workflow nodes, CEL, schedules, webhooks, seeding, agent export/import | [agents-workflows](sub-skills/agents-workflows/SKILL.md) |
| built-in tools, generic API tool, MCP, artifacts, code execution, Read Document, sandbox, remote device, widget, Chatwoot | [tools-integrations](sub-skills/tools-integrations/SKILL.md) |
| `/api/answer`, `/stream`, attachments, SSE, reconnect, `/v1/chat/completions`, structured output, multimodal clients, idempotency, `/mcp` | [api-client-operations](sub-skills/api-client-operations/SKILL.md) |

## Runtime topology rule

Use the ASGI composition for full behavior:

```bash
uvicorn application.asgi:asgi_app --host 0.0.0.0 --port 7091
```

The Flask development server exposes the WSGI app only. It omits `/mcp` and the native-async reconnect reader at `GET /api/messages/<id>/events`; use Flask only for a deliberately reduced inner loop.

A full deployment normally has:

- the ASGI web application;
- Postgres as the canonical user-data store;
- Redis for cache, Celery broker/results, schedules, and realtime coordination;
- at least one Celery worker (a bare worker consumes all queues; split `docsgpt` and `parsing` only when needed);
- the frontend or another API client;
- optional vector-store, sandbox, object-storage, OAuth connector, and model-provider services.

Read [architecture and terminology](references/architecture-and-terminology.md) before changing boundaries across these components.

## Minimal readiness checks

For a source-development checkout, use Python 3.12 and install the backend requirements into an isolated environment. This bundle includes the exact [0.18.0 backend requirements snapshot](references/backend-requirements-0.18.0.txt); use the target release's manifest only after checking provenance/version drift. Do not run bootstrap setup scripts during ordinary feature work when explicit environment configuration is sufficient.

From the runtime skill root:

```bash
python -m pip install -r references/backend-requirements-0.18.0.txt
python -c "from application.version import get_version; print(get_version())"
python -c "from application.asgi import asgi_app; print(type(asgi_app).__name__)"
```

For a running service, use the bundled read-only checker:

```bash
python scripts/check_deployment.py --base-url http://localhost:7091
```

Add `--token` only for a non-production test credential or pass `--token-env` so the credential is not written into shell history. Read the script help before probing a shared deployment.

## Safety and verification

- Treat `.env`, API keys, OAuth client secrets, JWT secrets, SCIM tokens, S3 credentials, and sandbox tokens as secrets. Never place them in logs or exported agent YAML.
- Back up Postgres and object storage before migrations or backfills. Do not infer success from a Celery task id; poll status and inspect the resulting source/artifact.
- Changing chunking or embedding dimensions requires re-ingestion. Query-time retrieval settings usually do not.
- GraphRAG requires both pgvector and its feature flag. Hybrid keyword retrieval is pgvector-specific; other stores fall back to vector behavior.
- Tool calls can perform external side effects. Use per-action approval and idempotent APIs for writes.
- Imported agents are drafts and exported secrets are stripped. Preview import plans before committing.

Read [cross-cutting troubleshooting](references/troubleshooting.md) when failures span multiple components.

## Version and staleness

Read [repository provenance](references/repo-provenance.md) before relying on exact routes, settings, schemas, or defaults in a different checkout. Refresh this graph when the commit, package version, public API, or major evidence paths change.
