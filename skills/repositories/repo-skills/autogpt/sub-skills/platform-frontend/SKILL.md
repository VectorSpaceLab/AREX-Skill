---
name: platform-frontend
description: "Develop and validate the AutoGPT Platform Next.js frontend,
  generated API hooks, Builder/Copilot UI, design system, and frontend tests."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Platform Frontend

Use this sub-skill for the `autogpt_platform/frontend` Next.js App Router
application: authenticated platform pages, Builder, Copilot, Library,
Marketplace, settings, teams, generated API hooks, feature flags, design-system
components, and frontend test suites.

## Reference map

- Read [frontend architecture](references/frontend-architecture.md) for route
  groups, component/hook structure, state, API clients, auth, and design rules.
- Read [API and testing](references/api-and-testing.md) for Orval generation,
  MSW handlers, Vitest integration tests, Playwright happy paths, Storybook,
  and command ordering.
- Read [troubleshooting](references/troubleshooting.md) for Corepack/pnpm,
  stale OpenAPI, auth redirects, build/type errors, MSW, and seeded E2E data.
- Run `python scripts/frontend_preflight.py --repo <checkout>` for a read-only
  Node/package/layout check. It does not install packages or launch Next.js.

## Development sequence

1. Work from `autogpt_platform/frontend`. Enable Corepack so the
   `packageManager` field selects the pinned pnpm version, then install only
   the dependencies required for the task.
2. For a page, use the App Router under `src/app`, keep page logic in a hook
   when it is non-trivial, and colocate feature components and helpers.
3. For server data, use Orval-generated React Query hooks under
   `src/app/api/__generated__/endpoints/`; regenerate from the backend OpenAPI
   source rather than hand-editing generated files.
4. Use Tailwind design tokens, the design-system components, and the Icon atom
   with Hugeicons. Do not introduce legacy component paths or raw internal
   links when the project convention provides a component.
5. Add a page-level Vitest/RTL/MSW integration test for new feature behavior.
   Use Playwright only for a critical real-browser journey and Storybook for
   visual/design-system behavior.

## Required checks after frontend changes

```bash
pnpm format
pnpm lint
pnpm types
pnpm test:unit
```

Use `pnpm generate:api` after intentional backend API/OpenAPI changes. Full
`pnpm test` or `pnpm test-ui` builds the app and requires the backend stack and
seeded test data; do not run it as a casual smoke check.

## Routing boundaries

- Backend route/schema/OpenAPI source changes belong to
  [platform-backend](../platform-backend/SKILL.md).
- Docker, service startup, env files, and migrations belong to
  [platform-stack](../platform-stack/SKILL.md).
- Classic frontend/agent references belong to [classic-agents](../classic-agents/SKILL.md).
