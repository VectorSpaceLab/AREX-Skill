# Package Overview

## Purpose

Read this for a compact Nexent monorepo map before routing to a focused sub-skill.

## What Nexent contains

Nexent combines:

- Python SDK distribution `nexent`: agent runtime, models, tools, MCP/A2A integration, context, sandbox, monitoring, data-processing helpers, vector DB clients, storage, scheduler, skill loading, and memory APIs.
- FastAPI backend: HTTP apps, services, database helpers, auth/tenant permissions, prompts, model/provider management, agent/skill repositories, data-process orchestration, memory, knowledge, MCP, A2A, and northbound APIs.
- Next.js frontend: App Router pages, service clients, typed contracts, chat streaming UI, configuration pages, stores/hooks, and i18n.
- Deployment: Docker Compose, Kubernetes/Helm, offline image packages, SQL migrations/init, env examples, monitoring assets, image builds, and uninstall/upgrade tooling.

## Cross-layer rules

- Backend constants own environment parsing. Do not scatter `os.getenv()` reads across services or SDK modules.
- Services own business orchestration and should raise domain exceptions; app layers map those errors to HTTP responses.
- SDK code should remain parameter/config driven and testable without deployment env vars.
- Frontend service clients and TypeScript types must track backend route and payload changes.
- Deployment env examples and SQL init/migrations must track backend operator settings and schema changes.

## Install and verification surfaces

- SDK-only tasks: install the `nexent` package for Python 3.11 and run import/signature checks.
- Backend tasks: install backend dependencies and include the SDK source/package expected by backend tests.
- Data-process tasks: optional extras may pull heavy document/OCR/Ray/Celery dependencies; use tiny fixtures or import checks first.
- Frontend tasks: use Node 18+ and frontend package scripts when dependencies are present.
- Deployment tasks: live operations require Docker or Kubernetes/Helm plus configured env files and persistent storage decisions.

## Scenario placement

Nexent primarily belongs to the agent framework/tooling and Python AI API service scenarios. It also overlaps with RAG/document-processing, AI memory, frontend integration, and deployment operations. Route by the user's task surface, not just by the directory named in the request.
