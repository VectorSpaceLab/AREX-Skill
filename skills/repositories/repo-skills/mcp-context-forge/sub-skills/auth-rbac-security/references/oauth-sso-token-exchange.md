# OAuth, SSO, DCR, and Token Exchange

## When to read

Read this for SSO provider configuration, browser OAuth flows, Dynamic Client
Registration, trusted external IdP API tokens, or gateway token-exchange
configurations.

## SSO/OIDC operating rules

- SSO providers are local configuration objects with encrypted client secrets,
  issuer/JWKS metadata, trusted domains, optional team mapping, and approval
  policy.
- External IdP tokens accepted for API auth must map to a local user record.
  Local `is_admin` and team membership decide ContextForge authorization.
- Provider claims can provision or map users, but they do not directly grant
  local admin bypass or arbitrary teams.
- Team/group mapping should fail closed: unmapped or revoked teams should not
  broaden a session.
- Machine-to-machine trusted IdP tokens still use session-style team resolution
  once provisioned locally.

## OAuth gateway flows

ContextForge can store OAuth tokens for upstream gateways and refresh/fetch
upstream tools after user consent. Treat these as user-scoped credentials:

1. Register or update the gateway with the intended OAuth mode.
2. Start an authorization flow for that gateway and current user.
3. Store access/refresh token material encrypted.
4. Use health checks and tool fetches with the consenting user's token when
   available.
5. Never log raw access tokens, refresh tokens, authorization codes, code
   verifiers, or client secrets.

## Dynamic Client Registration

DCR creates or normalizes upstream OAuth client records for a gateway. When
editing or debugging DCR:

- validate issuer, token endpoint, redirect URIs, grant types, response types,
  and token endpoint auth method before persisting.
- normalize issuer/client records consistently so duplicates do not leave stale
  clients.
- handle encrypted registration access tokens as secrets.
- add tests for invalid issuer, invalid redirect URI, unsupported grant type,
  duplicate client, and deleted gateway cases.

## Token exchange gateways

Token exchange is an OAuth 2.0 On-Behalf-Of pattern. ContextForge receives a
user token, exchanges it with a trusted authorization server, and forwards only
the exchanged token to the downstream MCP server.

Security boundaries:

- The inbound ContextForge JWT is the `subject_token` posted to the configured
  `token_url`.
- `token_url` is an SSRF/egress boundary and must be validated at create/update
  time.
- Creating or modifying token-exchange gateways is privileged.
- The original inbound JWT must never be forwarded upstream.
- Audit token-exchange operations with correlation IDs.
- Do not log subject tokens, exchanged tokens, refresh tokens, client secrets,
  or full Authorization headers.

## Trusted proxy and query auth

- Inbound client auth via URL query parameters is not allowed.
- Legacy `INSECURE_ALLOW_QUERYPARAM_AUTH` is only for outbound peer interop and
  must remain opt-in and host-restricted.
- Trusted proxy authentication requires explicit trust flags and trusted header
  boundaries. Do not treat arbitrary inbound headers as identity.

## CSRF and admin surfaces

State-changing Admin UI or admin API operations can require CSRF protection.
When debugging a browser/admin failure, check:

- CSRF enabled flag and exempt paths.
- `X-CSRF-Token` header and cookie pairing.
- secure/samesite cookie settings versus HTTP/HTTPS deployment.
- Referer/origin checks.
- Whether the route is intended for API bearer clients or browser admin UI.

## Test expectations

For OAuth/SSO/token-exchange changes, prefer narrow tests that prove both the
happy path and the denial path:

- untrusted issuer/audience rejected.
- disabled provider rejected.
- trusted external token maps to local session semantics.
- token-exchange gateway rejects invalid `token_url`.
- raw subject/exchanged tokens do not appear in logs.
- revocation or team membership drift narrows access as expected.
