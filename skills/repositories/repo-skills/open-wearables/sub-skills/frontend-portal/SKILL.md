---
name: frontend-portal
description: "React/TanStack Start frontend portal routes, API hooks, runtime
  configuration, and UI workflows for Open Wearables."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Frontend Portal

Use this sub-skill for Open Wearables frontend work in the React/TanStack Start portal: routes, protected pages, auth/session behavior, dashboard/users/detail screens, device pairing, provider coverage, sync monitoring, outgoing webhooks, settings tabs, API hooks/services/query keys, runtime API URL configuration, styling/components, and frontend test/lint/build workflows.

## Route the task

- For page routing, layout, auth guards, sidebar navigation, settings tabs, user detail panels, coverage matrix, pairing flows, syncs, webhooks, and reusable UI components, read [routes-and-components.md](references/routes-and-components.md).
- For service modules, `apiClient`, `API_ENDPOINTS`, runtime `VITE_API_URL` resolution, TanStack Query hooks, query-key invalidation, uploads, OAuth connection helpers, and SSE state, read [api-hooks-and-state.md](references/api-hooks-and-state.md).
- For local development commands, Node/pnpm requirements, environment variables, UI change checklists, and frontend verification commands, read [workflows.md](references/workflows.md).
- For symptoms and fixes around auth redirects, stale queries, runtime API URL drift, SSR hydration, provider icons, webhook enablement, sync streams, Tailwind v4, pnpm/Corepack, lint, and build failures, read [troubleshooting.md](references/troubleshooting.md).
- Before or after frontend edits, run the safe metadata/source checker when a checkout is available: `python skills/disco/open-wearables/sub-skills/frontend-portal/scripts/check_frontend_metadata.py --repo-root .`. The script only reads package metadata and source text; it does not install packages, call the network, or write application files.

## Boundaries

This sub-skill owns the portal-facing frontend contract. Route backend API implementation, database models, migrations, auth/token semantics, outgoing webhook delivery internals, and endpoint docs navigation to `backend-core`. Route provider OAuth strategy internals, coverage declarations, provider factory changes, import normalization, and provider webhook parsing to `provider-integrations`. Route MCP assistant tools and API-client behavior to `mcp-server`.

When a UI task spans boundaries, keep the frontend changes here but hand off server-side endpoint shape, permissions, provider capability truth, and docs/API-reference changes to the owning backend sub-skill.

## Non-negotiable frontend rules

- Use TanStack Router file routes and centralized route constants from `ROUTES` / `DEFAULT_REDIRECTS`; do not add ad hoc path strings for new navigation.
- Use the shared API layer: `API_ENDPOINTS`, service modules under `lib/api/services`, `apiClient`, and TanStack Query hooks under `hooks/api`.
- Do not read `import.meta.env.VITE_API_URL` directly in application code. Use `API_CONFIG.baseUrl`, which is resolved by `resolveApiUrl()` and the runtime config script.
- Use the query-key factory in `queryKeys` for all server state and invalidate or update the exact affected keys after mutations.
- Preserve SSR-safe auth guards: browser-only session checks must handle `typeof window === 'undefined'`.
- Keep Tailwind CSS v4 CSS-first: design tokens live in `styles.css`; do not reintroduce a JavaScript Tailwind config.
- Prefer existing shadcn/ui primitives, common components, feature components, `sonner` toasts, and React Hook Form + Zod validation before adding one-off patterns.

## Fast start for future agents

1. Classify the request as a route/component task, an API hook/state task, a workflow/tooling task, or a troubleshooting task.
2. Read the linked reference closest to that task; avoid reopening source files unless you are refreshing this generated skill or verifying drift.
3. For new UI backed by an endpoint, define the endpoint constant, service method, query key, hook, route/component usage, and mutation invalidation together.
4. For user-facing navigation, update `ROUTES`, the TanStack route file, and sidebar/settings tab wiring consistently.
5. Verify with the safe metadata checker, then run `pnpm run test`, `pnpm run lint`, `pnpm run format:check`, and `pnpm run build` when dependencies are available and the task warrants it.
