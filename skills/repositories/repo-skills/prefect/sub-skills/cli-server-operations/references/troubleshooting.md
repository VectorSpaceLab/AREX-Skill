# CLI And Server Troubleshooting

Use this guide to distinguish profile/API URL problems, settings validation failures, CLI parser errors, server readiness issues, Cloud credential problems, and database/service failures.

## First Five Checks

Run these read-only checks first:

```bash
prefect --version
prefect version
prefect profile ls
prefect config view --show-sources
python scripts/prefect_cli_doctor.py --check-help
```

If an API URL is configured, add:

```bash
prefect server status --output json
python scripts/prefect_cli_doctor.py --check-server --server-timeout 10
```

## Wrong Profile Or API URL

Symptoms:

- `prefect version` shows an unexpected profile or server type.
- `prefect server status` says no API URL is configured.
- `prefect api` reports network errors against the wrong URL.
- Cloud commands report unauthorized even though a profile has a key.

Checks and fixes:

```bash
prefect profile ls --output json
prefect profile inspect --output json
prefect config view --show-sources
prefect --profile PROFILE_NAME config view --show-sources
```

Environment variables override profile values. Check `PREFECT_PROFILE`, `PREFECT_API_URL`, `PREFECT_API_KEY`, `.env`, `prefect.toml`, and `[tool.prefect]` in `pyproject.toml` before editing profiles. For self-hosted servers, the API URL usually ends with `/api`; using the UI URL without `/api` is a common mistake. For Cloud, the API URL and API key must belong to the same workspace context.

If no API URL is configured, Prefect may use ephemeral mode for Python flows when allowed, but CLI commands that explicitly contact a configured server still need `PREFECT_API_URL`.

## Parser Errors Vs Settings Validation Errors

Parser errors happen before business logic runs. They usually show `Usage: prefect ...`, required parameter names, or invalid flags. Fix the command shape first:

```bash
prefect COMMAND --help
prefect SUBCOMMAND --help
```

Examples:

- `prefect api` requires both `METHOD` and `PATH`.
- `prefect profile use` requires `NAME`.
- `prefect shell watch` requires `COMMAND`.
- Many output flags only accept `json`.

Settings validation errors happen while loading or writing configuration. They mention unknown settings, invalid setting values, profile validation, or a Pydantic settings error. Fix with:

```bash
prefect config validate
prefect config view --show-sources
prefect config unset SETTING_NAME -y
```

`prefect config set` requires `NAME=value`, rejects unknown setting names, and cannot set `PREFECT_HOME` or `PREFECT_PROFILES_PATH`; use environment variables for those.

## Server Port Conflicts

Symptoms:

- `prefect server start` says the port is already in use.
- It says a background server is already running.
- Status checks hit the wrong server version or profile.

Fixes:

```bash
prefect server stop
prefect server start --port 4201
prefect config set PREFECT_API_URL=http://127.0.0.1:4201/api
prefect server status --wait --timeout 30
```

`prefect server stop` only stops a Prefect background server tracked by Prefect. If another process owns the port, identify and manage that process with system tools rather than assuming Prefect owns it.

## Database Migration Or Service Failures

Symptoms:

- Server startup fails during migrations.
- Multi-worker mode exits before serving.
- Background services duplicate work or do not run.
- Database grows despite retention settings.

Checks:

```bash
prefect config view --show-sources | grep -E 'DATABASE|MIGRATE|MESSAGING|REDIS|DOCKET|DB_VACUUM|EVENTS_RETENTION'
prefect server services ls
prefect server database upgrade --dry-run
```

For production: use PostgreSQL 14.9 or newer, enable required extensions, use Redis-backed messaging/event-ordering/lease-storage for multi-worker or scaled deployments, and disable automatic migrations on API startup. Run `prefect server database upgrade -y` only as a controlled migration step with backups and a maintenance plan.

If migrations time out on large tables, increase `PREFECT_API_DATABASE_TIMEOUT` and retry during a quiet window. Manual SQL recovery is a database-administrator task and should be based on the exact migration revision and backup state.

## Cloud Credential Problems

Symptoms:

- `prefect cloud login` fails in non-interactive mode.
- Cloud commands say unauthorized.
- Workspace switching appears to succeed but API calls still hit another workspace.

Checks and fixes:

```bash
prefect cloud workspace ls
prefect config view --show-sources
prefect profile inspect --output json
```

Non-interactive login requires `prefect cloud login --key ... --workspace ACCOUNT/WORKSPACE`. If `PREFECT_API_KEY` is set in the environment, it overrides the profile key and can block logging in with another key. Prefect Cloud keys are expected to use current key formats such as `pnu_` or `pnb_`; older Cloud 1-style keys are not valid for current Cloud workspaces.

Never paste keys into shared logs. Use masked config output unless the user explicitly asks to inspect secrets in a private terminal.

## API Command Failures

`prefect api METHOD PATH` requires a configured API URL or Cloud login. Common failures:

- `No API URL configured`: set `PREFECT_API_URL` or log in to Cloud.
- `--root` or `--account` on self-hosted: those flags are Cloud-only.
- HTTP 401/403: check API key and workspace.
- Network error: check API URL, DNS, proxy, TLS, and server status.
- JSON parse error: validate `--data` or stdin JSON.

Use `--verbose` to see request and response headers; authorization headers are masked by Prefect.

## Variables And Artifacts

Variables and artifacts require a reachable API. `prefect variable get NAME` and `prefect artifact inspect KEY` report not found when the object is absent in the active profile/workspace. Before creating or deleting, verify:

```bash
prefect version
prefect variable ls --output json
prefect artifact ls --output json
```

`prefect variable set` parses JSON when possible, so quote strings carefully. `prefect artifact delete KEY` can delete multiple artifact versions for the same key; confirm target profile and key.

## Shell Command Flows

`prefect shell watch` and `prefect shell serve` execute commands through the system shell. A non-zero subprocess exit code fails the Prefect flow run. Quote commands for the user's shell, avoid embedding secrets in command strings, and route deployment/schedule/runner problems from `shell serve` to `../deployments-workers/SKILL.md`.

## Plugin Diagnostics

If `prefect plugins diagnose` says plugins are disabled, enable with `PREFECT_PLUGINS_ENABLED=1`. If startup hooks are unsafe or unknown, force safe mode:

```bash
PREFECT_PLUGINS_SAFE_MODE=1 prefect plugins diagnose
```

When safe mode is disabled, plugin diagnostics may execute startup hooks and import third-party plugin code. Confirm before running it in production-like environments.

## Dashboard Problems

`prefect dashboard open` requires `PREFECT_UI_URL`. For local self-hosted operation, set the API URL for clients and set or infer a separate UI URL for browser access. If the UI is behind a reverse proxy, verify `PREFECT_UI_URL`, `PREFECT_UI_API_URL`, and proxy forwarding headers.

## Hard Diagnosis Patterns

- **Recover from wrong profile/API URL:** compare `prefect version`, `prefect config view --show-sources`, `prefect --profile NAME config view --show-sources`, and `prefect server status --output json`; identify whether environment variables, profile values, or project TOML files are winning.
- **Separate parser from validation:** if output starts with command usage, fix flags/arguments with `--help`; if output names setting validation or unknown settings, inspect sources and run `prefect config validate` before retrying the command.
