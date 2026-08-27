# Backend API Reference

## When to read this

Read this when choosing an Airweave backend route, request body, response shape, filter dialect, auth mode, or error-handling strategy. Paths below are root-relative to the API host, for example `http://localhost:8001/collections`; do not prefix them with `/api/v1` in dashboard or Connect clients.

## Common request rules

- Regular API calls use the normal Airweave auth context: `Authorization: Bearer <token-or-api-key>` plus `X-Organization-ID` when an organization is selected.
- Dashboard calls also add `X-Airweave-Session-ID` when a PostHog session ID is available.
- Connect-session calls use `Authorization: Bearer <session_token>` after `POST /connect/sessions`; they do not carry an `ApiContext` user.
- Collection routes and search routes use collection `readable_id` values, not UUIDs.
- Source-connection, sync-job, webhook, API-key, and Connect session item routes use UUID-like IDs.
- The router tolerates trailing slashes, but examples should stay consistent with the tables below.

## Search v2: current tiered search surface

Mounted under `/collections/{readable_id}`.

| Route | Body | Response | Usage action | Notes |
| --- | --- | --- | --- | --- |
| `POST /collections/{readable_id}/search/instant` | `InstantSearchRequest` | `SearchV2Response` | `queries` | Direct embedding + Vespa retrieval. Supports `retrieval_strategy`, filters, `limit`, `offset`. |
| `POST /collections/{readable_id}/search/classic` | `ClassicSearchRequest` | `SearchV2Response` | `queries` | LLM builds a search plan, then retrieval executes. Supports filters, `limit`, `offset`. |
| `POST /collections/{readable_id}/search/agentic` | `AgenticSearchRequest` | `SearchV2Response` | `tokens` | Tool-calling agent loop. `limit` is optional and response is truncated to it when present. |
| `POST /collections/{readable_id}/search/agentic/stream` | `AgenticSearchRequest` | `text/event-stream` | `tokens` | Current streaming route. Emits JSON SSE frames until `done` or `error`. |
| `POST /collections/{readable_id}/search/browse` | `BrowseRequest` | `BrowseResponse` | `queries` | Paginated entity listing, not ranked search. Requires collection-browse feature; otherwise returns 404. |

### V2 request shapes

```json
// Instant
{
  "query": "deployment guide",
  "retrieval_strategy": "hybrid",
  "filter": [
    {
      "conditions": [
        {
          "field": "airweave_system_metadata.source_name",
          "operator": "equals",
          "value": "notion"
        }
      ]
    }
  ],
  "limit": 10,
  "offset": 0
}
```

```json
// Classic
{
  "query": "find onboarding documentation",
  "filter": [
    {
      "conditions": [
        {
          "field": "airweave_system_metadata.entity_type",
          "operator": "in",
          "value": ["NotionPageEntity", "SlackMessageEntity"]
        }
      ]
    }
  ],
  "limit": 10,
  "offset": 0
}
```

```json
// Agentic and agentic stream
{
  "query": "which docs explain OAuth callback recovery?",
  "thinking": false,
  "filter": [
    {
      "conditions": [
        {
          "field": "updated_at",
          "operator": "greater_than_or_equal",
          "value": "2025-01-01T00:00:00Z"
        }
      ]
    }
  ],
  "limit": 5
}
```

V2 `query` must be non-empty. Instant `retrieval_strategy` values are `hybrid`, `semantic`, or `keyword`; default is `hybrid`.

### V2 filter dialect

V2 filters are a list of groups. Conditions inside one group are combined with AND; groups are combined with OR.

Allowed fields:

- `entity_id`, `name`, `created_at`, `updated_at`
- `breadcrumbs.entity_id`, `breadcrumbs.name`, `breadcrumbs.entity_type`
- `airweave_system_metadata.entity_type`
- `airweave_system_metadata.source_name`
- `airweave_system_metadata.original_entity_id`
- `airweave_system_metadata.chunk_index`
- `airweave_system_metadata.sync_id`
- `airweave_system_metadata.sync_job_id`

Allowed operators:

- Scalar/text: `equals`, `not_equals`, `contains`
- Ordering: `greater_than`, `less_than`, `greater_than_or_equal`, `less_than_or_equal`
- List: `in`, `not_in`

Validation rules that matter in practice:

