# Source Connector Troubleshooting

## When to read this

Read this when connector behavior fails after a source class, registry entry, auth/config schema, browse tree, ACL path, federated search path, incremental cursor path, HTTP helper, concurrency helper, or source rate limit changes.

## Fast triage map

| Symptom | First checks | Likely owner |
| --- | --- | --- |
| Source missing from `/sources/` | `ALL_SOURCES`, decorator `short_name`, internal flag, feature flag, registry startup logs. | Source registry / decorator. |
| Source visible but fields wrong | `auth_config_class`, `config_class`, field metadata, `Fields.from_config_class()`, service feature filtering. | Auth/config schema. |
| Direct auth create fails | `validate_auth_schema()`, config validation, source `validate()`, external credential scope. | Connector `validate()` and auth schema. |
| OAuth shell stuck pending | OAuth create response, `claim_token` handling, verify-OAuth endpoint flow. | Backend API/OAuth flow; cross-link to `backend-api`. |
| Browse tree loads root but selection sync skips | Node ID parser metadata vs targeted sync expectations. | Connector browse-tree parser. |
| ACL search over-grants | Anonymous vs organization/user sharing links, group principals, membership expansion. | ACL extraction and broker inputs. |
| Federated source returns no results | Source has `federated_search=True`, connection authenticated, `search()` implemented, external API scopes. | Federated connector/search integration. |
| Incremental sync behaves like full sync | `supports_continuous`, cursor class, cursor update keys, force-full-sync flag, fallback logic. | Connector cursor logic. |
| Rate limit not enforced | Source `rate_limit_level`, feature flag, DB limit, Redis keys, injected `AirweaveHttpClient`. | Source rate limiting. |
| 403 treated as auth error | `raise_for_status()` mapping. | HTTP helper usage. |
| Large sync creates too many tasks | `process_entities_concurrent()` batch size and worker generator contract. | Connector batching. |

## Source script inventory decision

No helper script is bundled with this sub-skill. The connector-relevant source-maintained artifact is the SharePoint browse-tree manual test, but it requires real Microsoft tenant credentials, live source connections, and external SharePoint/AD state, so it is reference-only. Monke discovery/runs are external consumers of source behavior and are owned by the Monke E2E sub-skill, not this connector implementation sub-skill. Local stack, MCP, backend API, billing, and Temporal maintenance scripts are either owned by sibling sub-skills or are credentialed/production-mutating; do not copy them here as connector helpers.

## Registry and visibility failures

If a source is absent or returns 404 from source discovery:

1. Verify the source class is imported into the source package and included in `ALL_SOURCES`.
2. Verify `@source(short_name=...)` matches the API short name and entity definition module expectations.
3. Check `internal=True`: internal sources are filtered unless internal sources are enabled.
4. Check `feature_flag`: `SourceService` hides feature-flagged sources unless the organization has the matching `FeatureFlag` enum value. The SharePoint 2019 V2 flag is `sharepoint_2019_v2`.
5. Inspect registry startup failures. Template config mismatches raise at registry build; signature mismatches currently warn.
6. In self-hosted environments, OAuth-capable sources can be surfaced as BYOC-required; this is source metadata behavior, not a connector failure.

Native anchors:

```bash
cd backend
python -m pytest tests/unit/api/test_source_feature_flags.py -q
python -m pytest tests/e2e/smoke/test_sources.py -q
```

## Auth and config failures

For source connection create/update errors:

1. Identify inferred auth method from payload shape:
   - `credentials` object -> direct.
   - `access_token` -> OAuth token injection.
   - empty/omitted auth -> OAuth browser.
   - client/consumer pair -> BYOC.
   - `provider_readable_id` -> auth provider.
2. Confirm source supports the inferred method. Compatibility failures are expected for token injection on direct-only sources.
3. For direct auth, confirm `auth_config_class` exists and the model validates. Pure OAuth sources should not accept direct credentials unless they deliberately define direct auth.
4. For config errors, run through the source config model and check field-level feature flags. Disabled feature-gated fields return 403.
5. For OAuth template sources, validate all `required_for_auth` fields before initiating browser auth.
6. For auth providers, confirm the provider connection exists, the provider is supported by the source registry entry, and provider config validates.
7. For source validation, inspect the connector's `validate()` method and external API scope. It should use the same HTTP helper path as sync/search.

Native anchors:

```bash
cd backend
python -m pytest tests/e2e/smoke/test_source_connections_direct_auth.py -q
python -m pytest tests/e2e/smoke/test_source_connections_oauth.py -q
python -m pytest tests/e2e/smoke/test_source_connections_token_injection.py -q
python -m pytest tests/e2e/smoke/test_source_connections_auth_provider.py -q
```

