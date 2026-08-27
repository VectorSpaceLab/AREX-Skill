# Frontend Troubleshooting

## When to read

Read this when the portal has wrong API URLs, auth redirect loops, stale data, broken provider icons, webhook UI disabled unexpectedly, sync streams failing, SSR/hydration issues, pnpm/toolchain problems, Tailwind style drift, or build/lint/test failures.

## Quick triage

1. Run the safe checker to detect metadata, route, hook, and runtime-config drift:

   ```bash
   python skills/disco/open-wearables/sub-skills/frontend-portal/scripts/check_frontend_metadata.py --repo-root .
   ```

2. Confirm `VITE_API_URL` points at the backend the browser and SSR server should use.
3. Confirm route navigation uses `ROUTES` / `DEFAULT_REDIRECTS` and query state uses `queryKeys`.
4. Reproduce with the smallest static command available: `pnpm run test`, `pnpm run lint`, `pnpm run format:check`, then `pnpm run build`.
5. If the frontend is correct but backend data/auth/provider behavior is wrong, route the server-side investigation to `backend-core` or `provider-integrations`.

## Runtime API URL is wrong

Symptoms:

- Browser network tab points to an old API host after redeploy.
- Mobile app invitation dialog copies the wrong API Base URL.
- Provider icons load from a wrong host.
- Docker image works only when rebuilt with a different API URL.

Likely causes:

- Application code read `import.meta.env.VITE_API_URL` directly, so Vite inlined the build-time value.
- The root route stopped injecting `runtimeConfigScript()` before hydration.
- `API_CONFIG.baseUrl` was bypassed for image URLs or copy UI.
- SSR server environment does not provide `VITE_API_URL`, so the fallback is used.

Fix:

1. Search changed code for direct `import.meta.env.VITE_API_URL` reads outside the runtime-config helper.
2. Replace application reads with `API_CONFIG.baseUrl`.
3. Keep `runtimeConfigScript()` in the root route's document head before app hydration.
4. Ensure the runtime environment sets `VITE_API_URL` for the SSR frontend server.
5. Run the metadata checker; it verifies runtime-config markers and root injection.
6. Build after the fix. The same build should work against different runtime API URLs.

## Auth redirect loop or hydration mismatch

Symptoms:

- Protected pages bounce to login after a valid login.
- Browser console shows hydration mismatch around initial redirects.
- `/` renders differently on server and client.
- Login/register pages redirect incorrectly for signed-in users.

Likely causes:

- A route guard accessed localStorage during SSR.
- `beforeLoad` did not guard with `typeof window === 'undefined'`.
- Session expiration cleared `ow_auth_token` but UI still assumes authenticated state.
- API returned `401`, causing `apiClient` to clear session and redirect.

Fix:

1. Keep protected and public auth route guards browser-only.
2. Use `DEFAULT_REDIRECTS` for authenticated/unauthenticated redirects.
3. Check session storage keys only through `lib/auth/session` helpers.
4. If a backend call returns `401`, debug token/auth behavior in `backend-core`; the frontend should clear session and route to login.
5. For `/`, keep a stable loading/spinner render that is safe for SSR and client hydration.

## Stale UI after mutations

Symptoms:

- A created/deleted user does not appear in the users table.
- Dashboard counts do not update after user or seed-data changes.
- Webhook detail saves but list rows still show old data.
- Provider toggles or live-sync mode revert unexpectedly.
- User detail data remains stale after XML upload, sync, or delete.

Likely causes:

- Mutation did not invalidate the relevant `queryKeys` family.
- A params object was omitted from a query key.
- Detail cache was not set after a mutation returned an updated record.
- Optimistic update did not roll back on error.

Fix:

1. Identify the hook that owns the mutation.
2. Match the affected UI to query-key families from [api-hooks-and-state.md](api-hooks-and-state.md).
3. Invalidate list families after create/delete/bulk updates.
4. Set detail cache on successful record updates where the server response has the full record.
5. Invalidate summaries/dashboard/health families when mutations affect aggregate data.
6. For optimistic changes, snapshot previous data in `onMutate` and restore it in `onError`.

## New route does not appear or navigation fails

Symptoms:

- A page exists but sidebar link fails.
- TanStack build cannot resolve a route.
- Links to parameterized users fail at runtime.
- Browser URL includes `/_authenticated` unexpectedly.

Likely causes:

- Route file path and `createFileRoute` id do not match TanStack conventions.
- `ROUTES` was not updated.
- Parameterized route lacks `params` in `Link`/`navigate`.
- Protected page was added outside the `_authenticated` pathless layout or linked with the internal file-route id.

Fix:

1. Add or fix the route file with the correct TanStack file-route id.
2. Add/update the public browser path in `ROUTES`.
3. Use `Link`/`navigate` with `params` for `$userId` and `$endpointId` routes.
4. Add sidebar entries only for top-level pages meant for main navigation.
5. Run `pnpm run build` to regenerate/validate route integration.

## Webhooks page says disabled

Symptoms:

- Webhooks page loads but Add webhook is disabled.
- Warning says outgoing webhooks are not enabled.
- Webhook endpoints are not fetched.

Likely causes:

- `useConfig()` returned `outgoing_webhooks_enabled !== true`.
- Backend feature flag/environment is off.
- Config endpoint failed and UI is showing the config error branch.

Fix:

1. Confirm the frontend uses `useConfig()` before `useWebhookEndpoints(webhooksEnabled)`.
2. If config failed, retry and inspect the API response.
3. If config is false, route backend flag/setup to `backend-core`; do not hard-enable frontend create buttons.
4. Keep the UI disabled until the instance config explicitly enables outgoing webhooks.

## Sync stream fails or provider cards do not update

