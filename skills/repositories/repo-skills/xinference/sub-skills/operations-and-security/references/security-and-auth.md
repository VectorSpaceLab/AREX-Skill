# Security and auth

Use this reference for authentication, authorization, OIDC, audit, and access
control. It is intentionally operational: it describes what to configure, what
state must persist, and how to recover when access is lost.

## Auth modes

- `XINFERENCE_AUTH_ADVANCED` defaults to enabled.
- Set it to `false` only when you intentionally want an unauthenticated
  deployment.
- When auth is disabled, every endpoint is served without a login or API key.

## First-run bootstrap

A fresh deployment starts with no admin account. The first administrator is
created through the public setup flow:

| Step | Surface | Notes |
| --- | --- | --- |
| Check bootstrap state | `GET /v1/admin/setup/status` | Reports whether first-run setup is still required. |
| Create the first admin | `POST /v1/admin/setup` | Requires a username and strong password; the first successful call wins. |

The bootstrap account receives the full administrator permission set. Do not
expose a not-yet-initialized instance to an untrusted network.

## Passwords, secrets, and persistence

| Variable | Default | Meaning |
| --- | --- | --- |
| `XINFERENCE_AUTH_DB_PATH` | `<XINFERENCE_HOME>/auth/auth.db` | User, permission, API-key, and refresh-token database. |
| `XINFERENCE_AUTH_JWT_SECRET_KEY` | auto-generated | JWT signing secret. Persisted on first run when unset. |
| `XINFERENCE_AUTH_ENCRYPTION_KEY` | auto-generated | Key used to encrypt stored API keys. Persisted on first run when unset. |
| `XINFERENCE_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access-token lifetime. |
| `XINFERENCE_PASSWORD_MIN_LENGTH` | `8` | Minimum password length enforced by login/setup/reset flows. |

Operator rule: if a deployment needs to survive restart, share the same auth
state across every process that serves the REST API. That means the same
`XINFERENCE_HOME`, or the same explicit paths and secret values.

## Permissions

A caller may only grant permissions they themselves hold. The `admin` scope is
the wildcard that implies everything.

- Model access: `models:list`, `models:read`, `models:write`, `models:register`
- API key management: `keys:create`, `keys:manage`
- User management: `users:manage`
- State access: `cache:list`, `cache:delete`, `virtualenv:list`, `virtualenv:delete`, `logs:list`, `monitor:view`
- Superuser wildcard: `admin`

Legacy scope names such as `models:start`, `models:stop`, `models:add`, and
`models:unregister` are mapped to the modern names for compatibility.

## API keys and login flows

| Flow | Surface | Notes |
| --- | --- | --- |
| CLI login | `xinference login` | Exchanges username and password for an access token. |
| SDK login | `Client(...).login(...)` | Same credentials flow as the CLI. |
| API key use | `Authorization: Bearer <api_key>` | Works for model query and inference endpoints. |
| Key creation | Admin API / Web UI | Requires `keys:create` for self-service and `keys:manage` for broader control. |

Important constraints:
- API keys can only reach model query and inference endpoints.
- They cannot be used to administer users or keys.
- If an account is flagged for a password change, the account must clear that
  flag before it can use the API again.

## Lost-admin recovery

If the first admin password is lost, use `xinference-reset-auth-password`
against the same auth database. It updates the password and revokes active
refresh tokens. That is the preferred recovery path for a bootstrap race or a
forgotten admin password.

## OIDC

OIDC is an addition to the built-in login system, not a replacement for it.
It requires advanced auth to remain enabled.

| Variable | Default | Meaning |
| --- | --- | --- |
| `XINFERENCE_OIDC_ENABLED` | `0` | Enable OIDC single sign-on. |
| `XINFERENCE_OIDC_ISSUER` | unset | OIDC issuer URL used for provider discovery. |
| `XINFERENCE_OIDC_CLIENT_ID` | unset | Client ID registered at the provider. |
| `XINFERENCE_OIDC_CLIENT_SECRET` | unset | Confidential-client secret. |
| `XINFERENCE_OIDC_REDIRECT_URI` | unset | Callback URL back to Xinference. |

OIDC operator checklist:
- Use a confidential client.
- Register the callback URL exactly as Xinference will use it.
- Expect first-login provisioning: users are created automatically with the
  provider `sub` claim and a minimal `models:list` grant.
- If OIDC is enabled, all required variables must be present or startup fails.

## Audit and brute-force protection

| Variable | Default | Meaning |
| --- | --- | --- |
| `XINFERENCE_AUDIT_LOG_RETENTION_DAYS` | `90` | How long audit logs are kept. |
| `XINFERENCE_AUDIT_ES_INDEX` | `xinference-audit-*` | Elasticsearch index pattern used by audit search. |
| `XINFERENCE_RATE_LIMIT_IP_MAX_FAILURES` | `10` | Invalid-key failures allowed per IP. |
| `XINFERENCE_RATE_LIMIT_KEY_MAX_FAILURES` | `5` | Invalid-key failures allowed per IP/key pair. |
| `XINFERENCE_RATE_LIMIT_IP_WINDOW_SECONDS` | `300` | Time window for the IP ban counter. |
| `XINFERENCE_RATE_LIMIT_KEY_WINDOW_SECONDS` | `300` | Time window for the IP/key ban counter. |
| `XINFERENCE_RATE_LIMIT_IP_BAN_SECONDS` | `3600` | Ban duration for an IP. |
| `XINFERENCE_RATE_LIMIT_KEY_BAN_SECONDS` | `3600` | Ban duration for an IP/key pair. |
| `XINFERENCE_ES_URL` | unset | When set, Audit Center queries Elasticsearch instead of local files. |

The audit trail records authenticated API activity, not every HTTP request.
Admin pages can inspect the audit trail and manage security settings at runtime.

## Network exposure

| Variable | Default | Meaning |
| --- | --- | --- |
| `XINFERENCE_ALLOWED_IPS` | unset | Restrict access to selected IPs or CIDR blocks. |
| `XINFERENCE_TRUSTED_PROXIES` | unset | Only trust forwarded client-IP headers from these peers. |

Security notes:
- The server middleware uses permissive CORS; do not treat origin matching as a
  security boundary.
- Use `XINFERENCE_ALLOWED_IPS`, ingress policy, and reverse-proxy controls for
  actual network restriction.
- When trusted proxies are configured, forwarded headers are honored only from
  those peers.

## Safe operator checklist

1. Verify whether auth is enabled before exposing the instance.
2. Create or recover the first admin before opening the service broadly.
3. Persist auth secrets and databases across restarts.
4. Use API keys for automation and passwords for human login.
5. Enable OIDC only when the provider callback and client secrets are ready.
6. Treat audit logs and security settings as admin-only surfaces.
