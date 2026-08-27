# Testing and Maintenance

This reference condenses ZenML repository maintenance rules for future agents. It assumes work happens inside an active ZenML checkout, but runtime skill content stays self-contained and does not depend on original documentation files.

## Maintenance Workflow

1. Identify changed areas and read the nearest AGENTS guidance that applies to every touched file. Root guidance applies repository-wide; nested guidance adds rules for docs, CLI, models, orchestrators, integrations, server, stores, schemas, and migrations.
2. Make focused changes only. Do not fix unrelated failures or mix feature work with broad whitespace/style churn.
3. Add or update tests when behavior changes and an adjacent test pattern exists. Integration-heavy external-service changes may need local/manual verification instead of broad automated tests.
4. Run the smallest useful checks first, then broaden only when confidence or review risk requires it.
5. Summarize checks run, checks skipped, why they were skipped, docs/test impact, and PR label expectations.

## Branch and PR Expectations

- Development targets `develop`, not `main`.
- PRs should be small, focused, and should follow the repository PR template.
- Every PR needs exactly one release-notes label: `release-notes` for user-facing changes or significant bug fixes, `no-release-notes` for internal maintenance, CI, docs-only, minor refactors, or non-user-facing work.
- Mention when full CI or slow CI is appropriate, especially for core execution, integrations, migrations, containers, server behavior, or dependency changes.

## Choosing Checks

Use the bundled selector for a first-pass command list:

```bash
python skills/zenml/sub-skills/maintenance/scripts/choose_targeted_checks.py src/zenml/client.py tests/unit/test_client.py
```

The helper prints recommendations only. Review its output against the actual change and user constraints before running anything.

### Safe Local Defaults

- Python syntax and imports for changed Python files: `python -m py_compile <files>`.
- Focused tests: `pytest <specific test file>` or `pytest <test file>::<test_name>`.
- Formatting for touched paths: `bash scripts/format.sh <paths>`.
- Lint/type checks for touched source areas: `ruff check <paths>`, `ruff format <paths> --check`, and `mypy <src paths>`.
- Spelling for docs/code text changes: `bash scripts/check-spelling.sh` when dev tooling is installed.

Avoid `pytest` with no path and avoid whole `tests/unit` or `tests/integration` unless the user explicitly asks or the change is broad enough to justify the time.

## Script Catalog

| Need | Maintainer-context command | Notes |
| --- | --- | --- |
| Format changed code/docs/workflows | `bash scripts/format.sh <paths>` | Mutates files; use scoped paths. Add `--no-yamlfix` when YAML tooling is unavailable or on Windows-like environments. |
| Full lint stack | `bash scripts/lint.sh` | Broad and dependency-heavy; prefer targeted `ruff`, `pydoclint`, and `mypy` first. |
| CI-like local checks | `bash scripts/run-ci-checks.sh` | Runs lint and spelling; broad and should usually be final, not iterative. |
| Unit test | `pytest tests/unit/path/to/test_file.py` | Preferred validation for most logic changes. |
| Integration test | `pytest tests/integration/path/to/test_file.py` | Use only for targeted integration behavior; may require extras, Docker, services, or credentials. |
| Test harness environment list | `./zen-test environment list` | Read-only discovery, but provisioning is mutating. |
| Provision integration environment | `./zen-test environment provision <name>` | Starts services and may build images; ask before running. |
| Migration branch check | `bash scripts/check-alembic-branches.sh` | Requires Alembic from local/server extras. Use after migration changes. |
| Migration replay | `bash scripts/test-migrations.sh` or manual `alembic upgrade head` | Expensive and mutating; use for schema/migration changes after setup. |
| Security scan | `bash scripts/check-security.sh` | Depends on dev/security tools and may be broad. |
| Typos | `bash scripts/check-spelling.sh` | Enforces US English spellings. |

## Area-Specific Guidance

### CLI and Client

- CLI list filters are coupled to Client method signatures. When adding a filter field, update the filter model, the Client method parameter list, and the filter-model instantiation inside the Client method.
- Do not import integration SDKs, server modules, or SQL schemas at CLI module top level.
- Validate CLI changes with a focused unit test and, when practical, command help or CliRunner coverage.

