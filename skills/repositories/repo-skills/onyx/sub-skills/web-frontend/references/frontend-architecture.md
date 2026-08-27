# Frontend Architecture

Use this reference to orient web changes before editing. It distills the web app structure, frontend proxy, feature service/hook pattern, and major UI surfaces.

## Runtime stack and package shape

- The web workspace is a Next.js 16 / React 19 app managed through `web/package.json` scripts. It uses strict TypeScript, React Compiler for production builds, Turbopack rooted at the `web/` workspace, and Next typed routes.
- `@onyx-ai/opal` and `@onyx-ai/shared` are local workspaces under `web/lib/`. The web app transpiles both packages in Next config.
- `@opal/*` aliases resolve to Opal source during app development. `@/*` resolves to `web/src/*`, and `@tests/*` resolves to `web/tests/*`.
- `web/src/lib/generated/` is reserved for generated artifacts and may be empty in a clean checkout. Do not hand-edit generated files.

## App Router layout and providers

The app uses Next App Router under `web/src/app/`.

- Root app shell: `web/src/app/layout.tsx` imports global CSS, web fonts, theme support, tooltips, analytics, health/banner queues, auth shell, product gating, modal root, and SWR global retry behavior.
- Root redirect: `/` redirects to `/app`.
- Auth routes live under `web/src/app/auth/**` and include login, signup, OAuth, SAML, password reset, verification, impersonation, and logout flows.
- Main user app routes live under `web/src/app/app/**`. Its layout runs server-side auth, disables static caching, then wraps children in project and voice-mode providers, Opal `RootLayout`, `AppSidebar`, and `AppChrome`.
- Admin routes live under `web/src/app/admin/**`. The admin layout goes through server-side admin auth and then renders the admin chrome.
- Enterprise-specific app/admin routes are under `web/src/app/ee/**` and `web/src/ee/**`; preserve CE/EE separation when editing feature gates.
- Craft build-mode UI lives under `web/src/app/craft/**` and `web/src/app/craft/v1/**`.

Prefer keeping server components for auth/layout boundaries and using client components only where React state, browser APIs, SWR, Zustand, or event handlers are needed.

## Frontend API proxy

All browser, test, and curl-style calls that exercise the local app should go through the frontend origin, for example `http://localhost:3000/api/persona`, not backend port `:8080` directly.

The catch-all route `web/src/app/api/[...path]/route.ts` proxies HTTP methods to `INTERNAL_URL` in development. It:

- preserves request method, query parameters, body, headers, abort signal, and streamed responses;
- copies `set-cookie` headers back to the browser response;
- injects a debug auth cookie in development when configured;
- returns 404 outside development unless the explicit preview override is enabled.

Next config also rewrites `/api/docs`, `/openapi.json`, PostHog ingest routes, and Craft webapp HMR routes. For frontend work, treat `/api/...` as the stable client boundary. Backend route behavior and schemas belong to backend-platform or agents-craft-and-tools.

## Feature data fetching and service modules

Use client-side SWR for most read paths. The root SWR config suppresses retries for auth/tier-gated `401`, `402`, and `403` responses.

Recommended pattern:

1. Add or reuse a key in `web/src/lib/swr-keys.ts` for GET-style cacheable reads.
2. Put feature-specific read hooks in `web/src/lib/<feature>/hooks.ts` and use `useSWR<T>(SWR_KEYS.foo, errorHandlingFetcher)`.
3. Put fetch/mutation helpers in `web/src/lib/<feature>/svc.ts` or a nearby feature service file. Use `/api/...` relative URLs.
4. Put server-only fetch/auth helpers in `svcSS.ts` files and keep them out of client components.
5. Components should show a loader, placeholder, empty state, or disabled state while their own data is loading rather than forcing top-level pages to fetch everything.
6. After mutations, call the relevant SWR `mutate` key or predicate. Use stable keys from `SWR_KEYS` instead of duplicated inline strings.

Manual `fetch()` is normal for mutations, uploads, streaming, and one-off setup calls. Parse errors through `parseErrorDetail` when user-facing detail matters.

## UI composition layers

Use these layers in order when building or changing UI:

