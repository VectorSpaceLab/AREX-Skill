# Dagster Cross-Cutting Troubleshooting

## Purpose

Read this when a Dagster task fails before it clearly belongs to a specific workflow. Route to the nearest sub-skill once the failure surface is identified.

## Install And Import Failures

Symptoms:
- `ModuleNotFoundError: No module named 'dagster'`
- `dagster: command not found`
- A user can import `dagster` but `dagster-webserver`, `dagster_graphql`, or `dagster_pipes` is missing.

Actions:
1. Confirm the active Python environment with `python -c "import sys; print(sys.executable)"`.
2. Run `python -c "import dagster as dg; print(dg.__version__)"`.
3. Run `python -m pip check` to catch dependency conflicts.
4. Install only the packages required by the current workflow: `dagster`, `dagster-webserver`, `dagster-graphql`, `dagster-pipes`, or a named integration package.
5. If editing the Dagster repo, use `sub-skills/repo-development/SKILL.md` and repository-specific `uv`/editable-install guidance instead of ad hoc global installs.

## CLI Target Loading Failures

Symptoms:
- `dagster definitions validate` cannot find definitions.
- CLI commands work in one directory but not another.
- Workspace/code-location errors mention missing modules, wrong attributes, or import errors.

Actions:
1. Choose exactly one loading target shape: `-f/--python-file`, `-m/--module-name`, `--package-name`, or `-w/--workspace`.
2. Add `-a/--attribute` only when definitions are not the default top-level value.
3. Add `-d/--working-directory` when local imports rely on a project root.
4. Run `dagster definitions validate` with the same target flags before executing assets/jobs.
5. Route to `sub-skills/cli-local-development/SKILL.md` for command syntax and target examples.

## Optional Dependency Gaps

Symptoms:
- A core asset imports but an integration-specific asset fails.
- Errors mention missing packages such as database clients, cloud SDKs, `dbt`, Spark, Pandas, or provider extras.

Actions:
1. Identify whether the failing import belongs to core Dagster, an integration package, or user project code.
2. Install the narrow package or extra needed for that workflow instead of broad all-in-one extras.
3. For external services, confirm credentials and network access separately from Python package installation.
4. If the workflow is outside this generated skill’s scope, record the needed integration and consider extending the skill.

## State, Daemon, And Instance Surprises

Symptoms:
- Schedules or sensors do not tick.
- Runs disappear between commands.
- The webserver and daemon disagree about jobs or run state.

Actions:
1. Confirm whether `DAGSTER_HOME` is set for every relevant process.
2. Confirm `dagster.yaml` is in that directory and readable.
3. Ensure exactly one daemon process is responsible for schedules, sensors, and run queue dequeueing in a deployment.
4. Route to `sub-skills/deployment-operations/SKILL.md` for durable storage, daemon, run queue, and service topology.

## Version And Provenance Drift

If this skill is used against a checkout whose commit, package version, or major evidence paths differ from `references/repo-provenance.md`, treat it as potentially stale and refresh it from the repository before relying on detailed API or CLI claims.
