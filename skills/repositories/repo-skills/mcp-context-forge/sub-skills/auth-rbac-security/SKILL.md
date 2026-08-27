---
name: auth-rbac-security
description: "Apply ContextForge authentication, token scoping, teams, RBAC,
  SSO/OAuth, CSRF, and security invariants without reimplementing policy
  helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Auth, RBAC, and Security

Use this sub-skill when the task touches ContextForge authentication,
authorization, token scoping, teams, roles, SSO/OAuth, CSRF, trusted proxy auth,
query-parameter auth restrictions, or security-sensitive regression tests.

## Route here for

- JWT, session-token, API-token, external-IdP, and personal/team token behavior.
- Visibility scoping by `teams`, including admin bypass, public-only scope, and
  session narrowing.
- RBAC permission checks, built-in roles, route decorators, and deny-path tests.
- SSO/OIDC providers, Dynamic Client Registration, OAuth callbacks, and
  token-exchange gateways.
- CSRF, Basic auth enablement, trusted proxy headers, query auth restrictions,
  audit logging, and security log triage.

## Reroute

- Registry entity payloads and API CRUD: [`../registry-admin-api/SKILL.md`](../registry-admin-api/SKILL.md).
- Runtime `.env` catalog and startup secret generation: [`../runtime-configuration/SKILL.md`](../runtime-configuration/SKILL.md).
- MCP transport session behavior: [`../mcp-transports-federation/SKILL.md`](../mcp-transports-federation/SKILL.md).
- Broad test/PR validation selection: [`../development-validation/SKILL.md`](../development-validation/SKILL.md).

## Read first

- [`references/auth-rbac-token-scoping.md`](references/auth-rbac-token-scoping.md) for the two-layer model and canonical helper rules.
- [`references/oauth-sso-token-exchange.md`](references/oauth-sso-token-exchange.md) for OAuth, SSO, and token-exchange boundaries.
- [`references/troubleshooting.md`](references/troubleshooting.md) for common 401/403, public-only, CSRF, and token issues.
- [`scripts/token_scope_probe.py`](scripts/token_scope_probe.py) for a safe, unsigned JWT/JSON claim classifier.

## Operating model

ContextForge uses two independent gates:

1. **Layer 1: token scoping** decides what resources a caller can see.
2. **Layer 2: RBAC** decides what actions the caller can perform.

Do not collapse the two layers. A caller can have an admin identity but a
public-only visibility scope, and a caller can see a resource while still being
forbidden from mutating or executing it.

## Canonical team-scope rules

- API/legacy token with missing `teams`: public-only `[]`.
- API/legacy token with `teams: []`: public-only `[]`.
- API/legacy token with `teams: null` and `is_admin: true`: admin-bypass scope
  `None`.
- API/legacy token with `teams: ["t1"]`: team plus public visibility.
- Session token: database membership is authoritative; JWT `teams` only narrows
  non-admin sessions and cannot broaden revoked membership.
- External trusted SSO/IdP API tokens use the session-token table after local
  user provisioning; do not trust external token teams for local authorization.

When you need to classify a token quickly, run:

```bash
python scripts/token_scope_probe.py --token "$TOKEN" --token-use api
python scripts/token_scope_probe.py --payload '{"email":"u@example.com","is_admin":true,"teams":null}' --token-use api
```

The helper does **not** verify signatures; use it only to reason about claim
shape and expected ContextForge visibility semantics.

## Implementation rules for code changes

- Use the existing auth helpers instead of duplicating policy tables.
- Use scoped-resource helpers for service list/read calls and identity helpers
  for audit/header masking.
- Add deny-path tests for unauthenticated, wrong-team, insufficient-permission,
  and feature-disabled cases whenever touching protected routes or transports.
- Keep token-scoped route authorization default-deny for unmapped protected
  paths.
- Do not accept inbound client auth tokens in URL query parameters.
- Never trust client-supplied owner/team/session fields; derive ownership from
  authenticated identity and server-side state.
- Never log raw subject tokens, exchanged tokens, OAuth client secrets, bearer
  tokens, API keys, or password hashes.

## Security-sensitive edit checklist

1. Identify whether the change affects visibility, action permission, or both.
2. Use canonical helpers for team interpretation and request identity.
3. Confirm feature flags and defaults; high-risk transports must be disabled by
   default unless explicitly enabled.
4. Add deny-path tests before happy-path-only tests.
5. Check audit and structured logging do not share caller transactions unless a
   deliberate design change is reviewed.
6. Route live MCP protocol/auth interactions to the transport sub-skill for
   endpoint-specific validation.

## Output style

When answering security questions, state the caller identity, token-use class,
visibility scope, required RBAC permission, and deny-path evidence separately.
If the user is debugging a token, ask for decoded claims only; do not ask for a
raw signing secret or private token value.
