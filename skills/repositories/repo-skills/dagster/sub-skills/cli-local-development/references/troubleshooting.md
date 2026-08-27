# CLI Local Development Troubleshooting

Use this guide when local `dagster` commands fail to import packages, load code locations, parse config, execute assets/jobs, or persist schedule/sensor/instance state.

## Environment And Import Failures

Symptoms:

- `dagster: command not found`
- `No module named dagster`
- `The dagster-webserver Python package must be installed in order to use the dagster dev command`
- A command exists in one shell but not another

Checks and fixes:

```bash
python -c "import dagster; print(dagster.__version__)"
python -m dagster --help
python scripts/dagster_cli_doctor.py --verbose
```

- If import fails, activate the environment where `dagster` is installed or install Dagster into the active environment.
- If `python -m dagster --help` works but `dagster --help` does not, the console script is not on `PATH`; use `python -m dagster ...` or repair the environment entry points.
- If `dagster dev` fails but other CLI commands work, install `dagster-webserver` into the same environment.
- If GraphQL-related commands or webserver APIs fail, verify `dagster-graphql` and route deeper API debugging to the GraphQL/webserver sub-skill.

## Wrong Working Directory Or Target Flags

Symptoms:

- `No arguments given and no [tool.dagster] block in pyproject.toml found`
- `Invalid set of CLI arguments for loading repository/job`
- `ModuleNotFoundError` for project-local imports
- `Location "..." not found in workspace`
- `Must provide --location`, `Must provide --repository`, or `Must provide --job`

Fixes:

```bash
# From the project root, rely on pyproject.toml or workspace.yaml when available.
dagster definitions validate

# Use a workspace file when locations are declared there.
dagster definitions validate -w workspace.yaml

# Use a module target plus explicit attribute.
dagster definitions validate -m my_project.definitions -a defs

# Use a file target plus working directory when relative imports depend on project root.
dagster definitions validate -f src/my_project/definitions.py -a defs -d .

# Disambiguate multi-location, multi-repository, or multi-job workspaces.
dagster job list -w workspace.yaml -l code_location -r repository_name
dagster job launch -w workspace.yaml -l code_location -r repository_name -j job_name
```

Guidance:

- Do not mix `-w`, `-f`, `-m`, `--package-name`, `--grpc-port`, or `--grpc-socket` for a single target unless command help explicitly permits it.
- Add `-d/--working-directory` when the command is launched from outside the project root.
- Add `-a/--attribute` when a file/module contains multiple definitions or the desired object is not named conventionally.
- Use `dagster definitions validate --verbose` to reveal hidden system frames when the non-verbose load error is too short.

## Definitions Validation Failures

Symptoms:

- `Validation failed for code location ...`
- Duplicate asset keys
- Invalid partition mappings
- User-code exceptions while importing definitions

Workflow:

```bash
dagster definitions validate -w workspace.yaml --log-level debug
dagster definitions validate -w workspace.yaml --verbose
dagster definitions validate -w workspace.yaml --load-with-grpc --verbose
```

- Treat validation failures as code-location load failures until proven otherwise; do not proceed to job launch or schedule/sensor operations with the same target.
- Check whether project code gates expensive import-time behavior on `DAGSTER_IS_DEFS_VALIDATION_CLI=1`.
- If in-process loading masks a serialization or process-boundary issue, retry with `--load-with-grpc`.
- If only one location in a multi-location workspace fails, use `-l/--location` on downstream commands to isolate healthy locations.

## Run Config And JSON/YAML Misuse

Symptoms:

- `Cannot specify both -c / --config and --config-json`
- `Invalid JSON-string given for --config-json`
- Missing required op/resource config at execution time
- Config appears overridden unexpectedly

Fixes:

```bash
# YAML files merge; later files override earlier files at key-level granularity.
dagster job execute -m my_project.jobs -a daily_job -c base.yaml -c override.yaml

# Quote globs when the CLI should receive the pattern.
dagster job launch -w workspace.yaml -j daily_job -c "conf/*.yaml"

# JSON must be valid JSON, including double quotes.
dagster job launch -w workspace.yaml -j daily_job --config-json '{"ops":{"load":{"config":{"limit":10}}}}'
```

