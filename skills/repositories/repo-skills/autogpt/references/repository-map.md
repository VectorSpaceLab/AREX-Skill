# AutoGPT Repository Map

## Product split

| Surface | Purpose | Main evidence and change area |
| --- | --- | --- |
| AutoGPT Platform | Current visual agent platform and self-hosted stack | `autogpt_platform/` |
| Platform backend | FastAPI services, graph execution, blocks, integrations, Prisma data layer | `autogpt_platform/backend/` |
| Shared platform libs | Shared Python auth and utility packages | `autogpt_platform/autogpt_libs/` |
| Platform frontend | Next.js App Router UI for Builder, Copilot, Library, Marketplace, settings, and auth | `autogpt_platform/frontend/` |
| Platform docs | Self-hosting, blocks, integrations, contributor guides | `docs/platform/`, `docs/integrations/` |
| AutoGPT Classic | Unsupported legacy agent, Forge framework, direct benchmark harness | `classic/` |

## Platform layout

- The Platform root contains Docker Compose definitions, `Makefile` commands,
  and default environment files.
- The backend package provides REST and WebSocket services, an executor,
  scheduler, database service, notifications, CoPilot services, reusable
  blocks, and integrations.
- The frontend is a Node 24 / pnpm project using Next.js, React, Tailwind,
  generated Orval API hooks, React Query, Vitest, Playwright, and Storybook.
- The platform uses PostgreSQL with Prisma, Redis, RabbitMQ, and other services
  supplied by the Compose stack. ClamAV and cloud/provider integrations are
  conditional runtime dependencies.

## Common task locations

| Task | Start in |
| --- | --- |
| Bring up or diagnose local Platform services | `platform-stack` sub-skill |
| Add a REST route or request/response model | `platform-backend` sub-skill; feature modules are organized under `backend/api/features/` |
| Add a block or provider integration | `platform-backend` sub-skill; block code is under `backend/blocks/` |
| Change database models or migrations | `platform-backend` sub-skill; schema is `backend/schema.prisma` |
| Change the visual builder, Copilot, library, marketplace, auth, or settings UI | `platform-frontend` sub-skill; pages live under `frontend/src/app/` |
| Consume a new backend API on the UI | Backend first, then frontend generated API guidance |
| Run legacy agent, Forge, or direct benchmark work | `classic-agents` sub-skill |

## Service-facing ports

The documented default local entry points are:

| Service | Default port |
| --- | --- |
| Platform frontend | 3000 |
| Platform WebSocket server | 8001 |
| Platform REST/execution API | 8006 |
| Classic agent/Forge server | 8000 |

Treat ports as configurable deployment details. Confirm the active Compose and
environment configuration before assuming a process is listening.
