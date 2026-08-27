# Auth and Security Troubleshooting

## `401 Unauthorized`

Likely causes:

- no bearer token or session cookie.
- expired token or missing required `exp`/`jti` claim when those checks are
  enabled.
- wrong signing key, issuer, or audience.
- Basic auth attempted while `API_ALLOW_BASIC_AUTH=false`.
- OAuth-enabled virtual server rejecting an unauthenticated MCP request even
  when global auth is relaxed.

Recovery:

1. Confirm the route is public; otherwise send `Authorization: Bearer ...`.
2. Decode claims without printing the token and check `exp`, `jti`, `iss`,
   `aud`, `token_use`, `is_admin`, and `teams`.
3. Use `scripts/token_scope_probe.py` to classify expected team visibility.
4. Check whether the request is an API token, session token, or trusted external
   IdP token; apply the matching table.
5. For browser/admin requests, check CSRF cookies and headers separately from
   bearer authentication.

## `403 Forbidden`

Likely causes:

- identity authenticated but lacks RBAC permission for the action.
- token scope is public-only, so admin-style permissions are denied by the
  public-only guard.
- caller can see a row but lacks mutate/execute permission.
- route is protected but lacks a mapping in token-scoped authorization and
  therefore fails closed.
- wrong team scope or revoked team membership.

Recovery:

1. Separate visibility from permission. First ask: can the caller see the row?
2. Then ask: which exact permission string is required?
3. Check roles at the right scope: global vs team.
4. Add or run a deny-path regression test before changing policy.
5. Do not bypass by trusting request body owner/team fields.

## Public-only admin surprise

Symptom: token has `is_admin: true`, but list results only include public rows
or admin routes deny access.

Reason: for API/legacy tokens, admin bypass requires `teams: null` plus
`is_admin: true`. Missing `teams` or `teams: []` is public-only.

Recovery: regenerate or adjust the token claims for the intended scope, or keep
it public-only if it is an intentionally reduced automation token.

## Session token team narrowing surprise

Symptom: session token with `teams: ["t1"]` loses access to another team, or a
revoked team claim returns only public rows.

Reason: session tokens resolve membership from the database first. JWT `teams`
only narrows non-admin sessions and cannot broaden revoked membership.

Recovery: inspect local user/team membership, role assignments, and auth cache
TTL before modifying JWT claims.

## CSRF failures

Symptoms include `403` on browser form or Admin UI state-changing requests even
with a valid login.

Check:

- `CSRF_ENABLED` and exempt path list.
- header name, cookie name, and SameSite/Secure settings.
- HTTP vs HTTPS deployment when secure cookies are enabled.
- Referer/origin checks behind reverse proxies.

Do not disable CSRF globally to fix one route. Add a narrow exempt path only if
that route is intentionally non-browser or has another validated protection.

## Token exchange failures

Symptoms: gateway create/update rejected, upstream OAuth token call fails, or
remote MCP server receives no bearer token.

Check:

- `token_url` validation and allowed egress domain.
- privileged permission for creating/modifying token-exchange gateways.
- authorization server response shape and timeout.
- logs redact both subject and exchanged tokens.
- remote server expects the exchanged token, not the original ContextForge JWT.

## Audit/security logging mistakes

- Existing audit logging call sites should not pass the request-scoped DB
  session into the audit service unless a deliberate transactional design change
  has been reviewed.
- Observability writes are best-effort separate-session writes. Do not assume
  they rollback with the main request.
- Redact Authorization headers, OAuth tokens, API keys, passwords, and encrypted
  secret values from logs and support bundles.
