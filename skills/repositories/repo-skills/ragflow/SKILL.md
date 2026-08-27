---
name: ragflow
description: "Work with RAGFlow, a full-stack Retrieval-Augmented Generation
  engine with deployment, backend APIs, SDK/HTTP integration,
  ingestion/retrieval, document parsing, agent workflows, and frontend
  integration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# RAGFlow

Use this repo skill when a task is about RAGFlow's source code, deployment, public API, Python SDK, document ingestion, retrieval, DeepDoc parsing, agent canvas/tooling, MCP/memory, or web frontend integration.

## Route by Task

| User task | Read |
| --- | --- |
| Start RAGFlow with Docker/source/Helm, change `.env` or `service_conf.yaml`, switch document engines, debug MySQL/Redis/MinIO/document-engine startup | [deployment-configuration](sub-skills/deployment-configuration/SKILL.md) |
| Add/debug Quart routes, RESTful versus legacy prefixes, auth/session/API-token behavior, Peewee service logic, system endpoints, chat channels | [backend-api-services](sub-skills/backend-api-services/SKILL.md) |
| Call RAGFlow from HTTP, Python SDK, OpenAI-compatible clients, streaming chat, retrieval endpoint, API keys, or client examples | [sdk-http-integration](sub-skills/sdk-http-integration/SKILL.md) |
| Work on datasets, documents, chunks, parser_config, task executors, retrieval search, metadata filters, RAPTOR, GraphRAG | [dataset-ingestion-retrieval](sub-skills/dataset-ingestion-retrieval/SKILL.md) |
| Change DeepDoc parsers, PDF OCR/layout/table behavior, parser backend choices, parser_config parsing options, file-type routing | [document-parsing](sub-skills/document-parsing/SKILL.md) |
| Work on agent canvas DSL, components, templates, tools, memory, MCP retrieval, sandbox/code execution, webhooks, debug traces | [agent-workflows](sub-skills/agent-workflows/SKILL.md) |
| Wire or debug React/Vite routes, API constants, services, hooks, React Query cache, dataset/chat/agent UI integration, frontend tests | [frontend-integration](sub-skills/frontend-integration/SKILL.md) |

## First Checks

1. Identify whether the user is deploying/using RAGFlow or modifying a checkout; deployment and SDK tasks often need no source-code changes.
2. For code changes, route to the focused sub-skill first, then use sibling cross-links when a workflow spans backend, ingestion, SDK, and frontend.
3. Keep the process model in mind: the API server and task executors are separate Python process types; a healthy UI does not prove document parsing workers are healthy.
4. Prefer `/api/v1` for newer public REST APIs and reserve `/v1` for legacy route families that still exist.
5. Treat document parsing, parser_config, and retrieval as a chain: file type and parser options affect chunks, embeddings, metadata, retrieval weights, and citation/reference outputs.

## Common Entry Points

- Deployment health: `GET /api/v1/system/healthz` and the deployment validator in [deployment-configuration/scripts/validate_env.py](sub-skills/deployment-configuration/scripts/validate_env.py).
- Backend route inventory: [backend-api-services/scripts/list_routes.py](sub-skills/backend-api-services/scripts/list_routes.py).
- SDK/API dry run: [sdk-http-integration/scripts/ragflow_api_smoke.py](sub-skills/sdk-http-integration/scripts/ragflow_api_smoke.py).
- Parser config review: [dataset-ingestion-retrieval/scripts/inspect_parser_config.py](sub-skills/dataset-ingestion-retrieval/scripts/inspect_parser_config.py).
- Parser routing smoke check: [document-parsing/scripts/parse_smoke.py](sub-skills/document-parsing/scripts/parse_smoke.py).
- Agent template review: [agent-workflows/scripts/inspect_agent_template.py](sub-skills/agent-workflows/scripts/inspect_agent_template.py).
- Frontend endpoint scan: [frontend-integration/scripts/check_web_api_keys.py](sub-skills/frontend-integration/scripts/check_web_api_keys.py).

## Cross-Cutting Notes

- RAGFlow 0.26.1 requires Python `>=3.13,<3.14` for the main Python project; the standalone Python SDK is published separately as `ragflow-sdk`.
- The backend uses Quart and Peewee; do not assume Flask synchronous handlers or SQLAlchemy models.
- The frontend uses React/Vite, React Query, service wrappers, and two API prefix families: newer `/api/v1` and legacy `/v1`.
- DeepDoc parser imports and OCR/layout backends have optional dependencies; missing parser packages should be handled as parser-backend issues, not generic API failures.
- Source-level inspection found a packaging caveat: a plain editable install can fail if package metadata expects a top-level `graphrag` package while GraphRAG code is under `rag/graphrag`. Use repo-supported `uv` setup or source inspection until packaging is fixed.

## References

- [Repo provenance](references/repo-provenance.md) records the source state and evidence paths used to create this skill.
- [Routing metadata](references/repo-routing-metadata.json) is consumed by `repo-skills-router` during import.
- [Troubleshooting](references/troubleshooting.md) summarizes cross-cutting failure routes and points to the nearest sub-skill.
