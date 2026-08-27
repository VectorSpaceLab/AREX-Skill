---
name: graphql-and-webserver
description: "Use when a coding agent needs to start or debug dagster-webserver,
  query Dagster GraphQL through the CLI or Python client, handle path prefixes,
  headers, auth, remote URLs, read-only webserver mode, or diagnose
  webserver/API failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# GraphQL And Webserver

Use this sub-skill for Dagster OSS webserver and GraphQL API workflows in an installed Dagster Python environment. It covers `dagster-webserver`, `dagster-graphql`, the `DagsterGraphQLClient`, remote GraphQL URLs, path prefixes, headers/auth, read-only serving, and API troubleshooting.

## Route Here

- Starting `dagster-webserver` directly, especially with `--host`, `--port`, `--path-prefix`, `--read-only`, or logging/database timeout flags.
- Running one-off GraphQL queries with `dagster-graphql --text`, `--file`, `--predefined`, `--variables`, `--remote`, or `--output`.
- Using `DagsterGraphQLClient` for run status, job submission, repository-location reload/shutdown, run termination, custom headers, custom auth, HTTPS, timeouts, or path prefixes.
- Debugging `/graphql`, `/server_info`, workspace target selection, invalid variables JSON, remote URL validation, connection errors, read-only mutation failures, or API response `__typename` errors.

## Route Elsewhere

- Core Dagster asset/job/Definitions modeling: use `../asset-definitions/SKILL.md` if that sub-skill exists.
- Local `dagster` CLI project validation, asset materialization, schedule/sensor commands, or `dagster dev`: use `../cli-local-development/SKILL.md` if that sub-skill exists.
- Production deployment topology, daemon, instance storage, run launchers, Kubernetes, or service operations: use `../deployment-operations/SKILL.md` if that sub-skill exists.
- Dagster Plus authorization and cloud deployment administration: treat this sub-skill only as a client/API caution and route cloud operations elsewhere if available.

## Start Here

1. Decide whether the task is server-side (`dagster-webserver`), CLI query (`dagster-graphql`), or Python client (`DagsterGraphQLClient`).
2. For server startup, choose a workspace target deliberately: `-w/--workspace`, `-f/--python-file`, `-m/--module-name`, package target flags, `-a/--attribute`, and `-d/--working-directory` as appropriate.
3. For GraphQL CLI queries, provide exactly one query source: `--text`, `--file`, or `--predefined`; add `--variables` as a JSON string only when the query declares variables.
4. For remote webservers, verify the public base URL and path prefix before querying; the GraphQL endpoint is the base URL plus `/graphql` after any prefix.
5. Use `python scripts/graphql_health_check.py --help` from this sub-skill directory to inspect safe helper options before any network call.

## References

- [Workflows and API Reference](references/workflows.md) for concrete webserver, GraphQL CLI, Python client, path-prefix, header/auth, and read-only examples.
- [Troubleshooting](references/troubleshooting.md) for install/import failures, optional dependency gaps, CLI/API misuse, connection errors, path-prefix problems, read-only failures, and GraphQL response errors.
- [GraphQL health-check script](scripts/graphql_health_check.py) for a safe `--dry-run` command printer or optional read-only GraphQL health query against a webserver URL.

## Safety Notes

- `dagster-webserver` starts a long-running service; do not launch it as a smoke test unless the user asked to start a server.
- `dagster-graphql` mutations and `DagsterGraphQLClient` methods such as `submit_job_execution`, `terminate_run`, `reload_repository_location`, and `shutdown_repository_location` can mutate deployment state.
- Prefer read-only queries such as `version`, `repositoriesOrError`, or run-status lookups when diagnosing connectivity.
- Never print secrets from auth headers or tokens; pass them via environment variables or secret managers and redact them in logs.