- Ordering only works on date fields or `chunk_index`.
- `contains` only works on text fields.
- `in` and `not_in` require a list value; scalar operators reject list values.
- Date values must be ISO 8601 strings such as `2024-01-15T00:00:00Z`.
- `chunk_index` must receive a numeric value.

### V2 response shape

All non-streaming v2 tiers return:

```json
{
  "results": [
    {
      "entity_id": "page-abc123",
      "name": "Production Deployment Guide",
      "relevance_score": 0.94,
      "breadcrumbs": [
        {"entity_id": "ws-1", "name": "Workspace", "entity_type": "WorkspaceEntity"}
      ],
      "created_at": "2025-02-10T09:15:00Z",
      "updated_at": "2025-03-18T16:30:00Z",
      "textual_representation": "# Production Deployment Guide\n...",
      "airweave_system_metadata": {
        "source_name": "notion",
        "entity_type": "NotionPageEntity",
        "sync_id": "...",
        "sync_job_id": "...",
        "chunk_index": 0,
        "original_entity_id": "page-abc123"
      },
      "access": {"viewers": null, "is_public": null},
      "web_url": "https://source.example/item",
      "url": null,
      "raw_source_fields": {}
    }
  ]
}
```

### Agentic stream events

`POST /collections/{readable_id}/search/agentic/stream` returns SSE frames in the form `data: {json}\n\n`.

| Event `type` | Key fields | Meaning |
| --- | --- | --- |
| `started` | `request_id`, `tier`, `collection_readable_id` | Search accepted and request ID is available. |
| `thinking` | `thinking`, `text`, `duration_ms`, `diagnostics` | LLM reasoning/iteration text and token diagnostics. |
| `tool_call` | `tool_name`, `duration_ms`, `diagnostics` | Agent tool execution such as search/read/collect/navigation/count/review. |
| `reranking` | `duration_ms`, `diagnostics` | Reranking stage completed. |
| `done` | `results`, `duration_ms`, optional `diagnostics` | Terminal success; `results` is the v2 result list. |
| `error` | `message`, `duration_ms`, optional `diagnostics` | Terminal failure. Transient provider failures can mention rate limits or 503s. |

The response includes `Cache-Control: no-cache`, `X-Accel-Buffering: no`, and media type `text/event-stream`. Client abort/cancel is normal; the server attempts to cancel the background task and close Pub/Sub.

### Browse response

`POST /collections/{readable_id}/search/browse` accepts:

```json
{
  "filter": [{"conditions": [{"field": "airweave_system_metadata.source_name", "operator": "equals", "value": "sharepoint"}]}],
  "limit": 50,
  "offset": 0,
  "sync_ids": ["sync-uuid"],
  "entity_types": ["SharePointFileEntity"],
  "name_query": "budget"
}
```

It returns `{results, total, limit, offset}`. `limit` is capped at 200. `name_query` requires at least two characters and is translated to a backend regex match. This is collection browsing, not browse-tree node selection.

## Admin search-adjacent routes

Mounted under `/admin/collections/{readable_id}` and require admin context.

| Route | Body/query | Purpose |
| --- | --- | --- |
| `POST /admin/collections/{readable_id}/search/agentic/stream` | `InternalAgenticSearchRequest` with optional `model` | Admin/eval stream with model override such as `provider/model`. |
| `POST /admin/collections/{readable_id}/search/instant/as-user?user_principal=email@example.com` | `InstantSearchRequest` | Search with access-control filtering as a user principal. |
| `POST /admin/collections/{readable_id}/search/classic/as-user?user_principal=email@example.com` | `ClassicSearchRequest` | Classic search as a user principal. |
| `POST /admin/collections/{readable_id}/search/agentic/as-user?user_principal=email@example.com` | `AgenticSearchRequest` | Agentic search as a user principal. |

## Legacy search routes

Legacy routes are also mounted under `/collections/{readable_id}`. Keep them available for compatibility, but prefer v2 tiered routes for new work.

| Route | Shape | Notes |
| --- | --- | --- |
| `GET /collections/{readable_id}/search?query=...&response_type=raw&limit=10&offset=0` | Query parameters | Deprecated. Adds `X-API-Deprecation` headers. `response_type` is `raw` or `completion`. |
| `POST /collections/{readable_id}/search` | `SearchRequest` or `LegacySearchRequest` | Primary legacy-compatible POST. Returns `SearchResponse` or `LegacySearchResponse` depending on body schema. |
| `POST /collections/{readable_id}/search/stream` | `SearchRequest` or `LegacySearchRequest` | SSE stream for advanced legacy search. Emits `connected`, `heartbeat`, search events, `done`, or `error`. |
| `GET /collections/internal/filter-schema` | none | Returns JSON schema for the legacy Qdrant-style filter dict. |

