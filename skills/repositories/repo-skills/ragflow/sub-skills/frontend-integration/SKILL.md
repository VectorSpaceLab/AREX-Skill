---
name: frontend-integration
description: "Modify and debug RAGFlow web frontend API integration, routes,
  services, hooks, React Query cache, dataset/chat/agent flows, and frontend
  tests."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Frontend Integration

Use this sub-skill when changing or debugging RAGFlow's web frontend integration: React/Vite app setup, route registration, API endpoint constants, request clients, service wrappers, React Query hooks, dataset/chat/agent page flows, parser-config forms, agent DSL bridge behavior, and frontend Jest/lint commands.

## Start Here

1. Locate the seam in the frontend stack before editing: route -> page -> hook -> service -> endpoint key -> request client.
2. For architecture and page-flow orientation, read `references/frontend-architecture.md`.
3. For endpoint constants, request/service/hook conventions, cache invalidation, and the static checker, read `references/api-client-patterns.md`.
4. For common failures, read `references/troubleshooting.md`.
5. For API prefix and key audits, run the bundled read-only helper from this skill directory: `python scripts/check_web_api_keys.py --root <ragflow-checkout>`.

## Scope Boundaries

- Include frontend files under `web/`, especially routes, app providers, endpoint constants, request clients, services, hooks, dataset pages, chat pages, agent canvas/pages, and focused Jest tests.
- Exclude backend route/service implementation details; pair with `backend-api-services` when a frontend change requires backend route contracts or response-shape changes.
- Exclude public SDK/client recipes; pair with `sdk-http-integration` for external HTTP/SDK users rather than web UI internals.
- Exclude ingestion/retrieval internals; pair with `dataset-ingestion-retrieval` when parser_config or retrieval behavior crosses into backend processing.

## High-Value Workflows

- Add an endpoint by updating endpoint constants, adding or adapting a service method, exposing a focused hook, wiring the page, and invalidating the exact affected query keys after mutations.
- Fix page navigation by keeping the `Routes` enum, lazy route config, nested route paths, and navigation helpers aligned.
- Debug dataset parser forms by checking frontend normalization before blaming the backend: parser extras move into `ext`, RAPTOR extras move into `raptor.ext`, and child-chunk UI fields map into `parent_child`.
- Debug agent canvas persistence by preserving the canonical DSL shape: `graph` for React Flow layout plus `components` for executable topology.

## Validation Commands

Run commands from `web/` after dependencies are installed:

- `npm run lint` for ESLint on TypeScript/React source.
- `npm run type-check` for TypeScript checks.
- `npm run build` for Vite production build.
- `npm run test -- src/hooks/tests/parser-config-utils.test.ts --runInBand` for parser_config normalization.
- `npm run test -- src/pages/agent/utils/tests/dsl-bridge.test.ts --runInBand` for agent DSL bridge round trips.
- `npm run test -- src/utils/tests/chat.test.ts --runInBand` for chat utility escaping/LaTeX behavior.

## Guardrails

- New REST-style frontend endpoints should normally use `/api/v1`; reserve `/v1` for legacy web endpoints that still exist there.
- Prefer the Axios client and `registerNextServer` for new service code; preserve deprecated request patterns only where existing services still depend on them.
- Keep query keys stable and invalidations explicit; stale data after a successful mutation is usually a missing or mismatched `invalidateQueries` call.
- Do not put long implementation notes in this `SKILL.md`; keep detailed patterns and troubleshooting in `references/`.
