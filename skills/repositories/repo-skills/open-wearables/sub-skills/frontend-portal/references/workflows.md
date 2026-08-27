# Frontend Workflows

## When to read

Read this for frontend development setup, command selection, UI change checklists, runtime environment variables, and validation strategy. These workflows are safe instructions for a normal development checkout; they do not require credentials unless the backend feature being exercised needs them.

## Toolchain facts

Package metadata requires:

- Node.js `>=22.0.0`.
- pnpm `>=10.0.0`.
- package manager: `pnpm@10.13.1+sha512.37ebf1a5c7a30d5fabe0c5df44ee8da4c965ca0c5af3dbab28c3a1681b70a256218d05c81c9c0dcf767ef6b8551eb5b960042b9ed4300c59242336377e01cfad`.

Use Corepack to provide the pinned pnpm version when pnpm is not already available.

## Environment variables

The frontend `.env` shape is:

```bash
VITE_API_URL=http://localhost:8000
NODE_ENV=development
```

`VITE_API_URL` is intentionally consumed at runtime through `resolveApiUrl()` and `API_CONFIG.baseUrl`. Do not bypass the runtime-config layer.

## Package scripts

Run commands from the frontend package directory in a checkout:

| Command | Package script | Purpose |
| --- | --- | --- |
| `pnpm run dev` | `vite dev --port 3000` | Start local TanStack Start/Vite development server on port 3000. |
| `pnpm run build` | `vite build` | Build the SSR frontend. Vite output directory is configured as `dist`; the SSR server output is handled by TanStack Start/Nitro. |
| `pnpm run serve` | `vite preview` | Preview a production build. |
| `pnpm run test` | `vitest run` | Run Vitest tests. Current source-level utility tests cover activity-stat calculations and date formatting. |
| `pnpm run lint` | `oxlint -c .oxlintrc.json src` | Static lint check. |
| `pnpm run lint:fix` | `oxlint -c .oxlintrc.json --fix src` | Auto-fix supported lint violations in `src`. |
| `pnpm run format` | `prettier --write "src/**/*.{ts,tsx,js,jsx,json,css,md}"` | Format source. |
| `pnpm run format:check` | `prettier --check "src/**/*.{ts,tsx,js,jsx,json,css,md}"` | Check formatting without writes. |

Use `pnpm run lint:fix && pnpm run format` after source edits when auto-fixes/formatting are acceptable. Use `pnpm run format:check` in verification when avoiding writes.

## Safe metadata/source check

The bundled checker validates the frontend package metadata, route/hook/service inventory, runtime-config source markers, route constants, query-key families, and this sub-skill's frontmatter without installing packages:

```bash
python skills/disco/open-wearables/sub-skills/frontend-portal/scripts/check_frontend_metadata.py --repo-root .
```

Useful variants:

```bash
python skills/disco/open-wearables/sub-skills/frontend-portal/scripts/check_frontend_metadata.py --repo-root . --json
python skills/disco/open-wearables/sub-skills/frontend-portal/scripts/check_frontend_metadata.py --repo-root /path/to/checkout --skill-root skills/disco/open-wearables/sub-skills/frontend-portal
```

Run this before deeper pnpm checks when you need a quick drift signal or when dependencies are not installed.

## First setup workflow

1. Ensure Node satisfies the package `engines.node` requirement.
2. Enable or prepare pnpm through Corepack if needed.
3. Install dependencies with the lockfile: `pnpm install`.
4. Create frontend env from the expected shape and set `VITE_API_URL` to the backend API URL for the environment.
5. Start the backend/API separately when exercising live portal behavior.
6. Start the frontend: `pnpm run dev`.
7. Visit the local frontend server and sign in/register against the configured backend.

If the task does not need live UI behavior, prefer static checks (`check_frontend_metadata.py`, lint, tests, build) over starting long-running servers.

## Adding a route or page

1. Decide whether the page is public or protected.
   - Public pages live outside the `_authenticated` route group.
   - Protected pages use the `_authenticated` layout and are reachable through public URL paths such as `/dashboard`, `/users`, or `/settings`.
2. Add the TanStack file route using `createFileRoute` and keep route params/search validation close to the route.
3. Add or update `ROUTES` and, if it is a default redirect target, `DEFAULT_REDIRECTS`.
4. Add sidebar navigation only for top-level protected pages that users should browse directly.
5. For settings, update the `tabs` array with an id, label, and component; keep tab-local form state inside the tab component.
6. Use existing layout primitives: `PageHeader`, `Tabs`, `Dialog`, `AlertDialog`, `Button`, `Input`, `Label`, `Skeleton`, `ErrorState`, and common components.
7. Add API hooks through the service/query-key workflow rather than calling `fetch` directly, except for the existing OAuth authorization redirect pattern.
8. Verify route constants and source inventory with the bundled checker, then run lint/build as appropriate.

