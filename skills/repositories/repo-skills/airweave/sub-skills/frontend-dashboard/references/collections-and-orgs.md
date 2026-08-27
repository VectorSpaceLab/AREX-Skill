# Collections, Organizations, and Dashboard Routes

## When to read this

Read this before changing collection pages, organization context, dashboard route behavior, billing/admin/webhook/auth-provider pages, browse-tree UI, usage gating, or the cron schedule display utility.

Pair endpoint details with sibling [backend-api](../../backend-api/SKILL.md) when request/response shape matters.

## App and protected-route flow

The app wraps protected routes with `AuthGuard` and `DashboardLayout`.

Protected routes include:

- `/` dashboard
- `/collections` collection list
- `/collections/:readable_id` collection detail
- `/collections/:readable_id/browse-tree` browse-tree selection demo
- `/auth-providers`
- `/webhooks`
- `/organization/settings`
- `/billing/setup`
- `/billing/portal`
- `/admin`

Public routes include login/callback/onboarding and billing success/cancel pages.

`DashboardLayout` renders the persistent sidebar, collection creation modal, side panel flow, user profile dropdown, theme switcher, and the global usage checker.

## Organization store behavior

The organization store tracks:

- `organizations`
- `currentOrganization`
- loading state
- billing info/loading state
- deduplication state for organization and billing requests

Selection rules:

1. Keep the persisted current organization if it still exists.
2. Otherwise prefer the primary organization.
3. Otherwise choose the first organization.

Only `currentOrganization` is persisted. Switching organizations clears billing info and clears usage cache; API-client auto-switching also clears other organization-specific stores.

Key actions and endpoints:

- Initialize/fetch organizations: `GET /users/me/organizations`
- Create organization: `POST /organizations`
- Set primary: `POST /organizations/{orgId}/set-primary`
- Invite user: `POST /organizations/{orgId}/invite`
- Remove member: `DELETE /organizations/{orgId}/members/{userId}`
- Leave organization: `POST /organizations/{orgId}/leave`
- Billing info: `GET /billing/subscription`

Feature flags are read from `currentOrganization.enabled_features`; `hasFeature(flag)` is the dashboard helper. Browse-tree collection UI is gated by the collection-browse feature flag.

Role helpers from the organization context treat `owner` and `admin` as managers; only `owner` can delete an organization.

## Usage store and app-level checks

`UsageChecker` runs once in the dashboard layout and whenever `currentOrganization.id` changes. It checks common actions:

```ts
{
  source_connections: 1,
  entities: 1,
  queries: 1,
  team_members: 1,
}
```

The usage store uses:

- `POST /usage/check-actions` for bulk checks.
- `GET /usage/check-action?action=...` in the search box for query/token checks.

Caching and safety:

- Results cache briefly and in-flight checks are deduplicated.
- Missing unchecked actions default to allowed in the UI.
- Organization switches clear the cache.
- Reasons include `usage_limit_exceeded` and `payment_required`; UI tooltips route users toward billing/settings.

Use usage checks to disable buttons and explain limits, but do not treat them as authorization.

## Collections store and event bus

The collections store owns collection list state, total count, loading/error state, and request deduplication.

Key endpoints:

- List cached collections: `GET /collections`
- Count collections: `GET /collections/count`, optionally with `search`
- Paginated/search list: `GET /collections?skip=...&limit=...&search=...`

Event bus names:

- `collection:created`
- `collection:updated`
- `collection:deleted`
- `source_connection:updated`

`subscribeToEvents()` refreshes collections after create/update/delete events. `clearCollections()` is used when organization context changes.

## Dashboard page

The dashboard page loads collections, collection count, and sources. It shows:

- Up to three top collections.
- A create-collection source picker.
- API key card.
- learning/explore cards.

Create-collection entry points use the collection creation store. Source buttons infer auth mode from source metadata:

- Auth types starting with `oauth2` use OAuth mode.
- `api_key` and `basic` use direct-auth mode.

Source and entity usage gates disable source selection when the current plan cannot create more source connections or process more entities.

Connection-error redirects store details under a localStorage key and use a short URL signal (`connected=error`) rather than putting sensitive detail in the URL.

## Collections list page

The collections list page provides full collection browsing with:

- 24 items per page.
- Debounced search input (300 ms).
- Separate total and filtered counts.
- Create Collection button gated by `source_connections` and `entities` usage checks.
- Pagination controls and loading overlays.

When editing this page, keep count refresh and list refresh in sync after collection events.

## Collection detail page

The collection detail page is keyed by collection `readable_id`.

Data flow:

1. `GET /collections/{readable_id}` loads collection metadata.
2. `GET /source-connections/?collection={readable_id}` loads source connections.
3. For each source connection, `GET /source-connections/{connection.id}` loads detail, including sync job status.
4. The first connection is selected by default unless the URL names a newly added source connection.
5. `GET /sources/{short_name}` determines browse-tree support for the selected connection.

Main behaviors:

- Edit collection name with `PATCH /collections/{readable_id}`.
- Delete collection with exact readable-ID confirmation and `DELETE /collections/{readable_id}`.
- Copy collection readable ID to clipboard.
- Add sources through the collection creation flow.
- Show search when a collection has a readable ID; disable search when no sources are connected.
- Show browse tab only when the organization has the browse feature flag.
- Show a re-select-nodes button when the selected source supports browse tree.

OAuth callback contract:

