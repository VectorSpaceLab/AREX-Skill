---
name: cli-server-operations
description: "Operate Prefect CLI, profiles, settings, server, Cloud, variables,
  artifacts, shell command flows, and diagnostics safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# CLI And Server Operations

Use this sub-skill when a task asks how to operate Prefect from the command line, switch profiles, manage settings, check server/API readiness, start or inspect a self-hosted server, authenticate to Prefect Cloud, use shell-command flows, inspect variables or artifacts, or gather operational diagnostics.

## Start Here

1. Read `references/cli-reference.md` for the root command map, session flags, profile/config commands, Cloud/API commands, variables, artifacts, shell, dashboard, and plugin diagnostics.
2. Read `references/server-operations.md` before starting, stopping, scaling, migrating, or troubleshooting a self-hosted Prefect server.
3. Read `references/troubleshooting.md` when behavior differs by profile, API URL, settings source, Cloud credentials, parser errors, database migration state, or server port availability.
4. Run `python scripts/prefect_cli_doctor.py --help` to see safe read-only diagnostic checks; the script never starts a server or mutates Prefect state unless explicitly extended by a future maintainer.

## Safe Operating Rules

- Prefer read-only checks first: `prefect --version`, `prefect version`, `prefect config view`, `prefect profile ls`, `prefect server status --output json`, and command `--help`.
- Treat `prefect server start`, `prefect server services start`, `prefect shell serve`, and background modes as long-running service operations that require explicit user approval and a stop plan.
- Treat `prefect server database reset`, `downgrade`, `upgrade`, and `stamp` as database-mutating operations; require explicit production safety confirmation, backups, and a rollback plan.
- Treat Cloud login/logout, workspace switching, variables, artifact deletion, and API write requests as user-context mutations; confirm target profile and workspace first.
- Keep deployment/work-pool/worker flag details in `../deployments-workers/SKILL.md`; keep events, automations, blocks, assets, and concurrency primitives in `../events-blocks-assets/SKILL.md`; keep Python client coding and settings APIs in `../api-client-settings/SKILL.md`.

## Common Task Routing

- **Profile or setting mismatch:** inspect `PREFECT_PROFILE`, `prefect profile ls`, `prefect profile inspect`, and `prefect config view --show-sources`; then use `references/troubleshooting.md`.
- **Local server readiness:** set `PREFECT_API_URL` to the server API endpoint, run `prefect server status --wait --timeout 30 --output json`, or use `scripts/prefect_cli_doctor.py --check-server`.
- **Self-host startup:** use `references/server-operations.md`; start with SQLite only for local single-server use, and use PostgreSQL plus Redis-backed settings for multi-worker or scaled deployments.
- **Cloud context:** use `prefect cloud login`, `prefect cloud workspace ls`, and `prefect cloud workspace set` only after confirming credentials and workspace; never print API keys.
- **CLI parser vs settings errors:** parser errors show command usage and missing/invalid parameters; settings errors mention validation, unknown settings, or invalid profile values before command execution.
