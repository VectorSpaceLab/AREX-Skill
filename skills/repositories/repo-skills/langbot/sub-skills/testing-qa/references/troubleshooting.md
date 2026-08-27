# Testing and QA Troubleshooting

## `uv run` Changes the Environment

Use `uv run --no-sync` after local SDK installation. Otherwise the resolver may
restore pinned dependencies.

## Focused Test Imports Fail from Circular Dependencies

Some tests use lazy imports to avoid circular import issues. Prefer existing
fixtures and import helpers instead of adding top-level imports that reintroduce
cycles.

## PostgreSQL or Vector Tests Skip

Check required service env vars and service availability. Skips are acceptable
for unrelated changes but not for a task that claims to verify that backend.

## Box Integration Skips

Real Box integration requires Docker/Podman and socket access. If Docker is
installed but tests skip/fail, check current-user socket permission.

## Frontend E2E Fails Before Test Logic

Confirm `pnpm install`, browser availability, mocked backend/Space APIs, and
test server startup before diagnosing product behavior.

## `lbs` Plan Shows `manual_check`

Do not mark the case pass until the listed preconditions/setup items were
checked in the same run and all evidence requirements were collected.
