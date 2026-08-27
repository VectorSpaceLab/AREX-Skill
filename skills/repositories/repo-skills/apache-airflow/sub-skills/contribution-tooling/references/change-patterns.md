<!-- SPDX-License-Identifier: Apache-2.0 -->

# Change Patterns

Use this reference to decide what else must change with an Airflow repository edit.

## Universal Coding Rules

- Write **Dag** in prose, preserving literal tokens such as `DAG`, `dag_id`, `dag`, `airflow dags test`, and path names.
- Keep imports at module top level unless a documented exception applies: circular import avoidance, lazy loading for worker isolation, or `TYPE_CHECKING`.
- Use `time.monotonic()` for durations, not `time.time()`.
- No `assert` in production code.
- In `airflow-core`, functions that accept `session` use keyword-only `*, session` and must not call `session.commit()`.
- Do not add new direct `raise AirflowException(...)`; use a built-in exception or dedicated exception type.
- Translate domain exceptions to `HTTPException` at FastAPI route boundaries so missing rows and invalid input do not become `500` responses.
- Avoid unbounded bulk `DELETE` or `UPDATE` in scheduler loops or interval tasks. Batch with limits and commit between batches, and ensure cleanup filters are indexed.
- Name functions and methods with action verbs such as `get_`, `extract_`, `find_`, `compute_`, and `build_`.

## Documentation, News, and Changelogs

- Add or update docs when behavior, public APIs, config, CLI output, provider usage, chart parameters, or migration instructions change.
- Newsfragments are only for user-facing major or breaking changes in distributions that consume them: `airflow-core/newsfragments/`, `chart/newsfragments/`, and `dev/mypy/newsfragments/`.
- Do not add newsfragments for internal refactors, CI/build/release tooling, tests-only changes, or dev-only scripts.
- Never add provider newsfragments. For important user-visible provider changes, edit that provider's `docs/changelog.rst` directly just below the `Changelog` header. Routine provider features and fixes usually need no changelog edit because release managers derive entries from commits.
- Never add `airflow-ctl` newsfragments. For important `airflow-ctl` release notes, edit `airflow-ctl/RELEASE_NOTES.rst`.
- Task SDK user-facing changes ship through `airflow-core`, so use `airflow-core/newsfragments/` only when the change is truly user-visible and significant enough.

## Generated Files

Do not hand-edit generated files unless the source tree explicitly documents dependency edits as preserved inputs. Regenerate through hooks or scripts and commit the result.

Common generated surfaces:

- OpenAPI specs and clients under API codegen paths.
- UI generated OpenAPI clients under UI `openapi-gen/` paths.
- Task SDK generated models.
- Provider dependency files such as `generated/provider_dependencies.json`.
- Provider `pyproject.toml` files are generated from templates except documented dependency sections that are preserved; after provider dependency edits, run `prek update-providers-dependencies --all-files`.
- Migration reference filenames and docs are normalized by `prek update-migration-references --all-files`.

When generated files drift after code changes, run the relevant `prek` hook rather than manually patching the generated output.

## API and FastAPI Changes

For public API endpoints:

- Prefer reusable public endpoints over UI-only endpoints when the contract should be stable and community-facing.
- Place route handlers under the appropriate `api_fastapi/core_api/routes` public or UI area.
- Use explicit Pydantic response models and typed query/body parameters so OpenAPI docs are generated accurately.
- Add tests for query parameters, permissions, error handling, response models, and pagination/filtering behavior.
- Run `prek` after route/model changes so persisted OpenAPI specs are regenerated.
- If a generated OpenAPI spec or generated client changes, expect broad CI impact.

Execution API changes have an extra versioning contract:

- Any schema or behavior change that affects existing clients requires a Cadwyn version migration.
- Version modules use `vYYYY_MM_DD` naming based on the expected Airflow release date.
- Core execution logic should remain version-agnostic; migrations adapt older clients.
- Add tests for both the latest head model and the version-specific migration behavior.

## CLI Changes

Airflow ships two CLIs:

- `airflow`: core CLI for legacy commands and admin/local operations that have no Public API equivalent.
- `airflowctl`: standalone CLI that talks to a running Airflow instance through the Public API.

Decision rules:

- New remote functionality achievable through the Public API belongs in `airflowctl`, not duplicated in `airflow`.
- Existing `airflow` remote commands that are Public API-achievable should delegate through the `airflowctl` HTTP client/operations layer rather than directly touching the metadata DB.
- Admin/local commands without a reasonable Public API representation can stay in `airflow`.
- Add `airflow-ctl/tests/` coverage for new `airflowctl` commands and `airflow-core/tests/cli/` coverage when rewiring existing `airflow` commands.

