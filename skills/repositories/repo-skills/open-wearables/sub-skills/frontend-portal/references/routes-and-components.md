# Routes and Components

## When to read

Read this when modifying portal navigation, protected layouts, auth pages, dashboards, users, device pairing, coverage, syncs, webhooks, settings tabs, reusable components, or styling. It is distilled from the frontend route/component source and is intended to be enough for routine UI work without reopening source evidence.

## Portal stack facts

- Framework: TanStack Start with React 19 and TanStack Router file routes.
- Server state: TanStack Query through a root `QueryClientProvider`.
- Forms: React Hook Form with Zod validation on auth and complex forms.
- Notifications: `sonner` toasts.
- Styling: Tailwind CSS 4, shadcn/ui primitives, dark UI by default.
- Build output: the frontend is an SSR Node application, not a static-only build.

## Route topology

TanStack route files use the `_authenticated` pathless layout for protected application pages. Public URLs come from route constants; internal `createFileRoute('/_authenticated/...')` ids are not the browser URL.

| Browser route | Route role | Primary UI / behavior | Key state and services |
| --- | --- | --- | --- |
| `/` | Entry redirect | Client-side and browser-only `beforeLoad` redirect to dashboard or login. Renders a spinner during SSR/hydration. | `isAuthenticated()`, `DEFAULT_REDIRECTS` |
| `/login` | Public auth | Login form, brand preview card, redirects authenticated users to dashboard. | `useAuth().login`, `authService.login`, `setSession` |
| `/register` | Public auth | Register form with Zod validation, password visibility toggles, auto-login after successful registration. | `useAuth().register`, `registerSchema` |
| `/forgot-password` | Public auth | Email form that always shows a generic success message after submit. | `useAuth().forgotPassword`, `forgotPasswordSchema` |
| `/reset-password?token=...` | Public auth | Token-validated password reset; strips token from visible URL after load. | `useAuth().resetPassword`, `resetPasswordSchema` |
| `/accept-invite?token=...` | Public team onboarding | Invitation acceptance form; invalid-token and success states. | `useAcceptInvitation`, `acceptInvitationSchema` |
| `/dashboard` | Protected overview | Platform metrics, data metrics, recent users, and last-synced users. | `useDashboardStats`, `useUsers` |
| `/users` | Protected user list | Search/sort/paginated table, create-user dialog, delete confirmation. | `useUsers`, `useCreateUser`, `useDeleteUser` |
| `/users/$userId` | Protected user detail | Profile, workouts, activity, sleep, body, scores, conditional women's health tab, Apple XML upload, pairing link, mobile app invitation code. | `useUser`, `useUserDataSummary`, `useAppleXmlUpload`, health hooks |
| `/users/$userId/pair` | Public pairing layout | Outlet for pairing pages. | TanStack `Outlet` |
| `/users/$userId/pair/` | Public pairing picker | OAuth provider selection with optional `redirect_url` passthrough; lists enabled cloud providers and existing connections when authenticated. | `useOAuthConnect`, `useOAuthProviders(true, true)`, `useUserConnections` |
| `/users/$userId/pair/success` | Public pairing result | Success UI, invalidates connection queries, optional return-to-app link. | `queryClient.invalidateQueries(queryKeys.connections.all(userId))` |
| `/users/$userId/pair/error` | Public pairing result | Error UI with retry and optional return-to-app link. | `useOAuthProviders` |
| `/widget/connect` | Public widget demo | Embeddable provider-selection card; currently simulates OAuth and posts messages to a parent window. | `useOAuthProviders(true, true)`, `API_CONFIG.baseUrl` |
| `/coverage` | Protected provider coverage | Capability explanation, provider selector, provider detail, matrix tabs. | `useCoverage`, `CoverageMatrix`, `ProviderDetail` |
| `/syncs` | Protected sync monitor | Filters sync runs by user/provider/status/source and paginates by overfetching one extra row. | `useAllSyncRuns`, `useOAuthProviders`, `ROUTES.user` |
| `/webhooks` | Protected outgoing webhooks | Lists endpoints, create/delete dialogs, disabled-instance warning. | `useConfig`, `useWebhookEndpoints` |
| `/webhooks/$endpointId` | Protected webhook detail | Overview/edit form, secret reveal, test event, delivery attempts with filters and cursor-style iterator stack. | `useWebhookEndpoint`, `useUpdateWebhookEndpoint`, `useWebhookAttempts`, `useWebhookEventTypes` |
| `/settings` | Protected settings | Local tab state for credentials, providers, priorities, data lifecycle, team, security, and seed data. | Many settings hooks; see below |

## Root and protected layout

The root route renders the full HTML shell:

- `QueryClientProvider` wraps the portal.
- `Toaster` enables `sonner` notifications.
- TanStack Router and Query devtools appear only in development.
- `runtimeConfigScript()` is injected before the app hydrates, publishing `window.__APP_CONFIG__.apiUrl` for runtime backend URL resolution.
- `Scripts` from TanStack Router is rendered at the end of the body.

The `_authenticated` layout:

- Uses `beforeLoad` to skip checks during SSR (`typeof window === 'undefined'`) and redirects unauthenticated browser users to `DEFAULT_REDIRECTS.unauthenticated`.
- Renders `SimpleSidebar` and an `Outlet` for protected pages.
- Relies on local session storage managed by `lib/auth/session` and API-client 401 handling.

## Central navigation constants

All internal route paths are centralized in `ROUTES`:

- Public: `login`, `register`, `forgotPassword`, `resetPassword`, `acceptInvite`.
- Protected: `dashboard`, `users`, `user`, `webhooks`, `syncs`, `settings`, `coverage`.
- Widget: `widgetConnect`.