Symptoms:

- User profile shows no active sync progress.
- Sync stream error displays a status code.
- Connections do not refresh after pairing or sync start.
- One provider card opens many redundant network streams.

Likely causes:

- `useSyncStatusStream` opened without a `userId` or with `enabled=false`.
- Backend SSE endpoint rejected auth or returned non-stream response.
- Code opened one stream per connection instead of grouping events once per user.
- Terminal events are not invalidating sync queries.

Fix:

1. Use one `useSyncStatusStream(userId)` at the profile-section level.
2. Group active events and recent runs by provider, then pass them to `ConnectionCard`.
3. Verify the stream request includes `Accept: text/event-stream` through `syncStatusService.openStream`.
4. For auth/endpoint failures, route to `backend-core`.
5. Ensure terminal statuses invalidate `queryKeys.syncStatus.all` and start events invalidate `queryKeys.connections.all(userId)`.

## Provider icons or coverage labels look wrong

Symptoms:

- Provider logo images 404.
- Coverage matrix shows wrong providers or categories.
- A green dot is interpreted as synced data.

Likely causes:

- Relative `icon_url` was concatenated against the wrong base URL.
- Provider coverage backend declarations changed but frontend assumptions did not.
- UI copy conflates provider capability with actual user data.

Fix:

1. Build icon URLs with `API_CONFIG.baseUrl` or `new URL(icon_url, API_CONFIG.baseUrl)` consistently.
2. Keep coverage page copy clear: coverage is capability, not synced volume.
3. If provider names, icons, or capability truth changed, route the source-of-truth fix to `provider-integrations`.
4. Keep frontend matrix rendering generic over the coverage response instead of hardcoding provider columns.

## Pairing/OAuth flow fails

Symptoms:

- Pairing picker shows no providers.
- Clicking provider returns "Failed to get authorization URL".
- Success page does not update protected profile connections.
- Return-to-app link is lost.

Likely causes:

- `useOAuthProviders(true, true)` returns no enabled cloud providers.
- Backend OAuth authorize endpoint rejected `user_id`, `redirect_uri`, or provider config.
- `redirect_url` search param was not preserved through success/error URLs.
- Success page did not invalidate `queryKeys.connections.all(userId)`.

Fix:

1. Confirm Providers settings has enabled providers.
2. Use `useOAuthConnect({ userId, redirectUrl })` for the real pairing flow.
3. Preserve `redirect_url` through search validation and success/error links.
4. Invalidate connections on success.
5. Route provider-specific OAuth backend errors to `provider-integrations`.

## Apple XML upload fails

Symptoms:

- Upload button rejects a file immediately.
- Toast says invalid file type or file too large.
- Upload succeeds but user data does not show immediately.

Likely causes:

- File extension is not `.xml` and MIME is not `text/xml` or `application/xml`.
- File size exceeds frontend max-size constant.
- Large files use the S3 path and backend processing is asynchronous.
- Health/data-summary queries were not invalidated.

Fix:

1. Keep file validation in `useAppleXmlUpload`.
2. Ensure direct and S3 upload success paths invalidate user detail and active health queries.
3. Tell users asynchronous processing may take time after S3 upload.
4. Route presigned URL, S3, SQS, and import processing errors to `backend-core` or `provider-integrations` depending on the server owner.

## Tailwind/style changes do not compile or tokens are missing

Symptoms:

- `bg-*` or `text-*` utilities for new tokens do not exist.
- Inline styles using theme variables resolve to empty values.
- `dark:` variants stop working.
- Build fails after adding a Tailwind config.

Likely causes:

- Tailwind v4 CSS-first conventions were bypassed.
- Token was placed only in `@theme` but no utility uses it, so it was not emitted.
- Variable references were not declared in `@theme inline`.
- A legacy JavaScript config or `@config` was introduced.

Fix:

1. Add durable raw variables to `:root`.
2. Map variable-based utilities in `@theme inline`.
3. Keep static tokens in `@theme`.
4. Keep `@custom-variant dark (&:where(.dark, .dark *))`.
5. Use standard duration utilities or arbitrary values reading variables; there is no generated `duration-fast` namespace.
6. Run format/lint/build after style changes.

## pnpm, tests, lint, or build fail

Symptoms:

- `pnpm` command is missing.
- Install rejects Node version.
- Vitest import aliases fail.
- Oxlint or Prettier reports changed files.
- Build fails around ESM/Nitro/TanStack Start.

Likely causes:

- Node is below `>=22.0.0` or pnpm is below `>=10.0.0`.
- Corepack has not prepared the pinned pnpm.
- Dependencies are not installed from the lockfile.
- Formatting/lint changes are required.
- New route/service imports violate TypeScript strictness or path alias rules.

Fix:

1. Check Node and pnpm versions against package metadata.
2. Use Corepack to prepare pnpm when needed.
3. Install dependencies with `pnpm install`.
4. Run `pnpm run format` or `pnpm run lint:fix` only when it is acceptable to modify source.
5. Run `pnpm run format:check`, `pnpm run lint`, `pnpm run test`, and `pnpm run build` for verification.
6. If dependencies are unavailable, run the bundled metadata checker and record frontend native checks as deferred rather than faking a pass.

## When to stop and reroute

Stop frontend-only work and route elsewhere when:

- Endpoint authorization, schema, or backend error mapping is unknown (`backend-core`).
- Provider registration, OAuth scopes, webhook ingestion, or coverage declarations are the issue (`provider-integrations`).
- Assistant/MCP tool behavior is the issue (`mcp-server`).
- The task requires real credentials, live provider OAuth accounts, S3 writes, webhook delivery to external URLs, or other network/credential side effects not explicitly authorized.