Suggested checks:

```bash
pytest tests/unit/cli/<target_test>.py
ruff check src/zenml/cli tests/unit/cli
mypy src/zenml/cli src/zenml/client.py
```

### Models, Stores, and Server

- Domain models, ORM schemas, store methods, client methods, CLI commands, migrations, and docs often need synchronized updates.
- Code outside server internals must not import from server modules; client/core code should use shared models and `Client` abstractions.
- Code outside store internals should not import SQL schemas directly; use `Client` or `client.zen_store` with dependency checks.
- FastAPI route work should keep synchronous `def` handlers where repository guidance requires it and should rely on dependency injection rather than new module-level mutable globals.

Suggested checks:

```bash
pytest tests/unit/zen_stores/<target_test>.py
pytest tests/unit/zen_server/<target_test>.py
ruff check src/zenml/models src/zenml/zen_stores src/zenml/zen_server tests/unit
mypy src/zenml/models src/zenml/zen_stores src/zenml/zen_server
```

### Integrations and Optional Dependencies

- Flavor files must not import optional integration libraries at module level. Use standard library, Pydantic, and ZenML core types in flavor configs; import implementation classes inside `implementation_class` properties; use `TYPE_CHECKING` for optional implementation type hints.
- Integration implementation modules may import their SDKs because they load only when the integration is used.
- Dependency bounds should support the declared Python range and avoid unbounded upper versions. Dropping support for an old dependency version is breaking and should be documented.

Suggested checks:

```bash
pytest tests/integration/integrations/<integration>/<target_test>.py
ruff check src/zenml/integrations/<integration> tests/integration/integrations/<integration>
mypy src/zenml/integrations/<integration>
```

Run the optional-import checker from the stacks-and-integrations sub-skill when flavor imports changed.

### Orchestrators and Step Operators

- `get_orchestrator_run_id()` must return one stable ID for all steps in a pipeline run and a unique ID across runs.
- Dynamic pipeline child runs, retries, and resumed execution require stable child keys and orchestration IDs.
- New step operators should implement submit/status/wait/cancel and persist backend job IDs immediately after submission.

Suggested checks:

```bash
pytest tests/unit/orchestrators/<target_test>.py
pytest tests/unit/execution/pipeline/dynamic/test_child_pipelines.py
ruff check src/zenml/orchestrators src/zenml/integrations/<integration>
mypy src/zenml/orchestrators src/zenml/integrations/<integration>
```

### Migrations

- Database schema changes require Alembic migrations unless the change is intentionally non-schema-only.
- Never edit existing migrations that already belong to `main`/`develop`; create a new migration with a descriptive message.
- Test upgrade paths from existing data where practical. Downgrade support is usually not required.
- Run branch checks after adding migrations.

Suggested checks:

```bash
bash scripts/check-alembic-branches.sh
alembic upgrade head
pytest tests/unit/zen_stores/<target_test>.py
```

## Dependency and Environment Notes

Install local development dependencies only when the user permits environment mutation:

```bash
pip install -e ".[server,dev]"
```

Some tests require integrations. The broad installer can install many optional packages and may take a long time; prefer the smallest extra or integration package needed for the changed area. If dev dependencies are missing, report the missing tool and recommend the minimal install rather than silently broadening scope.

## CI Mapping

- Fast CI covers basic unit tests, linting, type checks, spelling, and docs-related checks.
- Slow/full CI is appropriate for broad integrations, external services, server deployments, tutorial pipelines, templates, containers, and expensive end-to-end behavior.
- Dependency audit, CodeQL, Trivy, zizmor, spellcheck, markdown links, release-label enforcement, and docs publishing have separate workflows; run local equivalents only when relevant and safe.

## What Not To Do

- Do not run the entire suite by default.
- Do not provision Docker/server/integration environments without explicit user approval.
- Do not edit generated docs output when source docs or docstrings are the real source.
- Do not introduce top-level optional SDK imports into CLI, core, flavor, or server-disconnected code.
- Do not leak tokens, secret values, config paths, local env paths, or private checkout paths in logs or PR summaries.
