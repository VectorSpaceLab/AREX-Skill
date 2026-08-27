# Cross-cutting troubleshooting

Use this file when the failure spans multiple Observal layers or when the correct owner is unclear. Then route to the closest sub-skill for detailed recovery.

## First triage

1. Identify whether the symptom is CLI, server, harness telemetry, web, or repo-policy/build.
2. Check auth/server reachability before blaming hooks or frontend state.
3. Prefer read-only diagnostics first: `observal auth status`, `observal scan`, `observal doctor`, helper scripts, route import checks, and focused tests.
4. After uncertain mutation failures, read current state before retrying.
5. Record skipped heavy checks such as Docker, E2E, live services, or network refreshes.

## Owner map

| Symptom | Likely owner | First action |
| --- | --- | --- |
| CLI command missing, help path wrong, JSON polluted by Rich output, prompt blocks automation | `cli` | Read `sub-skills/cli/references/command-workflows.md` and run the CLI contract helper. |
| Server route import failure, API auth or model/schema mismatch, ClickHouse/Postgres migration confusion | `server` | Run server route helper and read server troubleshooting. |
| `observal scan`/`doctor patch` misses a harness, sessions do not reconcile, parser output is wrong | `harness-telemetry` | Run harness registry helper and follow telemetry pipeline troubleshooting. |
| React page does not load, token refresh loops, hardcoded harness list, route not found, UI types drift | `web` | Run web contract helper and read web troubleshooting. |
| Which tests/docs/skills/screenshots/changelog policy apply, or pre-commit/license/release failure | `repo-development` | Run repo inspector and read testing/quality plus repo scripts references. |

## Common recovery patterns

### CLI and bundled skills drift

Symptoms:
- A command was added/renamed but `/observal` guidance still documents old syntax.
- Command help examples do not match actual flags.
- JSON mode emits banners or tables.

Recovery:
1. Update command docstrings/help with canonical paths.
2. Ensure `OutputMode` and `output_json` are used for structured output.
3. Update the matching CLI docs and bundled skill files.
4. Regenerate the command reference with `make sync-skill`.
5. Run focused CLI tests and `tests/test_observal_skill*.py`.

### Backend import or route failure

Symptoms:
- Importing route registry fails.
- New route does not appear in OpenAPI or web calls 404.
- Auth route accepts stale or wrong credentials.

Recovery:
1. Confirm the owning router is imported by `routes.py` or its package `_router.py`.
2. Use `api.deps` auth dependencies and JWT bearer model unless the design explicitly changes.
3. Keep route schemas in `schemas/` and DB operations in services/models.
4. Run `python sub-skills/server/scripts/check_server_routes.py --server-path . --pretty`.
5. Add focused route/service tests with mocked Redis, ClickHouse, network, and LLM boundaries.

### Migration boundaries

Symptoms:
- ClickHouse DDL appears in startup code.
- Alembic revision chain forks or duplicates.
- Tests fail around retention/resource tuning/migration jobs.

Recovery:
1. Put PostgreSQL changes in Alembic revisions.
2. Put ClickHouse changes in numbered SQL files under the ClickHouse migrations directory and use the ClickHouse migration runner.
3. Run the migration-chain checker and focused migration tests.
4. Do not use runtime startup code for new schema creation.

### Harness telemetry missing sessions

Symptoms:
- Doctor says hooks are patched but no sessions appear.
- Reconcile finds files but parser output is empty or malformed.
- Layer hashes or managed file attribution are wrong.

Recovery:
1. Verify CLI config/auth and server reachability.
2. Run `observal scan` and `observal doctor` for the target harness.
3. Check harness registry capability, adapter files, hook specs, session parser id, and layer config through the harness helper.
4. Ensure MCP commands are direct; do not introduce telemetry wrappers or OTLP env vars.
5. Check local outbox/retry behavior before declaring hook delivery broken.

### Frontend API/auth issues

Symptoms:
- 401 loop after refresh.
- Component hardcodes harness capabilities.
- UI compiles but uses inline response types or raw colors.

Recovery:
1. Verify `web/src/lib/api.ts` auth storage split and refresh behavior.
2. Fetch harness metadata through server config and `useHarnesses()`.
3. Add shared response types to the central type barrel or feature type module.
4. Use OKLCH semantic tokens from the stylesheet.
5. Run typecheck and targeted Playwright list/spec only when the stack is available.

### Heavy checks requested accidentally

If a task does not require live databases, Docker Compose, browser automation, external accounts, or network refreshes, do not run those by default. Use root tests and static helpers. If a live check is necessary, state the prerequisite and run the smallest command that proves the behavior.
