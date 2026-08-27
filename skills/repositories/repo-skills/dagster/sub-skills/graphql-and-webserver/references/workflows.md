# Workflows and API Reference

This reference covers safe Dagster webserver startup and GraphQL access patterns. Use it with the router in `../SKILL.md` and the failure guide in `troubleshooting.md`.

## Webserver Startup

`dagster-webserver` loads a Dagster workspace/code location and serves both the UI and GraphQL API.

Common local patterns:

```bash
dagster-webserver --help
dagster-webserver -p 3000 -h 127.0.0.1 -w workspace.yaml
dagster-webserver -p 3333 -f path/to/definitions.py -a defs
dagster-webserver -m my_package.definitions -a defs --uvicorn-log-level info
```

Important serving flags:

- `--host` / `-h`: bind host; default is loopback for local-only serving.
- `--port` / `-p`: port; default is `3000` when not explicitly provided.
- `--path-prefix` / `-l`: non-root serving prefix such as `/dagster`; clients must include the same prefix.
- `--read-only`: starts with mutations such as launching runs and toggling schedules disabled.
- `--uvicorn-log-level` / `--log-level`: webserver log level: `critical`, `error`, `warning`, `info`, `debug`, or `trace`.
- `--dagster-log-level`: Dagster event log level: `critical`, `error`, `warning`, `info`, or `debug`; can also come from `DAGSTER_WEBSERVER_LOG_LEVEL`.
- `--log-format`: `colored`, `json`, or `rich`.
- `--code-server-log-level`: log level for code servers spawned by the webserver.
- `--db-statement-timeout`, `--db-pool-recycle`, `--db-pool-max-overflow`: instance database tuning knobs; use only when diagnosing storage/backend issues.
- `--live-data-poll-rate`: UI polling interval in milliseconds.
- `--suppress-warnings`: filters Python warnings while hosting.

Workspace target flags are shared with other Dagster CLIs. Keep the same target flags across validation, webserver startup, and GraphQL CLI calls to avoid loading a different repository than intended.

## GraphQL Endpoint Basics

The webserver exposes GraphQL at `/graphql`. With a path prefix, the endpoint becomes `<base-url>/<prefix>/graphql`, for example `http://localhost:3000/dagster/graphql`.

Use the browser GraphQL playground at the same `/graphql` route for schema exploration in a development environment. For scripted checks, prefer small read-only queries:

```graphql
query VersionQuery {
  version
}
```

```graphql
query RepositoriesQuery {
  repositoriesOrError {
    __typename
    ... on RepositoryConnection {
      nodes {
        name
        location { name }
      }
    }
    ... on PythonError { message }
  }
}
```

## `dagster-graphql` CLI

`dagster-graphql` executes a GraphQL document against either a locally loaded workspace or a remote `dagster-webserver`.

Run help first when uncertain:

```bash
dagster-graphql --help
```

Choose exactly one query source:

```bash
dagster-graphql --text 'query { version }' -w workspace.yaml
dagster-graphql --file query.graphql -f path/to/definitions.py -a defs
dagster-graphql --predefined launchPipelineExecution --variables '{"executionParams": {...}}' -w workspace.yaml
```

Useful flags:

- `--text` / `-t`: inline GraphQL document.
- `--file`: read the GraphQL document from a file.
- `--predefined` / `-p`: use a predefined query; currently includes `launchPipelineExecution`.
- `--variables` / `-v`: JSON-encoded variables string.
- `--remote` / `-r`: base URL for a remote webserver.
- `--output` / `-o`: write the response to a file, useful when logs would mix with stdout.
- `--ephemeral-instance`: use an ephemeral local Dagster instance for local workspace execution instead of resolving from `DAGSTER_HOME`.

Remote query example:

```bash
dagster-graphql \
  --remote http://localhost:3000 \
  --text 'query { version }'
```

For a webserver behind a prefix, include the prefix in the remote base URL:

```bash
dagster-graphql \
  --remote http://localhost:3000/dagster \
  --text 'query { version }'
```

The CLI remote path performs a sanity check against `/server_info` and posts the GraphQL body to `/graphql` relative to the supplied base URL. If the URL omits `http://` or `https://`, the CLI rejects it before querying.

