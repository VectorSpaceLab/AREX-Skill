# Router and Service Troubleshooting

## `Could not import HttpRouter. Please run pip install clearml[router]`

Likely causes:

- The base `clearml` package is installed without the optional router extra.
- One or more router dependencies are missing: `fastapi`, `uvicorn`, or `httpx`.
- Code imports `HttpRouter` from `clearml.router`, which does not export the class in this version.

Checks:

```bash
python sub-skills/routers-services/scripts/router_extra_check.py --json
```

Recovery:

```bash
python -m pip install "clearml[router]"
```

Then use:

```python
from clearml import Task
router = Task.current_task().get_http_router()
```

Do not use:

```python
from clearml.router import HttpRouter
```

## FastAPI, Uvicorn, or HTTPX Import Errors

Symptoms include `ModuleNotFoundError: No module named 'fastapi'`, `uvicorn`, or `httpx`, or the same `UsageError` from `Task.get_http_router()`.

Recovery:

- Install `clearml[router]` into the same Python environment that runs the service.
- Verify with `router_extra_check.py`; the script reports dependency names without starting a proxy.
- If a deployment image or ClearML Agent queue is used, ensure the image/requirements include `clearml[router]`, not just `clearml`.

## Port Already in Use

Symptoms include uvicorn startup errors such as address already in use or a proxy that never accepts requests.

Likely causes:

- Another local process already listens on the configured `incoming_port`.
- A previous proxy subprocess is still alive.
- Multiple services share the default `9000` router port.

Recovery:

- Choose a unique `incoming_port` in `router.set_local_proxy_parameters()`.
- Stop the previous service/proxy process before starting a new one.
- Use `default_target` carefully; it does not change the listening port.
- Generate a plan with `router_plan.py --incoming-port <port>` before changing live code.

## Route Does Not Match Requests

Symptoms include 404 from the proxy, traffic going to the default target, or callbacks not running.

Likely causes:

- `source` does not start with `/` or does not match the requested prefix.
- The request path is sent to the upstream service directly instead of the proxy port.
- No route exists and no `default_target` is configured.

Recovery:

- Use `source="/v1/predict"` for proxy requests sent to `http://<proxy-host>:<incoming-port>/v1/predict`.
- Remember that ClearML registers both the exact source and nested paths under it.
- Use `default_target` only for unmatched paths that should still proxy somewhere.
- Remove/recreate a route with the same `source` if callback or target behavior needs to change.

## Callback Failures

Symptoms include 500 responses, stalled proxy requests, missing latency values, or exceptions from callback code.

Likely causes:

- Callback signature does not accept `persistent_state`.
- `response_callback` assumes `request_callback` already populated a key.
- Callback returns a plain object instead of a FastAPI `Request` or `Response` when replacing data.
- Callback performs slow blocking work or stores unbounded payloads.

Recovery:

- Use `request_callback(request, persistent_state)`, `response_callback(response, request, persistent_state)`, and `error_callback(request, error, persistent_state)`.
- Guard reads from `persistent_state` with `.get()` or `.pop(..., None)`.
- Return `None` to keep the original request/response, or return a proper FastAPI object when replacing one.
- Keep callbacks lightweight and avoid printing credentials, headers, or raw payloads.

## Endpoint Telemetry Hangs or Sends Unexpected Server Calls

Symptoms include the route waiting for endpoint metadata, serving-registration failures, or unwanted server traffic during local tests.

Likely causes:

- `endpoint_telemetry=True` is the default for `create_local_route()`.
- No external endpoint URL is available yet, so telemetry waits for one.
- ClearML server credentials or serving APIs are unavailable.
- The route is a local smoke test, not a real served endpoint.

Recovery:

- Pass `endpoint_telemetry=False` for local tests and dry runs.
- If telemetry is required without waiting for server assignment, pass an explicit `endpoint_url` in the telemetry dictionary.
- Use `report_statistics=False` when request/resource statistics are not needed.
- Confirm ClearML server credentials and feature support before enabling telemetry in production.

## `deploy(wait=True)` or `wait_for_external_endpoint()` Times Out

Symptoms include `None` returned after the timeout or warnings about no endpoint assignment.

Likely causes:

- No ClearML router/agent/server component assigned an external endpoint.
- The server feature set does not support external endpoint routing.
- The wait timeout is too short for the environment.
- `endpoint_name` does not match the requested endpoint.

Recovery:

- Use `wait=False` when only requesting endpoint registration and a later poll is acceptable.
- Increase `wait_timeout_seconds` for real deployments; keep it short for tests.
- Call `task.list_external_endpoints(protocol="http")` or `router.list_external_endpoints()` to inspect current assignments.
- For named endpoints, pass the same `endpoint_name` to request and wait calls when using the lower-level Task API.

## Static Route Errors

Symptoms include `ValueError` for missing, disabled, unsupported, or non-load-balanced static routes.

Likely causes:

- `static_route` names a route that is not registered on the ClearML server.
- The route exists but is disabled.
- The server version or feature set does not support static routes.
- The route is active but not load-balanced.

Recovery:

- Treat `static_route` as a server-side route name, not a local URL path.
- Use regular `create_local_route(source="/path", ...)` for local proxy path routing.
- Ask the ClearML administrator to create/enable/load-balance the static route before using it.

## Long-Running Service Safety

Symptoms include runaway cleanup/monitor/autoscaler loops, accidental deletion, unexpected cloud activity, or remote queue jobs that cannot be stopped easily.

Recovery checklist:

- Add `--local`, `--dry-run`, or equivalent switches for service scripts when designing new code.
- Keep destructive actions such as task cleanup behind explicit `force_delete` or dry-run checks.
- Store cloud/Slack/API secrets in approved secret stores or environment variables, never in skill snippets or public config examples.
- Use a clear sleep interval and stop mechanism for loops.
- Route queue launch and ClearML Agent behavior to the remote-execution sub-skill before calling `execute_remotely()`.

## Server Credentials and Feature Support

Router deployment, endpoint waits, static routes, and telemetry all require a configured ClearML client session and supporting server features. If local planning works but deployment fails:

- Confirm `Task.init()` succeeds in the target environment.
- Confirm the user has access to the ClearML server project/queue/service features.
- Prefer plan-only snippets until credentials and server access are confirmed.
- Do not run examples that require live servers, cloud credentials, Slack credentials, or infinite loops as verification without explicit user approval.