These tests are credentialed. Missing API keys, OAuth apps, Composio accounts, or provider credentials should be treated as environment blockers.

## Browse-tree and targeted-sync failures

For browse-tree bugs:

1. Confirm source discovery says `supports_browse_tree=true`.
2. Confirm browse tree source lifecycle can instantiate and validate the source connection.
3. Reproduce with the exact parent ID and check the emitted node list.
4. For selection bugs, inspect persisted selections. `node_metadata` must contain the fields targeted sync consumes.
5. Compare each emitted `source_node_id` prefix with `parse_browse_node_id()` branches. For SharePoint Online, file IDs use `file:{drive_id}|{item_id}` and targeted sync expects `drive_id` and `item_id` metadata.
6. Confirm selection dispatch created a sync job; selection persistence and sync execution fail in different layers.
7. Check auth method differences: delegated SharePoint browse uses signed-in user Graph permissions; app-only browse uses application Graph permissions.

Manual SharePoint browse-tree testing is reference-only because it needs real Microsoft tenant state and credentials; do not copy it into this skill as a runnable script.

## Access-control failures

For SharePoint Online ACL bugs, separate entity ACL extraction from membership expansion:

- Entity ACL extraction maps Graph permission objects to `AccessControl(viewers, is_public)`.
- Membership expansion maps Entra/SP groups to users or nested groups for broker-time resolution.

Rules to preserve:

- Anonymous sharing links set `is_public=True` and do not need a viewer.
- Organization-scoped and users-scoped sharing links are not public. When a SharePoint unique item ID is available, they translate to a specific `group:sp:sharinglinks.<itemId>.<ScopeRole>.<linkId>` viewer.
- Unknown link scopes should be conservative: do not mark public and do not fabricate viewers.
- Users map to `user:{email}` when possible; unresolved Graph IDs can become `user:id:{uuid}` and later be resolved.
- Entra groups map to `group:entra:{group_id}` on entities and `entra:{group_id}` in membership records.
- SharePoint site groups map to `group:sp:{normalized_name}` on entities and `sp:{normalized_name}` in membership records.
- The "Everyone except external users" claim becomes a synthetic group and is populated by enumerating internal tenant members.
- Site-group tracking is site-scoped; the same SP group name on two sites must not collide.

Native anchors:

```bash
cd backend
python -m pytest tests/unit/platform/sources/test_sharepoint_online_acl.py -q
python -m pytest tests/unit/platform/sources/test_sharepoint_online_group_expansion.py -q
python -m pytest tests/unit/platform/sources/test_sharepoint2019v2.py -q
python -m pytest tests/unit/platform/sources/test_sharepoint2019v2_dirsync.py -q
```

The SharePoint 2019 V2 tests cover legacy/on-prem DirSync edge cases: BER integer encoding for the incremental-values flag, member range add/remove parsing, tombstone DN cleanup, cookie roundtrip, permission-error fallback behavior, and deletion entity validation.

## Federated search failures

Slack is the concrete inspected federated source:

- Decorator has `federated_search=True` and org-level source rate limiting.
- `search(query, limit)` calls Slack search APIs and returns entities.
- `generate_entities()` intentionally raises because Slack is search-time only.
- Search result entities need stable metadata such as `airweave_system_metadata.source_name` for filtering and mixed-source search.

Troubleshoot in this order:

1. Confirm the source connection is authenticated and has no sync object when it is federated-only.
2. Confirm source registry entry says `federated_search=true` and source connection responses propagate that flag.
3. Confirm the search layer instantiates the source and calls `source.search()` rather than vector-only retrieval.
4. Confirm external scopes: Slack missing `search:read`, invalid token, inactive account, or provider account issues should surface as source/search errors.
5. In mixed collections, check filters on `airweave_system_metadata.source_name`; source filters should exclude federated sources that do not match.

Credentialed native anchors:

```bash
cd backend
python -m pytest tests/e2e/smoke/test_federated_search.py -q
python -m pytest tests/e2e/smoke/test_search_v2_federated.py -q
```

## Continuous sync and cursor failures

A continuous source needs all of the following:

- `supports_continuous=True` in the decorator.
- A typed `cursor_class` in the decorator.
- `generate_entities()` that accepts `cursor` and updates stable keys.
- Full-sync behavior when cursor data is absent or invalid.
- Incremental behavior that emits only new/changed/deleted entities when cursor data is valid.

GitHub uses repository pushed timestamps and optional PR updated timestamps. SharePoint Online uses per-drive Graph delta tokens and a full-sync-required fallback. The `incremental_stub` E2E is the safest API-level cursor regression anchor.