- Use either repeated `-c/--config` or `--config-json`, not both.
- Prefer YAML files for complex config because shell quoting JSON is error-prone.
- Generate a starter config with `dagster job scaffold_config ...` when schema shape is unclear.

## Asset Materialization Failures

Symptoms:

- Missing `--select`
- `Asset has partitions, but no '--partition' option was provided`
- Unknown partition key
- Partition range rejected
- Selected assets cannot be materialized in one implicit job

Fixes:

```bash
dagster asset list -m my_project.definitions -a defs
dagster asset materialize -m my_project.definitions -a defs --select raw_customers
dagster asset materialize -m my_project.definitions -a defs --select daily_sales --partition 2026-06-21
dagster asset materialize -m my_project.definitions -a defs --select daily_sales --partition-range 2026-06-01...2026-06-07
```

- Use `dagster asset list` to confirm the asset key and selection syntax before materializing.
- Use exactly one of `--partition` or `--partition-range`.
- Partition ranges require selected assets to support single-run backfill policy.
- If selected assets have incompatible partition definitions, split the materialization into compatible selections.

## Job Execute Versus Job Launch

Symptoms:

- `job execute` cannot load a workspace target
- `job launch` submits a run but daemon/launcher behavior is unexpected
- Multiple jobs require `--job`

Guidance:

- Use `dagster job execute` with `-f`, `-m`, or `--package-name` when you want direct execution in the current Python environment.
- Use `dagster job launch` with `-w`, `-f`, `-m`, or project metadata when you want to submit through the configured Dagster instance and run launcher.
- Use `dagster job list` or `dagster job print` to confirm job names before executing.
- For op subsets, pass `--op-selection` with expressions such as `extract`, `*transform`, or `*extract,load+`.

## Schedule And Sensor State Surprises

Symptoms:

- Schedule/sensor start succeeds but state disappears later
- `DAGSTER_HOME` appears unset
- Preview works but daemon ticks do not happen
- Cursor operations affect the wrong environment

Fixes:

```bash
dagster instance info
dagster schedule list -w workspace.yaml
dagster sensor list -w workspace.yaml
dagster sensor preview file_sensor -w workspace.yaml --cursor previous_cursor
```

- Set `DAGSTER_HOME` to the intended instance before mutating schedule/sensor state.
- Remember that `list`, `preview`, `start`, and `stop` all load user code; validate the workspace first if imports are failing.
- Preview evaluates schedule/sensor code, but a running daemon is still needed for normal automated ticks.
- Use `dagster sensor cursor SENSOR_NAME --set VALUE` and `dagster sensor cursor SENSOR_NAME --delete` carefully; they mutate instance cursor state.

## Instance And Storage Issues

Symptoms:

- Ephemeral instance warning
- Migration skipped because `DAGSTER_HOME` is unset
- Reindex unavailable on ephemeral instances
- Concurrency limits unsupported

Fixes:

```bash
dagster instance info
dagster instance migrate
dagster instance reindex
dagster instance concurrency get --all
```

- Ephemeral instances are appropriate for quick local execution but not for persistent schedule/sensor state.
- Persistent instance operations require `DAGSTER_HOME` to point at the intended instance directory.
- Global concurrency limits require event log storage that supports them; some local SQLite setups may not.
- Confirm before running `migrate`, `reindex`, or concurrency `set`, because they mutate instance storage.

## Debug Artifact Issues

Symptoms:

- `Could not find run with run_id ...`
- Debug import succeeds into the wrong instance
- Debug file cannot be read

Fixes:

```bash
dagster instance info
dagster debug export <run_id> run-debug.gz
dagster debug import run-debug.gz
```

- Confirm the current instance before exporting or importing debug payloads.
- If a run is not found, verify the run ID and that the active `DAGSTER_HOME` points at the instance that contains the run.
- Debug import mutates the current instance by adding run snapshots/events; do not use it as a read-only inspection step.

## Doctor Script Interpretation

Run:

```bash
python scripts/dagster_cli_doctor.py --verbose
```

Interpretation:

- Import failure means the active Python environment is not ready for local Dagster CLI work.
- Console-script failure with successful module execution usually means `PATH` or entry points need repair.
- A failed `--help` command for a group may indicate an optional package gap or a version mismatch.
- The script intentionally avoids `dagster dev` service startup, code-location loading, job execution, and state mutation.
