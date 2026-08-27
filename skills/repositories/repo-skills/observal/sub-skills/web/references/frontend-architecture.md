# Frontend Architecture

This reference distills the web frontend operating model. Use it to find the right files and keep changes aligned with the existing Observal UI architecture.

## Stack and runtime shape

| Concern | Operating fact |
|---|---|
| App type | Vite 6 single-page app, not Next.js |
| UI runtime | React 19, TypeScript 6, JSX runtime `react-jsx` |
| Routing | TanStack Router file routes generated from `web/src/routes/` |
| Data | TanStack Query hooks over a typed `/api/v1` fetch wrapper |
| Components | shadcn/ui-style primitives plus Observal domain components |
| Styling | Tailwind CSS 4 reading semantic OKLCH tokens from `web/src/app.css` |
| Charts/tables | Recharts 3 and TanStack Table |
| Dev proxy | Vite proxies `/api` and `/health` to the local API server on port 8000 |

`web/vite.config.ts` wires `TanStackRouterVite({ routesDirectory: "./src/routes" })`, React, `@` as an alias for `web/src`, `import.meta.env.VITE_APP_VERSION` from `web/package.json`, manual vendor chunks, and local dev server port 3000.

`web/src/main.tsx` creates the TanStack router from `routeTree.gen`, uses default preload `intent`, and renders `RouterProvider`. Treat `web/src/routeTree.gen.ts` as generated output; route fixes belong in route files and the Vite/TanStack plugin should regenerate the tree.

## Directory map

| Path | Owns |
|---|---|
| `web/src/routes/` | File routes, layouts, route params, search-param validation |
| `web/src/pages/` | Lazy page modules for larger screens while route migration continues |
| `web/src/components/ui/` | Reusable UI primitives |
| `web/src/components/layouts/` | `AuthGuard`, `RoleGuard`, page headers, dashboard shell |
| `web/src/components/nav/` | Registry sidebar, command menu, nav user, star/banner affordances |
| `web/src/components/registry/` | Agent/component cards, edit forms, pull/install command, harness badges, review form, status/version controls |
| `web/src/components/review/` | Review detail/diff sheets and validation badges |
| `web/src/components/traces/` | Trace detail, span tree, trace-oriented display components |
| `web/src/components/shared/` | Skeleton, error, empty, not-found, retention/version banners |
| `web/src/hooks/` | TanStack Query hooks, auth/role guards, deployment config, harness list, feature-specific API hooks |
| `web/src/lib/` | API wrapper, shared types barrel, query client, theme provider, GraphQL WS, registry-name helpers, utilities |
| `web/src/app.css` | Tailwind v4 import, OKLCH tokens, theme classes, semantic color/status/chart/sidebar tokens |

## Route model

The route tree uses pathless layout segments whose file names begin with `_`. Public URLs do not include these underscore segments.

| Route file pattern | Public surface |
|---|---|
| `web/src/routes/__root.tsx` | Global error boundary, query client, theme provider, dynamic title, version mismatch banner |
| `web/src/routes/(auth)/login.tsx` | `/login` unauthenticated login and first-run init |
| `web/src/routes/(auth)/register.tsx` | `/register` unauthenticated registration |
| `web/src/routes/(auth)/device.tsx` | `/device` device authorization confirmation |
| `web/src/routes/_authed.tsx` | Authenticated shell with auth guard, help provider, sidebar, command menu, toaster, outlet |
| `web/src/routes/_authed/index.tsx` | `/` registry home |
| `web/src/routes/_authed/agents/index.tsx` | `/agents` agent list |
| `web/src/routes/_authed/agents/$agentId.tsx` | `/agents/$agentId` agent detail |
| `web/src/routes/_authed/agents/$namespace.$slug.tsx` | slash-qualified agent reference route |
| `web/src/routes/_authed/agents/builder.tsx` | `/agents/builder` visual agent builder |
| `web/src/routes/_authed/agents/$agentId/insights/$reportId.tsx` | `/agents/$agentId/insights/$reportId` insight report detail |
| `web/src/routes/_authed/components/index.tsx` | `/components` component browser |
| `web/src/routes/_authed/components/$componentId.tsx` | `/components/$componentId` component detail |
| `web/src/routes/_authed/components/$type.$namespace.$slug.tsx` | slash-qualified component reference route |
| `web/src/routes/_authed/leaderboard.tsx` | `/leaderboard` downloads/rating leaderboard |
| `web/src/routes/_authed/teamspaces.tsx` and `$handle` | teamspace list/detail, including child outlet behavior |
| `web/src/routes/_authed/wiki/index.tsx` | `/wiki` help/wiki content |
| `web/src/routes/_authed/insights/$reportId.tsx` | Legacy report redirect into the agent-scoped report route |
| `web/src/routes/_authed/_admin.tsx` | Reviewer/admin pathless layout with role guard and retention banner |
| `web/src/routes/_authed/_admin/review.tsx` | `/review`, with typed `tab=agents|components|teamspaces` search validation |
| `web/src/routes/_authed/_admin/dashboard.tsx` | `/dashboard`, with typed `tab` and `range` search validation |
| `web/src/routes/_authed/_admin/users.tsx` | `/users` user management |
| `web/src/routes/_authed/_admin/settings.tsx` | `/settings` super-admin settings |
| `web/src/routes/_authed/_admin/sso.tsx` | `/sso` SSO admin surface |
| `web/src/routes/_authed/_admin/audit-log.tsx` | `/audit-log` audit log surface |
| `web/src/routes/_authed/_admin/security-events.tsx` | `/security-events` security events |
| `web/src/routes/_authed/_admin/diagnostics.tsx` | `/diagnostics` admin diagnostics |
| `web/src/routes/_authed/_user.tsx` | User pathless layout |
| `web/src/routes/_authed/_user/account.tsx` | `/account` profile/account page |
| `web/src/routes/_authed/_user/inbox.tsx` | `/inbox` personal work feed |
| `web/src/routes/_authed/_user/traces/index.tsx` | `/traces` trace list with search filters |
| `web/src/routes/_authed/_user/traces/$traceId.tsx` | `/traces/$traceId` trace/session detail |

