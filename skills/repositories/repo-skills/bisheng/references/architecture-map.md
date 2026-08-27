# Architecture Map

## When to read

Read this for a compact map of BiSheng's repository layout, process topology, source roots, public routes, and storage dependencies before choosing a focused sub-skill.

## Repository shape

BiSheng is a monorepo with three main products and supporting deployment/docs material:

| Path | Runtime | Main stack | Owns |
| --- | --- | --- | --- |
| `src/backend/` | API, Celery workers, Linsight worker | Python 3.11+, FastAPI, Celery, SQLModel, LangGraph, LangChain, uv | `/api/v1`, `/api/v2`, DDD modules, RAG, workflow engine, Linsight, permissions, tenants, migrations, ops scripts |
| `src/backend/bisheng_langchain/` | Imported backend extension package | LangChain extension modules | custom chains, chat models, document loaders, embeddings, vector stores, RAG retrievers, agents, GPT tools, Linsight runtime |
| `src/frontend/platform/` | Admin / builder SPA | Vite 5, React, TypeScript, Zustand, React Context, react-query v3, bs-ui | app builder, workflow/skill editors, model/admin/knowledge pages, system/approval/tenant UI |
| `src/frontend/client/` | End-user workspace SPA | Vite 6, React, TypeScript, Recoil, TanStack Query v4, shadcn/Radix | chat, app chat, Linsight task mode, app center, knowledge browsing, subscriptions, PWA |
| `docker/` | Compose deployment | Docker Compose, Nginx, service entrypoints | MySQL, Redis, backend API/worker, frontend, Milvus stack, Elasticsearch, MinIO, optional FT/OnlyOffice/Unstructured services |
| `docs/` and `features/` | Development evidence | Markdown SDD + architecture | constitution, SDD workflow, subsystem architecture, feature specs/design/tasks |
| `scripts/`, `tools/`, `src/backend/scripts/` | Maintainer/ops helpers | Bash/Python | arch guard, RBAC/ReBAC checks, export/template tools, data backfills, migrations, diagnostics |

## Runtime topology

The normal full stack has two SPAs and one FastAPI backend behind an Nginx/proxy entry. FastAPI handles frontend-facing `/api/v1` and external/RPC `/api/v2`; commercial deployments can insert a Java gateway in front of FastAPI for SSO/OAuth, sensitive-word filtering, rate limiting, and WebSocket proxying.

Backend asynchronous execution is split by process type:

- **API server:** `bisheng.main:app` initializes app context and registers routers.
- **Knowledge worker:** Celery `knowledge_celery` queue handles document parsing, embedding, vector writes, retries, copies, and rebuilds.
- **Workflow worker:** Celery `workflow_celery` queue executes and resumes LangGraph workflow DAGs.
- **Default worker and beat:** telemetry, information sync, tenant/permission retry tasks, and scheduled jobs.
- **Linsight worker:** `bisheng/linsight/worker.py` is an independent Redis-queue worker for autonomous task mode.

Storage engines are MySQL/DM8-compatible relational DB, Redis, Milvus, Elasticsearch, MinIO, and OpenFGA. Knowledge/RAG uses Milvus for dense vectors and Elasticsearch for sparse/BM25 recall. Tenant isolation prefixes external storage for non-default tenants.

## Backend route and module landmarks

- App factory and lifespan: `src/backend/bisheng/main.py`.
- API registration: `src/backend/bisheng/api/router.py` creates `/api/v1` and `/api/v2` router groups.
- DDD business modules: top-level directories such as `knowledge/`, `linsight/`, `permission/`, `tenant/`, `approval/`, `llm/`, `user/`, `channel/`, `message/`, `finetune/`, `tool/`, `workstation/`.
- Workflow engine exception to DDD folder shape: `workflow/graph`, `workflow/nodes`, `workflow/edges`, `workflow/callback`, `workflow/common`.
- Shared infrastructure: `core/`, `common/`, `database/models/`, `worker/`.
- v2 external integration APIs: `open_endpoints/api/`.

## Frontend landmarks

- Platform route registry: `src/frontend/platform/src/routes/index.tsx`; route permissions are filtered by backend `web_menu` keys with admin/department/child-admin fallbacks.
- Platform request wrapper: `src/frontend/platform/src/controllers/request.ts`; API modules live in `src/frontend/platform/src/controllers/API/`.
- Client route registry: `src/frontend/client/src/routes/index.tsx`; basename is normally `/workspace` and routes are guarded by plugin/menu gates.
- Client request wrapper: `src/frontend/client/src/api/request.ts`; query hooks live under `src/frontend/client/src/hooks/queries/`.
- Platform i18n uses namespace files in `public/locales/{en-US,zh-Hans,ja}/`; Client i18n uses bundled `src/locales/{en,zh-Hans,ja}/translation.json`.

## Important invariants

- `docs/constitution.md` is the architecture law source. `scripts/arch-guard.sh` enforces several laws.
- Root `AGENTS.md` gives cross-repo rules; deeper `AGENTS.md` files add backend, frontend, and script-specific conventions.
- New backend tests belong under `src/backend/test/<module>/`.
- Non-trivial features follow SDD: spec, design, tasks, branch, wave-by-wave implementation, task review, e2e, code review.
- `features/` documents feature work; generated repo-skill verification artifacts are separate under `skills/tests/bisheng/` and are not runtime skill content.
