# Backend API Workflows

## When to read this

Read this for task-level API recipes that combine routes correctly. For exact endpoint schemas, see [api-reference.md](api-reference.md). For failure recovery, see [troubleshooting.md](troubleshooting.md).

The examples use a local API host and placeholder secrets:

```bash
export AIRWEAVE_API_URL="http://localhost:8001"
export AIRWEAVE_API_KEY="aw_..."          # or another bearer token from your auth setup
export AIRWEAVE_ORG_ID="org-uuid-if-needed"

api() {
  local method="$1" path="$2" body="${3:-}"
  if [ -n "$body" ]; then
    curl -sS -X "$method" "$AIRWEAVE_API_URL$path" \
      -H "Authorization: Bearer $AIRWEAVE_API_KEY" \
      -H "X-Organization-ID: $AIRWEAVE_ORG_ID" \
      -H "Content-Type: application/json" \
      --data "$body"
  else
    curl -sS -X "$method" "$AIRWEAVE_API_URL$path" \
      -H "Authorization: Bearer $AIRWEAVE_API_KEY" \
      -H "X-Organization-ID: $AIRWEAVE_ORG_ID"
  fi
}
```

If organization headers are not required in the active auth mode, omit `X-Organization-ID`.

## Workflow: collection to searchable data

Use this when a user wants to create a collection, connect a source, wait for sync, then search.

1. Create a collection and save `readable_id`.

   ```bash
   collection_json=$(api POST /collections/ '{"name":"Support Docs"}')
   readable_id=$(printf '%s' "$collection_json" | python -c 'import json,sys; print(json.load(sys.stdin)["readable_id"])')
   printf 'collection=%s\n' "$readable_id"
   ```

2. Discover source requirements before constructing the source-connection payload.

   ```bash
   api GET /sources/github | python -m json.tool
   ```

   Check `auth_methods`, `auth_fields`, `config_fields`, `supports_continuous`, `federated_search`, `supports_browse_tree`, and `supported_auth_providers`. For source-specific config semantics, route to sibling `source-connectors`.

3. Create a source connection.

   Direct-auth example:

   ```bash
   conn_json=$(api POST /source-connections "$(cat <<JSON
   {
     "name": "GitHub Docs",
     "short_name": "github",
     "readable_collection_id": "$readable_id",
     "config": {"repo_name": "company/docs", "branch": "main"},
     "authentication": {"credentials": {"personal_access_token": "REDACTED"}},
     "sync_immediately": true
   }
   JSON
   )")
   conn_id=$(printf '%s' "$conn_json" | python -c 'import json,sys; print(json.load(sys.stdin)["id"])')
   ```

   For OAuth browser flow, follow the dedicated OAuth workflow below instead of assuming the connection is immediately authenticated.

4. Poll the connection detail until the last sync job completes or fails.

   ```bash
   while true; do
     detail=$(api GET "/source-connections/$conn_id")
     status=$(printf '%s' "$detail" | python -c 'import json, sys; d=json.load(sys.stdin); job=((d.get("sync") or {}).get("last_job") or {}); print(job.get("status") or d.get("status") or "unknown")')
     echo "status=$status"
     case "$status" in completed|failed|cancelled|error|needs_reauth) break;; esac
     sleep 3
   done
   ```

5. Search with the appropriate tier.

   Instant retrieval:

   ```bash
   api POST "/collections/$readable_id/search/instant" '{"query":"deployment guide","retrieval_strategy":"hybrid","limit":10}' | python -m json.tool
   ```

   Classic retrieval:

   ```bash
   api POST "/collections/$readable_id/search/classic" '{"query":"find onboarding docs","limit":10}' | python -m json.tool
   ```

   Agentic non-streaming:

   ```bash
   api POST "/collections/$readable_id/search/agentic" '{"query":"which docs explain release rollback?","limit":5}' | python -m json.tool
   ```

6. Clean up only when the user explicitly wants deletion. Deleting a source connection or collection cascades synced data cleanup.

   ```bash
   api DELETE "/source-connections/$conn_id" | python -m json.tool
   api DELETE "/collections/$readable_id" | python -m json.tool
   ```

