---
name: prefect
description: "Route Prefect SDK, CLI, server, deployment, event, client,
  settings, and repository-development tasks to focused self-contained
  guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Prefect Repo Skill

Use this skill for Prefect, the Python workflow orchestration platform. It helps future agents author workflows, operate the CLI/server, create deployments and workers, use Python clients/settings, work with events/blocks/assets, and safely modify the Prefect repository.

## Start Here

1. Confirm the package or checkout matches this skill with [references/repo-provenance.md](references/repo-provenance.md) before relying on version-specific details.
2. For installation, use `pip install -U prefect` or `uv add prefect`; for repository development use the repo's `uv`/`just` workflows from `repo-development`.
3. Run the read-only bundled checker when diagnosing an environment:

```bash
python scripts/check_prefect_environment.py --check-cli --json
```

4. Choose the focused sub-skill below. Keep root guidance for routing, shared install/API troubleshooting, and cross-skill decisions.

## Route By Task

| Task | Read |
| --- | --- |
| Write or debug `@flow` / `@task` code, states, futures, retries, caching, results, hooks, transactions, local tests | [flow-task-authoring](sub-skills/flow-task-authoring/SKILL.md) |
| Create deployments, `prefect.yaml`, schedules, `flow.serve`, `prefect deploy`, work pools, work queues, workers, deployment runs | [deployments-workers](sub-skills/deployments-workers/SKILL.md) |
| Operate CLI profiles/config/server/Cloud, variables, artifacts, shell command flows, dashboard, server/database diagnostics | [cli-server-operations](sub-skills/cli-server-operations/SKILL.md) |
| Use `get_client`, `PrefectClient`, schemas, settings/profile APIs, `temporary_settings`, or the `prefect-client` package split | [api-client-settings](sub-skills/api-client-settings/SKILL.md) |
| Use events, automations, blocks, variables, assets, notification blocks, and concurrency limits | [events-blocks-assets](sub-skills/events-blocks-assets/SKILL.md) |
| Modify the Prefect repository itself, choose focused tests, follow `AGENTS.md`, update generated artifacts, handle `prefect-client` sync | [repo-development](sub-skills/repo-development/SKILL.md) |

## Core Package Facts

- Distribution: `prefect`; import: `prefect`; console command: `prefect`.
- This skill was generated against Prefect `3.6.24` on Python `3.11`, with package metadata declaring Python `>=3.10,<3.15`.
- The full `prefect` package includes SDK, CLI, server, and database dependencies; the separate `prefect-client` distribution ships a lightweight client-facing subset.
- The CLI uses `prefect COMMAND [OPTIONS]` with session flags such as `--profile` and `--prompt/--no-prompt`.
- Many workflows require a reachable Prefect API from a self-hosted server or Prefect Cloud; local flow/task authoring can run without starting a server.

## Safe Defaults

- Start with read-only checks: `python -c "import prefect; print(prefect.__version__)"`, `prefect version`, `prefect --help`, and the bundled environment checker.
- Do not start long-running services such as `prefect server start`, `prefect worker start`, `prefect flow serve`, or event streams unless the user asks for them and has a stop plan.
- Do not run server database reset/downgrade/upgrade/stamp commands without explicit environment, backup, and rollback confirmation.
- Do not create deployments, variables, blocks, automations, concurrency limits, or Cloud workspace changes until the active profile/API URL/workspace is verified.
- Keep provider-specific integration behavior (`prefect-aws`, `prefect-dbt`, Kubernetes, Docker extras, etc.) shallow here; use or create dedicated integration skills for deep integration package work.

## Bundled Helpers

- Root: `scripts/check_prefect_environment.py` checks import, version, CLI availability, selected command help, and setting/profile signals without contacting a live API unless `--check-server` is requested.
- Flow/task authoring: `sub-skills/flow-task-authoring/scripts/flow_task_smoke.py` runs deterministic local SDK smoke examples.
- Deployments/workers: `sub-skills/deployments-workers/scripts/validate_prefect_yaml.py` validates common `prefect.yaml` shape; `deployment_command_builder.py` prints commands without executing them.
- CLI/server operations: `sub-skills/cli-server-operations/scripts/prefect_cli_doctor.py` runs read-only CLI and server-readiness diagnostics.
- API/client/settings: `sub-skills/api-client-settings/scripts/inspect_prefect_settings.py` summarizes settings and validates profiles TOML.
- Events/blocks/assets: `sub-skills/events-blocks-assets/scripts/validate_automation.py` validates automation JSON/YAML locally.
- Repo development: `sub-skills/repo-development/scripts/select_prefect_tests.py` suggests focused validation commands for changed paths.

## Shared Troubleshooting

Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting failures: install/import issues, optional extras, `prefect-client` omissions, API URL/profile confusion, server/database readiness, credentials, command side effects, and stale repo evidence.

## Skill Boundaries

- This is a Prefect Python/core repository skill. It intentionally does not deeply cover the legacy Vue UI, React UI-v2 implementation, load testing, benchmarks, or every integration package.
- Source repo files, tests, examples, and docs were used as evidence, but runtime instructions in this skill use bundled references/scripts and public Prefect APIs instead of requiring the original checkout.
- For a checkout whose commit, dirty state, package version, or public routes differ from [references/repo-provenance.md](references/repo-provenance.md), run `refresh-repo-skill` before trusting version-specific guidance.
