# Source Registry and Connector Contract

## When to read this

Read this before adding or changing an Airweave source connector, source decorator metadata, source registry output, source feature flags, supported auth providers, entity-definition exposure, or capability flags such as continuous sync, federated search, access control, browse tree, and source rate limits.

## Source class contract

Connector classes inherit `BaseSource`. The source lifecycle creates instances with injected dependencies; source implementations should not instantiate their own global credential manager, logger, or HTTP client.

Required source hooks:

| Hook | Connector obligation | Expected use |
| --- | --- | --- |
| `@source(...)` | Declare identity, auth/config classes, and capabilities. | Registry and API discovery. |
| `create(*, auth, logger, http_client, config)` | Return a configured source instance using injected dependencies and typed config. | Source lifecycle, sync, validation, federated search. |
| `generate_entities(*, cursor=None, files=None, node_selections=None)` | Yield entities for sync; use cursor and selected nodes when supported. | Sync pipeline. |
| `validate()` | Prove credentials/config are usable with a lightweight source API call. | Source connection create/update and lifecycle. |
| `search(query, limit)` | Implement only when `federated_search=True`. | Search-time federated results. |
| `get_browse_children(parent_node_id)` / `parse_browse_node_id(node_id)` | Implement only when `supports_browse_tree=True`. | Lazy browse tree and targeted sync. |
| `generate_access_control_memberships()` | Implement when group expansion is required for `supports_access_control=True`. | ACL membership ingestion. |

`BaseSource.process_entities_concurrent()` is the shared bounded-concurrency helper. It keeps task count proportional to `batch_size`, supports sync or async item iterables, optional order preservation, and `stop_on_error` behavior.

## Decorator fields that matter

The `source(...)` decorator sets class attributes consumed by the registry and service layer:

| Field | Meaning | Connector check |
| --- | --- | --- |
| `name`, `short_name` | Display name and globally unique source identifier. | `short_name` must match config/entity module expectations and API clients. |
| `auth_methods` | Supported `AuthenticationMethod` values. | Include only methods the source lifecycle can validate and instantiate. |
| `oauth_type`, `requires_byoc` | OAuth token lifecycle and BYOC requirement. | OAuth browser sources can also expose `oauth_byoc` automatically. |
| `auth_config_class` | Direct credential schema. | Direct auth requires this; pure OAuth sources can leave it `None`. |
| `config_class` | Source-specific configuration schema. | Fields become API-visible config fields. |
| `labels` | Discovery categories. | Keep user-facing and short. |
| `supports_continuous`, `cursor_class` | Cursor-based sync support. | Decorator raises if continuous is true without a cursor class. |
| `federated_search` | Search-time source API querying instead of full sync. | Implement `search()` and avoid scheduling full sync as the primary path. |
| `supports_temporal_relevance` | Whether source entities have time signals for ranking. | Set false for sources such as code repositories when recency is not meaningful. |
| `supports_access_control` | Entity-level ACL support. | Set `entity.access` and emit memberships when groups must expand. |
| `supports_browse_tree` | Lazy source browsing and selected-node sync. | Implement browse methods and keep IDs parsable. |
| `rate_limit_level` | `org`, `connection`, or unset. | Controls Redis key shape when rate limiting feature is enabled. |
| `feature_flag` | Organization feature required to see/use source. | Service hides source on list/detail when the flag is absent. |
| `internal` | Internal/test source visibility. | Hidden unless internal sources are enabled. |

## Registry build flow

`SourceRegistry.build()` reads `ALL_SOURCES` from the source package once at startup. It filters internal sources, validates source contracts, then precomputes `SourceRegistryEntry` objects keyed by `short_name`.

For each source, the registry:

1. Validates template OAuth config fields against integration settings when a URL template exists.
2. Warns when `create()` or `generate_entities()` signatures drift from the BaseSource v2 contract.
3. Converts `auth_config_class` and `config_class` into `Fields` via `Fields.from_config_class()`.
4. Computes supported auth providers from each provider's `blocked_sources` list.
5. Computes runtime auth fields:
   - Direct auth: field names from `auth_config_class`.
   - OAuth with refresh or rotating refresh: `access_token` and `refresh_token`.
   - OAuth access-only: `access_token`.
6. Resolves output entity definition short names from the entity definition registry.
7. Stores capability flags, `rate_limit_level`, `feature_flag`, and labels for fast API reads.

The registry does not query the database for source metadata. If a source is missing from `/sources/`, first check decorator metadata, `ALL_SOURCES`, internal-source settings, feature flag gating, and startup-time registry errors.

## API source discovery behavior

`SourceService` maps registry entries to the public `Source` schema for `GET /sources/` and `GET /sources/{short_name}`. Pair this with sibling [backend-api](../../backend-api/SKILL.md) for endpoint lifecycle details.

