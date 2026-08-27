---
name: open-api-and-cli
description: "Use SwanLab's object-oriented Api and swanlab api CLI for
  metadata, filters, runs, metrics, media, logs, and exports."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SwanLab Open API and CLI

Use this sub-skill when the task is to read or manage SwanLab cloud/self-hosted
metadata through `swanlab.Api` or the `swanlab api` command group.

## Route here for

- `swanlab.Api` construction, credential-safe query patterns, entity factories,
  `ApiResponseType`, lazy entity `.wrapper()` calls, and JSON payload handling.
- User, workspace, project, run/experiment, self-hosted instance, and admin
  metadata queries.
- Project/run path validation, project-name validation, filters, groups, sorts,
  pagination, summaries, metric key listing, scalar metrics, media metrics, logs,
  and export URL flows.
- `swanlab api ... --help` and non-interactive CLI use with `--host`,
  `--api-key`, `--save`, paging flags, filter JSON, and range flags.

## Route away

- Credential storage, `swanlab login`, mode selection, settings files, and host
  precedence belong to the settings-and-modes sub-skill.
- Creating experiment runs or logging scalars/media from training code belongs to
  the experiment-tracking or media-and-custom-charts sub-skills.
- Syncing local/offline run directories or converting TensorBoard/W&B/MLflow
  records belongs to the sync-and-converters sub-skill.

## First reads

1. Read [references/api-reference.md](references/api-reference.md) for the Python
   object model, path shapes, filters/sorts/groups, pagination, metrics, logs,
   CSV/export URL behavior, and self-hosted admin checks.
2. Read [references/cli-reference.md](references/cli-reference.md) for command
   names, common flags, JSON output, safe help checks, filter JSON, and
   non-interactive usage.
3. Read [references/troubleshooting.md](references/troubleshooting.md) when a
   path, API key, host, HTTP status, filter query, pagination, self-hosted
   permission, or CLI automation problem appears.
4. Run [scripts/check_api_validation.py](scripts/check_api_validation.py) after
   editing this sub-skill or when you need a no-network sanity check of the
   validation contracts.

## Operating checklist

- Validate path shape before making remote calls: workspace is one segment,
  project is `workspace/project`, and run is `workspace/project/run`.
- Treat `Api()` construction and any entity property/wrapper/iterator as
  network-capable. Only CLI help and bundled validation helpers are intended to
  be safe without credentials.
- Prefer `series()`, `metrics()`, `summary()`, `medias()`, `logs()`, and
  `export_logs()` for current run data workflows. `column()` and `columns()` are
  deprecated compatibility surfaces.
- For CLI automation, use explicit arguments and flags; do not rely on prompts.
  Help commands are safe, but query commands need valid credentials and network
  access.
