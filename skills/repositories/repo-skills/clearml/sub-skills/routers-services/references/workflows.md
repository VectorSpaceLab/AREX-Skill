# Router and Service Workflows

## Workflow: Distinguish Base Package vs Router Extra

Use this when `Task.get_http_router()` fails or the user asks whether the router is available.

1. Confirm the base package imports:

   ```bash
   python - <<'PY'
   import clearml
   from clearml import Task
   print(clearml.__version__)
   print(hasattr(Task, "get_http_router"))
   PY
   ```

2. Run the bundled import-only check:

   ```bash
   python sub-skills/routers-services/scripts/router_extra_check.py --json
   ```

3. Interpret results:

   - `clearml_importable=true` and missing `fastapi`, `uvicorn`, or `httpx` means the base package is installed but `clearml[router]` is not complete.
   - A direct import such as `from clearml.router import HttpRouter` can fail even when router files exist because the package `__init__` does not export `HttpRouter` in this version.
   - The supported entry point is `Task.get_http_router()` after installing the optional router dependencies.

4. Fix the environment with the optional extra:

   ```bash
   python -m pip install "clearml[router]"
   ```

## Workflow: Plan a Local Proxy Route Without Starting It

Use the planner before touching live ports or ClearML endpoints:

```bash
python sub-skills/routers-services/scripts/router_plan.py \
  --project "Serving" \
  --task-name "Local predict proxy" \
  --incoming-port 9000 \
  --source /v1/predict \
  --target http://localhost:8000/predict \
  --default-target http://localhost:8000 \
  --telemetry false \
  --callbacks
```

The script prints a code snippet only. It never imports ClearML router modules, starts uvicorn, binds a port, or contacts a server.

When adapting the snippet:

- Keep `source` as the proxy-facing path prefix, such as `/v1/predict`.
- Keep `target` as the upstream local URL, such as `http://localhost:8000/predict`.
- Choose a unique `incoming_port`; default router examples use `9000`.
- Set `endpoint_telemetry=False` for local tests and CI-like dry runs.
- Add a `default_target` only when unmatched paths should still proxy to the local service; otherwise leave it unset so unmatched paths return 404.

## Workflow: Build the Live Local Proxy

Use this only after dependencies and port choice are confirmed.

```python
import time
from clearml import Task

def request_callback(request, persistent_state):
    persistent_state["started_at"] = time.time()

def response_callback(response, request, persistent_state):
    started_at = persistent_state.pop("started_at", None)
    if started_at is not None:
        print("proxy latency", time.time() - started_at)

def error_callback(request, error, persistent_state):
    persistent_state["last_error"] = repr(error)

task = Task.init(project_name="Serving", task_name="Local predict proxy")
router = task.get_http_router()
router.set_local_proxy_parameters(
    incoming_port=9000,
    default_target="http://localhost:8000",
    log_level="warning",
    access_log=False,
)
router.create_local_route(
    source="/v1/predict",
    target="http://localhost:8000/predict",
    request_callback=request_callback,
    response_callback=response_callback,
    error_callback=error_callback,
    endpoint_telemetry=False,
)
endpoint = router.deploy(wait=True, wait_timeout_seconds=90.0)
print(endpoint)
```

Expected behavior:

- The proxy binds to `0.0.0.0:<incoming_port>`.
- Requests to `/v1/predict` and nested paths under it proxy to the target URL.
- `deploy(wait=True)` requests an HTTP external endpoint and returns endpoint data or `None` after timeout.
- `endpoint_telemetry=False` prevents endpoint telemetry registration/reporting for the route.

## Workflow: Use Request, Response, and Error Callbacks

Callbacks can be synchronous or async. All callbacks for one route receive the same `persistent_state` dictionary.

Good callback uses:

- Store request start time in `request_callback` and report latency in `response_callback`.
- Add lightweight counters in `persistent_state`.
- Return a replacement FastAPI `Response` when the upstream result needs a controlled transformation.
- Record an error summary in `error_callback` for debugging.

Avoid these callback patterns:

- Storing full request or response bodies in `persistent_state` indefinitely.
- Printing secrets, headers with tokens, or raw user payloads.
- Performing long blocking work inside callbacks; it stalls proxy forwarding.
- Returning plain dictionaries when the proxy expects a FastAPI `Request` or `Response` object for replacement.