## Adding a settings tab backed by a new endpoint

This is a common cross-boundary case. Keep the UI work here, but route endpoint implementation and authorization to `backend-core`.

1. Confirm the backend endpoint path, method, auth, payload, response type, and error shape.
2. Add an `API_ENDPOINTS` constant and a typed service method.
3. Add a `queryKeys` family if the setting is independent from existing state.
4. Add hooks for load/save operations with `enabled` guards and focused invalidation.
5. Create a tab component that owns local form state, initializes from query data, computes `hasChanges`, validates locally, and disables save while invalid or pending.
6. Use optimistic updates only when the rollback path is clear. Otherwise save and invalidate.
7. Surface changed/unsaved state clearly, following Providers and Data Lifecycle patterns.
8. If the endpoint is external API surface, coordinate docs/API-reference navigation with `backend-core`.
9. Validate with the checker, `pnpm run lint`, `pnpm run format:check`, and `pnpm run build` when dependencies are installed.

## Adding or changing API hooks

1. Add endpoint constants in `API_ENDPOINTS`; use functions for path parameters.
2. Add or extend a service module. Services should return typed values and use `apiClient` helpers.
3. Add a query-key method under the relevant family. Include params in the key when they affect the result.
4. Add a hook in `hooks/api`. Keep required IDs and date ranges in `enabled`.
5. In mutation hooks, invalidate affected list/detail/summary/dashboard keys and set detail cache when returning updated records.
6. Use `getErrorMessage(error)` and `toast` in user-triggered mutations.
7. If backend behavior is uncertain, stop at frontend scaffolding and route server semantics to `backend-core`.

## Updating user-detail panels

- Add data fetches through `use-health` or `use-users` hooks.
- Keep date range state at the user-detail page level when the tab section needs a top-level tab label and one date selector per panel.
- Reuse section components and `DateRangeSelector`/`DateFilter` primitives.
- Maintain `DataSummarySection` consistency after mutations by invalidating `queryKeys.health.dataSummary(userId)`.
- For provider connection actions, update connection state and sync/backfill state together.
- For destructive data actions, use confirmation dialogs and state clearly that deletion is irreversible.

## Updating pairing/provider UI

- Use `useOAuthProviders(true, true)` for provider pickers that should show enabled cloud providers.
- Use `API_CONFIG.baseUrl` for relative provider icon URLs.
- Public pairing supports `redirect_url` search validation and passes it through success/error pages.
- `useOAuthConnect` builds the OAuth `redirect_uri` and redirects to the backend-provided `authorization_url`.
- Success pages must invalidate the user's connection query so protected profile state refreshes after OAuth completes.
- Provider internals, provider registration, coverage declarations, and OAuth backend strategy changes belong to `provider-integrations`.

## Updating webhooks UI

- Gate endpoint list/create UI on `useConfig().data?.outgoing_webhooks_enabled === true`.
- Use `useWebhookEventTypes` for event-type selectors; it is treated as effectively static (`staleTime`/`gcTime` infinity).
- Keep endpoint updates in the detail cache and invalidate the endpoint list.
- Secret reveal should stay opt-in and not load until explicitly enabled.
- Delivery attempts use filters plus iterator stack; reset the stack when filters change.
- Outgoing delivery implementation, signatures, retries, and backend feature flags belong to `backend-core`.

## Updating coverage UI

- Coverage data comes from `useCoverage` and `metaService.getCoverage`.
- Treat coverage as code capability; do not present it as synced data volume or user-specific availability.
- Matrix tabs are timeseries, workout, sleep, women's health, and health scores.
- Provider names/icons/badges come through shared source badge helpers.
- Provider capability truth and coverage drift fixes belong to `provider-integrations`.

## Updating styling or UI primitives

1. Prefer existing shadcn/ui components and variants.
2. Use `cn()` for conditional classes.
3. Add design tokens in `styles.css`: raw HSL triplets in `:root`, variable mappings in `@theme inline`, static tokens in `@theme`.
4. Keep `.dark` class behavior and `@custom-variant dark` intact.
5. Do not add a JavaScript Tailwind config or legacy `@config` unless intentionally migrating the design system.
6. Validate with format/lint/build after CSS changes.

## Native verification candidates

After this sub-skill is integrated into the full repo skill, useful frontend-native candidates are:

- `pnpm run test` for existing Vitest utility tests around activity calculations and date formatting.
- `pnpm run lint` for Oxlint source checks.
- `pnpm run format:check` for Prettier consistency.
- `pnpm run build` for TanStack Start/Vite/Nitro SSR build integrity.

Do not treat absence of a live backend as a frontend build failure unless the change explicitly requires a live API. For endpoint-coupled features, pair frontend checks with backend tests or a synthetic usability case that asserts route/hook behavior and clear failure states.
