# Auth, Config, and Source Connection Validation

## When to read this

Read this before changing connector auth methods, source credential schemas, config fields, OAuth/BYOC/token-injection behavior, auth-provider support, template config handling, or source connection validation. Pair with sibling [backend-api](../../backend-api/SKILL.md) for exact source-connection endpoint shapes and OAuth callback verification.

## Auth method model

Airweave source connections use nested authentication payloads. The API infers `AuthenticationMethod` from the fields present; callers do not send an explicit method string.

| Method | Payload shape | Connector registry requirement | Creation behavior |
| --- | --- | --- | --- |
| `direct` | `authentication: {"credentials": {...}}` | Source includes `AuthenticationMethod.DIRECT` and `auth_config_class`. | Validate auth schema, validate source reachability, create credential + connection + authenticated source connection. Defaults `sync_immediately=True`. |
| `oauth_token` | `authentication: {"access_token": "...", "refresh_token"?: "...", "expires_at"?: ...}` | Source supports `OAUTH_TOKEN`; OAuth token is not blank or expired. | Validate config and token by creating a lightweight source. Defaults `sync_immediately=True`. |
| `oauth_browser` | `authentication` omitted or `{}` | Source supports `OAUTH_BROWSER`; if `requires_byoc`, empty browser auth is rejected. | Creates unauthenticated shell connection, OAuth init session, proxy auth URL, and one-time `claim_token`. Defaults `sync_immediately=False`. |
| `oauth_byoc` | `authentication: {"client_id": "...", "client_secret": "..."}` or OAuth1 `consumer_key` + `consumer_secret` | Source supports OAuth browser; BYOC is automatically accepted when browser auth is supported. | Same shell flow as OAuth browser, but provider URL uses caller-supplied client credentials. `sync_immediately=True` is rejected. |
| `auth_provider` | `authentication: {"provider_readable_id": "...", "provider_config"?: {...}}` | Source includes `AUTH_PROVIDER`; chosen provider is not in its blocked sources. | Validate provider config, create authenticated source connection, optionally trigger sync. Defaults `sync_immediately=True`. |

`BaseSource.get_supported_auth_methods()` automatically exposes `oauth_byoc` when `oauth_browser` is supported. Compatibility checks still reject unsupported methods with a message listing supported values.

## SourceConnection schema rules

Important Pydantic validation from `SourceConnectionCreate` and nested auth models:

- `name` is optional; if omitted, the service defaults to `{Source Name} Connection`.
- `readable_collection_id` is required for connection creation.
- Direct authentication credentials cannot be empty.
- OAuth token `access_token` cannot be empty or whitespace-only and cannot be expired when `expires_at` is provided.
- OAuth2 BYOC requires both `client_id` and `client_secret`, or neither.
- OAuth1 BYOC requires both `consumer_key` and `consumer_secret`, or neither.
- OAuth1 and OAuth2 BYOC credential pairs cannot be mixed in the same payload.
- Updates require at least one field and only direct auth connections can update `authentication` credentials through the update schema.

Connector-facing consequence: if a test sends a partial BYOC payload or token injection to a non-OAuth source, the expected failure is a 400/422 validation or compatibility error, not a connector runtime error.

## Auth config vs source config

Keep the two model families separate:

- Auth config classes describe credentials or secrets needed for direct auth. Example: `GitHubAuthConfig.personal_access_token`; `SharePointOnlineAppAuthConfig.tenant_id`, `client_id`, `client_secret`, `private_key`, and optional `certificate`.
- Source config classes describe non-secret source selection/options. Example: `GitHubConfig.repo_name`, `branch`, `sync_pull_requests`; `SharePointOnlineConfig.site_url`, `include_personal_sites`, `include_pages`, sensitivity-label filters; Slack's config is intentionally empty.

Public field metadata comes from Pydantic `Field` information and `json_schema_extra`:

| Metadata | Effect | Common use |
| --- | --- | --- |
| `is_secret` | Marks config/auth field as secret in API-visible schema. | API keys, client secrets, private keys, certificates. |
| `feature_flag` | Field appears only when organization has the feature. | Experimental config options. |
| `required_for_auth` | Field is needed before OAuth provider URL generation. | Template-backed OAuth sources. |
| `auth_provider_field` | Auth provider may supply this config field at runtime. | Provider-returned instance URLs. |
| `exclude_from_ui` | Registry omits field from UI-facing `Fields`. | Internal/autopopulated fields. |

Use validators for source identifiers and URLs. URL/host config values should pass SSRF-safe validation when they affect outbound requests.

## Validation path for direct and token credentials

Direct and token flows validate before persisting authenticated connections:

1. `SourceValidationService.validate_config(short_name, config, ctx)` gets the registry entry, validates against `config_ref`, rejects disabled feature-gated fields, and returns a plain dict.
2. `SourceValidationService.validate_auth_schema(short_name, auth_fields)` validates direct credentials against `auth_config_ref`; pure OAuth sources without direct auth return a 422 for direct credentials.
3. `SourceLifecycleService.validate(short_name, credentials, config)` normalizes credentials, builds a lightweight auth provider, creates a source with a plain `AirweaveHttpClient`, parses typed config, calls `source.create(...)`, then calls `source.validate()`.
4. Source errors are translated to HTTP errors by source-connection creation code. Auth/credential failures should not be hidden as successful connections.

