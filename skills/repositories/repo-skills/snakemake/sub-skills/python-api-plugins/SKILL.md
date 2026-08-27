---
name: python-api-plugins
description: "Use Snakemake 9.23.1 programmatically with SnakemakeApi,
  WorkflowApi, DAGApi, settings dataclasses, and plugin-aware settings."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Python API Plugins

Use this sub-skill when a task embeds Snakemake in Python, translates CLI behavior to API calls, constructs `SnakemakeApi` / `WorkflowApi` / `DAGApi`, passes settings dataclasses, or diagnoses executor, scheduler, storage, logger, or report plugin settings.

## Route by Need

- API lifecycle, settings dataclasses, CLI-to-API mappings, and safe embedding patterns: read [api-reference.md](references/api-reference.md).
- Plugin registry surfaces, settings object shapes, optional plugin imports, and executor/storage/report/logger/scheduler plugin handling: read [plugin-settings.md](references/plugin-settings.md).
- Common API and plugin failures: read [troubleshooting.md](references/troubleshooting.md).
- Safe local API dry-run and DAG/summary probe: run `python scripts/api_dryrun_example.py --help`.

## Fast Pattern

1. Prefer `with SnakemakeApi(output_settings=OutputSettings(...)) as snakemake_api:` so log handlers and workdir changes are cleaned up.
2. Build a `WorkflowApi` with explicit `ResourceSettings(cores=1)` for local dry-runs and a specific `snakefile`/`workdir` when embedding.
3. Build a `DAGApi` via `workflow_api.dag(DAGSettings(...))`, then call non-mutating methods (`printdag()`, `summary()`) or execute through `execute_workflow(executor="dryrun", execution_settings=ExecutionSettings(...))`.
4. Pass plugin settings as plugin-specific settings objects, not arbitrary dicts, and validate by letting the plugin registry raise a clear API error.
5. Do not add `--reason` when translating CLI examples; Snakemake 9.23.1 does not accept that flag, though dry-run output includes reasons.

## Boundaries

- Route ordinary CLI commands, profiles, targets, cores/jobs, scheduler flags, and dry-run recipes to `../execution-cli/SKILL.md`.
- Route storage-provider installation, deployment methods, conda/container behavior, archives, and source deployment to `../deployment-storage/SKILL.md`.
- Route config files, sample sheets, schemas, PEPs, and data-driven inputs to `../configuration-data/SKILL.md`.
- Route Snakefile syntax, rules, wildcards, modules, checkpoints, scripts, and wrappers to `../workflow-authoring/SKILL.md`.
- Route linting/report/test/debug artifact interpretation to `../debugging-reporting/SKILL.md` unless the user specifically needs the API method call.
