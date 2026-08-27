# Auth, RBAC, and Token Scoping

## When to read

Read this when a task involves request identity, resource visibility, route
permissions, team membership, token claims, or an unexpected `401`/`403`.

## Two-layer contract

| Layer | Question | Main artifacts | Typical failure |
| --- | --- | --- | --- |
| Token scoping | What rows can this caller see? | token `teams`, local session/user DB membership, request auth context | empty lists, hidden team/private resources, public-only results |
| RBAC | What action can this caller perform? | roles, permissions, route decorators, permission service | `403` after the resource is visible |

Keep the layers independent. Do not use an RBAC role to decide visibility, and
do not treat visibility as permission to mutate or execute.

## Token team interpretation

### API and legacy JWT tokens

| JWT state | `is_admin: true` result | `is_admin: false` result |
| --- | --- | --- |
| no `teams` key | public-only `[]` | public-only `[]` |
| `teams: null` | admin bypass `None` | public-only `[]` |
| `teams: []` | public-only `[]` | public-only `[]` |
| `teams: ["team-id"]` | team plus public | team plus public |

Admin bypass for this token class requires both `teams: null` and
`is_admin: true`. A missing `teams` claim is not bypass.

### Session tokens

Session tokens use the local database as the authority. The JWT `teams` claim
can only narrow a non-admin session:

- local admin user: `None` admin-bypass scope regardless of JWT `teams`.
- non-admin and JWT `teams` missing/null/empty: full DB team membership.
- non-admin and JWT `teams: ["t1"]`: intersection of DB teams and `t1`.
- non-admin and JWT teams all revoked: `[]`, public-only fail-closed scope.

External IdP tokens accepted as API authentication are provisioned into this
session-token pathway; local user state remains authoritative.

## Scope return values

| Value | Meaning | Query behavior |
| --- | --- | --- |
| `None` | admin bypass visibility | skip visibility filtering while preserving identity for audit/owner cases |
| `[]` | public-only | only public rows; no team rows and no owner-private broadening |
| `["t1", ...]` | team-scoped | public plus matching team rows plus permitted private owner rows |

## Canonical helper use

Use project helpers instead of hand-parsing token claims:

- token class interpretation lives in the auth layer.
- request-scoped resource visibility should come from the scoped access helper.
- request identity for audit/header masking should come from the request identity
  helper.
- raw triples are only for documented Layer-1 exceptions such as forwarding an
  internal auth context, run ownership capture, or tool-execution authorization.
- route token-scope grants should use the RBAC middleware policy helper; empty
  token scopes mean runtime-inherited RBAC, not deny-all.

When editing code, add a short comment for any legitimate Layer-1 exception so
future maintainers do not copy raw team parsing into ordinary route handlers.

## Built-in role families

- `platform_admin`: global `*` permissions.
- `team_admin`: team-scoped administration plus tool/resource/prompt/server and
  token permissions.
- `developer`: team-scoped create/update/delete/read/execute for main working
  entities.
- `viewer`: team-scoped read/execute style access.
- `platform_viewer`: global read-oriented access for platform visibility.

Do not assume a role grants visibility outside the token scope. For example,
public-only automation can still be denied visibility even if the identity has a
broad role.

## Protected route change checklist

1. Identify the exact permission string required for the action.
2. Ensure the route uses the standard permission dependency/decorator.
3. Derive caller email/admin/scope through canonical helpers.
4. Do not trust body fields such as `owner_email`, `team_id`, or session owner.
5. Add tests for unauthenticated, wrong team/public-only, insufficient role, and
   disabled feature flag when relevant.
6. If the route forwards auth context internally, validate and fail closed on
   malformed public-only contexts.

## Useful mental tests

- `is_admin=true`, missing `teams`: should be public-only for API/legacy tokens.
- `teams=null`, `is_admin=false`: should be public-only, not bypass.
- session token with JWT `teams=[revoked]`: should demote to public-only.
- admin session with JWT `teams=[t1]`: should remain DB-admin bypass.
- empty token scope in generated token catalog: should inherit RBAC at runtime,
  not deny everything.