New-style legacy POST body:

```json
{
  "query": "kubernetes config",
  "retrieval_strategy": "hybrid",
  "filter": {"must": [{"key": "source_name", "match": {"value": "GitHub"}}]},
  "offset": 0,
  "limit": 10,
  "expand_query": false,
  "interpret_filters": false,
  "rerank": false,
  "generate_answer": false
}
```

Legacy `SearchRequest.query` has a 2048-token cap. Legacy `retrieval_strategy` values are `hybrid`, `neural`, or `keyword`. `temporal_relevance` is accepted for compatibility but ignored; the response adds `X-Feature-Removed: temporal_relevance` when it is requested.

Legacy response shape:

```json
{"results": [{"entity_id": "...", "source_name": "...", "md_content": "..."}], "completion": null}
```

Legacy request/response details differ from v2: legacy filters are a dict with `must`, `should`, and `must_not`, and result metadata commonly appears under `system_metadata` or flattened fields rather than v2 `airweave_system_metadata`.

## Collections

Mounted under `/collections`.

| Route | Body/query | Response | Notes |
| --- | --- | --- | --- |
| `GET /collections/?skip=0&limit=100&search=term` | query | `Collection[]` | Sorted newest first; `search` matches name/readable ID. |
| `GET /collections/count?search=term` | query | integer | Count with same optional search term. |
| `POST /collections/` | `CollectionCreate` | `Collection` | Creates `readable_id` if omitted. |
| `GET /collections/{readable_id}` | path | `Collection` | 404 when not found. |
| `PATCH /collections/{readable_id}` | `CollectionUpdate` | `Collection` | `readable_id` is immutable. |
| `DELETE /collections/{readable_id}` | path | deleted `Collection` | Deletes collection and cascades source connections/synced data cleanup. |

`CollectionCreate` fields:

```json
{
  "name": "Finance Data",
  "readable_id": "finance-data-reports",
  "sync_config": {
    "handlers": {
      "enable_vector_handlers": true,
      "enable_postgres_handler": true
    }
  }
}
```

`name` length is 4-64. `readable_id` must be lowercase letters, numbers, and hyphens, with no leading/trailing hyphen. `Collection` responses include `id`, `name`, `readable_id`, `status`, `vector_size`, `embedding_model_name`, timestamps, organization/user fields, optional `sync_config`, and `source_connection_summaries`.

## Source connections

Mounted under `/source-connections`.

| Route | Body/query | Response | Notes |
| --- | --- | --- | --- |
| `GET /source-connections/callback` | OAuth query params | 303 redirect | Public OAuth callback. Supports OAuth2 `state`/`code` and OAuth1 `oauth_token`/`oauth_verifier`. |
| `POST /source-connections/{id}/verify-oauth` | `{ "claim_token": "..." }` | `SourceConnection` | Verifies OAuth flow ownership and triggers deferred sync. |
| `POST /source-connections/{id}/reinitiate-oauth` | none | `SourceConnection` | For unauthenticated connections only; returns fresh `auth_url` and `claim_token`. |
| `POST /source-connections` | `SourceConnectionCreate` | `SourceConnection` | Creates direct, OAuth browser, OAuth token, BYOC, or auth-provider connection. |
| `GET /source-connections?collection={readable_id}&skip=0&limit=100` | query | `SourceConnectionListItem[]` | Lightweight list; optional collection filter. |
| `GET /source-connections/{id}` | path | `SourceConnection` | Full auth/config/schedule/sync/entity detail. |
| `PATCH /source-connections/{id}` | `SourceConnectionUpdate` | `SourceConnection` | Update name/description/config/schedule/direct credentials. |
| `DELETE /source-connections/{id}` | path | deleted `SourceConnection` | Cancels running syncs and schedules destination/raw storage cleanup. |
| `POST /source-connections/{id}/run?force_full_sync=false` | query | `SourceConnectionJob` | Starts async sync. `force_full_sync` matters for continuous sources. |
| `GET /source-connections/{id}/jobs?limit=100` | query | `SourceConnectionJob[]` | Newest jobs first. |
| `POST /source-connections/{id}/jobs/{job_id}/cancel` | path | `SourceConnectionJob` | `pending`/`running` → `cancelling` → `cancelled`; invalid terminal jobs return an error. |
| `GET /source-connections/authorize/{code}` | path | 303 redirect | Short-lived proxy redirect to provider authorization URL. |