When adding a route:

1. Put the route file under the correct layout segment.
2. Use `createFileRoute(...)` and keep public URL behavior consistent with pathless segments.
3. For large pages, lazy-load from `web/src/pages/...` and keep route files thin.
4. Add `validateSearch` for query params that affect data fetches, tabs, filters, or deep links.
5. Update `RegistrySidebar` and `CommandMenu` only when the new surface should be globally discoverable.
6. Do not rely on sidebar visibility as security. Server authorization is authoritative; client role guards only prevent flicker and route confusion.

## Layout and navigation

The root route wraps the app in:

- `ErrorBoundary`
- `QueryClientProvider` from `makeQueryClient()`
- `ThemeProvider defaultTheme="system"`
- `VersionMismatchBanner`
- `DynamicTitle`

The authenticated shell wraps content in:

- `AuthGuard` from `web/src/components/layouts/auth-guard.tsx`
- `HelpProvider`
- `SidebarProvider`
- `RegistrySidebar`
- `SidebarInset` and `Outlet`
- `CommandMenu`
- `Toaster`

`RegistrySidebar` groups nav items into Registry, Review, My Work, and Admin. Review/Admin/User visibility is driven by cached role plus `hasMinRole`; authenticated-only items are hidden until a session token is present. The sidebar also reads deployment branding and server version through query hooks, and it shows the inbox unread badge only for unread count.

## Page and component conventions

- Prefer `PageHeader`, `ErrorState`, `EmptyState`, and skeleton layouts for consistent loading/error/empty states.
- Prefer existing registry components for agent/component cards, review forms, edit forms, status badges, version dropdowns, harness badges, and pull commands.
- Prefer existing trace components for session detail/span-tree rendering instead of duplicating trace parsing in pages.
- Use TanStack Table for sortable/filterable tables.
- Use accessible controls from `web/src/components/ui/` before adding new primitive variants.
- Keep route-local helper functions in page modules unless they are reused across surfaces; then move them to `web/src/lib/` or a domain component.

## Harness-aware UI

The frontend must treat the server as the source of truth for harness names, display names, capabilities, supported models, and default harness.

Existing patterns:

- `useHarnesses()` fetches `/api/v1/config/harnesses` and returns `data` plus `defaultHarness`.
- `HarnessBadges` maps stored harness slugs to server display names.
- `PullCommand` builds `observal agent pull <agent> --harness <harness>` using the server default when valid, otherwise the first server-provided harness.

For a new registry page that needs harness data, import `useHarnesses()` or compose a new hook around `config.harnesses`. Do not copy a static harness array into the component.

## Theme and design tokens

`web/src/app.css` defines Tailwind v4 theme tokens using OKLCH values. Important token families:

- Base: `background`, `foreground`, `muted`, `popover`, `card`, `header`, `border`, `input`, `ring`
- Actions: `primary`, `secondary`, `accent`, `destructive`, `primary-accent`
- Status: `success`, `warning`, `info`
- Sidebar: `sidebar-*`
- Charts: `chart-1` through `chart-8`
- Surfaces: `surface-raised`, `surface-sunken`

Theme classes include light, dark, midnight, forest, sunset, solarized light/dark, dracula, nord, monokai, gruvbox, catppuccin, tokyo night, one dark, and rose pine. `ThemeProvider` stores the chosen theme under `observal-theme`, resolves `system` from `prefers-color-scheme`, and writes the resolved theme class to `document.documentElement.className`.

When changing visuals:

1. Use Tailwind classes backed by semantic tokens, such as `bg-card`, `text-muted-foreground`, `border-border`, `text-success`, or `bg-surface-sunken`.
2. If a new semantic token is truly needed, define it in `@theme inline` and every theme class that needs a custom value.
3. Do not add raw hex/rgb colors to components.
4. Do not add remote font/CDN dependencies; typography is local/system-token based.
5. Check at least light, dark/system, and one non-default theme for major visual changes.

## Ownership boundaries

- Web owns frontend routing, components, hooks, theme, local storage behavior, and Playwright-facing UI flows.
- Server owns FastAPI routes, data shape authority, auth enforcement, migrations, jobs, and insight generation semantics.
- CLI owns Typer command hierarchy and bundled command skills. Web may display commands such as `observal agent pull`, but command behavior belongs to CLI.
- Harness telemetry owns harness registry/adapters/hook specs/session parsers/ingestion delivery. Web only renders server-provided harness/session data.
- Repo-development owns broad contributor policy, release/compliance workflow, and non-web test strategy.
