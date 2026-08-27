---
name: frontend-development
description: "Modify Langflow's React/Vite frontend, graph workspace, stores,
  icons, frontend tests, and UI/backend contract touchpoints."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Frontend Development

Use this sub-skill when a task changes Langflow's browser UI: the visual flow workspace, React components, Zustand stores, API controllers/hooks, frontend tests, custom icons, Vite build configuration, or UI/backend data contracts.

Route Python API/service implementation to `../backend-runtime/SKILL.md`. Route Python component class semantics, component indexes, and backend component compatibility to `../component-development/SKILL.md`; this sub-skill covers the frontend consequences of those backend changes.

## Start Here

1. Confirm Node.js is at least `20.19.0` and npm is available. The frontend package is private and is built with React, TypeScript, Vite, Biome, Jest, Playwright, `@xyflow/react`, Axios, and Zustand.
2. For local UI development, run the backend and frontend separately: start the backend on port `7860`, then run the Vite frontend on port `3000`. Set `VITE_PROXY_TARGET=http://localhost:7860` when the frontend should proxy API calls to a non-default backend.
3. Use [references/frontend-architecture.md](references/frontend-architecture.md) before touching graph nodes, stores, API controllers, or tests.
4. Use [references/ui-contracts-and-icons.md](references/ui-contracts-and-icons.md) before changing backend/frontend contracts, icon names, lazy icon imports, or component palette display behavior.
5. Use [references/troubleshooting.md](references/troubleshooting.md) when npm install, Vite, Jest, Playwright, proxy, schema, icon, auth, or backend readiness failures appear.

## Common Commands

Run frontend commands from the frontend package directory unless using a root `make` target.

- Install dependencies as part of full repo setup: `make init`.
- Start the dev frontend through the repo target: `make frontend`.
- Start directly from the frontend package: `npm start`.
- Build production assets: `npm run build`.
- Run Jest unit tests: `npm test` or a targeted Jest invocation.
- Run Playwright e2e tests when safe and dependencies are installed: `npx playwright test tests/core --project=chromium`.
- Format and lint frontend code: `make format_frontend`, `npm run check-format`, `npm run lint`, and `npm run type-check`.

## Bundled Helper

Use [scripts/check_frontend_package.py](scripts/check_frontend_package.py) for a safe static check of a frontend `package.json` before attempting npm commands:

```bash
python scripts/check_frontend_package.py src/frontend/package.json
```

The helper verifies that expected npm scripts such as `start`, `build`, `test`, and at least one quality gate are present without running Node, npm, Vite, Jest, or Playwright.

## Task Checklist

- Identify whether the change is UI-only, a UI/backend contract change, or a backend component display refresh; route backend semantics to the right sibling sub-skill before editing frontend assumptions.
- Keep backend component class names stable. The frontend uses backend-provided component types/templates and can flag updates, but renaming a backend component class breaks saved flows.
- Update the closest store, controller query, custom node helper, or UI component instead of adding cross-cutting state in unrelated files.
- Add or update focused Jest tests for stores, controllers, hooks, and UI utilities; use Playwright for graph workspace or full browser regression behavior.
- Validate with the narrowest relevant command first, then expand to lint/type/build or Playwright only when the environment supports it.
