# Prefect CLI Reference

This reference summarizes CLI behavior verified against Prefect 3.6 command help and source behavior. Use it for copyable CLI operations; route deployment, work-pool, worker, event, automation, block, asset, and Python client coding details to sibling sub-skills.

## Root CLI Shape

`prefect --help` exposes a lazy command map. Core commands owned here:

| Command | Use |
| --- | --- |
| `prefect config` | View, validate, set, and unset Prefect settings in the active profile. |
| `prefect profile` / `prefect profiles` | Create, list, inspect, switch, delete, rename, and populate profiles. |
| `prefect server` | Start a server, check status, stop background server, manage database migrations, and manage loop services. |
| `prefect cloud` | Log in/out and manage Cloud workspaces plus Cloud-only resources. |
| `prefect api` | Make direct requests through the configured Prefect API or Cloud client. |
| `prefect dashboard open` | Open the configured UI URL in a browser. |
| `prefect shell watch` | Execute a shell command and observe it as a Prefect flow run. |
| `prefect shell serve` | Serve a deployment that runs a shell command; route deployment details to `../deployments-workers/SKILL.md`. |
| `prefect variable` | List, inspect, get, set, unset, or delete variables through the API. |
| `prefect artifact` | List, inspect, or delete artifacts through the API. |
| `prefect plugins diagnose` | Inspect plugin settings and discoverable plugins. |
| `prefect version` | Print detailed version, profile, server type, and database context. |

Session parameters are available at the root: `--profile` selects a profile for a single CLI run, and `--prompt` / `--no-prompt` toggles interactive prompts. Prefer the long `--profile` form in reusable instructions to avoid ambiguity with subcommand flags.

## Version And Environment Checks

Use these before deeper troubleshooting:

```bash
prefect --version
prefect version
prefect --help
```

`prefect --version` prints only the package version. `prefect version` prints a structured human-readable block including Prefect version, API version, Python version, profile, server type, and, when available, server/database details.

## Settings With `prefect config`

Command map:

| Command | Notes |
| --- | --- |
| `prefect config view` | Displays active settings; supports `--show-defaults`, `--show-sources`, `--show-secrets`, and `--output json`. |
| `prefect config validate` | Validates the current profile and rewrites deprecated setting names when needed. |
| `prefect config set NAME=value ...` | Writes setting values to the active profile. |
| `prefect config unset NAME ...` | Removes setting values from the active profile; use `-y` / `--yes` to skip confirmation. |

Useful read-only checks:

```bash
prefect config view --show-sources
prefect config view --show-defaults --output json
prefect config validate
```

Use `prefect config set PREFECT_API_URL=http://127.0.0.1:4200/api` to point the active profile at a local self-hosted API. Use `prefect config unset PREFECT_API_URL -y` to remove that profile value. Environment variables, `.env`, `prefect.toml`, and `pyproject.toml` can still override profile values, so use `--show-sources` when a setting appears wrong.

`prefect config set` rejects unknown setting names and refuses to modify `PREFECT_HOME` or `PREFECT_PROFILES_PATH`; set those as environment variables instead.

## Profiles With `prefect profile`

Command map:

| Command | Notes |
| --- | --- |
| `prefect profile ls` | Lists profile names; supports `--output json`. |
| `prefect profile inspect [NAME]` | Shows settings for a profile; supports `--output json`. |
| `prefect profile create NAME [--from EXISTING]` | Creates an empty profile or copies an existing one. |
| `prefect profile use NAME` | Sets active profile and checks connectivity. |
| `prefect profile delete NAME` | Deletes a non-active profile; prompts interactively. |
| `prefect profile rename OLD NEW` | Renames a profile and warns if `PREFECT_PROFILE` still points at the old name. |
| `prefect profile populate-defaults` | Adds stock default profiles while preserving existing profiles. |

`prefect profile use NAME` classifies the resulting API context as Cloud connected, Cloud unauthorized, self-hosted server connected, server error, ephemeral, unconfigured, or invalid API. If it reports an error, inspect the profile and active environment before changing anything:

