# Frontend Dashboard Troubleshooting

## First checks

1. Confirm the task belongs to the dashboard. If it is about backend endpoint implementation, connector internals, Connect widget internals, MCP, or Monke, route to the sibling sub-skill instead.
2. Check whether the failure is auth, organization context, usage/billing, endpoint shape, or build/test related.
3. For endpoint schemas and backend status codes, cross-check sibling [backend-api](../../backend-api/SKILL.md).
4. For frontend validation, prefer these safe checks from the frontend package:

```bash
npm test -- src/utils/cronParser.test.ts
npm run lint
npm run build
```

Run the cron parser test as the smallest native check; lint/build are broader later-integration checks.

## Auth-disabled dev mode behaves differently from Auth0

Symptoms:

- The app renders without Auth0 login.
- API calls include a development bearer token.
- Admin pages are visible unexpectedly.

Likely cause:

- Auth is disabled through runtime/Vite auth configuration.
- In auth-disabled mode, the dashboard uses a mock Developer user and `is_admin` defaults to true unless explicitly disabled.

Recovery:

- For local OSS/dev behavior, this is expected.
- To test non-admin UI in dev mode, set the dev-admin flag to false in the frontend environment.
- To test Auth0 behavior, ensure auth is enabled and Auth0 domain, client ID, and audience are configured.
- Remember that billing setup redirects home when auth is disabled.

## Requests hang or fire before Auth0 is ready

Symptoms:

- Initial dashboard calls appear delayed.
- Console logs mention queued requests or auth initialization.
- Calls resume after login/token setup.

Likely cause:

- `apiClient` queues requests until `tokenProvider.isReady()` returns true.
- Auth0 token initialization or user-profile enrichment is still in progress.

Recovery:

- Do not bypass `apiClient` for dashboard data loads.
- Check the auth context's `tokenInitialized`, `auth0IsLoading`, and `isAuthenticated` state.
- Avoid adding requests outside the provider tree; the token provider is wired by `ApiAuthConnector`.

## `401` or `403` after login

Symptoms:

- First request fails, then retries.
- Persistent `403` refreshes organizations.
- UI buttons disappear or disable after permission changes.

Likely cause:

- Token expired, user lost org permissions, or active organization is stale.

Recovery:

- Let the one-shot token refresh happen; do not add loops.
- If retry is still `403`, inspect organizations after `initializeOrganizations()` refreshes them.
- Confirm the active organization is valid for the user.
- If a mutation fails, switch organizations manually; mutations intentionally do not auto-switch.

## Wrong organization or stale resource URL

Symptoms:

- A GET succeeds but the UI switches organizations and retries.
- A mutation returns not found/forbidden even though the resource exists elsewhere.
- Collections, API keys, or auth-provider connections disappear after opening a resource.

Likely cause:

- A response included an accessible `organization_id` different from the current organization.
- The API client auto-switched on a successful GET and cleared organization-scoped caches.

Recovery:

- This is expected for stale GET resource links outside the homepage.
- For mutation failures, verify the current organization before retrying.
- Ensure new GET responses that include `organization_id` are safe to trigger auto-switching.
- Do not move auto-switching to mutations.

## API path or base URL errors

Symptoms:

- Frontend calls 404 while backend routes exist.
- Requests go to the frontend dev server instead of the backend.
- Calls include `/api/v1` and fail.

Likely cause:

- Endpoint was built with the wrong prefix or API base URL.

Recovery:

- Use `apiClient` and root-relative endpoint strings such as `/collections`.
- Do not prefix dashboard calls with `/api/v1`.
- Check runtime `window.ENV.API_URL` and Vite API URL configuration.
- For local frontend development, remember the Vite server runs separately from the backend API.

## Usage or billing gates disable UI

Symptoms:

- Create Collection, Add Source, Source buttons, or Search are disabled.
- Tooltips say source connection, entity, query, token, or payment limit reached.
- Switching organization changes which controls are enabled.

Likely cause:

- `UsageChecker` or `SearchBox` usage checks returned `usage_limit_exceeded` or `payment_required`.

Recovery:

- Inspect usage store `actionChecks` for the relevant action.
- Re-run checks after changing organization or billing state.
- Check organization billing info and billing status.
- In OSS billing mode, subscription fetch can return a billing-disabled response and the UI should not require action.
- Do not assume disabled UI means the backend would reject every call; it is a user-facing preflight gate.

## Search input disabled

Symptoms:

- Search textarea is disabled.
- Search shows "Connect a source to enable search."
- Tier icons are disabled or auto-switch.

Likely cause:

- The collection has no source connections.
- Query or token usage is blocked.
- The usage check is still loading.

Recovery:

- Confirm source connections are loaded for the collection readable ID.
- Check usage responses for `queries` and `tokens`.
- Agentic search depends on token allowance; instant/classic depend on query allowance.
- If both query and token allowances are blocked, all tiers remain disabled.

## Search request returns `422`

Symptoms:

- Search response displays a validation detail instead of generic failure.
- Filters or request body were recently changed.

Likely cause:

- Backend rejected filter or body shape.

Recovery:

