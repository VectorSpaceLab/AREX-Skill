---
name: repo-maintenance
description: "Maintain the Langflow monorepo safely across tests, formatting,
  generated files, versioning, migrations, releases, docs, and CI-adjacent
  checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Langflow Repo Maintenance

Use this sub-skill for repository-wide Langflow maintenance: setup, focused validation, formatting, linting, package/workspace version updates, generated artifacts, Alembic and extension migration guardrails, docs checks, and CI-style safety checks.

## Route First

- Use this sub-skill for `make init`, backend/frontend test selection, `uv` sync caveats, formatting, generated component indexes, docs builds, package version updates, migration guards, release checks, and CI helper failures.
- Route production runbooks, Docker Compose, cloud deployment, storage volumes, runtime secrets, and operational environment variables to `../deployment-and-operations/SKILL.md`.
- Route Python component class design, inputs/outputs, bundles, and component-specific tests to `../component-development/SKILL.md`.
- Route FastAPI route/service/auth/database implementation details to `../backend-runtime/SKILL.md` after this sub-skill helps choose checks.
- Route `lfx run`, `lfx serve`, and executor behavior to `../executor-cli/SKILL.md`; route SDK client implementation to `../sdk-and-api-clients/SKILL.md`.

## Maintenance Workflow

1. Classify the touched area: root package metadata, backend/base, `lfx`, SDK, frontend, docs, migrations, generated artifacts, or bundle/extension policy.
2. Read [references/maintainer-checks.md](references/maintainer-checks.md) for setup, generated-file, migration, versioning, docs, and CI-style guardrails.
3. Read [references/testing-and-formatting.md](references/testing-and-formatting.md) to choose the smallest safe command set before broad test runs.
4. Use [references/troubleshooting.md](references/troubleshooting.md) when install/imports, optional dependencies, config/schema, CLI/API usage, backend/runtime, or environment boundaries fail.
5. Run the bundled deprecated-import checker when changing components, bundles, or LangChain import paths:

```bash
python scripts/check_deprecated_imports.py
python scripts/check_deprecated_imports.py src/lfx/src/lfx/components src/bundles --format github
```

## Common Command Map

```bash
make check_tools
make init
make backend
make frontend
make format_backend
make format_frontend
make format_frontend_check
make unit_tests args="src/backend/tests/unit/services/authorization/test_guards.py -q" async=false
make lfx_test args="tests/unit/cli/test_validate_command.py -q"
make sdk_test args="tests/test_serialization.py -q"
make test_frontend_file src/__tests__/path/to/test.test.tsx
make build_component_index
make alembic-check
make docs_build
make patch v=1.10.2
```

Prefer focused commands while iterating, then broaden to package-level checks before handoff. Always use `uv run` or Make targets for Python commands in this workspace.

## Safety Rules

- Do not rename released component classes, mutate persisted flow identifiers, or remove migration-table entries without an explicit compatibility plan.
- Do not run credentialed provider tests, live external services, GPU/transformer workloads, Docker/cloud deployment, package publishing, or destructive database migration commands unless the user explicitly asks and the environment is safe.
- Before package-specific tests in `src/backend/base`, `src/lfx`, or `src/sdk`, sync that package's dev dependencies; the root workspace sync may not install all package-local test extras.
- For generated files, rebuild with the repository command and review the diff; do not hand-edit generated frontend bundles, component indexes, lockfiles, or migration tables unless the generator/guard says so.

## Evidence Distilled

This guidance is distilled from Langflow maintainer docs, development setup docs, root and frontend Make targets, Python workspace metadata, package Makefiles, migration and CI helper scripts, backend/LFX/SDK/frontend test layouts, installed package facts, and existing repo-agent instructions. Runtime files here are self-contained; source paths named in prose are evidence names, not required reading for future agents.
