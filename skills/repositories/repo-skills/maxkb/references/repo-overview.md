# Repo overview

## Core surfaces
| Surface | Key paths | Owned by |
| --- | --- | --- |
| Runtime and startup | `main.py`, `apps/manage.py`, `apps/maxkb/*`, `apps/ops/celery/*`, `installer/*` | `runtime-architecture` |
| Workflow, chat, MCP | `apps/application/*`, `apps/chat/*`, `apps/common/handle/*` | `workflow-chat-mcp` |
| Knowledge and models | `apps/knowledge/*`, `apps/models_provider/*`, `apps/local_model/*` | `knowledge-models` |
| Frontend | `ui/*` | `frontend-integration` |
| Admin and management | `apps/users/*`, `apps/system_manage/*`, `apps/folders/*`, `apps/homepage/*`, `apps/oss/*`, `apps/tools/*`, `apps/trigger/*` | `admin-access` |

## Interaction map
- `runtime-architecture` defines the route prefixes, settings source, Celery queues, and static asset contract.
- `workflow-chat-mcp` consumes model providers and emits SSE/OpenAI-compatible responses.
- `knowledge-models` links retrieval/search behavior with provider catalogs and the local model runtime.
- `frontend-integration` mirrors backend surface areas in Vue router modules and Vite build targets.
- `admin-access` owns the management surfaces for permissions, folders, homepage metrics, OSS, tools, and triggers.

## Maintenance style
- Keep changes incremental and narrowly scoped.
- Preserve formatting and existing naming patterns.
- Prefer documentation and safe static checks before live-service checks.
