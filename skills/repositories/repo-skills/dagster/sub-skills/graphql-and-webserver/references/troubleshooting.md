# Troubleshooting GraphQL And Webserver

Use this guide when `dagster-webserver`, `dagster-graphql`, or `DagsterGraphQLClient` fails. Start with the smallest safe read-only check, then move outward to target selection, URL/prefix/auth, and response-level errors.

## Install and Import Failures

Symptoms:

- `dagster-webserver: command not found`
- `dagster-graphql: command not found`
- `ModuleNotFoundError: No module named 'dagster_graphql'`
- `ImportError` from optional webserver or GraphQL dependencies

Checks:

```bash
python -c "import dagster, dagster_graphql, dagster_webserver; print(dagster.__version__)"
dagster-webserver --help
dagster-graphql --help
```

Likely causes and fixes:

- The active Python environment does not include `dagster-webserver` or `dagster-graphql`; install the matching Dagster packages in the same environment used to run commands.
- The shell resolves a different Python/CLI than expected; compare `python -c 'import sys; print(sys.executable)'` with the command resolution the user intends.
- Optional webserver dependencies are missing or mismatched; reinstall the Dagster webserver package set rather than copying imports from another environment.
- Avoid relying on `dg`/project creation tooling when it was not verified in the target environment; use already installed `dagster-webserver` and `dagster-graphql` surfaces for this sub-skill.

## Webserver Does Not Start

Symptoms:

- Workspace/code location load errors before the server binds.
- Port already in use.
- Browser loads but repositories are missing.
- Logs show code server startup failures.

Checks and fixes:

- Run `dagster-webserver --help` to confirm CLI availability without starting a service.
- Confirm the workspace target flags point to the intended code: `-w`, `-f`, `-m`, package target flags, `-a`, and `-d` must match the user's project layout.
- If a port is occupied, choose another port with `--port` instead of killing unrelated processes.
- Increase visibility with `--uvicorn-log-level info` or `debug`, and `--code-server-log-level debug` for code-location startup issues.
- If definitions import slowly or fail, route code modeling/import fixes to the asset or local CLI sub-skill rather than changing GraphQL usage.
- If database/storage errors appear, avoid changing run launcher or instance config in this sub-skill; route production instance issues to deployment operations.

## GraphQL CLI Target Selection Errors

Symptoms:

- `Must select one and only one of text (-t), file (--file), or predefined (-p)`.
- A query runs against the wrong repository.
- A remote URL works in a browser but the local CLI query loads a local workspace instead.

Rules:

- Query source: pass exactly one of `--text`, `--file`, or `--predefined`.
- Target mode: use `--remote` for a running webserver; omit `--remote` only when you want the CLI to load a local workspace in-process.
- Workspace target flags matter only for local execution; they do not select a repository on a remote webserver.
- Keep variables as a single valid JSON string after `--variables`.

Examples:

```bash
# Good: one inline query against local workspace loading flags
dagster-graphql --text 'query { version }' -w workspace.yaml

# Good: one query file against a remote webserver
dagster-graphql --file query.graphql --remote http://localhost:3000

# Bad: conflicting query sources
dagster-graphql --text 'query { version }' --file query.graphql
```

## Remote URL and Path Prefix Problems

Symptoms:

- `Host ... is not a valid URL. Host URL should include scheme`.
- Remote sanity check fails and says the host is not a `dagster-webserver` instance.
- HTTP 404 from `/graphql` or `/server_info`.
- Python client connects to `/graphql` but the server is actually under a prefix.

Fixes:

- For `dagster-graphql --remote`, include the scheme: `http://localhost:3000`, not `localhost:3000`.
- For a prefixed webserver, include the prefix in the remote base URL: `http://localhost:3000/dagster`.
- For `DagsterGraphQLClient`, pass `path_prefix="/dagster"`; do not put the prefix in `hostname`.
- `path_prefix` must start with `/` when non-empty. A trailing slash is safe and is stripped by the client.
- Check that reverse proxies preserve the prefix consistently for both `/server_info` and `/graphql`.

## Headers, Auth, and Unauthorized Responses

Symptoms:

- HTTP 401/403.
- GraphQL response has `__typename: UnauthorizedError`.
- Cloud or proxy access works in the browser but scripts fail.

Fixes:

- For Python, pass headers via `DagsterGraphQLClient(..., headers={...})` or pass a `requests.auth.AuthBase` instance via `auth=`.
- For CLI remote calls, `dagster-graphql` does not expose arbitrary header flags; use a Python client/script, a custom HTTP client, or a proxy that injects headers.
- Redact secrets in logs. Do not paste bearer tokens or API tokens into generated skill files, shell history, or handoff notes.
- Distinguish Dagster Plus/cloud authorization from local read-only mode. This sub-skill can identify `UnauthorizedError`, but cloud role/token administration should route to a cloud/deployment skill if available.

## Read-Only Mode Mutation Failures

Symptoms:

- Launch, terminate, reload, shutdown, schedule toggles, or asset wipe mutations fail with authorization-style errors.
- Queries still work.

Fixes:

- Check whether the webserver was started with `dagster-webserver --read-only`.
- Use read-only queries such as `version`, repository listing, run listing, or `get_run_status` for diagnostics.
- Do not work around read-only mode by issuing mutations through another client unless the user explicitly confirms they want a mutating operation against a writable target.

## GraphQL Response Errors

Symptoms:

- Response has top-level `errors`.
- Response object has `__typename` such as `PythonError`, `RunNotFoundError`, `RunConfigValidationInvalid`, `JobNotFoundError`, `PipelineNotFoundError`, `RunConflict`, or `UnauthorizedError`.
- `DagsterGraphQLClientError` wraps the response type and message/body.

Fixes:

- Always inspect `__typename`; Dagster GraphQL often returns typed error objects rather than only HTTP errors.
- For `RunConfigValidationInvalid`, validate the job's config shape and variable JSON; `runConfigData` is any-typed at GraphQL level but still must satisfy Dagster config schema.
- For job lookup ambiguity, pass `repository_location_name` and `repository_name` to `submit_job_execution` instead of relying on inference.
- For `RunNotFoundError`, verify the instance backing the webserver is the one that owns the run ID.
- For `PythonError`, read server/code-location logs; the problem may be in user definitions rather than in GraphQL syntax.

## Optional Dependency and API Drift Gaps

Symptoms:

- Client methods import but fail at runtime due to `gql`, `requests`, or transport errors.
- A query copied from older examples fails GraphQL validation.
- A low-level schema field differs from expected names.

Fixes:

- Prefer documented high-level `DagsterGraphQLClient` methods for common operations when possible.
- For raw GraphQL, explore the live schema in the `/graphql` playground or run a minimal introspection-safe query before assuming fields.
- Keep `dagster`, `dagster-graphql`, and `dagster-webserver` versions aligned in the same environment.
- Treat the GraphQL API as evolving; code defensively around response `__typename` and missing fields.

## Safe Escalation Checklist

Before running a mutating command or query:

1. Identify the target environment and URL.
2. Confirm whether the webserver is read-only or production-facing.
3. Confirm whether the operation launches, terminates, reloads, shuts down, wipes, or toggles state.
4. Prefer a read-only health query first.
5. Ask the user before issuing mutations against shared or production deployments.
