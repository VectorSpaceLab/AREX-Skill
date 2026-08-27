# SDK and API Server Reference

This reference distills SkyPilot's Python SDK and API server surfaces for future agents. It is self-contained; use the bundled inspection script to verify a locally installed SkyPilot package without starting the API server.

## Request Lifecycle

Most public SDK operations submit work to the SkyPilot API server and return a `RequestId[T]`. The request's final value is retrieved separately.

| Need | Pattern | Notes |
| --- | --- | --- |
| Submit and later inspect | `request_id = sky.launch(task, ...)` | Returns quickly after the request is accepted by the API server. |
| Wait for structured result | `result = sky.get(request_id)` | Raises the same request-side exception if the request failed or was cancelled. |
| Stream logs and return result | `result = sky.stream_and_get(request_id)` | Blocks, streams console logs, and returns the final request value when `follow=True`. |
| Query API request history | `sky.api_status(...)` or `sky api status` | Use request IDs or prefixes; filter fields/cluster when supported by the server. |
| Cancel API requests | `sky.api_cancel(request_ids)` or `sky api cancel` | Cancels API-server request records, not necessarily every cloud resource. Pair with operational cleanup guidance. |

Avoid passing `None` to `stream_and_get()` in multi-user or remote-server environments; it streams the latest request and can select another user's or process's request.

## Core SDK Equivalents

| CLI intent | Python SDK shape | Result handling |
| --- | --- | --- |
| `sky launch -c CLUSTER task.yaml` | `task = sky.Task.from_yaml('task.yaml'); request_id = sky.launch(task, cluster_name='CLUSTER')` | `job_id, handle = sky.get(request_id)` |
| `sky launch --dryrun ...` | `request_id = sky.launch(task, cluster_name='CLUSTER', dryrun=True)` | `sky.stream_and_get(request_id)` if the user wants optimizer/log output. |
| `sky exec CLUSTER task.yaml` | `request_id = sky.exec(task, cluster_name='CLUSTER')` | `job_id, handle = sky.get(request_id)` |
| `sky status CLUSTER` | `request_id = sky.status(['CLUSTER'])` | `clusters = sky.get(request_id)` |
| `sky start CLUSTER` | `request_id = sky.start('CLUSTER')` | `handle = sky.get(request_id)` |
| `sky stop CLUSTER` | `request_id = sky.stop('CLUSTER')` | `sky.get(request_id)` |
| `sky down CLUSTER` | `request_id = sky.down('CLUSTER')` | `sky.get(request_id)` after confirming deletion semantics. |
| `sky logs CLUSTER JOB_ID` | `sky.tail_logs('CLUSTER', job_id=JOB_ID, follow=True)` | Returns status or an iterator depending on `preload_content`/follow usage. |
| `sky jobs launch ...` | `sky.jobs.launch(task, name='JOB')` | `job_ids, handle = sky.get(request_id)`; route details to `managed-jobs`. |
| `sky serve up ...` | `sky.serve.up(task, service_name='SERVICE')` | `service_name, endpoint = sky.get(request_id)`; route details to `serving`. |

The public constructors `sky.Task`, `sky.Task.from_yaml(...)`, `sky.Task.from_yaml_config(...)`, `sky.Resources(...)`, and `sky.Storage(...)` cover common programmatic workflows. Keep detailed field validation in `task-yaml`; this sub-skill owns the request lifecycle and server-facing behavior.

## API Server Commands and SDK Calls

| CLI command | SDK function | Use when |
| --- | --- | --- |
| `sky api start` | `sky.api_start()` | Start the default local API server and dashboard. |
| `sky api start --deploy` | `sky.api_start(deploy=True)` | Bind for remote access; review authentication/network exposure first. |
| `sky api stop` | `sky.api_stop()` | Stop only the default local API server. It refuses remote endpoints. |
| `sky api logs` | `sky.api_server_logs(follow=True, tail=N)` | Inspect local server logs or stream remote server log path through the server. |
| `sky api status` | `sky.api_status(...)` | List API requests, optionally by request ID, status history, limit, fields, or cluster. |
| `sky api cancel` | `sky.api_cancel(...)` | Abort one or more API requests. |
| `sky api login -e URL` | `sky.api_login(endpoint=URL)` | Persist a remote API server endpoint for CLI and SDK. |
| `sky api logout` | `sky.api_logout()` | Clear remote endpoint/cookies; local servers use `sky api stop`. |
| `sky api info` | `sky.api_info()` | Read server health, API version, package version, commit, and user identity. |
| `sky dashboard` | `sky.dashboard(starting_page=None)` | Open the dashboard URL for the configured API server. |

