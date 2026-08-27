# Platform Backend Architecture

## Package boundaries

The backend lives under `autogpt_platform/backend` and is the `autogpt-platform-backend` Poetry project. Shared Python utilities are in `autogpt_platform/autogpt_libs` and are imported by the backend for auth and common platform behavior.

Key backend directories:

| Directory | Responsibility |
| --- | --- |
| `backend/api/` | FastAPI REST and WebSocket API layers, middleware, CORS, OpenAPI operation IDs |
| `backend/api/features/` | Feature-owned routers, models, DB helpers, and tests for admin, builder, chat, executions, library, store, search, workspace, integrations, orgs, MCP, and onboarding |
| `backend/blocks/` | Built-in graph blocks, provider-specific block packages, block tests, and block cost checks |
| `backend/sdk/` | Block-development SDK re-exports, `ProviderBuilder`, provider registry, and cost helpers |
| `backend/data/` | Prisma-backed data access, graph/execution models, credit, user, workspace, LLM registry, and service manager wrappers |
| `backend/executor*`, `backend/scheduler*`, `backend/notifications*` | Long-running graph execution, schedule, notification, and batch-executor processes |
| `backend/copilot/` | CoPilot chat, bot bridge, executor, artifacts, sharing, rate limits, and tool orchestration |
| `backend/integrations/` | OAuth, webhook, provider, and managed-credential infrastructure |
| `scripts/` | Maintainer workflows for tests, docs, Prisma stubs, OpenAPI, views, catalogs, and data utilities |

## Runtime process model

`backend.app.main()` starts a process set that includes the database manager, scheduler, batch executor, notification manager, platform linking manager, WebSocket server, REST server, execution manager, CoPilot chat bridge, and CoPilot executor. `backend.util.process.AppProcess` and `backend.util.service.AppService` provide background process lifecycle and HTTP/IPC-style service boundaries.

Use `poetry run app` only when the required services and env files are ready. For inspection or targeted validation, prefer import checks, `--help`, focused pytest, or a single service entry point.

## REST and WebSocket layers

REST routing is centralized by `backend/api/rest_api.py`, with feature routers under `backend/api/features/*`. The REST app applies CORS, security headers, auth/OpenAPI security metadata, gzip, instrumentation, and a custom OpenAPI operation-id generator. Local app startup verifies auth settings, connects Prisma and Redis, initializes block registries, loads the LLM catalog, registers managed providers, and runs migrations/repairs that require the selected database.

WebSockets are in `backend/api/ws_api.py`. They authenticate via JWT unless auth is disabled, subscribe users to graph execution channels, and require both Prisma and Redis during lifespan startup.

## Data and service boundaries

`DatabaseManager` exposes many data operations through service methods. Do not return raw Prisma model objects across service boundaries; convert to application-layer Pydantic models first. Data functions for feature ownership usually live near the feature under `backend/api/features/<feature>/` or in `backend/data/` for cross-cutting entities.

Prisma schema and generated client state are load-bearing. For schema edits, review `schema.prisma`, add migrations, run migration/generation commands, and use the test database path for tests.

## Graph, blocks, and execution

Agent workflows are graph definitions containing nodes, links, schemas, execution metadata, schedules, triggers, and store/library records. Blocks are Python classes registered from `backend/blocks/`; execution services validate inputs, resolve credentials, charge costs, run blocks, stream updates, and persist outputs.

When changing graph execution, inspect both API models and executor/runtime consumers. When changing block schemas or output names, expect frontend Builder, generated models, saved graph compatibility, and store/library behavior to be affected.

## Workspace and media responsibilities

Persistent user files use `WorkspaceManager` and workspace database/storage models. Ephemeral block processing uses `store_media_file()` with explicit return formats:

- `for_local_processing` for ffmpeg, PIL, MoviePy, or local tools.
- `for_external_api` for data URIs sent to external providers.
- `for_block_output` for outputs that become `workspace://` in CoPilot sessions and data URIs in graph contexts.

Both workspace writes and media normalization perform virus scanning. Do not bypass these layers with ad hoc filesystem writes for user content.

## Feature ownership clues

- Builder/graphs/executions: `backend/api/features/builder`, `backend/data/graph`, `backend/data/execution`, executor modules.
- Library/store/marketplace: `backend/api/features/library`, `backend/api/features/store`, search embeddings, store agent loaders.
- Integrations/OAuth/webhooks: `backend/api/features/integrations`, `backend/integrations`, provider `_config.py` files.
- CoPilot/chat/artifacts: `backend/api/features/chat`, `backend/copilot`, workspace storage.
- Admin/analytics/cost/rate limits: `backend/api/features/admin`, credit and catalog modules.
