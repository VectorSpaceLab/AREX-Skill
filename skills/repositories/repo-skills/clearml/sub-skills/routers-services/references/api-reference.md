# Router and Service API Reference

## Optional Router Extra

ClearML installs the router surface as an optional dependency group. The base package can expose `Task.get_http_router()`, but router imports require the router extra:

```bash
python -m pip install "clearml[router]"
```

The extra installs these runtime dependencies: `fastapi>=0.115.2`, `uvicorn>=0.31.1`, and `httpx>=0.27.2`. If these are missing, `Task.get_http_router()` raises a ClearML `UsageError` with the message `Could not import HttpRouter. Please run pip install clearml[router]`.

Do not import `HttpRouter` from `clearml.router`; the router package initializer does not export it in this version. Use `Task.get_http_router()` from an initialized or current `Task` instead.

## Task Entry Points

### `Task.get_http_router()`

Use this method on the current ClearML Task to get a cached `HttpRouter` instance:

```python
from clearml import Task

task = Task.init(project_name="Serving", task_name="HTTP proxy")
router = task.get_http_router()
```

The method imports `clearml.router.router.HttpRouter` lazily and wraps import failures in the router-extra `UsageError`. It returns the same router object for repeated calls on the same Task.

### `Task.request_external_endpoint()`

Use this lower-level method when you already run a service on a port and want ClearML to request an external endpoint without configuring a local proxy:

```python
endpoint = task.request_external_endpoint(
    port=8000,
    protocol="http",
    wait=True,
    wait_interval_seconds=3.0,
    wait_timeout_seconds=90.0,
    static_route=None,
    endpoint_name="api",
)
```

Important parameters:

- `port`: local service port to expose.
- `protocol`: `"http"` or `"tcp"`; `HttpRouter.deploy()` uses only `"http"`.
- `wait`: when `True`, waits for server assignment and returns endpoint data or `None`.
- `static_route`: route name registered on the ClearML server, not a URL path; requires advanced router support and a server version that supports static routes.
- `endpoint_name`: optional identifier for multiple endpoints on one Task.

A successful wait returns a dictionary with `endpoint`, `browser_endpoint`, `port`, `protocol`, and `name`. Requesting an endpoint adds the `external_service` system tag to the Task.

### `Task.wait_for_external_endpoint()`

Use this to poll for one endpoint after a previous request:

```python
endpoint = task.wait_for_external_endpoint(
    wait_interval_seconds=3.0,
    wait_timeout_seconds=90.0,
    protocol="http",
    endpoint_name="api",
)
```

Use `protocol=None` only when you want to wait for both `http` and `tcp` endpoints; in that mode `endpoint_name` is not allowed. A timeout returns `None` for a single protocol or a partial list for multi-protocol waits.

### `Task.list_external_endpoints()`

Use this to inspect endpoints already assigned to a Task:

```python
for endpoint in task.list_external_endpoints(protocol="http"):
    print(endpoint["name"], endpoint["browser_endpoint"] or endpoint["endpoint"])
```

Each endpoint dictionary includes `endpoint`, `browser_endpoint`, `port`, `protocol`, and `name`. Passing `protocol=None` lists both HTTP and TCP endpoints.

## `HttpRouter` Methods

Get a router through `task.get_http_router()`. Avoid constructing `HttpRouter` directly.

### `set_local_proxy_parameters()`

```python
router.set_local_proxy_parameters(
    incoming_port=9000,
    default_target="http://localhost:8000",
    log_level="warning",
    access_log=False,
    enable_streaming=True,
)
```

Parameters:

- `incoming_port`: local proxy port. Defaults to `9000` when omitted.
- `default_target`: optional base URL for unmatched paths. When omitted, unmatched paths return 404.
- `log_level`: uvicorn log level such as `critical`, `error`, `warning`, `info`, `debug`, or `trace`.
- `access_log`: enables or disables uvicorn access logging.
- `enable_streaming`: forwards streaming responses with chunked transfer encoding when `True`.

Call this before `create_local_route()` or `deploy()`. Both route creation and deployment can start the proxy if it does not already exist.

### `create_local_route()`