`DEFAULT_REDIRECTS.authenticated` points to dashboard and `DEFAULT_REDIRECTS.unauthenticated` points to login. Use these constants for redirects and navigation. For parameterized users, use `ROUTES.user` with TanStack `params: { userId }` when practical.

## Sidebar ownership

`SimpleSidebar` owns the main protected navigation:

- Dashboard, Users, Webhooks (Beta badge), Syncs, Data Coverage, Settings.
- Documentation is an external link and is not part of the route constants.
- Active state is `location.pathname.startsWith(item.url)`.
- Logout calls `useAuth().logout` and displays the injected `__APP_VERSION__`.

When adding a protected top-level page, update all of these together: route file, `ROUTES`, sidebar menu item, relevant hooks/services/query keys, and tests/build validation.

## Major page/component owners

| Area | Main components | Notes |
| --- | --- | --- |
| Dashboard | `StatsGrid`, `DataMetricsSection`, `RecentUsersSection`, loading/error states | Uses dashboard stats plus two limited user lists sorted by `created_at` and `last_synced_at`. |
| Users list | `UsersTable`, create/delete dialogs | Form validates max field lengths and basic email format before create. Pagination default is 9 rows. |
| User detail | `ProfileSection`, `DataSummarySection`, `ConnectionCard`, `ActivitySection`, `SleepSection`, `WorkoutSection`, `BodySection`, `ScoresSection`, `WomensHealthSection` | Tabs are local state. Women's Health tab appears only when data summary says data exists. Apple XML upload is chosen through `useAppleXmlUpload`. |
| Provider connections | `ConnectionCard` | Shows provider icon, status, scopes, linked users, live sync mode, Garmin backfill progress, disconnect/delete-data dialogs, historical sync, force live sync, SSE active status, and recent sync runs. |
| Pairing | Pair picker, success, error pages | Public route with optional developer-app `redirect_url`; OAuth authorization uses `API_CONFIG.baseUrl`. Success invalidates connection queries. |
| Coverage | `CoverageMatrix`, `ProviderDetail`, `SourceBadge` | Matrix tabs: timeseries categories, workout fields, sleep fields, women's health, health scores. Green dots are code capability, not user-specific synced data. The page is data-driven from the coverage API through `useCoverage`; provider coverage changes normally need no React edit unless the backend response shape, grouping, labels, icon fields, or display behavior changes. |
| Syncs | Table rows and filter selects | Supports provider/status/source/user filters. Limit is capped by a frontend `MAX_ALL_RUNS_LIMIT` of 10,000. |
| Webhooks | `WebhooksTable`, create/delete dialogs, `WebhookForm`, secret reveal, test-event dialog, attempts table | Create is disabled if instance config says outgoing webhooks are disabled. Attempts support event-type multi-select and status/limit filters. |
| Settings | Credentials, Providers, Priorities, Data Lifecycle, Team, Security, Seed Data | Each tab owns its own local form state and saves through a focused hook. |
| Common UI | `LoadingSpinner`, `ErrorState`, `MetricCard`, `SectionHeader`, `CursorPagination`, source/device badges | Prefer these before creating one-off loading, error, metric, or pagination markup. |
| shadcn/ui | Button, Card, Input, Label, Badge, Dialog, AlertDialog, DropdownMenu, Sheet, Sidebar, Table, Tabs, Tooltip, Switch, Skeleton, Sonner | Keep variants and class names consistent with existing primitives. |

## Settings tab map

- Credentials: shows runtime `API_CONFIG.baseUrl`, API keys (`useApiKeys`, create/update/delete), and SDK applications (`useApplications`, create/delete/rotate secret). Application secrets are one-time reveal values.
- Providers: lists OAuth providers, stores local toggle state, and bulk-updates changed `is_enabled` values.
- Priorities: reorders provider priorities and device type priorities, saving bulk priority payloads.
- Data Lifecycle: edits archive/delete policies, displays storage estimates and growth projections, can trigger an archival run after saving pending settings.
- Team: lists developers and pending invitations, creates/resends/revokes invitation links, and prevents deleting the current developer.
- Security: wraps `SecuritySettings`, which uses the auth password-change flow.
- Seed Data: custom synthetic-data form with presets, date ranges, provider selection, workout/sleep/time-series options, validation for sleep count and stage percentages, and a background-generation mutation.

## Styling and component conventions

- Tailwind v4 is CSS-first. There is no JavaScript Tailwind config; theme tokens are in `styles.css`.
- `:root` holds raw HSL triplet design tokens and durable variables such as durations.
- `@theme inline` maps variables into utility namespaces. Use `inline` for tokens that reference other variables.
- Dark mode is driven by a `.dark` ancestor through `@custom-variant`, not by system color preference.
- Use `cn()` for conditional classes and existing token utilities such as `bg-card`, `text-muted-foreground`, `border-border`, `text-success-muted`, and `text-destructive-muted`.
- Avoid relying on unused `@theme` variables directly in inline styles; Tailwind may remove unused generated variables.
- Do not reintroduce `tailwind.config.ts`, `@config`, or non-v4 configuration unless the frontend architecture is intentionally migrated.

## Accessibility and UX defaults

- Keep icon-only buttons labeled with `aria-label` or clear surrounding text.
- Keep loading and error states explicit on every route that fetches data.
- For destructive actions, use confirmation dialogs and explain irreversible effects.
- For one-time or secret values, show explicit copy affordances and warnings.
- For long IDs and URLs, use monospace text, truncation only when a copy action is available, and avoid losing the full value in forms/dialogs.