If a response callback changes response content, update `Content-Length` consistently or construct a new `fastapi.Response` so FastAPI handles headers correctly.

## Workflow: Configure Endpoint Telemetry

Use telemetry when the route represents a model/service endpoint that should appear in ClearML serving telemetry.

```python
router.create_local_route(
    source="/predict",
    target="http://localhost:8000/predict",
    endpoint_telemetry={
        "endpoint_name": "predict",
        "model_name": "fraud-detector",
        "model_version": "2026-06",
        "input_type": "json",
        "report_statistics": True,
    },
)
```

Telemetry reports request counts, latency, uptime, and machine statistics. It may wait for an endpoint URL and send serving API calls through the current ClearML Task session, so use `endpoint_telemetry=False` when:

- Running a local-only proxy test.
- The user has no configured ClearML server credentials.
- The route is not a model/service endpoint.
- Network calls are unsafe or unwanted.

If no external endpoint is requested but telemetry is still desired, provide `endpoint_url` in the telemetry dictionary so telemetry does not wait for server-populated endpoint data.

## Workflow: Deploy, Wait, List, and Remove

### Deploy and Wait

```python
endpoint = router.deploy(
    wait=True,
    wait_interval_seconds=3.0,
    wait_timeout_seconds=90.0,
)
if endpoint is None:
    print("No endpoint assigned before timeout")
else:
    print(endpoint["browser_endpoint"] or endpoint["endpoint"])
```

Use shorter wait timeouts for tests and longer timeouts only for real service deployment.

### List Assigned HTTP Endpoints

```python
for endpoint in router.list_external_endpoints():
    print(endpoint["name"], endpoint["port"], endpoint["browser_endpoint"] or endpoint["endpoint"])
```

For multiple endpoints without a local proxy, use Task methods:

```python
task.request_external_endpoint(port=8000, protocol="http", endpoint_name="primary", wait=True)
task.request_external_endpoint(port=8001, protocol="http", endpoint_name="api", wait=True)
print(task.list_external_endpoints(protocol="http"))
```

### Remove a Local Route

```python
router.remove_local_route("/v1/predict")
```

This stops the local route and route telemetry. It does not remove already requested external endpoint metadata from the ClearML server. Treat endpoint lifecycle cleanup as a server/admin concern unless the SDK adds a specific revoke API.

## Workflow: Use Static Routes Safely

Static routes are named ClearML server router routes, not proxy path prefixes. Use them only when the server has a matching enabled static route:

```python
endpoint = router.deploy(wait=True, static_route="prod-predict")
```

Failure signals include unsupported server version, missing route name, disabled route, or an active route that is not load-balanced. If the user is only mapping `/v1/predict` to a local service, use `create_local_route(source="/v1/predict", ...)` instead of `static_route`.

## Workflow: Package Long-Running Service Patterns

ClearML service examples show three recurring patterns:

- Cleanup service: `Task.init(..., task_type=Task.TaskTypes.service)`, connect a small config dictionary, optionally enqueue itself on a `services` queue, then run a bounded sleep loop.
- Monitoring service: `Task.init(..., task_type=Task.TaskTypes.monitor)`, parse credentials/options, optionally execute remotely on a services queue, then call a monitor loop.
- Autoscaler service: collect cloud/queue configuration, store it on the Task, optionally run remotely as a service, then start the autoscaler loop.

When the user asks for service code structure:

1. Keep local validation and configuration parsing separate from the infinite loop.
2. Initialize a `service` or `monitor` Task so the run is categorized correctly.
3. Connect only non-secret configuration with `task.connect()` or configuration objects.
4. Hand off remote queue launch details to the remote-execution sub-skill.
5. Add explicit stop conditions, sleep intervals, and dry-run modes when possible.
6. Avoid running cloud, Slack, cleanup, autoscaler, or infinite-loop examples as verification targets without user approval and credentials.

## Workflow: Decide Router vs Direct Endpoint Request

Use `HttpRouter` when the user needs:

- Path-based local proxying.
- Request/response/error callbacks.
- Endpoint telemetry per proxied route.
- A default target for unmatched paths.

Use `Task.request_external_endpoint()` directly when the user already has a service listening on a port and only needs ClearML to expose or track the endpoint.
