---
name: cli-local-development
description: "Use when a coding agent needs to run local Dagster OSS CLI
  commands for project scaffolding, workspace/code-location loading, local
  development, definitions validation, asset materialization, job
  execution/launch/listing, schedule/sensor operations, instance inspection, or
  debug export/import."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# CLI Local Development

Use this sub-skill for local `dagster` command-line workflows in an installed Dagster Python environment. It covers commands that inspect or run user code locally, validate code locations, start `dagster dev`, execute jobs/assets, manage schedule/sensor state, inspect the current instance, and collect debug artifacts.

## Route First

- Use this sub-skill for `dagster project`, `dagster dev`, `dagster definitions validate`, `dagster asset`, `dagster job`, `dagster schedule`, `dagster sensor`, `dagster instance`, and `dagster debug` usage.
- Route webserver startup internals, GraphQL API calls, GraphQL client code, and webserver debug viewing to `../graphql-and-webserver/SKILL.md` if that sub-skill exists.
- Route production instance storage, daemon deployment, run launcher configuration, and operational deployment configuration to `../deployment-operations/SKILL.md` if that sub-skill exists.
- Route `dg` component/project tooling to `../components-projects/SKILL.md` if that sub-skill exists; many legacy `dagster` commands now print supersession warnings but remain useful for local CLI support.

## Start Here

1. Confirm the environment can import Dagster and expose the needed commands with `python scripts/dagster_cli_doctor.py` from this sub-skill directory, or run its path from elsewhere.
2. Choose a loading target deliberately: `-f/--python-file`, `-m/--module-name`, `--package-name`, `-a/--attribute`, `-d/--working-directory`, or `-w/--workspace`.
3. Validate loading before executing work: `dagster definitions validate ...` with the same target flags.
4. For run config, use either repeated `-c/--config` YAML files/patterns or a single `--config-json` string, never both.
5. For persistent schedule/sensor/instance behavior, set `DAGSTER_HOME`; otherwise many commands use an ephemeral instance and state may disappear after the command exits.

## References

- [Local CLI workflows](references/workflows.md) for concrete command patterns, target selection, config merging, project scaffolding, local dev, validation, assets, jobs, schedules, sensors, instances, and debug commands.
- [Troubleshooting](references/troubleshooting.md) for import failures, target/load errors, optional dependency gaps, config misuse, partitions, schedule/sensor state, and instance surprises.
- [Dagster CLI doctor script](scripts/dagster_cli_doctor.py) for a safe environment and `--help` smoke check that does not start services or execute user code.

## Safety Notes

- `dagster dev` starts a local webserver and daemon; do not run it as a smoke test unless the user asked to start services.
- `dagster asset wipe`, schedule/sensor start/stop, `dagster instance migrate`, `dagster instance reindex`, and debug import mutate local Dagster state; confirm intent before running them.
- `dagster project from-example` may download examples; prefer `dagster project list-examples` or scaffold commands for offline checks.