Per-request behavior to preserve:

- Sources with `feature_flag` are hidden from list/detail unless `ctx.organization.enabled_features` contains the matching `FeatureFlag` enum value.
- Invalid feature-flag strings fail open with a warning rather than hiding the source.
- `config_fields` are filtered by per-field feature flags before serialization.
- In self-hosted mode, OAuth-capable sources are treated as `requires_byoc=True` so users supply their own client credentials.
- Public source responses include source identity, auth/config fields, supported auth providers, capability flags, labels, rate-limit level, and output entity definitions.

## Field model details

`Fields.from_config_class()` converts Pydantic fields into API-visible metadata:

- `name`, title, description, type, required flag, enum values, and array item type.
- `json_schema_extra["exclude_from_ui"]` hides a field from UI-facing field lists.
- `json_schema_extra["feature_flag"]` gates a field by organization feature.
- `json_schema_extra["is_secret"]` marks a field as secret.
- Literal types become string fields with `enum_values`.
- Optional/defaulted fields become not required.

Template config helpers are registry-sensitive: fields created with `RequiredTemplateConfig(...)` set `required_for_auth=True`; OAuth browser creation extracts and validates those fields before initiating provider auth.

## Capability examples from current connectors

| Source | Decorator/auth shape | Connector behavior | Validation and risk points |
| --- | --- | --- | --- |
| GitHub | `short_name="github"`, direct + auth provider, `GitHubAuthConfig`, `GitHubConfig`, `supports_continuous=True`, `GitHubCursor`, `rate_limit_level=org`, `supports_temporal_relevance=False`. | Syncs repo metadata, directories, files, optional merged PRs and review comments. Uses `last_repository_pushed_at` and `last_pr_updated_at` cursor data. | PAT format validation is in auth config; `validate()` checks repo and optional branch; branch must exist; deleted files emit deletion entities during incremental traversal. |
| Slack | OAuth browser + token + auth provider, access-only OAuth, `SlackAuthConfig`, empty `SlackConfig`, `federated_search=True`, `rate_limit_level=org`. | Searches Slack messages at query time via Slack Search API; `generate_entities()` raises intentionally. | Missing `search:read`, invalid token, inactive account, or Slack API errors must surface from `search()`/`validate()`. |
| SharePoint Online | OAuth browser + token + auth provider, rotating-refresh OAuth, no direct auth config, `SharePointOnlineConfig`, continuous cursor, ACL, browse tree, feature flag. | Delegated Graph auth; discovers explicit or all accessible sites; syncs sites, drives, files, pages; supports targeted sync and ACL memberships. | Browse-node encoding, site discovery, Graph permissions, SP group expansion, sharing-link translation, and sensitivity-label filters are common failure points. |
| SharePoint Online App | Direct `SharePointOnlineAppAuthConfig`, `SharePointOnlineConfig`, continuous cursor, ACL, browse tree, feature flag. | App-only Graph auth plus certificate-based SharePoint REST token exchange for SP site groups; uses app-only delta prefer headers. | Requires tenant/client credentials and certificate material; Graph and SharePoint-scoped tokens have separate failure modes. |

## New source implementation checklist

1. Choose a stable `short_name` and ensure the source class is imported into `ALL_SOURCES`.
2. Define direct credential schema only when using `AuthenticationMethod.DIRECT`. Use OAuth metadata for browser/token sources.
3. Define source config schema with strict validators for external identifiers, URL/host SSRF safety, and any template fields needed before OAuth.
4. Add the `@source(...)` decorator with accurate capability flags. Do not set `supports_continuous=True` without a typed cursor class.
5. Implement `create()` using injected `auth`, `logger`, `http_client`, and typed `config`. Cache only source-specific non-secret config values on `self`.
6. Implement `validate()` with the same HTTP/error helper path used by sync/search so credential failures map consistently.
7. Use `raise_for_status()` and source retry helpers for external API calls. Preserve token refresh on `401` only when the auth provider supports refresh.
8. For sync sources, yield typed entities with `airweave_system_metadata` filled by the pipeline where applicable, stable entity IDs, breadcrumbs, and deletion entities for incremental deletes.
9. For federated sources, implement `search()` and return entities with metadata/text suitable for search results. Do not emit sync entities just to satisfy tests.
10. For ACL sources, test `entity.access`, principal formats, group tracking, and `generate_access_control_memberships()` separately from content sync.
11. For browse-tree sources, add source-owned tests for emitted node IDs, parser metadata, malformed IDs, and targeted sync behavior.
12. Add or update native tests: source registry/list/detail, source validation, connector unit tests, continuous sync smoke, federated search smoke, source rate-limit smoke, and auth-flow smoke as applicable.
