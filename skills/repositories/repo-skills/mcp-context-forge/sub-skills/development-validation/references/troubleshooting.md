# Development Validation Troubleshooting

## Multiple Alembic heads

Symptom: Alembic reports multiple heads or tests fail with migration head
errors.

Recovery:

1. Run `cd mcpgateway && alembic heads`.
2. Update the new migration's `down_revision` to the actual current head if it
   was guessed incorrectly.
3. Avoid merge migrations unless the branch genuinely needs one.
4. Re-run the head check and targeted migration tests.

## Migration depends on live settings

Symptom: downgrade behavior changes across environments or imports
`settings` in downgrade.

Recovery: snapshot required setting values into `migration_metadata` during
upgrade and read them back during downgrade. Clean up snapshot rows at the end
of downgrade.

## Auth/RBAC tests pass only on happy path

Symptom: a protected feature works for admin but lacks wrong-team or
public-only regression coverage.

Recovery:

- Add unauthenticated, wrong team, insufficient permission, and feature-disabled
  tests.
- Use canonical auth helpers and token-scoping semantics.
- Check route permission mappings default-deny protected paths.

## Admin UI changed but bundle is stale

Symptom: tests or runtime still show old JS/CSS behavior.

Recovery:

```bash
make build-ui
npx vitest run
make lint-web
make test-ui-smoke
```

Use targeted Playwright page tests for the changed Admin tab.

## detect-secrets fails on false positives

- Python files: prefer inline allowlist comments when they do not break doctest
  assertions.
- Doctest strings or other file types: regenerate/audit `.secrets.baseline`.
- Never resolve a baseline conflict by keeping a newly introduced real secret.

## Live MCP tests fail because stack is not running

Symptoms: connection refused, missing runtime headers, Redis/PostgreSQL not
ready, or Keycloak unavailable.

Recovery:

1. Start the appropriate compose stack.
2. Check `/health` headers before protocol tests.
3. Run the smallest live test that matches the changed path.
4. Document external dependency skips rather than marking them passed.

## Rust mode confusion

Symptom: tests expect Rust public transport but health shows Python mounted, or
vice versa.

Recovery: inspect both runtime and mounted transport headers. Rust shadow means
Rust is present internally while Python still owns the public path.

## Stale PR review notes

When running the fixed-point PR review workflow, reset ephemeral notes from the
template at the start of a new review. Do not carry prior-cycle state into a new
PR.

## Sync SQLAlchemy in async handlers flagged as bug

This repository intentionally uses synchronous SQLAlchemy sessions in async
FastAPI handlers/middleware. Do not convert isolated call sites to async
without a broader migration plan.

## Audit or observability rollback errors

If a CRUD operation commits then audit logging reuses the same request-scoped
session, later rollback can fail. Existing audit call sites should call audit
logging without passing the shared DB session unless a reviewed design change
requires atomic audit writes.