### SourceConnectionCreate body patterns

Direct credentials:

```json
{
  "name": "GitHub Docs Repo",
  "short_name": "github",
  "readable_collection_id": "documentation-ab123",
  "config": {"repo_name": "company/docs", "branch": "main"},
  "authentication": {"credentials": {"personal_access_token": "..."}},
  "sync_immediately": true
}
```

OAuth browser:

```json
{
  "name": "Slack Workspace",
  "short_name": "slack",
  "readable_collection_id": "team-comms-xy789",
  "redirect_url": "https://app.example.com/connections"
}
```

OAuth token injection:

```json
{
  "name": "Notion Token",
  "short_name": "notion",
  "readable_collection_id": "docs-ab123",
  "authentication": {
    "access_token": "oauth-access-token",
    "refresh_token": "optional-refresh-token",
    "expires_at": "2026-01-01T00:00:00Z"
  }
}
```

Auth provider:

```json
{
  "name": "Gmail via Provider",
  "short_name": "gmail",
  "readable_collection_id": "emails-cd456",
  "authentication": {
    "provider_readable_id": "provider-connection-ab123",
    "provider_config": {"account_id": "acct_123"}
  }
}
```

Important source-connection schema behavior:

- `sync_immediately` defaults to `false` for OAuth browser/BYOC flows and `true` for direct/token/auth-provider flows.
- Direct credentials must not be empty.
- OAuth access tokens must not be blank and must not already be expired.
- OAuth2 BYOC requires both `client_id` and `client_secret` or neither.
- OAuth1 BYOC requires both `consumer_key` and `consumer_secret` or neither.
- OAuth1 and OAuth2 BYOC fields must not be mixed.
- `SourceConnectionUpdate.authentication` only accepts direct credentials and requires at least one updated field overall.

`SourceConnection` responses include `auth.method`, `auth.authenticated`, optional `auth.auth_url`, `auth.claim_token`, `status`, `config`, `schedule`, `sync.last_job`, `entities`, `federated_search`, and credential-error fields such as `error_category`, `error_message`, and provider settings information.

`SourceConnectionJob.status` values include `pending`, `running`, `completed`, `failed`, `cancelling`, and `cancelled` (case comes from the backend enum serialization). Job records include timing, inserted/updated/deleted/failed counts, error text, error category, and error details.

## Connect-session backend endpoints

Mounted under `/connect`. `POST /connect/sessions` is server-to-server with regular API auth. All other Connect endpoints use the returned `session_token` as `Authorization: Bearer <session_token>`.

| Route | Body | Response | Notes |
| --- | --- | --- | --- |
| `POST /connect/sessions` | `ConnectSessionCreate` | `ConnectSessionResponse` | Creates short-lived token for a collection. |
| `GET /connect/sessions/{session_id}` | none | `ConnectSessionContext` | Verifies token and rejects mismatched session ID with 403. |
| `GET /connect/sources` | none | `Source[]` | Filtered by `allowed_integrations` in the session. |
| `GET /connect/sources/{short_name}` | none | `Source` | 403/404 if not allowed or unavailable. |
| `GET /connect/source-connections` | none | `SourceConnectionListItem[]` | Session collection only; mode/allowed integrations enforced. |
| `GET /connect/source-connections/{connection_id}` | none | `SourceConnection` | Connection must belong to session collection and allowed integrations. |
| `DELETE /connect/source-connections/{connection_id}` | none | `SourceConnection` | Allowed in manage/all modes, not connect-only. |
| `POST /connect/source-connections` | `SourceConnectionCreate` | `SourceConnection` | Session collection is authoritative; client cannot override into another collection. |
| `POST /connect/source-connections/{connection_id}/reinitiate-oauth` | none | `SourceConnection` | Reauth flow within session restrictions. |
| `POST /connect/source-connections/{connection_id}/verify-oauth` | `{ "claim_token": "..." }` | `SourceConnection` | Claim-token verification within Connect. |
| `GET /connect/source-connections/{connection_id}/jobs` | none | `SourceConnectionJob[]` | Job history for session-scoped connection. |
| `GET /connect/source-connections/{connection_id}/subscribe` | SSE | `text/event-stream` | Real-time sync progress for the latest job. |

