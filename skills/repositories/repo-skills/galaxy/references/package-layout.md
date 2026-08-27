# Galaxy Package Layout

## Purpose

Read this when a task depends on Galaxy's repository shape, split package metadata, import paths, or install strategy.

## Repository Shape

Galaxy is a Python/web monorepo with these practical surfaces:

| Surface | Use it for |
| --- | --- |
| `lib/galaxy` import package | Main server, managers, services, tools, workflows, datatypes, object stores, web apps, and public Python internals. |
| `lib/tool_shed` and `lib/tool_shed_client` | Tool Shed server/client implementation and repository metadata workflows. |
| `packages/*` split packages | Package-centric development and distribution of smaller Galaxy components such as `galaxy-util`, `galaxy-config`, `galaxy-tool-util`, and web/framework packages. |
| `doc/source` | Admin, API, developer, generated API, and testing guidance. |
| `scripts/` | Repo-maintained automation and examples; treat many as service- or checkout-specific evidence unless bundled by this skill. |
| `client/` | Vue/TypeScript web client, pnpm workspace packages, Vite, Vitest, and generated API client. |
| `test/`, `lib/galaxy_test`, `packages/*/tests`, `client/tests` | Native behavior evidence and verification candidates. |

## Version Signals

Galaxy has multiple version signals:

- Root package metadata can be a placeholder for the checkout workflow.
- Split package metadata under `packages/*/pyproject.toml` currently uses package versions such as `26.1.dev0` for many components.
- Source runtime version is exposed by `galaxy.version.VERSION`; for this generated skill baseline it reports `26.2.dev0`.

When diagnosing staleness, compare the current checkout's source version and split-package metadata against [repo-provenance.md](repo-provenance.md).

## Install Strategy

Use the smallest environment that matches the task:

1. For config/schema/tool-util inspection, install or use split packages such as `galaxy-util`, `galaxy-config`, `galaxy-schema`, and `galaxy-tool-util` plus their runtime dependencies.
2. For full server work, expect many dependencies, service assumptions, database state, optional storage backends, and possibly client build behavior.
3. For client work, use the `client/` pnpm workspace and do not mix it with Python package installation unless the task also needs backend startup.
4. For Tool Shed and integration tests, expect a running service/test harness rather than a pure import-only workflow.

The root checkout may not behave like a simple `pip install -e .` package in every generated or partial checkout. If editable root install fails due package discovery or generated split-package layout, switch to the package-specific workflow that matches the task instead of installing broad dev/test extras.

## Public Import Checks

Use import checks as orientation, not as proof that a full service is runnable:

```bash
python - <<'PY'
import galaxy.version
print(galaxy.version.VERSION)
PY
```

For tool-util and config work, useful module checks include:

```bash
python - <<'PY'
import galaxy.config
import galaxy.config.schema
import galaxy.tool_util.verify.script
import galaxy.tool_util.validate_test_format
print('galaxy package inspection ok')
PY
```

If an import fails because an optional dependency is missing, decide whether that dependency belongs to the selected workflow. Do not install all optional groups just to inspect an unrelated sub-skill.

## Split Package Cautions

- Split packages share the `galaxy` namespace; multiple editable installs can contribute modules to the same import package.
- Some package metadata refers to optional or service-heavy dependencies not needed for config/tool-util inspection.
- Package tests under `packages/*/tests` are useful when editing a specific split package, but a root task may need higher-level tests from `test/` or `lib/galaxy_test`.
- Full application packages can pull web, AI/provider, job, storage, and server dependencies; run them only when they are in scope.