Native anchor:

```bash
cd backend
python -m pytest tests/e2e/smoke/test_continuous_sync.py -q
```

Expected incremental-smoke pattern: first full sync inserts all initial entities, second sync after config expansion inserts only new entities, third no-change sync inserts/updates zero, and `force_full_sync=true` ignores cursor to support orphan cleanup.

## Source rate-limit failures

Source rate limiting is opt-in per source and per organization:

1. Source decorator sets `rate_limit_level` to `org` or `connection`.
2. Organization has the `source_rate_limiting` feature flag.
3. A DB limit exists for `(organization, source_short_name)` via `/source-rate-limits/{source_short_name}`.
4. Runtime source lifecycle builds `AirweaveHttpClient` with a `SourceRateLimiter`.
5. The client checks Redis before outbound requests and converts internal limit failures to HTTP 429 with `Retry-After`.
6. Source retry helpers should retry 429 with `Retry-After` backoff.

Redis key shape:

- Org-level: `source_rate_limit:{org_id}:{source_short_name}:org:org`
- Connection-level: `source_rate_limit:{org_id}:{source_short_name}:connection:{source_connection_id}`

Native anchor:

```bash
cd backend
python -m pytest tests/e2e/smoke/test_source_rate_limiting.py -q
```

This test toggles feature flags and inspects Redis through Docker. It is local-stack and credential dependent; run sequentially because it flushes Redis and manipulates org feature flags.

## HTTP helper and retry failures

Connectors should call `raise_for_status(response, source_short_name=..., token_provider_kind=..., context=..., entity_id=...)` after external HTTP responses. Expected mappings:

- 2xx: no exception.
- 401: `SourceAuthError` with source and token-provider kind.
- 403: `SourceEntityForbiddenError`, not auth error.
- 404: `SourceEntityNotFoundError`, not auth error.
- 429: `SourceRateLimitError` with parsed or default retry-after.
- 5xx: `SourceServerError`.
- 3xx unexpected redirects: generic source error including location.
- Some disguised 400 rate-limit payloads map to `SourceRateLimitError`.

Native anchor:

```bash
cd backend
python -m pytest tests/unit/platform/sources/test_http_helpers.py -q
```

## Concurrency and batching failures

Use `BaseSource.process_entities_concurrent()` when a source needs bounded parallel entity work. The worker must return an async iterator. Preserve:

- Bounded task count (`batch_size` workers plus producer), not one task per item.
- Support for sync and async input iterables.
- Optional `preserve_order` buffering.
- `stop_on_error=True` propagates worker errors and cancels tasks.
- `stop_on_error=False` logs worker errors and continues with other entities.

Native anchor:

```bash
cd backend
python -m pytest tests/unit/platform/sources/test_process_entities_concurrent.py -q
```

## Validation anchors

Representative connector-facing native candidates:

| Candidate | Safety | What it proves |
| --- | --- | --- |
| `tests/unit/platform/sources/test_http_helpers.py` | Safe unit | HTTP status to source exception mapping. |
| `tests/unit/platform/sources/test_process_entities_concurrent.py` | Safe unit | Bounded concurrency and error behavior. |
| `tests/unit/platform/sources/test_sharepoint_online_acl.py` | Safe unit | SharePoint permission and sharing-link ACL extraction. |
| `tests/unit/platform/sources/test_sharepoint_online_group_expansion.py` | Safe unit | SharePoint site group parsing and site-scoped tracking. |
| `tests/unit/api/test_source_feature_flags.py` | Safe unit | Feature-flag source visibility logic. |
| `tests/e2e/smoke/test_sources.py` | Local stack | Source listing/detail schema and visibility. |
| `tests/e2e/smoke/test_continuous_sync.py` | Local stack | Cursor and force-full-sync behavior through public API. |
| `tests/e2e/smoke/test_entity_definitions.py` | Local stack | Registry-backed entity definitions and source connection entity counts. |
| `tests/e2e/smoke/test_federated_search.py` / `test_search_v2_federated.py` | Credentialed | Slack federated search and mixed-source filtering. |
| `tests/e2e/smoke/test_source_rate_limiting.py` | Credentialed/local-stack | Org vs connection rate limits, Redis keys, feature flag behavior, Lua atomicity. |
| `tests/e2e/smoke/test_source_connections_*` | Credentialed/local-stack | Direct, OAuth, BYOC, token injection, and auth-provider connection behavior. |

Do not downgrade missing external credentials to passing validation. Mark those checks skipped/blocked until credentials and external accounts are available.
