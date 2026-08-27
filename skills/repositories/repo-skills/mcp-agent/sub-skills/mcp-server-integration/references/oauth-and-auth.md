# OAuth and Authentication

This reference covers authentication for both directions:

- an `mcp-agent` app connecting to protected upstream MCP servers;
- an `mcp-agent` app exposing its own OAuth-protected FastMCP server.

Keep secrets in `mcp_agent.secrets.yaml`, environment variables, or deployment secret mechanisms. Do not hard-code bearer tokens, client secrets, refresh tokens, or Redis credentials in public runtime files.

## Downstream OAuth for Upstream MCP Servers

Configure OAuth per server under `mcp.servers.<name>.auth.oauth`.

```yaml
mcp:
  servers:
    github:
      transport: streamable_http
      url: "https://api.example.com/mcp"
      auth:
        oauth:
          enabled: true
          authorization_server: "https://auth.example.com"
          resource: "https://api.example.com/mcp"
          client_id: "${OAUTH_CLIENT_ID}"
          client_secret: "${OAUTH_CLIENT_SECRET}"
          scopes: ["read:items"]
          redirect_uri_options:
            - "http://127.0.0.1:33418/callback"
          include_resource_parameter: true
```

Core fields:

| Field | Use |
| --- | --- |
| `enabled` | Enables OAuth for this upstream server. |
| `scopes` | Scopes requested during authorization. |
| `resource` | Protected resource identifier sent as the RFC 8707 `resource` parameter. |
| `authorization_server` | Preferred authorization server root; provider metadata is discovered from it. |
| `client_id`, `client_secret` | OAuth client credentials. Use placeholders/secrets. |
| `access_token`, `refresh_token`, `expires_at`, `token_type` | Optional pre-seeded token values. |
| `redirect_uri_options` | Candidate redirect URIs for the authorization code flow. |
| `extra_authorize_params` | Extra query parameters for authorization requests. |
| `extra_token_params` | Extra form parameters for token requests. |
| `require_pkce` | Defaults to `true`; keep enabled unless a provider cannot support PKCE. |
| `use_internal_callback` | Prefer the app server’s internal callback route when available. |
| `include_resource_parameter` | Defaults to `true`; disable for providers that reject `resource`. |

How it works:

1. The streamable HTTP transport sees `auth.oauth.enabled: true`.
2. If the app context has a token manager, the connection uses an OAuth HTTP auth handler.
3. The auth handler uses the configured server name, scopes, server config, and current user identity.
4. If a token is absent or expired, the OAuth flow can send `auth/request` upstream or fall back to local loopback/internal callback behavior.
5. Stored tokens are reused for subsequent calls when the token store permits it.

If the context has no token manager, OAuth auth is skipped with a warning. In that case, check global `oauth` settings and app initialization.

## Global OAuth Settings

Global settings control token persistence and callbacks.

```yaml
oauth:
  token_store:
    backend: memory
    refresh_leeway_seconds: 60
  flow_timeout_seconds: 300
  callback_base_url: "https://agent.example.com"
  loopback_ports: [33418, 33419, 33420]
```

Token store options:

| Backend | Use | Notes |
| --- | --- | --- |
| `memory` | Local development and short-lived processes | Tokens vanish on restart. |
| `redis` | Multi-process or durable workflow pre-authorization | Requires Redis connection settings and the package extra that provides Redis support. |

Redis example:

```yaml
oauth:
  token_store:
    backend: redis
    redis_url: "${REDIS_URL}"
    redis_prefix: "mcp_agent:oauth_tokens"
    refresh_leeway_seconds: 60
```

Troubleshooting Redis:

- If imports fail for the Redis backend, install the package with the Redis extra in the runtime environment.
- If tokens are not reused across worker processes, confirm every process points at the same `redis_url` and `redis_prefix`.
- If refresh occurs too late, increase `refresh_leeway_seconds`.

## OAuth Resource Metadata

Some protected resource servers require RFC 8707 resource indicators and protected-resource metadata.

Checklist for remote OAuth MCP servers:

- Set `resource` to the protected resource identifier expected by the provider.
- Keep `include_resource_parameter: true` unless the provider rejects it.
- If the provider has multiple authorization servers, set `authorization_server` to the intended one.
- Normalize trailing slashes mentally when comparing provider metadata; the implementation handles common trailing-slash mismatches.
- For providers that reject `resource`, set `include_resource_parameter: false` and document why.

