# Frontend Architecture

## Package Shape

Langflow's browser UI is a private npm package built with React 19, TypeScript, Vite, SWC, Tailwind, Biome, Jest, Playwright, Axios, React Query, Zustand, and `@xyflow/react`. The package requires Node.js `>=20.19.0`; the development guide recommends Node `22.12` LTS with npm `10.9` or newer.

The production Langflow server serves compiled frontend assets. In development, run the FastAPI backend and Vite frontend separately: the backend listens on `7860`, while the Vite dev server listens on `3000` and proxies API routes to the backend.

## Runtime Configuration

The Vite config loads environment from the frontend process and from the repository `.env`. Important values are:

- `VITE_PROXY_TARGET`: overrides the backend proxy target; defaults to `http://localhost:7860`.
- `VITE_PORT`: overrides the Vite dev-server port; defaults to the configured frontend port or `3000`.
- `BACKEND_URL`: compiled into `import.meta.env.BACKEND_URL` with a default of `http://localhost:7860`.
- `LANGFLOW_AUTO_LOGIN`, `ACCESS_TOKEN_EXPIRE_SECONDS`, and feature flags such as extension reload are compiled into `import.meta.env` for browser behavior.
- `BASENAME`, `API_ROUTES`, `PORT`, and `PROXY_TARGET` are centralized in customization config constants.

Vite proxies API routes matching `/api/v1/`, `/api/v2/`, and `/health` by default. If a browser request bypasses those routes, the frontend may hit the wrong origin and show CORS, 404, auth, or network failures even when the backend is healthy.

## Primary Source Areas

- `CustomNodes/` owns graph node rendering, node update behavior, node input/output layout, validation status display, template mutation helpers, and React Flow integration points.
- `components/` contains shared UI primitives and common components. Prefer existing UI primitives before introducing a new design pattern.
- `controllers/` contains API access functions, Axios interceptors, and React Query hooks. Contract changes usually start here before reaching stores or UI components.
- `stores/` contains Zustand state for flows, auth, alerts, messages, folders, shortcuts, types/templates, and utility flags.
- `icons/` contains custom icon components plus eager and lazy import maps used by component cards, nodes, and UI controls.
- `src/__tests__/` and colocated `__tests__/` directories contain Jest tests; `tests/` contains Playwright browser tests and assets.

## Graph Workspace Model

Langflow's graph workspace uses `@xyflow/react`. The app wraps the UI in a `ReactFlowProvider`; graph state is stored primarily in `flowStore` and manager stores.

Key graph concepts:

- Nodes and edges use React Flow `Node`, `Edge`, and `ReactFlowJsonObject` types.
- Generic Langflow components render through `CustomNodes/GenericNode` and related helper components.
- Node data contains backend-provided component metadata, templates, inputs, outputs, icon names, build status, and user-edited code state.
- `flowStore` owns nodes, edges, build state, React Flow instance, update queues, undo snapshots, selected inputs/outputs, and component update flags.
- `typesStore` receives backend component data and derives display types, templates, component field sets, and display names.
- React Flow internal updates must be triggered when node templates, handles, or output visibility change so edges and handles stay aligned.

When modifying node UI, check whether the change affects:

1. Node layout only.
2. Template fields or advanced/hidden field processing.
3. Handles, output visibility, or edge validation.
4. Build status, validation status, or code-update behavior.
5. Persisted flow JSON or saved component data.

Persisted flow compatibility matters. Avoid changing node ids, backend component class identifiers, or serialized flow data shape unless the matching backend migration/upgrade behavior is handled elsewhere.

## Stores and State Management

Zustand stores follow a pattern of `create<StoreType>((set, get) => ({ ... }))`. Store actions frequently call other stores via `otherStore.getState()` for graph-wide coordination.

Practical rules:

- Use selectors in React components to avoid unnecessary rerenders.
- Prefer existing store actions over directly mutating complex graph state.
- When adding flow-state fields, update the associated type definitions and tests.
- Keep async API side effects in controllers or React Query hooks when possible; stores should coordinate state, not duplicate API clients.
- When updating graph nodes in response to backend code validation, use existing pending-update helpers so build/run actions do not race node refreshes.

## API Controllers and Query Hooks

The frontend uses an Axios instance configured with the frontend base URL and credentials behavior. The interceptor layer:

- Adds customization headers to same-origin requests and selected fetch requests.
- Prevents duplicate requests when configured helpers detect them.
- Handles auth failures by attempting refresh-token renewal when auto-login is not active.
- Avoids recursive refresh attempts for auth-maintenance endpoints such as refresh, login, logout, and auto-login.
- Clears build-running UI state after failed build/API requests.

API paths are built with the frontend base URL helper and usually target backend routes under `/api/v1/` or `/api/v2/`. When a backend contract changes, update the TypeScript API types, controller function, React Query hook, store consumer, and focused tests together.

## Testing Strategy

Start with the narrowest safe check:

- Static package script check: `python scripts/check_frontend_package.py src/frontend/package.json`.
- Formatting/lint: `npm run check-format`, `npm run lint`, or `make format_frontend` when dependencies are installed.
- Unit tests: `npm test -- --runTestsByPath <test-file>` or `npm test` for all Jest tests.
- Type/build: `npm run type-check` and `npm run build` for contract or build-impacting changes.
- Browser regressions: `npx playwright test tests/core --project=chromium` for graph workspace behavior; this starts a backend and frontend via Playwright config when the Python and Node environments are ready.

Do not run credentialed, network-heavy, or broad e2e tests unless the user has approved the environment and time cost. Record skipped candidates for later verification instead of forcing them.

## Backend Component Index Refresh Pitfall

The frontend component palette and graph nodes depend on backend component metadata. During backend component development, dynamic loading can be enabled on the backend so component changes appear without rebuilding the index. Without dynamic loading, backend component changes may require rebuilding the component index and refreshing the browser before the UI sees updated components.

Frontend symptoms of backend index drift include missing palette entries, stale node templates, nodes marked as updates available, hidden outputs not matching backend outputs, or validation requests returning templates that do not match the current UI. Route the backend indexing work to `../component-development/SKILL.md`, then use this sub-skill to update UI display, icon, tests, and controller assumptions.
