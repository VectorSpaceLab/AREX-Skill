---
name: identity-permissions-tenancy
description: "Operate on BiSheng JWT auth, RBAC/ReBAC/OpenFGA permissions,
  tenant isolation, admin scope, approval center, commercial gateway
  integration, and cursor permission performance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# identity-permissions-tenancy

Use this sub-skill when a task touches BiSheng authentication, authorization, resource ownership, OpenFGA/ReBAC, RBAC menu permissions, multi-tenant isolation, admin scope, approval workflows, SSO/org sync, commercial gateway behavior, or cursor-pagination permission performance.

## Start here

Run bundled helper commands from this sub-skill directory, or adjust the script path to this directory after import.


1. Run the read-only pattern checker before or after a permission/tenant-sensitive edit:
   ```bash
   python scripts/check_arch_rules.py --repo-root <bisheng-checkout>
   ```
2. Read [references/workflows.md](references/workflows.md) for auth, PermissionService, tenant ContextVar, gateway, approval, and cursor workflows.
3. Read [references/troubleshooting.md](references/troubleshooting.md) for missing permissions, invisible resources, tenant leaks, SSO/gateway, and cursor list failures.

## Owned responsibilities

- JWT/auth user loading, menu keys, and role/user/group relationships.
- PermissionService, OpenFGA/ReBAC model, failed tuple retry, owner grants, relation models, and resource authorization.
- Tenant ContextVar, SQLAlchemy tenant filter, tenant storage prefixes, tenant tree/admin scope, user-tenant membership, and quota hierarchy.
- Approval center and menu-approval mode when they affect access decisions.
- Commercial gateway integration, SSO/OAuth/LDAP/WeCom org sync, sensitive-word gateway filters, and rate/online limits.
- Cursor pagination patterns where permission filtering and DM8 keyset compatibility determine list correctness.

## Route sibling areas instead of duplicating them

- Use `backend-core` for generic FastAPI routes, schemas, service layering, and non-permission models.
- Use `frontend-apps` for React route guards and UI rendering after the backend permission contract is known.
- Use `knowledge-rag` for parser/vector/retrieval internals after visibility is proven correct.
- Use `workflow-engine` for graph execution after app visibility and permissions are proven correct.
- Use `deployment-maintenance` for running operational backfill/migration scripts.

## Non-negotiables

- New resource authorization must go through PermissionService/OpenFGA-aware services; do not add direct role-access table shortcuts.
- Resource creation must write owner/authorization tuples or enqueue failed tuple compensation as designed.
- ORM tenant filtering applies to SELECT; raw SQL and bulk update/delete require explicit tenant-safe handling.
- Use tenant bypass helpers only for intentional cross-tenant maintenance reads/writes.
- Cursor pagination under permission filtering must advance by the last DB row, not the last visible row.
- Frontend 403 and menu visibility bugs should not be patched until backend/menu/plugin permission data is understood.