```python
router.create_local_route(
    source="/v1/predict",
    target="http://localhost:8000/predict",
    request_callback=request_callback,
    response_callback=response_callback,
    endpoint_telemetry=False,
    error_callback=error_callback,
)
```

Parameters:

- `source`: path prefix on the proxy. ClearML registers both the exact source and `source/{path:path}` for common REST methods.
- `target`: upstream URL to receive proxied requests. The proxy appends a captured suffix when the request uses a nested path.
- `request_callback(request, persistent_state)`: optional pre-forward hook. It may be sync or async and may return a replacement FastAPI `Request`.
- `response_callback(response, request, persistent_state)`: optional post-forward hook. It may be sync or async and may return a replacement FastAPI `Response`.
- `error_callback(request, error, persistent_state)`: optional hook invoked when forwarding raises an exception.
- `endpoint_telemetry`: `True` for default telemetry, `False` to disable, or a dictionary of telemetry parameters.

All callbacks share one per-route `persistent_state` dictionary. Use it for small per-route counters or timing data, not for secrets or unbounded payload storage.

### `remove_local_route()`

```python
router.remove_local_route("/v1/predict")
```

This removes the local route mapping and stops endpoint telemetry for that route when telemetry is active. It does not revoke an external endpoint already requested from the ClearML server.

### `deploy()`

```python
endpoint = router.deploy(
    wait=True,
    wait_interval_seconds=3.0,
    wait_timeout_seconds=90.0,
    static_route=None,
)
```

`deploy()` ensures the local proxy is running and calls `Task.request_external_endpoint(port=<proxy-port>, protocol="http", ...)`. With `wait=False`, it returns `None` after requesting the endpoint. With `wait=True`, it returns endpoint data or `None` on timeout.

Use `static_route` only when a named route exists and is enabled on the ClearML server. The route name is validated by the backend router service and may fail if the server lacks advanced/static-route support.

### `wait_for_external_endpoint()` and `list_external_endpoints()`

`HttpRouter.wait_for_external_endpoint()` delegates to `Task.wait_for_external_endpoint(protocol="http", ...)`. `HttpRouter.list_external_endpoints()` delegates to `Task.list_external_endpoints(protocol="http")`.

## Proxy Internals to Account For

- The proxy backend is FastAPI + uvicorn + httpx.
- Starting the proxy creates a multiprocessing subprocess and binds uvicorn to `0.0.0.0` on the configured port.
- Supported REST methods are `GET`, `POST`, `PUT`, `DELETE`, `PATCH`, and `OPTIONS`.
- With a `default_target`, unmatched paths proxy to `default_target + request.url.path`.
- With `enable_streaming=False`, the proxy buffers request/response bodies instead of streaming upstream responses.

## Endpoint Telemetry Parameters

Pass `endpoint_telemetry=False` to disable telemetry. Pass a dictionary to enable telemetry with custom metadata:

```python
endpoint_telemetry={
    "endpoint_name": "predict",
    "model_name": "fraud-detector",
    "model_version": "2026-06",
    "input_type": "json",
    "report_statistics": False,
}
```

Supported keys include `endpoint_url`, `endpoint_name`, `model_name`, `model`, `model_url`, `model_source`, `model_version`, `app_id`, `app_instance`, `tags`, `system_tags`, `container_id`, `input_size`, `input_type`, `report_statistics`, `preprocess_artifact`, and `force_register`.

Telemetry registers a serving container and reports request counts, latency, uptime, and machine statistics through the current ClearML Task. It waits for an endpoint URL when one is not supplied, so disable telemetry for local tests that should not contact a server or wait on external routing.

## Service Task Surfaces

ClearML service examples use the same Task surface as other workflows:

```python
task = Task.init(project_name="DevOps", task_name="Cleanup Service", task_type=Task.TaskTypes.service)
# For remote service launch, hand off to the remote-execution sub-skill before calling:
# task.execute_remotely(queue_name="services", exit_process=True)
```

Useful task types for service-like code include `Task.TaskTypes.service` for long-running service jobs and `Task.TaskTypes.monitor` for monitor/alert loops. Long-running service launch, queues, agents, and `execute_remotely()` routing belong in the remote-execution sub-skill; scheduler/controller automation belongs in the automation-pipelines sub-skill.
