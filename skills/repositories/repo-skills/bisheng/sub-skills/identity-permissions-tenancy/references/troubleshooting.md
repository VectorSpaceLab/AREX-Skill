# Identity, Permissions, Tenancy, and Gateway Troubleshooting

## User cannot see a resource

Likely causes:
- Missing owner or relation tuple in OpenFGA.
- Role/menu key missing or stale.
- Tenant mismatch or disabled tenant.
- Frontend route guard is using the correct key but backend data omitted it.

Recovery:
- Check the owning resource service's PermissionService path.
- Confirm tenant context and user-tenant membership.
- Check whether a startup/manual backfill is required for upgraded data.
- Only edit frontend route guards after backend permission data is verified.

## User can see too much

Likely causes:
- Raw SQL or bulk statement bypassed tenant filtering.
- Direct role-access query bypassed PermissionService and tenant-aware semantics.
- Admin/tenant-admin short-circuit applied to a non-admin path.

Recovery:
- Search for raw SQL, direct roleaccess usage, and manual tenant conditions.
- Use `scripts/check_arch_rules.py` as a first pass.
- Add denial tests, not only happy-path admin tests.

## Resource list has duplicates or short pages

Likely causes:
- Cursor scan loop advances by last visible row instead of last DB row.
- DM8 row-value tuple comparison was used.
- Cursor token context/key length mismatch is swallowed rather than returned as the module error code.

Recovery:
- Use expanded keyset helper behavior.
- Keep permission filtering and cursor advancement separate.
- Reset frontend cursor on invalid-cursor error codes.

## Tenant context is missing in workers or scripts

Symptoms:
- Queries return default-tenant rows unexpectedly.
- Multi-tenant mode raises missing tenant context.
- Worker writes data under the wrong tenant.

Recovery:
- Confirm Celery tenant signal import and task headers.
- For one-off scripts, use app context and tenant bypass/set helpers intentionally.
- Do not assume API middleware has run inside scripts or worker subprocesses.

## Gateway SSO loop or callback failure

Likely causes:
- Frontend proxy points to FastAPI when gateway-only OAuth endpoint is required.
- Gateway cannot call backend SSO sync endpoint.
- Cookie domain/path/SameSite mismatch.
- Third-party user identifier mapping changed.

Recovery:
- Distinguish `/api/oauth2/*` gateway routes from `/api/v1/**` backend routes.
- Verify gateway and backend share Redis where cache invalidation depends on it.
- Check cookie settings and frontend base paths.

## Sensitive-word or rate limit behavior is unexpected

Likely causes:
- Gateway filters are active in commercial mode.
- Request path matches gateway `filter-url` rules.
- Group/resource limit cache is stale.

Recovery:
- Verify whether the request went through the gateway.
- Check gateway-sensitive routes before backend chat/assistant code.
- Route generic backend chat flow to `backend-core` or `workflow-engine` only after gateway filtering is ruled out.
