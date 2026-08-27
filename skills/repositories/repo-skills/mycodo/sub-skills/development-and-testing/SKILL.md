---
name: development-and-testing
description: "Maintain Mycodo source, tests, docs, API, database migrations,
  translations, and CI-safe development loops."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Mycodo Development and Testing Sub-skill

Use this sub-skill when acting as a Mycodo maintainer/developer: locating source owners, changing Flask web UI/API/forms/templates/static assets, adding or modifying database models and Alembic migrations, refreshing generated docs/manual pages, selecting safe tests, and diagnosing development failures.

This sub-skill is CPU/source-inspection oriented. This production run did **not** verify Raspberry Pi GPIO/I2C/UART/1-Wire/Bluetooth/camera hardware, systemd/nginx/InfluxDB services, Docker orchestration, backup/restore flows, or full installer execution. Treat those as unverified until a user provides hardware/service authorization and evidence.

## First decisions

1. Identify the change surface:
   - Flask page/route/form/template/static: use the source map, then the API/database reference if data or API behavior changes.
   - REST API endpoint: use the API/database reference and run focused API checks.
   - Inputs, Outputs, Functions, Actions, Widgets module metadata: use the source map and docs-generation sections.
   - database schema or settings DB behavior: use the Alembic/model workflow before editing forms/routes.
   - docs/manual/translations: use the testing-and-docs reference.
2. Decide whether the check can be software-only. If it requires GPIO/I2C/UART/1-Wire/Bluetooth/camera, InfluxDB, systemd/nginx, Docker, network, credentials, or installer mutation, stop and ask for explicit environment approval.
3. Prefer bundled helper checks over broad native scripts or full CI emulation. The helper never runs manual hardware tests by default.

## Read/run map

- Read [references/source-map.md](references/source-map.md) when you need to locate code owners, understand Mycodo's source layout, refresh version/provenance facts, or decide which source modules are coupled.
- Read [references/testing-and-docs.md](references/testing-and-docs.md) when selecting tests, distinguishing software tests from manual hardware tests, regenerating manual/API docs, updating translations, or mapping a change to CI-like checks.
- Read [references/database-and-api-development.md](references/database-and-api-development.md) before changing SQLAlchemy models, Alembic migrations, Flask-RESTX API resources, auth/media-type behavior, or web UI routes/forms/templates that persist data.
- Read [references/troubleshooting.md](references/troubleshooting.md) when a focused check fails, dependency claims are unclear, generated docs drift, API responses differ from expectations, or a requested validation wants hardware/services.
- Run [scripts/run_selected_checks.py](scripts/run_selected_checks.py) from any Python environment with Mycodo's base/testing dependencies installed. It accepts `--repo-root` and prints every command before executing it with a timeout.

## Safe helper examples

```bash
python path/to/development-and-testing/scripts/run_selected_checks.py --repo-root /path/to/Mycodo
python path/to/development-and-testing/scripts/run_selected_checks.py --repo-root /path/to/Mycodo upgrade-check pytest-abstract-input
python path/to/development-and-testing/scripts/run_selected_checks.py --repo-root /path/to/Mycodo pytest-custom-function-update --timeout 180
python path/to/development-and-testing/scripts/run_selected_checks.py --repo-root /path/to/Mycodo --dry-run pytest-flask-api-readonly
```

Default behavior is `import-smoke` only. Add explicit check names for focused pytest selections. Do not use this helper as proof of hardware, InfluxDB service health, Docker, installer, backup/restore, or production web UI availability.

## Maintenance operating rules

- Use Mycodo terminology exactly: Inputs, Outputs, Functions, Actions, Widgets, Dashboards, PID, Conditional, Trigger, InfluxDB, daemon, web UI.
- Keep edits minimal and in the owning layer. Routes should delegate persistence/service work to `utils_*` helpers; forms should define validation and choices; templates should render and submit; models should own schema; Alembic should own schema evolution.
- For web UI changes, consider the full chain: route, form, template/static JavaScript, `utils_*` mutator, SQLAlchemy model, permissions, flash/JSON messages, and any daemon/client side effect.
- For API changes, preserve `/api` prefix, Flask-RESTX namespace ownership, `application/vnd.mycodo.v1+json` media type, X-API-KEY authentication path, and error response conventions.
- For module catalog changes, update module `*_INFORMATION` metadata and corresponding parser assumptions. A metadata change can affect Add dropdowns, dependency prompts, generated Supported-* docs, measurements/channels, and daemon controller startup.
- For database changes, do not rely on `db.create_all()` as a migration substitute. Add an Alembic revision, update model defaults, check upgrade/downgrade behavior, and update version/provenance notes when release version facts change.
- For docs/manual changes, identify whether the file is hand-authored, generated from module metadata, generated from `docs_templates`, generated from pybabel translations, or generated from the API schema. Edit the owner, not only the output.
- For translations, add or preserve `gettext`/`lazy_gettext` strings in source, regenerate catalogs only in an environment with Babel tooling, and avoid machine-translating `.po` content unless asked.
- For dependencies, distinguish base requirements, testing requirements, docs requirements, and module-specific `dependencies_module` declarations. Do not run dependency installers, apt, npm global installs, or system service changes without explicit approval.
- For version/provenance refresh, reconcile README latest version, `MYCODO_VERSION`, `ALEMBIC_VERSION`, the newest Alembic revision, changelog top release, CI Python version, and dependency pins.

## Focused edit-test loops

- Import or pure Python change: run `import-smoke`; add `upgrade-check` if Python-version compatibility matters.
- Input base/controller behavior: run `pytest-abstract-input`; if changing shared Input iteration/read semantics, also run the broader input software tests after confirming dependencies.
- Custom Function update behavior: run `pytest-custom-function-update`; verify no production custom directory or daemon restart occurs during tests.
- REST API endpoint behavior: read the API/database reference, update tests or expectations for Accept headers/auth/permissions, then run `pytest-flask-api-readonly` or a narrower endpoint-specific pytest selection.
- Database model/migration: read the Alembic workflow, validate against a temporary database copy, then run focused Flask/API tests that exercise the new field.
- Module metadata and generated docs: run an import/parse smoke first, regenerate only the owned generated docs, and inspect the generated diff for Inputs, Outputs, Functions, Actions, Widgets naming and dependencies.
- Translations/templates/static: run import-smoke plus the smallest web UI endpoint/template test that renders the changed page; regenerate message catalogs only when Babel tooling is present.

## Hard stops

Stop and ask before any of these actions:

- Running manual hardware tests or code that touches Raspberry Pi GPIO/I2C/UART/1-Wire/Bluetooth/camera devices.
- Starting/stopping systemd services, changing nginx, changing InfluxDB, running full installers/upgraders, Docker compose flows, backup/restore scripts, or commands requiring sudo.
- Installing apt packages, global npm tools, or broad optional device dependencies.
- Mutating a real installed Mycodo database or `/opt/Mycodo` instance without a backup and explicit user authorization.
- Treating CPU/source-inspection success as proof of hardware, daemon, web UI deployment, or InfluxDB service behavior.

## Handoff checklist

When you finish a development task, report changed source surfaces, focused checks run, generated docs/translations/migration files refreshed, hardware/service/installer/Docker/backup/restore gaps, and version/provenance fields that should be refreshed before release.
