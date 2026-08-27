# Shared Prefect Troubleshooting

Use this reference for failures that cut across more than one Prefect sub-skill. Route workflow-specific details to the nearest sub-skill after the shared cause is isolated.

## Install Or Import Fails

Symptoms:

- `ModuleNotFoundError: No module named 'prefect'`.
- `prefect: command not found`.
- `pip check` reports broken requirements.
- A user imports `prefect.server` or CLI modules from an environment that only has `prefect-client`.

Checks:

```bash
python -c "import prefect; print(prefect.__version__)"
python -m pip show prefect
prefect version
python scripts/check_prefect_environment.py --check-cli
```

Recovery:

- Install the full package with `pip install -U prefect` or `uv add prefect` when CLI/server/deployment operations are required.
- Use `prefect-client` only for lightweight client-facing code; it is not a full server/CLI runtime.
- Avoid installing all optional integration extras unless the task explicitly requires them. Provider packages such as `prefect-aws`, `prefect-dbt`, or `prefect-kubernetes` are separate integration distributions.
- If the repository checkout is being developed, use the repo-development sub-skill and the repository's `uv` workflow rather than ad hoc package manager commands.

## Wrong API URL, Profile, Or Workspace

Symptoms:

- CLI commands talk to an unexpected ephemeral server, local server, or Cloud workspace.
- Client calls fail with connection errors, unauthorized errors, or 404s for objects that exist elsewhere.
- Settings appear correct in code but differ in CLI output.

Checks:

```bash
prefect profile ls
prefect config view --show-sources
prefect version
python scripts/check_prefect_environment.py --show-settings
```

Recovery:

- Confirm `PREFECT_PROFILE`, `PREFECT_API_URL`, `PREFECT_API_KEY`, `.env`, `prefect.toml`, `pyproject.toml`, active profile, and defaults in that order of likely surprise.
- For self-hosted server use, API URLs usually end in `/api`; the UI URL alone is not enough for clients.
- For Cloud, ensure API key and workspace URL belong to the same account/workspace.
- Route command-level profile fixes to `sub-skills/cli-server-operations/SKILL.md`; route Python settings-source debugging to `sub-skills/api-client-settings/SKILL.md`.

## Server Or Database Not Ready

Symptoms:

- Deployment, block, variable, automation, event stream, work pool, or worker commands fail because the API is unreachable.
- `prefect server status` fails or hangs.
- Database migration or service commands fail in a self-hosted environment.

Safe checks:

```bash
prefect server status --output json
python scripts/check_prefect_environment.py --check-server --server-timeout 10
```

Recovery:

- For local experimentation, start one Prefect server deliberately and keep the terminal/session that owns it visible.
- For production-like self-hosting, prefer PostgreSQL and deliberate service/database operation plans; do not run reset/downgrade/upgrade/stamp commands without backups and explicit confirmation.
- Workers, automations, blocks, variables, and concurrency limits are server-backed. Passing local script validation does not prove the server-side object exists.

## Command Has Side Effects

Prefect commands are often convenient but many are mutating:

- `prefect deploy` can create or update deployments, schedules, queues, and deployment metadata.
- `prefect deployment run` creates a flow run.
- `prefect worker start`, `prefect flow serve`, `prefect shell serve`, `prefect server start`, and `prefect events stream` are long-running processes.
- `prefect variable set/unset`, block commands, automation commands, concurrency-limit commands, and Cloud workspace commands mutate server or Cloud state.
- `prefect server database reset/downgrade/upgrade/stamp` mutates database schema or data.

Start with help, validation, or read-only inspect/list commands. Ask for target profile/workspace confirmation before writes.

## Optional Dependencies And Integrations

Symptoms:

- Worker type asks to install a missing package.
- Block type exists in docs but cannot import.
- Docker, Kubernetes, AWS, dbt, Dask, Ray, Snowflake, or other provider workflows fail with missing optional packages or credentials.

Recovery:

- Use the full Prefect skill only for general Prefect routing and base package behavior.
- Install provider packages only for the requested integration workflow.
- Keep credentials in blocks, environment variables, or external secret systems; do not put secrets in examples, logs, or skill artifacts.
- Prefer a dedicated integration package skill for deep `src/integrations/*` changes or provider-specific runtime usage.

## Skill Staleness

Run `refresh-repo-skill` when:

- The current commit differs from `references/repo-provenance.md`.
- Generated skill paths, public CLI help, decorator signatures, deployment APIs, client/settings APIs, or schema files changed.
- The user is asking about a new Prefect capability not covered by a sub-skill.
- The task targets UI-v2 or integration internals that this core skill intentionally treats as out of scope.