## Metadata Database Migrations

When ORM/schema changes require a migration:

```bash
breeze generate-migration-file -m "short migration message"
prek update-migration-references --all-files
```

Rules:

- Do not reference ORM classes inside migration scripts; migrations must remain stable after models evolve.
- Expect migration filenames and migration references to be normalized by `prek`.
- When rebasing migration conflicts, resolve non-migration conflicts first, then run `prek update-migration-references --all-files` and stage the generated updates.
- SQLite parent-table rebuild migrations using `op.batch_alter_table` need foreign-key round-trip safety. Keep the disable-FK wrapper around the entire body before DML/DDL opens an implicit transaction.
- Run the relevant migration CI command from the workflow when a migration changes upgrade/downgrade behavior.

## Provider Changes

Provider packages are independent distributions under `providers/<provider>/`.

Keep these surfaces synchronized:

- `provider.yaml` metadata, including integrations, connection types, hooks, operators, sensors, transfers, extra links, auth backends, logging handlers, and dependency metadata.
- Provider `pyproject.toml` dependency and optional-extra sections.
- Provider docs under `providers/<provider>/docs`.
- Provider unit/integration/system tests under `providers/<provider>/tests`.

Provider rules:

- Do not upper-bound dependencies by default; add upper bounds only with strong justification.
- When adding dependencies, update the provider dependency source and run `prek update-providers-dependencies --all-files`; rebuild the Breeze CI image if dependency changes require it.
- For optional packages not installable in default CI, keep them in provider optional dependencies and use the documented pre-extras install manifest flow when needed; do not add them as unconditional runtime dependencies.
- Provider `Connection.extra` values must be allowlisted. Never pass `**conn.extra_dejson`, loop all extras into kwargs, or let connection editors control arbitrary client/library options.
- Example Dags should be clear, modern, parse cleanly, avoid secrets, document required external dependencies, and demonstrate one feature or concept.
- Breaking provider changes need clear communication in `docs/changelog.rst` with a migration path.

## UI Changes

For React/TypeScript UI work:

- Use strict TypeScript; do not use `any` or suppress type errors.
- Use configured aliases (`src/*`, `openapi/*`, `tests/*`) instead of deep relative imports.
- Use generated OpenAPI clients; do not hand-write raw `axios` API calls.
- Reuse existing translation keys; do not add placeholder English strings to non-English locale files.
- Use `react-icons`, preferring existing dominant icon sets before adding a less common set.
- Place reusable app components in `src/components/`; reserve `src/components/ui/` for customized Chakra components.
- Do not add manual `useMemo` or `useCallback`; the React compiler handles memoization.
- UI-only source changes can select UI checks without Python unit tests, but API contract changes can force broad regeneration and CI.

## Helm Chart Changes

Before adding or moving chart parameters/components, decide whether the feature belongs in the chart or a Kustomize overlay:

- Belongs in the chart only when it is required to run Airflow, removal would require Airflow config changes, and it has no external owner.
- Belongs in Kustomize if it can be standalone Kubernetes resources, is environment-specific, has an external owner, or requires CRDs the chart does not install.
- A component that qualifies for Kustomize stays in the chart until a working overlay exists; never remove a chart component without a replacement overlay.
- Defaults should be sensible and least-privilege at chart level.
- Changes to chart templates, values, docs, or schemas usually need Helm tests and documentation/schema updates.

## CI, Prek Hook, and Dev Tooling Changes

- Changes to `dev/breeze/src`, `scripts/ci`, workflows, Dockerfiles, or generated provider dependencies have broad CI blast radius.
- If selective-check behavior changes, update both the implementation and the selective-check docs in the same PR, and adjust tests for selective checks.
- New `dev/` scripts should be Python scripts with inline script metadata and should be documented with `uv run` invocations.
- New prek hook scripts should reuse `scripts/ci/prek/common_prek_utils.py`, be registered in the appropriate pre-commit config, and place slow Breeze-dependent hooks near the end.

## Security Review Checklist

Flag or avoid:

- Scheduler paths that execute Dag/user code.
- Task execution code that accesses the metadata DB directly instead of the Execution API.
- Provider code importing core internals or worker supervisor plumbing.
- SQLAlchemy relationship access in loops without eager loading.
- Queries on `run_id` without `dag_id`.
- Mapped task instance queries that omit `map_index`.
- Database-specific SQL without cross-DB handling for PostgreSQL, MySQL, and SQLite.
- Files, connections, or sessions opened without a context manager or `try/finally`.
- Unbounded caches such as `@lru_cache(maxsize=None)`.
- Heavy multi-process imports that are not guarded by `TYPE_CHECKING`.
