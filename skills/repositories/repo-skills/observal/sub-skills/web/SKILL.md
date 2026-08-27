---
name: web
description: "Guide agents modifying Observal's Vite/React/TanStack Router web
  frontend, query hooks, auth storage, registry/admin/traces/insights pages,
  theme tokens, type centralization, and UI verification."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Observal Web Frontend Router

Use this sub-skill when the task touches the Observal web UI: Vite/React route files, lazy page modules, shared UI components, TanStack Query hooks, auth/session storage, registry/admin/traces/insights pages, theme tokens, frontend type contracts, or Playwright/screenshot verification.

Do **not** use this sub-skill for CLI command semantics, FastAPI route/business logic, database migrations, harness adapter/session-parser behavior, telemetry hook delivery, release policy, or cross-repo contribution workflow. Route those to the owning sub-skill.

## Route the request

- Architecture, route ownership, page/component layout, navigation, theme tokens: read `references/frontend-architecture.md`.
- API wrapper, TanStack Query hooks, auth storage/refresh, server-fetched harness data, type placement: read `references/api-hooks-and-types.md`.
- Verification commands, E2E selection, screenshot expectations, and expected signals: read `references/ui-testing.md`.
- Install, import, auth/API, config, optional dependency, telemetry/harness, and workflow failure recovery: read `references/troubleshooting.md`.

## Non-negotiable rules

1. The frontend is a Vite SPA with React 19 and TanStack Router; it is not Next.js.
2. File routes live under `web/src/routes/`; complex routes usually lazy-load modules under `web/src/pages/`. Do not edit `web/src/routeTree.gen.ts` by hand.
3. Use TanStack Query hooks. Add reusable API calls to `web/src/lib/api.ts`, wrap them in the closest `web/src/hooks/use-*-api.ts` module, and export reusable hooks through `web/src/hooks/use-api.ts` when appropriate.
4. Do not hardcode harness lists or capabilities in frontend code. Use server data from `/api/v1/config/harnesses` through `useHarnesses()`.
5. Keep shared API response types in `web/src/lib/types.ts` or one of the files it reexports. Avoid inline shared response types in components.
6. Auth storage is deliberately split: access token in `sessionStorage`, refresh token and cached profile fields in `localStorage`. Do not widen `localStorage` use unless the auth model is intentionally changed.
7. Use semantic OKLCH theme tokens from `web/src/app.css` and the theme provider. Do not add raw hex/rgb colors or external font CDNs to components.
8. For user-visible UI changes, provide targeted verification and screenshots for touched states before claiming completion.

## Default work loop

1. Identify the owning route/page/component/hook from the architecture reference.
2. If new server data is needed, update API types, `api.ts`, query hook module, and query invalidation before wiring components.
3. Add or change route files with TanStack Router helpers and typed `validateSearch` where query params matter.
4. Use shared layout, loading, empty, error, table, registry, review, traces, and shadcn/ui primitives instead of one-off patterns.
5. Run the bundled static helper, then the smallest safe frontend checks for the change.
6. Escalate instead of patching around missing backend contracts, CLI command changes, harness telemetry gaps, or deployment policy decisions.
