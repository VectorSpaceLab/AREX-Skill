# Argilla package overview

Read this before choosing between the SDK, server-ops, and legacy-migration routes.

## What this skill covers

Argilla 2.x combines a Python SDK, a server package, a web UI/service stack, and legacy compatibility guidance:

- `argilla` Python SDK: client connection, datasets, settings, fields, questions, records, suggestions, responses, metadata, vectors, search/filter/similar, import/export, users, workspaces, markdown/media helpers, and webhooks.
- `argilla_server` package: FastAPI app, Typer CLI, database migrations/users, search-engine reindexing, worker process, Docker/Spaces startup behavior, OAuth/SSO, telemetry, and service configuration.
- Legacy migration: `argilla.v1` compatibility calls and migration recipes from Argilla v1/Rubrix task-specific datasets into current `rg.Settings` + `rg.Dataset` workflows.

## Package split

| Distribution/import | Role | Typical install/use |
| --- | --- | --- |
| `argilla` / `import argilla as rg` | Current Python SDK | `python -m pip install argilla`; needs an Argilla server for live operations |
| `argilla-server` / `import argilla_server` | Server package and FastAPI app | Most users deploy via Docker or Hugging Face Spaces; Python CLI is `python -m argilla_server` |
| `argilla-v1` / `import argilla_v1` plus `import argilla.v1 as rg_v1` shim | Legacy compatibility | Use only for migration or legacy maintenance; avoid broad old optional extras in current 2.x environments |
| Frontend web app | Argilla UI implementation | Not selected for this runtime skill; user-level UI behavior is covered through SDK/server docs |

## Dependency and environment notes

- Current SDK and server inspection used Python 3.11 with Argilla 2.8.0dev0.
- Current SDK constructors often require an API key or default client. Prefer explicit `rg.Argilla(api_url=..., api_key=...)`.
- `argilla-server` CLI in this snapshot works with Typer 0.9.x and Click 8.1.x. A symptom like `TypeError: Secondary flag is not valid for non-boolean flag` usually indicates an incompatible Click/Typer combination; see server troubleshooting.
- `argilla-v1` has older constraints such as `httpx<=0.26` and many optional ML integrations. Keep deep v1 inspection separate from the current server/SDK environment.
- Docker/Spaces/Kubernetes deployments require services or external infrastructure: database, Elasticsearch/OpenSearch, Redis, persistent storage, OAuth apps/secrets, and sometimes Hugging Face tokens.

## Selected extraction scope

This skill focuses on future-agent operation of public user-facing Argilla workflows:

- Current SDK dataset authoring and record workflows.
- Server deployment, CLI, configuration, and troubleshooting.
- Legacy v1/Rubrix migration into current 2.x.
- Safe bundled templates for SDK datasets, webhooks, server CLI checks, local Compose, and migration planning.

It intentionally excludes:

- Internal Nuxt/Vue frontend development.
- Repository CI/release/docs-generation internals.
- Heavy legacy training/monitoring/weak-supervision integrations.
- Old notebooks and examples that require credentials, network services, or long-running training.
- Live Docker/Kubernetes/server/HF Hub actions unless a user explicitly asks for those operations.

## Best route by task

- If the user wants code that creates or manipulates Argilla datasets, start with `python-sdk`.
- If the user wants a server, deployment configuration, OAuth, reindexing, or startup debugging, start with `server-ops`.
- If the user mentions v1, Rubrix, `DatasetForTextClassification`, `DatasetForTokenClassification`, `DatasetForText2Text`, or old dataset migration, start with `legacy-migration`.
- If the user asks for generic dataset processing with no Argilla server/UI/API involvement, do not force this skill; use a more general dataset-processing skill.