`sky.api_start()` validates local hosts and refuses to start a local server while a remote endpoint is configured. Clear the remote endpoint or unset `SKYPILOT_API_SERVER_ENDPOINT` before starting a local server.

## Remote Server Login and Endpoint Selection

- `sky.api_login(endpoint='https://...')` stores the endpoint in SkyPilot config and makes future CLI/SDK calls use that API server.
- `SKYPILOT_API_SERVER_ENDPOINT` temporarily overrides the endpoint. Login/logout intentionally refuse to modify persistent config while this environment variable is set because the source of truth is ambiguous.
- Remote login supports service account tokens via `sky.api_login(endpoint=..., service_account_token='sky_...')`, OAuth/browser flows, and no-browser/manual fallback flows depending on server capability.
- Use `sky.api_info()` after login to confirm the endpoint, health, API version, SkyPilot version, commit, and authenticated user.
- For local testing of remote behavior, connect to an alternate forwarded endpoint with `sky api login -e http://host:port`, then switch back or logout when done.

## Async SDK

`sky.client.sdk_async` mirrors many synchronous SDK calls and returns awaitable values. Many convenience wrappers submit the underlying request, stream logs by default, and return the final result rather than exposing a raw request ID.

```python
from sky.client import sdk_async as sky_async

job_id, handle = await sky_async.launch(task, cluster_name='demo', dryrun=True)
clusters = await sky_async.status(['demo'])
requests = await sky_async.api_status(limit=10)
```

Use `StreamConfig` with async methods that support log streaming. If `stream_logs` is `None`, those wrappers return `await get(request_id)` without streaming. When the code already has a request ID string, call `await sky_async.get(request_id)` or `await sky_async.stream_and_get(request_id)` explicitly.

## API Versioning and Compatibility

SkyPilot clients and servers exchange version headers on REST calls. The server exposes an API version and minimum compatible version, and the client records the remote API version during communication.

Key rules for future agents:

- Use `sky.api_info()` or `sky api info` to inspect remote status and versions before diagnosing compatibility problems.
- New SDK functions may be decorated with a minimum API version. Against older remote servers they raise `APINotSupportedError` with an upgrade/downgrade hint.
- Some newer arguments are handled with soft compatibility: for example, older servers may ignore unsupported filters or fields after warning.
- If the client is too old for a newer server, upgrade the local SkyPilot package. If the server is too old for a newer client, ask the server administrator to upgrade the server or downgrade the client to a compatible release.
- When modifying the source repo, new APIs must preserve backward compatibility and should use API-version gates; route source changes to `repo-development`.

## Dashboard and Deployment Notes

- The local API server serves the dashboard under `/dashboard` on the configured server URL.
- In a source checkout, dashboard static output must be rebuilt before restarting the API server when dashboard code changed: `npm --prefix sky/dashboard install` then `npm --prefix sky/dashboard run build`, followed by `sky api stop` and `sky api start`.
- For Docker or Kubernetes deployments, the API server is normally started with `sky api start --deploy --foreground` inside the container/pod.
- For production/high availability deployments, back the API server with PostgreSQL and preserve configured Helm values on upgrade. Use `helm upgrade ... --reuse-values` when updating an existing deployment so database, credentials, auth, and storage settings are not lost.
- API server resource sizing matters most when the remote API server manages jobs directly. If a separate remote jobs controller is used, API server resources mainly affect request handling and dashboard/API latency.

## Safe Conversion Checklist

When converting a CLI launch/status/jobs flow to Python SDK:

1. Convert the YAML or inline command to `sky.Task.from_yaml(...)` or `sky.Task(...)` with `sky.Resources(...)`.
2. Decide whether the flow is cluster, managed jobs, or serve; use this sub-skill only for request/server mechanics and route behavior-specific flags to the owning sub-skill.
3. Submit with the matching SDK function and store the returned `RequestId`.
4. Use `sky.stream_and_get(request_id)` for user-visible provisioning/job logs or `sky.get(request_id)` for quiet structured results.
5. Add `sky.api_info()` or `sky.api_status(limit=...)` checks when the code must work against remote servers.
6. Avoid `stream_and_get(None)` and other latest-request shortcuts in shared API server environments.
7. Provide cleanup using SDK equivalents such as `sky.stop(...)`, `sky.down(...)`, `sky.jobs.cancel(...)`, or `sky.serve.down(...)`, with destructive actions confirmed by the user.
