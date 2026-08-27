# Testing and Build

## Purpose

Read this before running frontend checks, adding tests, changing TypeScript imports, or debugging npm/Vite/Vitest failures.

## Package scripts

Run from `apps/web` unless using the bundled wrapper script.

| Command | Purpose | Notes |
|---|---|---|
| `npm install` | Install frontend dependencies from `package-lock.json`. | Node engine is `>=20`; Node 22 is the primary target. |
| `npm run dev` | Start Vite dev server. | Serves UI on `http://localhost:3020`; proxies API/WebSocket calls to the backend configured in `vite.config.ts`. |
| `npm run typecheck` | `tsc -b --noEmit`. | Strict TypeScript gate; catches import/type/unused issues. |
| `npm run lint` | ESLint flat config with `--max-warnings 0`. | React hooks and react-refresh rules are enabled. |
| `npm test` | `vitest run`. | Uses jsdom and `vitest.setup.ts`. |
| `npm run test:watch` | Interactive Vitest watch mode. | Use for local iteration, not final handoff. |
| `npm run build` | `tsc -b && vite build`. | Production bundle under `dist/`; includes a type build first. |
| `npm run preview` | Preview built bundle. | Requires a prior build. |
| `npm run gen:api` | Generate `src/api/schema.ts` from running backend OpenAPI. | Generated file is not the active hand-written client surface. |
| `npm run gen:api:file` | Generate `src/api/schema.ts` from local `openapi.json`. | Useful when backend is not running. |

Full frontend gate:

```bash
cd apps/web
npm run typecheck
npm run lint
npm test
npm run build
```

Bundled selective wrapper from this sub-skill:

```bash
bash scripts/ui_static_check.sh --typecheck --lint --test --build
bash scripts/ui_static_check.sh --typecheck --test
bash scripts/ui_static_check.sh --help
```

## TypeScript/import conventions

Compiler settings in `tsconfig.app.json` include `strict`, `noUnusedLocals`, `noUnusedParameters`, `noFallthroughCasesInSwitch`, `isolatedModules`, and `verbatimModuleSyntax`.

Follow these rules:

- Use `@/` alias for imports from `src`, e.g. `import { runsApi } from '@/api/endpoints';`.
- Prefer named exports for pages/components.
- Use `import type` for type-only imports, e.g. `import type { Run, TaskType } from '@/api/types';`.
- Avoid `any`; ESLint permits it, but prefer `unknown` or a typed mirror.
- Prefix intentionally unused parameters with `_` to satisfy `@typescript-eslint/no-unused-vars`.
- Keep component modules component-only when practical. If a module must export helpers, consider moving helpers to `*.helpers.ts` to satisfy `react-refresh/only-export-components`.
- Do not rely on implicit globals beyond those declared in `eslint.config.js`.

## Test stack

The UI uses:

- Vitest.
- Testing Library React.
- Testing Library user-event.
- `@testing-library/jest-dom/vitest` via `vitest.setup.ts`.
- jsdom from Vite/Vitest config.

Pattern for components that use React Query:

```tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

function wrap(ui: React.ReactNode) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return <QueryClientProvider client={qc}>{ui}</QueryClientProvider>;
}
```

Pattern for endpoint mocks:

```tsx
const listMock = vi.fn();

vi.mock('@/api/endpoints', () => ({
  dataSourcesApi: {
    list: (id: string) => listMock(id),
  },
}));
```

Pattern for auth state tests:

```ts
localStorage.clear();
useAuthStore.setState({ accessToken: null, refreshToken: null, user: null });
```

Pattern for WebSocket tests:

- Replace `globalThis.WebSocket` with a controllable fake class.
- Drive `_open`, `_message`, `_close` inside `act()`.
- Set `useAuthStore` access token before rendering.
- Restore the real WebSocket and auth state in `afterEach`.

## Existing test coverage map

Representative tests to mirror when adding related UI:

| Area | Existing tests | What they assert |
|---|---|---|
| Dynamic setup form | `components/DynamicForm.test.tsx` | Structural rendering by schema kind, groups order, hide list, default application, default stripping, no hard-coded parameter contract. |
| Event stream | `components/EventStream.test.tsx` | WebSocket URL/token, live indicator, event rendering, terminal sentinel, auth close code. |
| Auth store/gate | `state/auth.test.ts`, `components/AuthGate.test.tsx` | Token persistence/clear, refresh behavior, gated rendering. |
| LLM modals/cards | `AnalyzeDatasetModal.test.tsx`, `ExperimentDesignerModal.test.tsx`, `RunExplainerCard.test.tsx`, `FailureDebuggerCard.test.tsx`, `DeploymentReviewModal.test.tsx`, `DriftAnalysisModal.test.tsx` | Endpoint body, opt-in vs auto-fire behavior, standard LLM advice envelope rendering. |
| Deployment prediction | `components/PredictTester.test.tsx` | JSON textarea seed, inline parse error, prediction response rendering. |
| Governance/admin pages | `pages/ApiKeysScreen.test.tsx`, `pages/AuditLogViewer.test.tsx`, `pages/WorkspaceMembers.test.tsx` | Query/mutation rendering and user interaction. |
| Setup/bootstrap | `pages/Setup.test.tsx` | First-run form behavior. |
| Leaderboard | `components/Leaderboard.test.tsx` | Legacy/common leaderboard behavior. |

## Testing guidelines

- Prefer behavior tests over snapshots.
- Use `userEvent` for real user interaction; use `fireEvent.change` when replacing the entire value of a controlled input or pasting invalid JSON.
- Disable React Query retries in tests to keep failures deterministic.
- Use `await screen.findBy...` or `waitFor` for async query/mutation results.
- Assert request bodies sent to endpoint mocks for forms and LLM widgets.
- Keep tests local to the component/page they cover.
- Mock only the endpoint group needed by the component; do not mock the axios client unless testing `client.ts` itself.
- For route-aware components, wrap with `MemoryRouter` and seed paths/params as needed.
- For components that touch `window.confirm`, mock it explicitly and restore it.
- For Plotly-heavy tests, prefer asserting wrapper/error/placeholder behavior rather than rendering full interactive charts.

## Build and lint gotchas

- `npm run build` runs TypeScript first, so a build failure can be a type error before Vite starts bundling.
- `verbatimModuleSyntax` makes type-only imports important. If TypeScript complains about importing a type as a value, change it to `import type`.
- `noUnusedLocals` and `noUnusedParameters` are compiler errors, not just lint warnings.
- `react-hooks/rules-of-hooks` catches hooks after early returns. Compute hooks before guard returns, as `TrialsCard` does.
- `react-refresh/only-export-components` warns when component files export non-component helpers. The lint command treats warnings as failures due to `--max-warnings 0`.
- `src/api/schema.ts` is ignored by ESLint; do not import it unless deliberately switching to generated types.
- `dist` and `node_modules` are ignored.

## Browser smoke path after a UI change

When a backend is available, a useful minimal smoke is:

1. Start backend and UI dev server.
2. Open `http://localhost:3020`.
3. Bootstrap or login.
4. Switch/open a workspace.
5. Navigate through the changed route using sidebar or direct URL.
6. If editing run/trial/deployment UI, open a known run/deployment and verify empty/loading/error states plus happy path.
7. If editing API client/auth, refresh a deep link and confirm the auth gate restores the session.
8. If editing event logs, start/open a run and confirm the WebSocket reaches live or terminal state.

## Required final check selection

Use the smallest check set that covers the edit, then run the full gate for broad or route-level changes:

- Types-only or endpoint signatures: `npm run typecheck`.
- Component or page logic: `npm run typecheck && npm test`.
- Styles/layout with lint-sensitive imports: `npm run typecheck && npm run lint`.
- Route/table/app-shell changes: `npm run typecheck && npm run lint && npm test && npm run build`.
- Before declaring a release-quality web change done: full gate.
