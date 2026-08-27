---
name: argilla
description: "Use Argilla 2.x for human-feedback dataset annotation, Python SDK
  dataset workflows, server deployment/operations, webhooks, and legacy
  v1/Rubrix migration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Argilla repo skill

Argilla is a self-hosted/open-source collaboration platform for building high-quality datasets for AI projects. Use this skill when a task involves Argilla 2.x SDK code, annotation dataset schemas, record logging, search/filter/export, Argilla server deployment, webhooks, or migration from Argilla v1/Rubrix.

The source project is mature/stable; prefer current documented Argilla 2.x workflows for new work and route legacy APIs only through the migration sub-skill.

## Fast route map

| User request signal | Read this first | Why |
| --- | --- | --- |
| Create/configure an Argilla dataset, fields/questions/metadata/vectors, log records, map columns, query/filter/export, use users/workspaces, or build a webhook listener | [`sub-skills/python-sdk/SKILL.md`](sub-skills/python-sdk/SKILL.md) | Current Argilla 2.x SDK API and dataset-feedback workflows |
| Deploy or operate the server with Hugging Face Spaces, Docker Compose, Kubernetes/Helm, `python -m argilla_server`, database/search/Redis, OAuth/SSO, telemetry, proxy/base URL, or reindexing | [`sub-skills/server-ops/SKILL.md`](sub-skills/server-ops/SKILL.md) | Server package, CLI, service stack, config, and operational troubleshooting |
| Migrate old Argilla v1/Rubrix users, workspaces, or task-specific legacy datasets into Argilla 2.x | [`sub-skills/legacy-migration/SKILL.md`](sub-skills/legacy-migration/SKILL.md) | Safe v1 compatibility and dataset schema migration guidance |
| Check whether this skill matches a checkout/version | [`references/repo-provenance.md`](references/repo-provenance.md) | Source commit, package versions, evidence paths, and refresh baseline |
| Need a high-level capability/dependency overview before choosing a route | [`references/package-overview.md`](references/package-overview.md) | Monorepo layout, package split, selected/excluded scope, and dependencies |
| Cross-cutting install/import/API-url/service troubleshooting | [`references/troubleshooting.md`](references/troubleshooting.md) | Quick triage and route-to-sub-skill guidance |

## Minimal install and import checks

For current SDK-only workflows:

```bash
python -m pip install argilla
python - <<'PY'
import argilla as rg
print(rg.__version__)
print(rg.Argilla)
PY
```

For server operations, the server package is separate in source and deployments often use Docker/Spaces. If installed as a Python package, check it without starting services:

```bash
python - <<'PY'
import argilla_server
print(hasattr(argilla_server, "app"))
PY
python -m argilla_server --help
```

Run [`scripts/check_argilla_env.py`](scripts/check_argilla_env.py) for a safe local import/version check. Add `--check-server` only when the user intentionally wants a live API check and provides a reachable API URL/key.

## Operating rules

1. Treat Argilla as a service-backed package. Dataset creation, record logging, user/workspace changes, Hub import/export, webhook registration, server starts, migrations, reindexing, and deployment commands can mutate data or contact external services.
2. For SDK work, create an explicit `rg.Argilla(api_url=..., api_key=...)` client before constructing resources unless environment defaults are guaranteed.
3. For private Hugging Face Spaces, keep the Argilla API key separate from the Hugging Face bearer token header.
4. For deployment work, validate configs and render CLI help before starting Docker/Kubernetes/server processes or running migrations.
5. For legacy migration, export/back up first; do not install broad old `argilla-v1` extras into a current Argilla 2.x server environment.
6. Do not route frontend implementation changes, repository CI, docs-generation, or heavy old notebooks through this runtime skill.

## Bundled safe helpers

- [`scripts/check_argilla_env.py`](scripts/check_argilla_env.py) checks package importability and versions and optionally performs a live `client.me` check.
- [`sub-skills/python-sdk/scripts/build_dataset_template.py`](sub-skills/python-sdk/scripts/build_dataset_template.py) generates a dry-run-safe SDK dataset template.
- [`sub-skills/python-sdk/scripts/webhook_listener_template.py`](sub-skills/python-sdk/scripts/webhook_listener_template.py) provides a webhook listener skeleton that is dry-run by default.
- [`sub-skills/server-ops/scripts/check_server_cli.py`](sub-skills/server-ops/scripts/check_server_cli.py) renders safe `argilla_server` CLI help without starting services.
- [`sub-skills/server-ops/scripts/docker-compose.argilla.local.yaml`](sub-skills/server-ops/scripts/docker-compose.argilla.local.yaml) is an adapted local Compose template; replace sample credentials and validate before running.
- [`sub-skills/legacy-migration/scripts/legacy_migration_skeleton.py`](sub-skills/legacy-migration/scripts/legacy_migration_skeleton.py) prints a safe TODO-based migration plan/template.