```bash
prefect profile ls --output json
prefect profile inspect NAME --output json
prefect --profile NAME config view --show-sources
```

## Cloud Context

Core Cloud commands:

| Command | Notes |
| --- | --- |
| `prefect cloud login` | Authenticates and writes `PREFECT_API_KEY` plus `PREFECT_API_URL` to the active profile. |
| `prefect cloud logout` | Removes Cloud API key and API URL from the active profile. |
| `prefect cloud workspace ls` | Lists accessible Cloud workspaces; supports `--output json`. |
| `prefect cloud workspace set --workspace ACCOUNT/WORKSPACE` | Changes the workspace API URL in the active profile. |

Non-interactive Cloud login requires both `--key` and `--workspace`. If `PREFECT_API_KEY` is already set in the environment, it overrides the profile and can prevent logging in with a different key. Never echo or record full API keys in notes or generated commands.

Cloud subcommands for assets, webhooks, and IP allowlists are Cloud-specific operational surfaces; confirm account, workspace, and authorization before modifying them.

## Direct API Requests

`prefect api METHOD PATH` sends requests through the configured Prefect client:

```bash
prefect api GET /health
prefect api GET /flows/filter --data '{}'
prefect api POST /variables/ --data '{"name":"demo","value":"ok"}'
```

Options include `--data` for inline JSON or `@filename`, repeated `-H` / `--header` values in `Key: Value` form, `--verbose` for request/response headers, and Cloud-only `--root` or `--account`. Self-hosted paths are relative to `PREFECT_API_URL`. The command exits with distinct classes for auth errors, client errors, server errors, and network errors; use `--verbose` when the response body matters.

## Dashboard

`prefect dashboard open` opens `PREFECT_UI_URL` in a browser. If that setting is absent, the command exits with an error. For a local server, the UI is usually reachable at `http://127.0.0.1:4200`, while the API URL usually ends in `/api`.

## Shell Command Flows

`prefect shell watch COMMAND` executes a shell command and records it as a Prefect flow run:

```bash
prefect shell watch "python -c 'print(42)'" --flow-name "diagnostic-shell" --tag cli
```

Options include `--log-output` / `--no-log-output`, `--flow-run-name`, `--flow-name`, `--stream-stdout` / `--no-stream-stdout`, and repeatable `--tag`. The shell command runs with `shell=True`; treat user-provided commands as arbitrary shell execution.

`prefect shell serve COMMAND --flow-name NAME` creates and serves a deployment for a shell command. It starts a runner and can run indefinitely unless `--run-once` is used. Route schedule, deployment, and runner troubleshooting to `../deployments-workers/SKILL.md`.

## Variables

Variables are API-backed key/value records. Commands:

```bash
prefect variable ls --output json
prefect variable inspect NAME --output json
prefect variable get NAME
prefect variable set NAME '{"json":"value"}' --overwrite
prefect variable unset NAME
```

Values are parsed as JSON when possible; otherwise they are stored as strings. `set` refuses to overwrite an existing variable without `--overwrite`. `unset` and `delete` are aliases for removal and prompt interactively when prompts are enabled.

## Artifacts

Artifacts are API-backed records created by flows and tasks. Commands:

```bash
prefect artifact ls --output json
prefect artifact inspect KEY --limit 10 --output json
prefect artifact delete KEY
prefect artifact delete --id UUID
```

`artifact ls` returns latest artifact collections by default; add `--all` to list artifact versions. Deletion can remove all artifacts for a key, so confirm the server, profile, and target key first.

## Plugin Diagnostics

`prefect plugins diagnose` reports whether plugins are enabled, plugin timeout, allow/deny lists, strict mode, safe mode, and discoverable plugin entry points. When safe mode is disabled, diagnostics can execute startup hooks. For low-risk diagnostics, force safe mode:

```bash
PREFECT_PLUGINS_SAFE_MODE=1 prefect plugins diagnose
```

Use `PREFECT_PLUGINS_ENABLED=1` to enable the plugin system and `PREFECT_PLUGINS_SAFE_MODE=0` only when the user explicitly wants hooks executed.