Common symptoms:

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Authorization URL lacks expected audience/resource | Missing `resource` or disabled `include_resource_parameter` | Add `resource` or re-enable the parameter. |
| Provider rejects `resource` | Provider does not support RFC 8707 for that flow | Set `include_resource_parameter: false`. |
| Wrong auth server selected | Metadata advertises multiple issuers | Set `authorization_server` explicitly. |
| Token endpoint says invalid client | Bad `client_id`/`client_secret` or wrong auth server | Verify secret source and provider registration. |

## Pre-authorizing Workflow Credentials

For workflows that run in the background and cannot complete an interactive OAuth flow at execution time, call the app server tool `workflows-store-credentials` before starting the workflow.

Payload shape:

```json
{
  "workflow_name": "github_org_search",
  "tokens": [
    {
      "access_token": "${ACCESS_TOKEN}",
      "refresh_token": "${REFRESH_TOKEN}",
      "server_name": "github",
      "scopes": ["read:org"],
      "expires_at": 1893456000,
      "authorization_server": "https://auth.example.com"
    }
  ]
}
```

Rules enforced by the server tool:

- `workflow_name` must exist in the app’s workflow registry.
- Each token must be a dictionary.
- `access_token` is required.
- `server_name` is required and must exist in the app server registry.
- A token manager must be available on the app context.
- Partial success is reported when some tokens are stored and others fail.

Use pre-authorization when:

- Temporal or another background executor will run without a browser session;
- the user already has a valid token from an external authorization step;
- a deployment wants to store per-user credentials before a long-running workflow begins.

## Protecting Your App Server with OAuth

To require OAuth bearer tokens from clients connecting to your exposed FastMCP server, configure top-level `authorization` settings before calling `create_mcp_server_for_app(...)`.

```yaml
authorization:
  enabled: true
  issuer_url: "https://auth.example.com"
  resource_server_url: "https://agent.example.com/mcp"
  service_documentation_url: "https://agent.example.com/docs"
  required_scopes: ["mcp.read", "mcp.write"]
  introspection_endpoint: "https://auth.example.com/oauth/introspect"
  introspection_client_id: "${INTROSPECTION_CLIENT_ID}"
  introspection_client_secret: "${INTROSPECTION_CLIENT_SECRET}"
  expected_audiences: ["agent.example.com"]
```

Important implementation behavior:

- When `authorization.enabled` is true, the app server builds FastMCP auth settings and a token verifier.
- Token introspection can be configured directly or discovered from authorization server metadata.
- Audience validation is enforced when authorization is enabled; `expected_audiences` is required for RFC 9068 compliance.
- The verifier checks both `aud` and `resource` claims when evaluating token audience/resource matches.
- If auth settings cannot be configured, the server logs an error and continues without effective auth; treat that as a deployment blocker.

## Internal OAuth Callback and Gateway Auth

The app server installs an internal callback route shaped like:

```text
/internal/oauth/callback/{flow_id}
```

Use `oauth.callback_base_url` when this route should be reachable from the authorization server. If no callback base URL is usable and `loopback_ports` are configured, local loopback can handle interactive client-side flows.

Some internal relay endpoints support optional shared-secret gateway auth. When a gateway token is configured, requests must send `Authorization: Bearer <token>`.

## Safe Secret Placement

Use these patterns:

```yaml
headers:
  Authorization: "Bearer ${REMOTE_MCP_TOKEN}"

auth:
  oauth:
    client_id: "${OAUTH_CLIENT_ID}"
    client_secret: "${OAUTH_CLIENT_SECRET}"

oauth:
  token_store:
    redis_url: "${REDIS_URL}"
```

Avoid these patterns:

- literal OAuth client secrets in config committed to a project;
- literal bearer tokens in `headers` examples;
- embedding tokens in WebSocket query parameters unless a provider forces it and the config is private;
- using the in-memory token store for multi-process or durable workflows that need token reuse.

## OAuth Debug Checklist

1. Confirm the server key in `mcp.servers` matches the `server_name` used by agents, direct clients, and stored tokens.
2. Validate the server transport first; OAuth cannot fix a bad URL or missing command.
3. Confirm `auth.oauth.enabled: true` on the protected upstream server.
4. Confirm global `oauth` settings create a token manager.
5. Check whether the provider expects or rejects the `resource` parameter.
6. Check `authorization_server` and metadata trailing slashes if the wrong issuer is selected.
7. For Redis token storage, verify the Redis extra is installed and `redis_url` is reachable.
8. For app-server OAuth protection, verify `expected_audiences`, `issuer_url`, and `resource_server_url` before exposing the server.