Credential validation uses the same source `validate()` method as lifecycle creation, so connector validation should exercise the same HTTP helper and retry/error translation path as sync/search.

## Runtime source lifecycle during sync/search

When a real source connection is used for sync, browse tree, or federated search, `SourceLifecycleService.create()` performs:

1. Load source connection and connection records.
2. Resolve source class and schemas from the registry.
3. Resolve auth configuration:
   - Directly injected access token has highest priority and becomes a `StaticTokenProvider`.
   - Auth-provider source connections create an auth-provider instance and request runtime auth fields computed by the registry.
   - Database credentials are decrypted and normalized; refresh-token credentials can be refreshed through OAuth services.
4. Build a token provider: `StaticTokenProvider`, `DirectCredentialProvider`, `OAuthTokenProvider`, or `AuthProviderTokenProvider`.
5. Build `AirweaveHttpClient` with org/source/source_connection_id and optional rate limiter. The source-rate-limiting feature flag controls enforcement.
6. Parse `config_fields` into the registry's `config_ref` model.
7. Call `source_class.create(auth=..., logger=..., http_client=..., config=...)` and then `source.validate()`.

Only auth-related validation errors are wrapped as source validation errors during lifecycle creation. Server, network, and source-rate-limit failures should propagate so schedules are not incorrectly paused as credential failures.

## Auth provider support

Supported auth providers are computed by registry from provider `blocked_sources`. A source using `AuthenticationMethod.AUTH_PROVIDER` can still show an empty provider list if all providers block it.

Auth-provider source connections:

- Require a real auth provider connection by `provider_readable_id`.
- Validate optional `provider_config` through the provider service.
- Ask the auth provider for the source's runtime auth fields. OAuth lifecycle fields such as refresh/client values are optional because providers can manage refresh.
- Can merge provider-returned config into source config, but user-provided config values take precedence.

If auth-provider sync fails, inspect both the source connector and the provider-specific credentials/config. The source is still responsible for `validate()` and external API behavior.

## OAuth browser and BYOC details

OAuth browser/BYOC creation creates a pending source connection and an initiation session. The create response returns `auth.auth_url` plus a one-time `auth.claim_token`; clients must later call OAuth verification with that claim token. See sibling [backend-api](../../backend-api/SKILL.md) for the endpoint lifecycle.

Connector-facing rules:

- `requires_byoc=True` blocks empty OAuth browser initiation and asks callers for custom client credentials.
- Self-hosted environments force OAuth-capable sources to appear BYOC-required in source metadata.
- Template config fields are validated before initiating OAuth so provider URLs can be rendered safely.
- OAuth browser/BYOC flows must not run immediate sync; sync starts only after callback verification.
- OAuth1 BYOC uses `consumer_key`/`consumer_secret`; OAuth2 BYOC uses `client_id`/`client_secret`.

## Token injection details

Token injection is the `oauth_token` flow, not a special endpoint. It is connector-facing because sources must support token-provider auth in `create()` and `validate()`.

Preserve these expectations from native tests:

- Invalid/empty/whitespace tokens are rejected during creation.
- Token injection on non-OAuth sources is rejected as unsupported.
- Valid token-injected connections are immediately authenticated and do not expose access tokens in detail/list responses.
- Token-injected connections can schedule syncs or trigger manual syncs.
- Optional `refresh_token` can be stored when provided, but access-only sources may not use it.

## Config examples from current connectors

| Connector | Auth schema | Source config | Notes |
| --- | --- | --- | --- |
| GitHub | `personal_access_token`, min length and token-prefix validation. | `repo_name` in `owner/repo` format, optional `branch`, `sync_pull_requests`. | `create()` stores PAT/token and config on instance; `validate()` checks repo and optional branch. |
| Slack | OAuth2 access token inherited by `SlackAuthConfig`. | Empty `SlackConfig`. | Federated search source; validation calls Slack `auth.test`. |
| SharePoint Online delegated | No direct auth config. | Site URL, personal-site/page flags, Purview label filters, encrypted/unlabeled file policy. | OAuth rotating refresh; uses Graph token and SharePoint-scoped token exchange for site groups. |
| SharePoint Online app | Tenant/client credentials plus Graph secret and certificate/private key for SharePoint REST. | Same SharePoint Online config. | App-only Graph token and certificate-based SharePoint REST token exchange are separate auth paths. |

## Validation anchors

Useful focused tests for this reference:

```bash
cd backend
python -m pytest tests/unit/api/test_source_feature_flags.py -q
python -m pytest tests/e2e/smoke/test_source_connections_token_injection.py -q
python -m pytest tests/e2e/smoke/test_source_connections_direct_auth.py -q
python -m pytest tests/e2e/smoke/test_source_connections_oauth.py -q
python -m pytest tests/e2e/smoke/test_source_connections_auth_provider.py -q
```

The E2E auth-flow tests require configured external credentials and a local backend stack. Treat missing credentials as an environment skip/blocker, not a connector-code failure.