- Opal primitives and components from `web/lib/opal/src/` through `@opal/components`, `@opal/layouts`, `@opal/icons`, `@opal/utils`, and `@opal/types`.
- Feature composites under `web/src/sections/**`, especially entity cards under `web/src/sections/cards/**` and feature-specific modals/menus/tables.
- App/page layout wrappers under `web/src/layouts/**` and Opal `SettingsLayouts`, `RootLayout`, and `SidebarLayouts`.
- `web/src/refresh-components/**` only as a fallback for production components not yet migrated to Opal.
- Avoid new use of legacy `web/src/components/**` except where existing code already depends on a legacy surface such as logo handling or a specialized markdown renderer.

Admin/settings pages commonly compose `SettingsLayouts.Root`, `SettingsLayouts.Header`, `SettingsLayouts.Body`, Opal cards/content, and feature-specific service/hooks. Cards for reusable entity displays should live under `web/src/sections/cards/**` rather than being copied into pages.

## Chat surface

The main chat UI is under `web/src/app/app/**` plus shared sections and providers.

- App chrome and sidebar: `web/src/layouts/chromes/AppChrome.tsx`, `web/src/sections/sidebar/**`, and project/sidebar helpers in `web/src/lib/sidebar/**`.
- Chat page and input: `web/src/app/app/page.tsx`, `web/src/sections/input/**`, `web/src/sections/chat/**`, and model selector sections.
- Message rendering and streaming packet display: `web/src/app/app/message/**`, especially timeline hooks/renderers for grouped packets, tool output, reasoning, deep research, generated images, code blocks, and resubmission.
- Chat services live in `web/src/app/app/services/**` and `web/src/lib/chat/**`.

Backend streaming, prompt construction, LLM routing, MCP/tool execution, and Craft sandbox behavior are not owned by this sub-skill; route those to agents-craft-and-tools.

## Admin surface

Admin entry routes are in `web/src/app/admin/**`; larger pages and reusable page bodies often live in `web/src/views/admin/**` and `web/src/sections/**`.

Common admin domains include agents, actions/MCP/OpenAPI tools, connectors, indexing status, documents, groups/users, service accounts, SSO/SCIM, security, billing/license, token rate limits, tracing, voice, image generation, web search, and Craft configuration. Keep API URLs relative to `/api/...` and preserve admin auth checks in the server layout.

When adding a new admin page, use the existing admin route layout, `SettingsLayouts`, Opal buttons/text/cards, a feature `svc.ts` for mutations, and a feature hook for reads.

## Craft frontend surface

Craft UI is a frontend for build-mode sessions and sandboxes. This sub-skill owns the rendered UI, client state, parsing, and tests; backend sandbox provisioning and opencode runtime behavior route to agents-craft-and-tools.

Important Craft frontend pieces:

- `web/src/app/craft/components/**`: chat/build panels, input bar, output preview, tool cards, approvals, sandbox notices, scheduled run banners, and session sidebar.
- `web/src/app/craft/hooks/**`: build session store/controller, streaming, pre-provision polling, wake-on-intent, live approvals, sandbox status reconciliation, and code highlighting.
- `web/src/app/craft/services/**`: API calls, external app services, restore/search-param helpers.
- `web/src/app/craft/utils/**`: packet parsing, path sanitization, local storage, stream item helpers, language highlighting, scheduled task run helpers, and subagent routing.
- `web/src/app/craft/v1/**`: Craft v1 routes for apps, tasks, scheduling, connectable apps, and registries.

Use Jest for isolated parser/store/component behavior and Playwright only when the browser flow must exercise real services.

## Generated and typed artifacts

- `bun run types:check` runs Next type generation and TypeScript checking. Use it after route, typed-route, provider, or shared type changes when Bun/dependencies are available.
- `web/src/lib/generated/` is intentionally generated/ignored. If imports from generated clients or DTOs fail, regenerate the relevant artifact rather than editing it manually.
- `/openapi.json` is available through the frontend rewrite when services are running, but backend OpenAPI generation and backend clients are owned by backend/CLI tooling, not this sub-skill.
- Opal and shared package `dist/` directories may be absent in a source checkout. Web development can resolve Opal through `@opal/*`, while package-style imports need built `dist` output.

## Change workflow checklist

Before editing a frontend feature:

1. Identify the route/page, feature `src/lib` owner, and UI layer owner.
2. Use `/api/...` relative URLs and existing SWR keys when possible.
3. Choose Opal components first; only fall back to refresh components where Opal has no equivalent.
4. Keep route/server auth checks in server files and browser interactions in client components.
5. Add or update the smallest Jest/RTL or Playwright coverage that proves user-visible behavior.
6. Run targeted checks when Bun and services are available; otherwise record the missing runtime prerequisite explicitly.
