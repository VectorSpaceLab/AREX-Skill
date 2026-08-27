# Local Dagster CLI Workflows

This reference is self-contained for future agents using the generated Dagster skill. Commands assume the active Python environment has the relevant Dagster packages installed and that the current directory is either a Dagster project root or a directory from which explicit target flags make sense.

## Command Families

`dagster` exposes these local development command groups:

- `dagster project`: scaffold projects and list/download examples.
- `dagster dev`: start a local Dagster webserver plus daemon for a workspace/code location.
- `dagster definitions validate`: load code locations and validate definitions.
- `dagster asset`: list, materialize, or wipe assets.
- `dagster job`: list, print, execute, launch, scaffold config, or backfill jobs.
- `dagster schedule`: preview/list/start/stop/logs/wipe schedule state.
- `dagster sensor`: list/start/stop/preview/cursor operations for sensors.
- `dagster instance`: inspect, migrate, reindex, and manage instance concurrency.
- `dagster debug`: export/import run debug payloads.

Run `dagster <group> --help` and `dagster <group> <command> --help` before relying on flags in an unknown Dagster version.

## Loading Targets

Most commands need either workspace options or Python pointer options. Keep these mutually exclusive unless help explicitly allows a combination.

### Workspace-Loading Commands

Use workspace-style targets for commands that load a full code location or repository through a workspace context, including `dagster dev`, `dagster definitions validate`, `dagster job list`, `dagster job launch`, `dagster schedule ...`, and `dagster sensor ...`.

Common target flags:

```bash
dagster definitions validate -w workspace.yaml
dagster definitions validate -f path/to/definitions.py -a defs
dagster definitions validate -m my_project.definitions -a defs
dagster definitions validate --package-name my_project -a defs
dagster definitions validate -f path/to/definitions.py -d path/to/project/root
```

Selection rules:

- With no explicit target, Dagster checks `pyproject.toml` for a `[tool.dagster]` block, then `workspace.yaml` in the current directory.
- Use `-w/--workspace` when a workspace file defines one or more code locations.
- Use `-f/--python-file` for a file target; repeat it for multiple files when the command supports composite loading.
- Use `-m/--module-name` for importable modules and `--package-name` for packages.
- Use `-a/--attribute` when the target object is not discoverable or when a file/module contains multiple loadable objects.
- Use `-d/--working-directory` when relative imports only work from the project root.
- Use `-l/--location` when a workspace has multiple code locations.
- Use `-r/--repository` when a code location has multiple repositories.
- Use `-j/--job` when a repository has multiple jobs.

### Python-Pointer Commands

Use Python pointer targets for commands that reconstruct a single repository/job in the same Python environment, including `dagster job execute`, `dagster job scaffold_config`, `dagster asset list`, and `dagster asset materialize`.

Examples:

```bash
dagster job execute -f path/to/jobs.py -a my_job
dagster job execute -m my_project.jobs -a my_job
dagster job execute -f path/to/repository.py -a my_repository -j daily_job
dagster asset list -m my_project.definitions -a defs
dagster asset materialize -m my_project.definitions -a defs --select raw_customers
```

If a target contains multiple repositories or jobs, pass `--repository/-r` or `--job/-j` as directed by the CLI error.

## Project Scaffolding

Legacy `dagster project` commands still exist for local bootstrapping, though newer `create-dagster` or `dg` flows may be preferred in current docs.

```bash
dagster project scaffold --name my_project
dagster project scaffold --name my_project --excludes README.md --excludes tests
dagster project scaffold --name my_project --ignore-package-conflict
dagster project list-examples
dagster project from-example --example assets_dbt_python --name my_example
```

Notes:

- `scaffold` fails if the target directory already exists.
- Valid `--excludes` values are `readme.md`, `setup`, and `tests`, case-insensitive in intent.
- Project names containing terms such as `dagster` or `dbt` may trigger PyPI package-conflict checks; use `--ignore-package-conflict` only when the user accepts the risk.
- `from-example` can perform network access; do not run it in offline or network-restricted contexts without confirmation.