## Workflow: choose the correct search tier, cancel, and retry

Use this when a user is toggling between instant, classic, and agentic search or debugging a mismatch between request body and response handling.

1. Preflight usage for the selected tier family.

   ```bash
   api GET '/usage/check-action?action=queries' | python -m json.tool
   api GET '/usage/check-action?action=tokens' | python -m json.tool
   ```

   - Instant/classic/browse/legacy search depend on `queries`.
   - Agentic and agentic stream depend on `tokens`.

2. Build the body for exactly one tier.

   - Instant: include `retrieval_strategy` only here. Values: `hybrid`, `semantic`, `keyword`.
   - Classic: no `retrieval_strategy` field in the public request body; the service plans retrieval.
   - Agentic: include optional `thinking` and optional `limit`; streaming/non-streaming share the same request body.

3. Use the v2 filter dialect for tiered routes.

   ```json
   [
     {
       "conditions": [
         {"field": "airweave_system_metadata.source_name", "operator": "equals", "value": "slack"},
         {"field": "updated_at", "operator": "greater_than", "value": "2025-01-01T00:00:00Z"}
       ]
     }
   ]
   ```

4. For agentic stream, run the bundled helper from this sub-skill directory or implement the same SSE parse loop.

   ```bash
   python scripts/agentic_search_stream.py \
     "$readable_id" "find deployment docs" \
     --host "$AIRWEAVE_API_URL" \
     --api-key "$AIRWEAVE_API_KEY" \
     --organization-id "$AIRWEAVE_ORG_ID" \
     --limit 5
   ```

5. Cancellation is client-side abort. It is normal for the UI/helper to stop reading and for the backend to cancel the background task in best-effort cleanup. Treat a local `cancelled` event as UI state, not a server event.

6. Retry only after classifying the failure.

   - Retry transient agentic/SSE failures that mention provider rate limits, queue saturation, or `503`.
   - Do not blindly retry 422 validation errors; fix body shape, filter dialect, field/operator/value combination, or empty query.
   - Recheck `/usage/check-action` after completion or cancellation because usage counters may have changed.

## Workflow: OAuth source connection with claim-token verification

Use this for standard backend source-connection OAuth flows and for the dashboard contract.

1. Create a source connection with no direct credentials, or with BYOC credentials when required by that source.

   ```bash
   response=$(api POST /source-connections "$(cat <<JSON
   {
     "name": "Slack Workspace",
     "short_name": "slack",
     "readable_collection_id": "$readable_id",
     "redirect_url": "https://app.example.com/connections"
   }
   JSON
   )")
   printf '%s\n' "$response" | python -m json.tool
   ```

2. Extract and persist both the source connection ID and `auth.claim_token` before opening the auth URL.

   ```bash
   conn_id=$(printf '%s' "$response" | python -c 'import json,sys; print(json.load(sys.stdin)["id"])')
   claim_token=$(printf '%s' "$response" | python -c 'import json,sys; print(json.load(sys.stdin)["auth"]["claim_token"])')
   auth_url=$(printf '%s' "$response" | python -c 'import json,sys; print(json.load(sys.stdin)["auth"]["auth_url"])')
   printf 'Open this URL in the browser: %s\n' "$auth_url"
   ```

   Dashboard code stores the token under `sessionStorage` key `oauth_claim_token:{source_connection_id}`. Keep the token until verification succeeds.

3. The public OAuth callback completes provider auth and redirects to the configured `redirect_url` with at least:

   ```text
   status=success&source_connection_id=<uuid>
   ```

   The callback preserves existing query parameters and URL fragments where possible.

4. After redirect, verify ownership using the claim token.

   ```bash
   api POST "/source-connections/$conn_id/verify-oauth" "{\"claim_token\":\"$claim_token\"}" | python -m json.tool
   ```

5. Only after the `verify-oauth` response succeeds, remove `oauth_claim_token:{source_connection_id}` from `sessionStorage`. This triggers the deferred sync for OAuth browser flows.

