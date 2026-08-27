# Backend API Troubleshooting

## When to read this

Read this when backend API calls fail, search tiers behave differently than expected, streaming search stalls, OAuth remains pending, Connect session calls return 401/403, webhook delivery cannot be debugged, or source-level rate limiting surprises a sync.

## Fast triage checklist

1. Confirm the exact route path. Most frontend/API-client paths are root-relative; do not add `/api/v1`.
2. Confirm identifier type: collection `readable_id` for collection/search routes; UUIDs for source connections, jobs, sessions, webhooks, and API keys.
3. Confirm auth mode: regular API token/user auth for main API routes; Connect `session_token` for `/connect/*` routes after session creation.
4. Confirm organization context: include `X-Organization-ID` when the auth context can access multiple organizations.
5. Confirm request dialect: v2 search filter list versus legacy search filter dict.
6. Check usage preflight only as a clue; backend usage checks remain authoritative.

## Route and status-code problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `404` on agentic stream | Obsolete agentic-stream path, missing `/collections/{readable_id}`, or collection readable ID typo. | Use `POST /collections/{readable_id}/search/agentic/stream`. Verify the collection with `GET /collections/{readable_id}`. |
| `404` on browse collection | Collection-browse feature flag not enabled, or wrong collection ID. | Treat 404 as intentional hiding when feature-gated. Use normal search tiers unless the org has the feature. |
| `404` on `/sources/{short_name}` | Source does not exist or is hidden by feature flag. | List visible sources with `GET /sources/`. Route source registry questions to `source-connectors`. |
| `403` on source rate-limit routes | `SOURCE_RATE_LIMITING` feature disabled or caller lacks manage-rate-limit role for mutations. | Enable the feature through admin flow if appropriate; use a user with the required role. |
| `403` on API-key management while using an API key | API-key management explicitly blocks API-key auth. | Use a user/session token with the manage-API-keys role. |
| `401`/`403` after token refresh in dashboard | Stale auth token or organization membership changed. | Clear cached token, refresh organization context, and retry once. Do not auto-switch organizations on mutations. |
| `429` from general API calls | Organization/API rate limiting. | Check response headers, respect `Retry-After`, and avoid concurrent bursts. |

## Search and filter failures

### Empty or too-long query

Symptoms:

- `422` with messages like `Query cannot be empty`.
- Legacy search may reject queries over the token cap.

Recovery:

- Trim and validate query before calling the API.
- Keep legacy `SearchRequest.query` under 2048 tokens.
- Do not send a search request for empty dashboard input.

### V2 filter validation errors

Symptoms:

- `422` from instant/classic/agentic with details mentioning field, operator, date, list, or scalar values.

Common causes and fixes:

| Cause | Example bad body | Fix |
| --- | --- | --- |
| Sent legacy dict to v2 route | `{ "filter": {"must": [...] } }` | Use `filter: [{"conditions": [...]}]`. |
| Invalid field | `field: "source_name"` | Use `airweave_system_metadata.source_name` for v2 source filtering. |
| Ordering on text | `source_name greater_than "slack"` | Use `equals`, `not_equals`, `contains`, `in`, or `not_in`. |
| `in` with scalar | `operator: "in", value: "slack"` | Use `value: ["slack"]`. |
| Scalar operator with list | `operator: "equals", value: ["slack"]` | Use `in`, or send one scalar value. |
| Bad timestamp | `created_at greater_than "yesterday"` | Use ISO 8601: `2025-01-01T00:00:00Z`. |
| Bad chunk value | `chunk_index equals "first"` | Use a number or numeric string. |

### Legacy filter errors

Symptoms:

- Legacy search accepts the route but returns 422/empty results or filtering seems ignored.

Recovery:

- Use the legacy dict shape: `{"must": [{"key": "source_name", "match": {"value": "stub"}}]}`.
- Validate the expected schema with `GET /collections/internal/filter-schema`.
- Do not send v2 `conditions` groups to `POST /collections/{readable_id}/search`.

### Search tier mismatch

Symptoms:

- Instant body rejected when copied from legacy snippets.
- Classic does not honor `retrieval_strategy` supplied by the UI/user.
- Agentic non-stream response is handled like SSE, or stream response is parsed as JSON.

Recovery:

- Instant: `POST /search/instant`, body includes `query`, optional `retrieval_strategy`, optional v2 `filter`, `limit`, `offset`.
- Classic: `POST /search/classic`, body includes `query`, optional v2 `filter`, `limit`, `offset`.
- Agentic JSON: `POST /search/agentic`, body includes `query`, `thinking`, optional v2 `filter`, optional `limit`; parse JSON.
- Agentic stream: `POST /search/agentic/stream`, same body; parse `data:` SSE frames.
- Recheck `/usage/check-action?action=queries` for instant/classic and `/usage/check-action?action=tokens` for agentic.

## Agentic SSE stream issues

### No events or stream stalls

Likely causes:

- Wrong route path.
- Proxy buffering SSE despite `X-Accel-Buffering: no`.
- Client code waits for JSON instead of reading streamed `data:` frames.
- Backend Pub/Sub or background search task failed before terminal event.
- LLM provider latency or transient queue/rate issue.

Recovery:

1. Try the bundled helper from this sub-skill directory:

   ```bash
   python scripts/agentic_search_stream.py COLLECTION_READABLE_ID "your query" --host http://localhost:8001
   ```

2. Confirm the first terminal event is either `done` or `error`.
3. Treat `503`, `rate`, `too_many_requests`, or `queue_exceeded` in the event `message` as likely transient provider issues; retry with backoff.
4. Treat a local client abort/cancel as normal cleanup, not a server-side failure.
5. If the stream returns HTTP 422, fix validation first; do not retry unchanged.

### Unknown event types in a client

The current v2 stream event set is `started`, `thinking`, `tool_call`, `reranking`, `done`, and `error`. Clients should tolerate unknown events by logging or ignoring them, because event diagnostics can evolve without changing the route.

## Usage and billing gates

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Search button disabled in dashboard | `/usage/check-action` says current tier family is blocked. | Inspect `reason` and `details`; switch tier only when the other action family is allowed. |
| Backend returns usage-limit error despite UI allowing action | UI preflight failed open or became stale. | Backend is authoritative. Show backend error and re-run usage check. |
| Agentic blocked but instant/classic allowed | `tokens` exhausted while `queries` remains available. | Switch to instant/classic or upgrade/resolve usage. |
| Instant/classic blocked but agentic allowed | `queries` exhausted while `tokens` remains available. | Switch to agentic only if the user accepts token-cost behavior. |
| Source creation fails with usage error | `source_connections` limit reached. | Delete unused connections or upgrade plan. |
| Sync run/create fails with usage error | `entities` limit or billing status blocks entity processing. | Check `/usage/check-action?action=entities`; resolve billing/usage before retrying. |

## OAuth source-connection pending states

### Connection remains `pending_auth`

Likely causes:

- The client opened `auth_url` but never called `verify-oauth`.
- The client removed the claim token before successful verification.
- The OAuth callback did not return to the expected redirect URL.
- The init/auth URL expired.

Recovery:

1. Read the source connection detail and confirm `auth.authenticated` is false and `auth.claim_token` was originally stored by the client, usually as `sessionStorage` key `oauth_claim_token:{source_connection_id}`.
2. If the claim token is still available, call:

   ```bash
   POST /source-connections/{id}/verify-oauth
   {"claim_token":"..."}
   ```

3. Remove the stored claim token only after that call succeeds.
4. If the token/auth URL is missing or expired, call `POST /source-connections/{id}/reinitiate-oauth`, store the fresh `claim_token`, open the fresh `auth_url`, and verify again.

### BYOC validation errors

Likely causes:

- OAuth2 BYOC provided only one of `client_id`/`client_secret`.
- OAuth1 BYOC provided only one of `consumer_key`/`consumer_secret`.
- OAuth1 and OAuth2 credential fields were mixed.
- A source requires BYOC/platform credentials that are not configured.

Recovery:

- Send complete pairs only.
- Use either OAuth1 or OAuth2 fields, not both.
- Check `/sources/{short_name}` for `requires_byoc`, `oauth_type`, and auth/config fields.

### Token-injection validation errors

Likely causes:

- Empty, whitespace-only, expired, or unsupported OAuth token payload.
- Source does not support direct token injection.

Recovery:

- Provide non-blank `access_token` and valid optional `refresh_token`/`expires_at`.
- Check source metadata before attempting token injection.