## Local Development Server

Use `dagster dev` for a local development deployment with webserver and daemon processes:

```bash
dagster dev -w workspace.yaml
dagster dev -m my_project.definitions -a defs
dagster dev -f path/to/definitions.py -d path/to/project/root --port 3000 --host 127.0.0.1
dagster dev --log-level debug --code-server-log-level debug --log-format rich
```

Important behavior:

- Requires `dagster-webserver` to be installed.
- Starts services and blocks until interrupted; do not run it as a noninteractive verification command.
- Sets development-mode environment markers internally while running.
- Warns if a local `dagster.yaml` exists but `DAGSTER_HOME` points elsewhere.
- Use `--verbose` to keep fuller code-server stack traces during local debugging.

## Definitions Validation

Validate code loading before launching runs:

```bash
dagster definitions validate
dagster definitions validate -w workspace.yaml
dagster definitions validate -f path/to/definitions.py -a defs
dagster definitions validate -m my_project.definitions -a defs --log-level debug
dagster definitions validate -w workspace.yaml --load-with-grpc --verbose
```

Validation behavior:

- Exit code `0` means all loaded locations passed validation.
- Exit code `1` means one or more locations loaded with errors or the asset graph has invalid partition mappings.
- Exit code `2` commonly indicates CLI usage errors, such as no target and no project metadata.
- The command sets `DAGSTER_IS_DEFS_VALIDATION_CLI=1`, allowing project code to gate expensive behavior during validation.
- Without `--verbose`, user-code errors hide many Dagster system frames; rerun with `--verbose` when the root cause is unclear.
- `--load-with-grpc` loads code locations using gRPC rather than in-process loading.

## Run Config Inputs

`dagster job execute`, `dagster job launch`, and `dagster asset materialize` support run config.

YAML config files:

```bash
dagster job execute -m my_project.jobs -a my_job -c base.yaml -c local.yaml
dagster job launch -w workspace.yaml -j daily_job -c "conf/*.yaml"
dagster asset materialize -m my_project.definitions -a defs --select raw_customers -c assets.yaml
```

JSON config:

```bash
dagster job launch -w workspace.yaml -j daily_job --config-json '{"ops":{"op_name":{"config":{"limit":10}}}}'
dagster asset materialize -m my_project.definitions -a defs --select raw_customers --config-json '{"resources":{}}'
```

Rules:

- Do not combine `-c/--config` with `--config-json`.
- Repeated `-c` values and glob patterns are merged; later files override earlier files at key-level granularity.
- Quote glob patterns so the CLI, not the shell, receives the pattern when that is desired.
- JSON strings must be valid JSON, not Python dict syntax.

## Assets

List assets:

```bash
dagster asset list -m my_project.definitions -a defs
dagster asset list -m my_project.definitions -a defs --select "group:finance"
```

Materialize assets:

```bash
dagster asset materialize -m my_project.definitions -a defs --select raw_customers
dagster asset materialize -m my_project.definitions -a defs --select raw_customers,clean_customers --partition 2026-06-21
dagster asset materialize -m my_project.definitions -a defs --select daily_sales --partition-range 2026-06-01...2026-06-07 -c base.yaml -c prod_like.yaml
```

Constraints:

- `--select` is required for materialization.
- Use either `--partition` or `--partition-range`, not both.
- Partition ranges require all selected assets to use a single-run backfill policy.
- Partitioned assets require an explicit partition unless the selected assets are unpartitioned.
- Selected assets must fit in one implicit asset job with compatible partition definitions.

## Jobs

Inspect jobs:

```bash
dagster job list -w workspace.yaml
dagster job list -w workspace.yaml -l code_location -r repository_name
dagster job print -w workspace.yaml -j daily_job --verbose
```

