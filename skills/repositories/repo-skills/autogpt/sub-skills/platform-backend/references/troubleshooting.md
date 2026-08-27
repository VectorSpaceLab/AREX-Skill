# Backend Troubleshooting

## Poetry install or import issues

Confirm Python satisfies the backend range and run commands from `autogpt_platform/backend`. If dependency installation succeeds but root package installation complains that the package cannot be found, treat it as a packaging-mode quirk and use the normal Poetry checkout workflow. Do not publish local path bootstraps or private environment commands in runtime docs.

## REST or WebSocket startup fails

REST and WebSocket lifespan startup connects to PostgreSQL and Redis, verifies auth settings, initializes blocks, runs graph/integration repair steps, and loads the LLM catalog. Check env files, service health, database URL, Redis URL, and catalog errors before debugging route code. Use import/help checks when services are not required.

## Auth or OpenAPI mismatch

For authenticated routes, use the repository auth helpers and `Security()` where OpenAPI security metadata matters. During tests, global fixtures can mock JWT payloads; if the test actually depends on user identity, override the auth dependency explicitly. If generated frontend hooks are wrong or absent, verify backend OpenAPI first and regenerate instead of editing generated frontend files.

## Prisma errors

Prisma failures usually come from missing migrations, stale generated client code, a wrong database URL, or a test harness that did not start its database. Run the migration/generation sequence for schema changes. Do not call destructive reset commands until the target database is confirmed disposable.

## Block tests hit providers

If `backend/blocks/test/test_block.py` starts contacting an external API, add or fix `test_mock`, `test_credentials`, and deterministic `test_output` for the block. Skip only when the block genuinely requires an external service and document why. Do not store real provider keys in tests.

## Workspace/media failures

Use `WorkspaceManager` for persistent user files and `store_media_file()` for block media normalization. A `workspace://` reference requires a workspace-aware execution context. Virus scanner failures are infrastructure failures; do not silently ignore them or bypass scanning.

## LLM catalog or model issues

The catalog is loaded during startup and is a single source of truth for costs, metadata, routing, and enabled state. A block-selectable model also needs an `LLMModel` enum entry. Retire models with the documented dry-run/migration CLI before rewriting stored graph nodes.

## Long-running or credentialed scripts

Transcript downloads, trace replay, analytics views, rate refreshes, store loading, and seed scripts may use credentials, network access, or database writes. Confirm data sensitivity and side effects before running them, and prefer help/dry-run modes where provided.