6. If the user never completed auth or the auth URL/init session expired, reinitiate while the connection is still unauthenticated.

   ```bash
   api POST "/source-connections/$conn_id/reinitiate-oauth" | python -m json.tool
   ```

   Replace the stored claim token with the fresh response value and repeat verification.

## Workflow: Connect session plus source connection

Use this for backend responsibilities in the embeddable Connect flow. Route iframe/postMessage details to `connect-widget`.

1. Your server creates a session using regular Airweave auth.

   ```bash
   session=$(api POST /connect/sessions "$(cat <<JSON
   {
     "readable_collection_id": "$readable_id",
     "allowed_integrations": ["slack", "github"],
     "mode": "all",
     "end_user_id": "customer-user-123"
   }
   JSON
   )")
   session_id=$(printf '%s' "$session" | python -c 'import json,sys; print(json.load(sys.stdin)["session_id"])')
   session_token=$(printf '%s' "$session" | python -c 'import json,sys; print(json.load(sys.stdin)["session_token"])')
   ```

2. Validate the session with the session token.

   ```bash
   curl -sS "$AIRWEAVE_API_URL/connect/sessions/$session_id" \
     -H "Authorization: Bearer $session_token" | python -m json.tool
   ```

   A mismatch between path session ID and signed token session ID returns 403.

3. List sources and connections in session scope.

   ```bash
   curl -sS "$AIRWEAVE_API_URL/connect/sources" \
     -H "Authorization: Bearer $session_token" | python -m json.tool

   curl -sS "$AIRWEAVE_API_URL/connect/source-connections" \
     -H "Authorization: Bearer $session_token" | python -m json.tool
   ```

4. Create a session-scoped source connection. The backend should enforce the session collection even if a client tries to send another `readable_collection_id`.

   ```bash
   curl -sS -X POST "$AIRWEAVE_API_URL/connect/source-connections" \
     -H "Authorization: Bearer $session_token" \
     -H "Content-Type: application/json" \
     --data "$(cat <<JSON
   {
     "name": "GitHub via Connect",
     "short_name": "github",
     "readable_collection_id": "$readable_id",
     "authentication": {"credentials": {"personal_access_token": "REDACTED"}},
     "sync_immediately": true
   }
   JSON
   )" | python -m json.tool
   ```

5. For OAuth within Connect, use the Connect verify/reinitiate endpoints with the same claim-token rule:

   ```bash
   curl -sS -X POST "$AIRWEAVE_API_URL/connect/source-connections/$conn_id/verify-oauth" \
     -H "Authorization: Bearer $session_token" \
     -H "Content-Type: application/json" \
     --data "{\"claim_token\":\"$claim_token\"}" | python -m json.tool
   ```

6. Subscribe to sync progress when a job exists.

   ```bash
   curl -N "$AIRWEAVE_API_URL/connect/source-connections/$conn_id/subscribe" \
     -H "Authorization: Bearer $session_token"
   ```

   Expect `connected`, `heartbeat`, progress frames, and terminal `completed`, `failed`, or `cancelled` statuses.

7. Respect session modes:

   - `connect`: create only; listing/deleting existing connections is forbidden.
   - `manage`: list/delete existing connections; creation is forbidden.
   - `reauth`: reauth-focused operations only.
   - `all`: all supported Connect operations.

## Workflow: browse tree selection before targeted sync

Use this when a source exposes hierarchical selection such as sites, lists, folders, files, or items.

1. Confirm source capability from source discovery.

   ```bash
   api GET /sources/sharepoint_online | python -m json.tool
   ```

   Look for `supports_browse_tree: true`. For source-specific node types and metadata semantics, route to `source-connectors`.

2. Create or fetch a source connection, then load root tree nodes.

   ```bash
   api GET "/source-connections/$conn_id/browse-tree" | python -m json.tool
   ```

3. Lazy-load children by source node ID, not UUID.

   ```bash
   api GET "/source-connections/$conn_id/browse-tree?parent_node_id=$source_node_id" | python -m json.tool
   ```