Execute a job in the same Python environment:

```bash
dagster job execute -m my_project.jobs -a daily_job
dagster job execute -f path/to/repository.py -a my_repository -j daily_job -c base.yaml -c local.yaml
dagster job execute -m my_project.jobs -a daily_job --tags '{"source":"cli"}' --op-selection '*extract,transform+'
```

Launch a job through the configured run launcher:

```bash
dagster job launch -w workspace.yaml -j daily_job
dagster job launch -w workspace.yaml -l code_location -r repository_name -j daily_job --run-id manual_daily_001
dagster job launch -w workspace.yaml -j daily_job --config-json '{"ops":{}}' --tags '{"source":"cli"}'
```

Generate config scaffolding:

```bash
dagster job scaffold_config -m my_project.jobs -a daily_job
dagster job scaffold_config -f path/to/repository.py -a my_repository -j daily_job --print-only-required
```

Backfill a partitioned job:

```bash
dagster job backfill -w workspace.yaml -j daily_job --partitions 2026-06-20,2026-06-21
dagster job backfill -w workspace.yaml -j daily_job --from 2026-06-01 --to 2026-06-07
dagster job backfill -w workspace.yaml -j daily_job --all --noprompt
```

Use `execute` for direct local execution in the current Python environment. Use `launch` when testing the configured Dagster instance and run launcher behavior.

## Schedules And Sensors

Schedules:

```bash
dagster schedule list -w workspace.yaml
dagster schedule list -w workspace.yaml --running
dagster schedule preview -w workspace.yaml
dagster schedule start daily_schedule -w workspace.yaml
dagster schedule start --start-all -w workspace.yaml
dagster schedule stop daily_schedule -w workspace.yaml
dagster schedule logs daily_schedule -w workspace.yaml
dagster schedule wipe -w workspace.yaml
```

Sensors:

```bash
dagster sensor list -w workspace.yaml
dagster sensor list -w workspace.yaml --stopped
dagster sensor start file_sensor -w workspace.yaml
dagster sensor start --start-all -w workspace.yaml
dagster sensor stop file_sensor -w workspace.yaml
dagster sensor preview file_sensor -w workspace.yaml --cursor previous_cursor
dagster sensor cursor file_sensor --set new_cursor -w workspace.yaml
dagster sensor cursor file_sensor --delete -w workspace.yaml
```

Operational notes:

- List and preview commands still load user code; validate the workspace first when load errors are suspected.
- Start/stop/cursor operations mutate instance state and require the intended `DAGSTER_HOME`.
- Preview commands evaluate schedule/sensor logic without relying on the daemon tick loop.

## Instance And Debug Commands

Inspect the current instance:

```bash
dagster instance info
dagster instance concurrency get --all
dagster instance concurrency get my_concurrency_key
dagster instance concurrency set my_concurrency_key 4
dagster instance concurrency delete my_concurrency_key
```

Maintenance commands:

```bash
dagster instance migrate
dagster instance reindex
```

Debug payloads:

```bash
dagster debug export <run_id> run-debug.gz
dagster debug import run-debug.gz
```

Notes:

- Without `DAGSTER_HOME`, `dagster instance info` reports an ephemeral instance.
- Ephemeral instances do not need migration and cannot be reindexed.
- Concurrency limits require storage that supports global concurrency limits.
- Debug export reads a run from the current instance; debug import writes run metadata/events into the current instance.

## Safe Verification Pattern

For command-support checks that should not start services or execute user code, prefer:

```bash
python scripts/dagster_cli_doctor.py --commands dagster,project,dev,definitions,asset,job,job-launch,schedule,sensor,instance,debug
```

For code-loading checks, prefer the least invasive target first:

```bash
dagster definitions validate -m my_project.definitions -a defs --log-level debug
```

Then reuse the exact same target flags for `job list`, `asset list`, `job launch`, or schedule/sensor commands.
