---
name: frontend-dashboard
description: "Operates Airweave's React dashboard: auth, organization context,
  API client behavior, collections, search UI, billing/admin pages, webhooks,
  auth providers, usage gates, and cron utilities."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Frontend Dashboard

Use this sub-skill when an Airweave task touches the React/Vite dashboard, user-facing app routes, dashboard API calls, auth state, organization switching, search UI, collection pages, billing/admin screens, webhooks, auth providers, usage gating, or cron schedule display utilities.

## Route to the right reference

- Read [references/api-client.md](references/api-client.md) before changing API calls, auth token handling, request headers, SSE/fetch behavior, or organization auto-switching.
- Read [references/search-ui.md](references/search-ui.md) before changing dashboard search tiers, filters, streamed agentic search traces, result rendering, or API-code snippets.
- Read [references/collections-and-orgs.md](references/collections-and-orgs.md) before changing dashboard collection pages, organization state, billing/admin routes, webhooks, auth-provider pages, browse-tree UI, usage checks, or cron parser behavior.
- Read [references/troubleshooting.md](references/troubleshooting.md) when diagnosing auth-disabled dev mode, Auth0 setup, stale organization context, usage/billing gates, search errors, OAuth callback state, admin hazards, or frontend build/test failures.
- Cross-link to sibling [backend-api](../backend-api/SKILL.md) for endpoint schemas, request/response shapes, auth/header semantics, search route contracts, source-connection OAuth behavior, and webhook payload semantics.

## Operating rules

1. Use the shared `apiClient` for dashboard API calls. Endpoint strings should be root-relative, such as `/collections`, not `/api/v1/collections`.
2. Preserve the auth-token provider lifecycle: the app wires `AuthContext` into `apiClient`, queues requests until auth is ready, and retries once after `401` or `403` by clearing the cached token.
3. Preserve organization context. `X-Organization-ID` comes from the current organization store; successful `GET` responses with a different accessible `organization_id` can auto-switch the active organization and clear organization-scoped caches. Mutations must not auto-switch.
4. Treat usage checks as user-facing gates, not backend authorization. Buttons/search tiers can be disabled from cached `/usage` checks, but failed or missing checks default to allowed and the backend remains the source of truth.
5. Keep admin and billing flows explicit. Admin pages require `user.is_admin`; sync delete/cancel/resync actions are destructive. Billing setup/portal routes redirect through backend-created Stripe sessions and should fail closed with toasts/navigation.
6. Keep Connect widget internals, MCP server internals, backend implementation details, and Monke orchestration out of this sub-skill. Route those to their sibling sub-skills.

## Safe validation anchors

- Cron parser unit behavior is the safe native anchor: run from the frontend package with `npm test -- src/utils/cronParser.test.ts`.
- Later integration should add `npm run lint` and `npm run build` for dashboard-wide static/build coverage.
- Do not introduce browser automation as a requirement for this sub-skill unless a later verification pass explicitly adds a frontend harness.