- OAuth return is detected from `status=success` and `source_connection_id` query params.
- The claim token is loaded from `sessionStorage` key `oauth_claim_token:{source_connection_id}`.
- The dashboard calls `POST /source-connections/{id}/verify-oauth` with `{ claim_token }`.
- Remove the sessionStorage token only after `verify-oauth` succeeds.
- If verification succeeds, clean the OAuth query params; if it fails, leave recovery evidence in logs/state rather than pretending the source is ready.

Connection status display distinguishes federated sources from synced sources. Federated active sources are ready for real-time search; regular sources use statuses such as `pending_auth`, `syncing`, `error`, `active`, and `inactive`.

## Browse-tree UI

The browse-tree page is a three-step wizard:

1. Browse and select source nodes.
2. Save selected nodes and trigger sync.
3. Search the synced subset, optionally as a specific user.

Key endpoints:

- Load connections for the collection: `GET /source-connections/?collection={readable_id}`
- Load tree nodes: `GET /source-connections/{sourceConnectionId}/browse-tree`, optionally with `parent_node_id`
- Load existing selections: `GET /source-connections/{sourceConnectionId}/browse-tree/selections`
- Save selections and trigger sync: `POST /source-connections/{sourceConnectionId}/browse-tree/select`
- Poll jobs: `GET /source-connections/{sourceConnectionId}/jobs`
- Search selected data normally: `POST /collections/{readable_id}/search`
- Search as user for ACL checks: `POST /admin/collections/{readable_id}/search/as-user?user_principal=...&destination=vespa`

The tree lazy-loads children, prefetches a shallow depth after auto-loading, treats descendants as implicitly selected when an ancestor is selected, and paginates visible children in batches of ten.

## Webhooks page

The webhooks page is a beta dashboard route with subscriptions and logs tabs.

Manage permission is derived from organization role (`owner` or `admin`). Non-managers can view but should not be able to create/edit.

Query/mutation hooks use TanStack Query with these routes:

- `GET /webhooks/subscriptions`
- `GET /webhooks/subscriptions/{id}` with optional `include_secret=true`
- `POST /webhooks/subscriptions`
- `PATCH /webhooks/subscriptions/{id}`
- `DELETE /webhooks/subscriptions/{id}`
- `POST /webhooks/subscriptions/{id}/recover`
- `GET /webhooks/messages`
- `GET /webhooks/messages/{id}` with optional `include_attempts=true`

When a secret is included, the hook disables normal caching freshness for that query.

## Auth providers page

The auth providers page lists provider types and configured provider connections.

Store endpoints:

- `GET /auth-providers/list`
- `GET /auth-providers/connections/`

The table fetches providers and connections in parallel. Clicking a provider:

- Opens the create flow only for managers when no connection exists.
- Opens a connection list/details flow when connections exist.
- Shows a toast instead of opening configuration for non-managers with no connection.

The page includes a coming-soon Klavis card in addition to real provider records.

## Billing routes

Billing data comes from the organization store via `GET /billing/subscription`.

`checkBillingStatus()` treats OSS billing as no action required, then checks payment-method requirements, grace periods, past-due subscriptions, and canceled subscriptions.

`/billing/setup`:

- Redirects home immediately when auth is disabled.
- Checks billing status on load.
- Navigates to success when an active subscription is observed.
- Polls briefly for Stripe webhook activation.
- Creates checkout with `POST /billing/checkout-session` and redirects to the returned checkout URL.
- Shows a dedicated error when a developer plan is awaiting Stripe listener/webhook activation.

`/billing/portal`:

- Calls `POST /billing/portal-session` with a return URL to organization settings.
- Redirects to the returned portal URL.
- On failure, shows a toast and navigates back to organization settings.

## Admin route

The admin dashboard renders only when `user.is_admin` is true. Non-admin users get an error toast and are sent to the dashboard.

Admin organizations tab:

- Lists organizations with `GET /admin/organizations` and query params for limit, search, sort field, and sort order.
- Loads available flags with `GET /admin/feature-flags`.
- Allows self-join via `POST /admin/organizations/{id}/add-self?role=...`.
- Upgrades orgs via `POST /admin/organizations/{id}/upgrade-to-enterprise`.
- Creates enterprise orgs via `POST /admin/organizations/create-enterprise`.
- Toggles feature flags with `POST /admin/organizations/{id}/feature-flags/{flag}/{enable|disable}`.

Admin syncs tab is operationally dangerous. It can search all syncs, resync selected syncs, cancel jobs, delete syncs, include slow ARF/Vespa counts, and filter by tags. Preserve explicit confirmation prompts and do not hide destructive consequences.

## Cron parser utility

The cron parser accepts only five-part cron expressions: minute, hour, day, month, weekday.

`parseCronExpression(expression)` returns `null` for empty, malformed, or unparsable expressions. Otherwise it returns:

- `description`
- `shortDescription`
- `descriptionLocal`
- `shortDescriptionLocal`

The local description converts fixed numeric UTC hour/minute fields to local time. Frequency-only schedules such as every N minutes/hours keep the same description. Complex or non-numeric hour/minute expressions fall back to the UTC description.

`formatTimeUntil(nextRun)` returns:

- `''` for null/undefined.
- `Now` for past dates.
- `in <1m`, `in Nm`, `in Nh`, `in Nh Nm`, or `in Nd` for future dates.

Use `npm test -- src/utils/cronParser.test.ts` from the frontend package as the safe native check for this utility.