- Cross-check tier body shape with backend API guidance.
- Verify `toBackendFilterGroups()` output.
- Ensure instant requests use `retrieval_strategy`; classic requests do not.
- Confirm agentic requests send `thinking` only to the agentic stream route.

## Agentic stream stalls or cancels

Symptoms:

- Trace stays in Thinking/Searching.
- Stop button emits cancelled state.
- UI shows a transient retry message.

Likely cause:

- The streamed response ended unexpectedly, the request was aborted, or the stream emitted incomplete frames.

Recovery:

- Check the browser/network stream and backend logs for SSE frame formatting.
- The parser expects blank-line-separated frames with `data:` lines containing JSON.
- Unknown events should be tolerated; `done` is needed for final results.
- Retrying should allocate a new sequence and abort the prior controller.

## API-code snippet uses placeholder key

Symptoms:

- Search code modal shows `YOUR_API_KEY`.

Likely cause:

- `/api-keys` returned no decrypted key or the call failed.

Recovery:

- Confirm the user/org has an API key.
- Confirm API key fetch uses the correct org header.
- Do not embed a real key in code examples; the modal should read it from the API response at runtime.

## OAuth return did not finish a source connection

Symptoms:

- URL has `status=success` but source remains pending.
- Sync never starts after OAuth.
- Session storage contains an OAuth claim token.

Likely cause:

- The dashboard did not successfully call `verify-oauth`, or the claim token was missing.

Recovery:

- Look for `oauth_claim_token:{source_connection_id}` in sessionStorage.
- Call `POST /source-connections/{id}/verify-oauth` with `{ claim_token }`.
- Remove the token only after a successful response.
- If verification fails, keep enough state/logging to retry or diagnose; do not silently clean the URL as if success occurred.

## Collection events do not refresh lists

Symptoms:

- Sidebar or collections list stays stale after create/update/delete.

Likely cause:

- The collection event bus was not emitted or subscribed.

Recovery:

- Emit `collection:created`, `collection:updated`, or `collection:deleted` after successful mutations.
- Ensure `subscribeToEvents()` is mounted in dashboard layout/app-level contexts that need refresh.
- Use force refresh when event-driven changes should bypass the short cache window.

## Webhooks cannot be managed

Symptoms:

- Add subscription is disabled.
- A non-manager sees existing webhooks but cannot edit.
- Create fails with endpoint verification details.

Likely cause:

- Current org role is not owner/admin, or backend webhook verification rejected the endpoint.

Recovery:

- Check `canManageOrganization()` against the current organization.
- Surface backend `detail` from failed create calls; it may contain endpoint verification errors.
- Avoid caching queries that include webhook signing secrets.
- Use recover/enable/disable actions through the webhook hooks so query invalidation refreshes UI.

## Auth provider configuration is blocked

Symptoms:

- Clicking an unconfigured auth provider shows "Only admins can configure auth providers".
- Provider list loads but no connections appear.

Likely cause:

- User is not owner/admin, or connections fetch is stale for the active org.

Recovery:

- Check current organization role.
- Refresh auth provider connections after create/update/delete.
- Remember auto-switching clears auth-provider connection cache.

## Billing setup or portal fails

Symptoms:

- Billing setup redirects home.
- Checkout/portal creation fails and navigates back.
- Developer plan shows a Stripe listener/webhook activation error.

Likely cause:

- Auth is disabled, Stripe session creation failed, or Stripe webhook activation has not been received.

Recovery:

- Auth-disabled local/dev mode intentionally skips billing setup.
- For checkout, confirm current organization and selected plan.
- For portal, confirm backend returns a portal URL.
- For developer plan activation, check Stripe webhook/listener configuration rather than retrying checkout.

## Admin route and sync actions are hazardous

Symptoms:

- `/admin` redirects home with an admin-required toast.
- Sync search includes slow count options.
- Cancel/delete/resync prompts appear.

Likely cause:

- User is not admin, or admin sync tooling is being used.

Recovery:

- Admin access is based on backend-enriched `user.is_admin`.
- Keep confirmation prompts for destructive sync delete and bulk delete.
- Treat ARF/Vespa count options as slower diagnostics.
- Do not convert admin destructive prompts into silent one-click actions.

## Cron schedule display looks wrong

Symptoms:

- Cron parser returns `null`.
- A six-field cron expression is not accepted.
- Local-time description is the same as UTC.
- Time-until text says `Now`.

Likely cause:

- The utility accepts only five fields.
- Complex hour/minute fields cannot be converted to local time and intentionally fall back to the original description.
- Past next-run values are displayed as `Now`.

Recovery:

- Normalize schedules to five cron fields before using `parseCronExpression()`.
- For fixed UTC hour/minute schedules, expect local display to replace the UTC time.
- Use `npm test -- src/utils/cronParser.test.ts` after changing parser or schedule UI.

## Build, lint, or test failures

Symptoms:

- Vitest cannot find the cron parser test.
- Lint catches React/TypeScript issues.
- Production build fails route chunk compilation.

Recovery:

- Run commands from the frontend package directory.
- Use `npm test -- src/utils/cronParser.test.ts` for the focused native candidate.
- Use `npm run lint` before accepting broad dashboard changes.
- Use `npm run build` for production compile coverage.
- If package dependencies are missing, install frontend dependencies with npm before running checks.