4. Submit selected source node IDs. The backend stores selection rows and triggers a targeted sync.

   ```bash
   api POST "/source-connections/$conn_id/browse-tree/select" "$(cat <<JSON
   {"source_node_ids": ["site-or-folder-source-id"]}
   JSON
   )" | python -m json.tool
   ```

5. Read current selections or poll the triggered job.

   ```bash
   api GET "/source-connections/$conn_id/browse-tree/selections" | python -m json.tool
   api GET "/source-connections/$conn_id/jobs" | python -m json.tool
   ```

## Workflow: webhook subscription, debugging, and recovery

Use this for receiving Airweave lifecycle events.

1. Create a subscription.

   ```bash
   sub=$(api POST /webhooks/subscriptions "$(cat <<JSON
   {
     "url": "https://api.example.com/webhooks/airweave",
     "event_types": ["sync.completed", "sync.failed", "source_connection.deleted"]
   }
   JSON
   )")
   sub_id=$(printf '%s' "$sub" | python -c 'import json,sys; print(json.load(sys.stdin)["id"])')
   ```

2. Optionally retrieve the secret for signature verification. Treat the value as sensitive.

   ```bash
   api GET "/webhooks/subscriptions/$sub_id?include_secret=true" | python -m json.tool
   ```

3. Inspect event messages and attempts.

   ```bash
   api GET '/webhooks/messages?event_types=sync.completed&event_types=sync.failed' | python -m json.tool
   api GET "/webhooks/subscriptions/$sub_id" | python -m json.tool
   ```

4. Pause and resume delivery with PATCH.

   ```bash
   api PATCH "/webhooks/subscriptions/$sub_id" '{"disabled": true}' | python -m json.tool
   api PATCH "/webhooks/subscriptions/$sub_id" '{"disabled": false}' | python -m json.tool
   ```

5. Recover failed messages after fixing the receiver.

   ```bash
   api POST "/webhooks/subscriptions/$sub_id/recover" '{"since":"2025-01-01T00:00:00Z"}' | python -m json.tool
   ```

6. Delete only when the user wants delivery stopped permanently.

   ```bash
   api DELETE "/webhooks/subscriptions/$sub_id" | python -m json.tool
   ```

## Workflow: source rate-limit configuration

Use this when diagnosing source sync throttling or configuring limits.

1. Check whether the source-rate-limiting feature is enabled for the organization. If not enabled, `GET /source-rate-limits` returns 403 and syncs skip source-level throttling.

   ```bash
   api GET /source-rate-limits | python -m json.tool
   ```

2. Inspect each source row:

   - `rate_limit_level: "org"` means all connections for that source share one org/source quota.
   - `rate_limit_level: "connection"` means each connection/account has an isolated quota.
   - `rate_limit_level: null` means the source does not participate in source-level rate limiting.

3. Set a limit when the user has manage-rate-limit permissions.

   ```bash
   api PUT /source-rate-limits/notion '{"limit":60,"window_seconds":60}' | python -m json.tool
   ```

4. Trigger syncs normally. Source rate limiting is enforced in the source execution path, not by returning 429 from the configuration endpoint.

   ```bash
   api POST "/source-connections/$conn_id/run" | python -m json.tool
   ```

5. Remove the configured limit to revert to no configured throttling for that source.

   ```bash
   api DELETE /source-rate-limits/notion
   ```

## Workflow: API-key-assisted search snippets

Use this for UI/API snippets that need a bearer token.

1. List existing API keys from a user session that can manage API keys. API-key auth itself is blocked from managing API keys.

   ```bash
   api GET /api-keys/ | python -m json.tool
   ```

2. If needed, create a key with a bounded expiration.

   ```bash
   api POST /api-keys/ '{"expiration_days":90}' | python -m json.tool
   ```

3. Use only the returned `decrypted_key` as a bearer token in external examples. Do not store it in skill files, logs, or committed fixtures.

4. Rotate or delete keys deliberately.

   ```bash
   api POST "/api-keys/$key_id/rotate" | python -m json.tool
   api DELETE "/api-keys/?id=$key_id" | python -m json.tool
   ```