## Python Client

Use `DagsterGraphQLClient` when a Python script needs higher-level methods for common Dagster operations.

Constructor shape:

```python
from dagster_graphql import DagsterGraphQLClient

client = DagsterGraphQLClient(
    hostname="localhost",
    port_number=3000,
    use_https=False,
    timeout=300,
    headers=None,
    auth=None,
    path_prefix="",
)
```

Supported constructor options:

- `hostname`: host without scheme, for example `localhost` or a deployment hostname.
- `port_number`: optional port; omit when the host already routes to the service port.
- `transport`: optional custom `gql` transport for advanced cases.
- `use_https`: builds an `https://` URL when true.
- `timeout`: request timeout in seconds.
- `headers`: extra HTTP headers; use this for bearer tokens, organization headers, or API tokens when appropriate.
- `auth`: `requests.auth.AuthBase` instance for custom HTTP authentication.
- `path_prefix`: non-root prefix. It must start with `/` when non-empty; a trailing slash is stripped.

Path-prefix examples:

```python
DagsterGraphQLClient("localhost", port_number=3000)._url
# http://localhost:3000/graphql

DagsterGraphQLClient("localhost", port_number=3000, path_prefix="/dagster")._url
# http://localhost:3000/dagster/graphql
```

Common methods:

```python
from dagster_graphql import DagsterGraphQLClient, DagsterGraphQLClientError

client = DagsterGraphQLClient("localhost", port_number=3000)

try:
    status = client.get_run_status("<run-id>")
except DagsterGraphQLClientError as exc:
    # exc.args often contain GraphQL __typename and message/body details.
    raise
```

Higher-level methods include:

- `get_run_status(run_id)`: returns a `DagsterRunStatus`; raises if the run is not found or the server returns a Python error.
- `submit_job_execution(...)`: launches a job run; can infer repository location/name only when the job name is unique.
- `reload_repository_location(repository_location_name)`: reloads repositories in a location.
- `shutdown_repository_location(repository_location_name)`: asks a code location server to shut down; rely on deployment supervision for restart.
- `terminate_run(run_id)` and `terminate_runs(run_ids)`: terminate active runs.

## Headers, Auth, HTTPS, and Path Prefixes

For Python client requests to a prefixed or authenticated endpoint:

```python
from dagster_graphql import DagsterGraphQLClient

client = DagsterGraphQLClient(
    "example.internal",
    use_https=True,
    path_prefix="/dagster",
    headers={"Authorization": "Bearer <redacted>"},
)
status = client.get_run_status("<run-id>")
```

Guidelines:

- Do not include `http://` or `https://` in the Python client `hostname`; use `use_https=True` for HTTPS.
- Do include the path prefix in `path_prefix`, not in `hostname`.
- For `dagster-graphql --remote`, pass a full base URL with scheme, host, optional port, and optional prefix.
- Redact tokens in logs and handoffs. Prefer environment variables or secret managers to literal headers.

## Read-Only Webserver Behavior

`dagster-webserver --read-only` allows inspection workflows but disables mutations such as launching runs and schedule toggles. When a mutation unexpectedly returns an authorization-style error, check whether the target webserver was intentionally started in read-only mode before debugging cloud auth or user permissions.

Safe read-only operations include version checks, repository/job listing, and run-status queries. Mutating operations include launch, terminate, reload, shutdown, schedule/sensor toggles, and asset wipes.

## Safe Helper Script

Use the bundled helper to print the exact remote CLI command before querying:

```bash
python scripts/graphql_health_check.py --url http://localhost:3000 --dry-run
python scripts/graphql_health_check.py --url http://localhost:3000/dagster --query version --dry-run
```

`--dry-run` intentionally refuses `--header` because `dagster-graphql` does not expose arbitrary remote header flags. For authenticated checks, either run this helper without `--dry-run` after confirming the target is safe, or write a Python client call with explicit redaction.

Run a real read-only HTTP query only when the user confirms the target URL is safe:

```bash
python scripts/graphql_health_check.py --url http://localhost:3000 --query version
```