## Connect-session failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `401` on `/connect/*` | Missing bearer session token, invalid auth format, malformed/tampered/expired token. | Pass `Authorization: Bearer <session_token>`. If expired, create a new session. |
| `403` on `GET /connect/sessions/{id}` | Path `session_id` does not match signed token session ID. | Extract/use the session ID returned by `POST /connect/sessions`. |
| `403` listing connections in `connect` mode | Mode allows creation but not managing existing connections. | Create a new session with `all` or `manage` if listing is required. |
| `403` creating in `manage` or `reauth` mode | Mode forbids creation. | Use `all` or `connect` mode. |
| Source hidden from Connect source list | `allowed_integrations` excludes it or source is feature-gated. | Adjust session `allowed_integrations` or source/org feature flags. |
| Connection create tries to override collection | Client sends a different `readable_collection_id`. | Backend should enforce session collection; fix client to display/use the session collection. |
| Sync progress subscribe returns 404 | Connection has no `sync_id` or no jobs yet. | Trigger/create sync first, then subscribe to latest job. |

For iframe token request/response, parent-origin validation, theme updates, close messages, and OAuth popup UX, route to `connect-widget`.

## Source connections, sync runs, and deletion

### Cannot run a sync

Possible causes:

- A sync is already `running` or `cancelling`.
- Connection is not authenticated or needs reauth.
- `entities` usage/billing check failed.
- Source-level rate limiting makes progress appear slow.

Recovery:

1. Read detail: `GET /source-connections/{id}`.
2. Read jobs: `GET /source-connections/{id}/jobs`.
3. If latest job is running, wait or cancel it.
4. If status needs auth, repair auth first.
5. If continuous sync needs a full reset, use `POST /source-connections/{id}/run?force_full_sync=true`.

### Cannot cancel a job

Possible causes:

- Job is already `completed`, `failed`, or `cancelled`.
- Job ID does not belong to the connection.
- Nothing is currently pending/running.

Recovery:

- Only cancel pending/running jobs.
- Expect immediate response status to move toward `cancelling`; worker cleanup can finish later.
- Multiple cancel requests may race; tolerate one success and later conflict/bad-request responses.

### Delete during active sync

Deleting a source connection cancels active work, removes database rows and sync metadata, then schedules vector/raw-storage cleanup. Deleting a collection cascades through connections and data cleanup. Always confirm the user wants destructive cleanup before running deletes.

## Webhook issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Create subscription rejects URL | Invalid URL or URL violates backend/Svix validation. | Use an HTTPS public endpoint for production. Localhost can be useful in dev only when accepted by the current config. |
| Create subscription rejects event types | Empty list, duplicate/invalid values, or too many event types for provider limits. | Use valid event names; keep subscription event count within accepted limits. |
| Custom secret rejected | Secret shorter than 24 chars. | Omit secret for generated secret or provide a longer one. |
| No delivered events | Subscription disabled, event type filter does not match emitted event, receiver failed health/delivery, or source action did not emit that event. | Check `GET /webhooks/subscriptions`, `GET /webhooks/messages`, and message attempts. |
| Signature verification fails | Used wrong header names/secret decoding or changed body before verification. | Verify against Svix-style `webhook-id`/`svix-id`, timestamp, signature headers and raw body bytes. Strip `whsec_` before base64-decoding when implementing manual verification. |
| Need replay after outage | Receiver was down or subscription disabled. | Fix receiver, then `POST /webhooks/subscriptions/{id}/recover` with `since` and optional `until`. |

Event messages can be filtered by repeated query parameters, e.g. `?event_types=sync.completed&event_types=collection.deleted`.

## Source rate-limit surprises

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `GET /source-rate-limits` returns 403 | Feature flag disabled. | Enable source-rate-limiting feature for the organization before configuring limits. |
| Limit configured but no throttling observed | Feature disabled during sync, source has `rate_limit_level: null`, or no source API calls hit the limiter. | Check source row in `GET /source-rate-limits`; route source execution details to `source-connectors`. |
| Two accounts appear to share a quota | Source `rate_limit_level` is `org`. | This is expected org-level aggregation. |
| Two accounts do not affect each other | Source `rate_limit_level` is `connection`. | This is expected per-connection isolation. |
| Sync times out under strict limits | Very low limit/window intentionally slows source calls. | Increase limit/window or accept longer sync duration. |
| No limit row exists | Limit was deleted or never configured. | With feature enabled but no configured limit, sync proceeds without source-level throttling. |

## Backend settings/import readiness

The prepared backend inspection environment verified the backend package import and selected schemas on Python 3.13. Runtime settings load eagerly, so live backend imports or scripts that initialize settings require the documented environment variables. In particular, `STATE_SECRET` and `SVIX_JWT_SECRET` must satisfy the backend validators' minimum length requirements. Use placeholder/local-development secrets only in private dev environments, never in public skill files or committed examples.