`ConnectSessionCreate`:

```json
{
  "readable_collection_id": "finance-data-ab123",
  "allowed_integrations": ["slack", "github", "notion"],
  "mode": "all",
  "end_user_id": "user_123"
}
```

Connect session modes:

- `all`: connect, manage, and reauth.
- `connect`: add new connections only; listing/managing existing connections is forbidden.
- `manage`: view/delete existing connections; creating new connections is forbidden.
- `reauth`: re-authentication-focused; unrelated create/delete operations are forbidden.

Connect sync SSE starts with `{"type":"connected","job_id":"..."}`, may send `heartbeat`, then progress frames with counters such as `inserted`, `updated`, `deleted`, `kept`, `skipped`, `entities_encountered`, and terminal `status` values (`completed`, `failed`, `cancelled`).

## Browse-tree selection routes

Mounted under `/source-connections/{source_connection_id}` and require regular API auth. These routes are backend API routes; source capability semantics belong in the `source-connectors` sub-skill.

| Route | Body/query | Response | Notes |
| --- | --- | --- | --- |
| `GET /source-connections/{id}/browse-tree/selections` | none | `NodeSelectionData[]` | Current stored selections. |
| `GET /source-connections/{id}/browse-tree?parent_node_id={source_node_id}` | optional query | `BrowseTreeResponse` | Lazy-load source tree root or children. `parent_node_id` is source ID string, not UUID. |
| `POST /source-connections/{id}/browse-tree/select` | `{ "source_node_ids": ["..."] }` | `NodeSelectionResponse` | Stores selections and triggers targeted sync. |

`BrowseTreeResponse` returns `{nodes, parent_node_id, total}`. Each node has `source_node_id`, `node_type`, `title`, optional `description`, optional `item_count`, `has_children`, and optional source-specific `node_metadata`.

## Sources and auth providers

### Source discovery

| Route | Response | Notes |
| --- | --- | --- |
| `GET /sources/` | `Source[]` | Catalog of visible connectors for the organization. Feature-gated sources are hidden. |
| `GET /sources/{short_name}` | `Source` | Full source metadata or 404 when unavailable/feature-gated. |

A `Source` includes `short_name`, `name`, `class_name`, `auth_methods`, `oauth_type`, `requires_byoc`, `auth_fields`, `config_fields`, `supported_auth_providers`, `labels`, `supports_continuous`, `federated_search`, `supports_access_control`, `rate_limit_level`, `feature_flag`, and `supports_browse_tree`.

### Auth provider metadata and connections

| Route | Body/query | Response | Notes |
| --- | --- | --- | --- |
| `GET /auth-providers/list` | none | `AuthProviderMetadata[]` | Available provider types. |
| `GET /auth-providers/detail/{short_name}` | none | `AuthProviderMetadata` | Provider details or 404. |
| `GET /auth-providers/connections/?skip=0&limit=100` | query | `AuthProviderConnection[]` | Organization provider connections. |
| `GET /auth-providers/connections/{readable_id}` | path | `AuthProviderConnection` | Detail by readable ID. |
| `POST /auth-providers/` | `AuthProviderConnectionCreate` | `AuthProviderConnection` | Requires manage-auth-provider role. |
| `PUT /auth-providers/{readable_id}` | `AuthProviderConnectionUpdate` | `AuthProviderConnection` | Replaces provided credentials fields. |
| `DELETE /auth-providers/{readable_id}` | path | `AuthProviderConnection` | Deletes provider connection. |

Provider connections are referenced from source-connection create bodies by `authentication.provider_readable_id`.

## API keys

Mounted under `/api-keys`. Management routes require an organization role that can manage API keys and explicitly block API-key auth for API-key management.

| Route | Body/query | Response | Notes |
| --- | --- | --- | --- |
| `POST /api-keys/` | `{ "expiration_days": 90 }` | `APIKey` | Plain `decrypted_key` is returned for storage. `expiration_days` must be 1-365. |
| `GET /api-keys/` | `skip`, `limit` query | `APIKey[]` | Lists keys with decrypted values for UI/snippets. |
| `GET /api-keys/{id}` | path | `APIKey` | 404 when not found. |
| `POST /api-keys/{id}/rotate` | none | new `APIKey` | Old key remains active until its expiration; new key defaults to 90 days. |
| `DELETE /api-keys/?id={uuid}` | query | deleted `APIKey` | Revokes the key. |

## Webhooks

Mounted under `/webhooks`. Responses use snake_case fields, matching delivered webhook payload style.

| Route | Body/query | Response | Notes |
| --- | --- | --- | --- |
| `GET /webhooks/messages?event_types=sync.completed&event_types=sync.failed` | query | `WebhookMessage[]` | Filter by repeated `event_types` query parameters. |
| `GET /webhooks/messages/{message_id}?include_attempts=true` | query | `WebhookMessageWithAttempts` | Includes attempts only when requested. |
| `GET /webhooks/subscriptions` | none | `WebhookSubscription[]` | Includes `health_status` and `disabled`. |
| `GET /webhooks/subscriptions/{subscription_id}?include_secret=true` | query | `WebhookSubscriptionDetail` | Optionally returns signing secret; treat as sensitive. |
| `POST /webhooks/subscriptions` | `CreateSubscriptionRequest` | `WebhookSubscription` | Creates endpoint subscription. |
| `PATCH /webhooks/subscriptions/{subscription_id}` | `PatchSubscriptionRequest` | `WebhookSubscription` | Update URL/types/disabled; optional recovery on enable. |
| `DELETE /webhooks/subscriptions/{subscription_id}` | path | `WebhookSubscription` | Permanently stops deliveries. |
| `POST /webhooks/subscriptions/{subscription_id}/recover` | `RecoverMessagesRequest` | `RecoveryTask` | Retries failed/pending messages for a time window. |

Create subscription body:

```json
{
  "url": "https://api.example.com/webhooks/airweave",
  "event_types": ["sync.completed", "sync.failed"],
  "secret": "whsec_optional_custom_secret_24_chars_min"
}
```

Event types include sync lifecycle (`sync.pending`, `sync.running`, `sync.completed`, `sync.failed`, `sync.cancelled`), source-connection lifecycle (`source_connection.created`, `source_connection.auth_completed`, `source_connection.deleted`), and collection lifecycle (`collection.created`, `collection.updated`, `collection.deleted`). Custom secrets must be at least 24 characters. Delivery attempts expose response body/status and derived `success`, `pending`, or `failed` status.

## Usage checks

Mounted under `/usage`.

| Route | Body/query | Response | Notes |
| --- | --- | --- | --- |
| `GET /usage/check-action?action=queries&amount=1` | query | `SingleActionCheckResponse` | Single preflight for `entities`, `queries`, `tokens`, `source_connections`, or `team_members`. |
| `POST /usage/check-actions` | `{ "actions": {"queries": 1, "tokens": 1} }` | `ActionCheckResponse` | Batch preflight keyed by action. |
| `GET /usage/dashboard?period_id={uuid}` | optional query | `UsageDashboard` | Current/previous billing-period usage and plan limits. |

`SingleActionCheckResponse`:

```json
{
  "allowed": true,
  "action": "queries",
  "reason": null,
  "details": null
}
```

When blocked, `reason` is `payment_required` or `usage_limit_exceeded`; `details` can include payment status, current usage, and limit.

## Source rate limits

Mounted under `/source-rate-limits`. These endpoints require the source-rate-limiting feature flag; mutating routes require a role that can manage rate limits.

| Route | Body | Response | Notes |
| --- | --- | --- | --- |
| `GET /source-rate-limits` | none | `SourceRateLimitResponse[]` | All sources merged with any configured org limit; sorted supported first. |
| `PUT /source-rate-limits/{source_short_name}` | `{ "limit": 60, "window_seconds": 60 }` | `SourceRateLimit` | Create or update one org/source limit. |
| `DELETE /source-rate-limits/{source_short_name}` | none | 204 | Removes configured limit; source proceeds unthrottled if no other limit applies. |

`SourceRateLimitResponse` includes `source_short_name`, `rate_limit_level` (`org`, `connection`, or `null`), optional `limit`, optional `window_seconds`, and optional DB record `id`. Runtime enforcement depends on the source registry's `rate_limit_level`: `org` shares quota across the organization/source, while `connection` isolates quota per source connection/account.
