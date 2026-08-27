# Client workflows and result contracts

Read this reference for concrete Python client usage. The signatures below are
verified against Earth2Studio 0.18.0a0. The service still controls which
workflow names and parameters are actually available.

## Install and discover

Install the optional client/server surface without assuming model extras:

```bash
uv pip install 'earth2studio[serve]'
```

The client needs `requests`; remote Zarr reads use the package's xarray/fsspec
stack and may use `aiohttp` for longer HTTP timeouts. Before submitting a model
request, make these read-only calls (with the endpoint and token supplied by a
secure runtime mechanism):

```python
from earth2studio.serve.client.client import Earth2StudioClient

client = Earth2StudioClient(
    base_url=api_url,
    workflow_name="<workflow returned by discovery>",
    timeout=60.0,
    max_retries=5,
    retry_backoff_factor=1.0,
    token=api_token,                 # omit when the gateway does not require it
)
print(client.health_check())
```

The HTTP discovery endpoints are:

- `GET /v1/infer/workflows` → `{"workflows": {name: description}}` for exposed
  workflows.
- `GET /v1/infer/{workflow_name}/schema` → the JSON Schema generated from the
  workflow's Pydantic `Parameters` model.
- `GET /health` and `GET /readiness` → a health response with `status` and
  `timestamp`; unhealthy responses use HTTP 503. `GET /liveness` only reports
  that the API process is alive. `GET /metrics` returns Prometheus text.

## Low-level asynchronous request

`InferenceRequest` serializes NumPy arrays, Python/numpy datetime and timedelta
values, and NumPy scalar values to JSON. It is still the workflow's schema that
decides whether a resulting value is valid.

```python
import time

from earth2studio.serve.client.client import Earth2StudioClient
from earth2studio.serve.client.models import InferenceRequest, RequestStatus

request = InferenceRequest(parameters={
    "forecast_times": ["2025-08-21T06:00:00"],
    "nsteps": 10,
    # Add only fields returned by the discovered workflow schema.
})

with Earth2StudioClient(api_url, workflow_name=workflow_name, token=api_token) as client:
    health = client.health_check()
    response = client.submit_inference_request(request)
    execution_id = response.execution_id
    print(response.status.value, execution_id)

    # For UI/monitoring control, poll yourself and expose progress.
    status = client.get_request_status(execution_id)
    while status.status not in {
        RequestStatus.COMPLETED,
        RequestStatus.FAILED,
        RequestStatus.CANCELLED,
    }:
        print(status.status.value, status.progress)
        # Choose a sleep interval appropriate to the workload.
        time.sleep(10.0)
        status = client.get_request_status(execution_id)

    if status.status != RequestStatus.COMPLETED:
        raise RuntimeError(status.error_message or status.status.value)
    result = client.get_request_results(execution_id, timeout=300.0)
```

For ordinary callers, avoid duplicating the loop:

```python
result = client.run_inference_sync(
    request,
    poll_interval=10.0,
    timeout=3600.0,
)
```

`wait_for_completion()` checks status every five seconds by default. Its
`timeout` is a total wait bound; on expiry it raises `RequestTimeoutError`.
`get_request_results()` raises an `Earth2StudioAPIError` for HTTP 202, because
results are not ready yet. `wait_for_completion()` raises an API error for
failed or cancelled executions. A status request may report
`accepted`, `queued`, `running`, `pending_results`, `completed`, `failed`, or
`cancelled`; the server can also retain an `expired` status even though the
client enum does not model it.

## Result manifest and files

The result model is:

- `InferenceRequestResults(request_id, status, output_files,
  completion_time, execution_time_seconds=None, storage_type=SERVER,
  signed_url=None)`.
- `OutputFile(path, size)` for each manifest entry.
- `result.result_paths()` returns one path per discovered `.zarr` root plus
  `.nc` files. It intentionally does not return every Zarr chunk.
- `client.result_root_path(result)` returns the relative path
  `/v1/infer/{workflow_name}/{request_id}/results/`.

Download a known file without writing to the working directory:

```python
for entry in result.output_files:
    buffer = client.download_result(result, entry.path, timeout=300.0)
    print(entry.path, entry.size, len(buffer.getbuffer()))
```

The returned `io.BytesIO` is in memory. A caller handling large NetCDF or
arbitrary binary outputs should provide its own bounded storage strategy rather
than assuming this helper streams to disk.

The server result endpoint first returns JSON metadata at
`.../results`; a specific file or the complete zip is served at
`.../results/{filepath}`. Results may be unavailable with HTTP 202 while queued,
running, or in `pending_results`; HTTP 400 after expiry; or HTTP 404 for a
failed, cancelled, missing, or non-exposed execution.

## High-level Earth2Studio interface

`RemoteEarth2Workflow` is useful when remote results feed local Earth2Studio
components:

```python
from earth2studio.serve.client.e2client import RemoteEarth2Workflow

remote = RemoteEarth2Workflow(
    base_url=api_url,
    workflow_name=workflow_name,
    device="cuda",                 # choose cpu when no local CUDA is available
    xr_args={"decode_coords": False},
    timeout=60.0,
    max_retries=5,
    token=api_token,
)
remote_result = remote(
    forecast_times=["2025-08-21T06:00:00"],
    nsteps=10,
)
print(remote_result.execution_id)
ds = remote_result.as_dataset()       # waits lazily until result is complete
source = remote_result.as_data_source()  # InferenceOutputSource
model = remote_result.as_model(iter_coord="lead_time")
for tensor, coords in model.create_iterator():
    pass
```

Calling `remote.to("cpu")` or `remote.to(torch.device("cuda"))` changes the
local tensor device and returns the same workflow object; it does not move the
server's model. `RemoteEarth2WorkflowResult` caches the completed result after
its first wait. Recreate it later with the same workflow and saved execution ID:

```python
from earth2studio.serve.client.e2client import RemoteEarth2WorkflowResult
remote_result = RemoteEarth2WorkflowResult(remote, saved_execution_id)
```

`as_dataset()` accepts only `.zarr` and `.nc` result paths. For Zarr, the
server-storage path is opened with `xarray.open_zarr` over HTTP and carries the
client Bearer token into storage options when present. For S3, the result's
signed URL is converted to an fsspec mapper. For NetCDF, the client downloads
one file and opens it with the `netcdf4` engine. `xr_args` are passed to the
relevant xarray open call.

`as_data_source()` wraps the dataset as `InferenceOutputSource`. `as_model()`
wraps that source as an iterable model. The default `iter_coord` is
`"lead_time"`; `"time"` is also accepted. The wrapper can convert absolute
`time` coordinates to lead times relative to the first time. It requires the
source coordinates to include `lead_time` for that conversion.

## Ensemble and local composition

There is no universal ensemble request schema. If discovery shows an ensemble
workflow, pass its exact fields. The repository's example conceptually uses:

```python
ensemble_result = remote(
    forecast_times=["2025-08-21T06:00:00"],
    nsteps=10,
    nensemble=8,
    batch_size=2,
    perturbation="spherical_gaussian",
    noise_amplitude=0.15,
)
```

Treat those names and values as an example contract only; validate them against
`/schema`. Higher `nensemble` and `nsteps` increase queue time, result size,
and model memory. `batch_size` is workflow-specific and should not exceed what
the deployed worker can handle. A returned `RemoteEarth2WorkflowResult` can be
used as a local diagnostic model input through `as_model()` or as a data source
through `as_data_source()`; local diagnostic model extras and hardware remain
separate prerequisites.

## Storage behavior and explicit client limits

`StorageType.SERVER` and `StorageType.S3` are the client enum values. For S3,
`download_result()` requires `result.signed_url`; it strips the first execution
ID path component before using the CloudFront mapper. Missing signed URLs are a
configuration failure, not a reason to fabricate a URL.

The server can also emit Azure object-storage metadata in deployments that have
that integration. This client implementation does not provide an Azure branch
in `as_dataset()` or `download_result()`; use the returned `remote_path`/
`blob_url` and an independently authorized Azure reader, or keep results on
server storage. Do not claim that any object-store provider is universally
available just because the server supports it.

The package does not implement a server-side auth policy. Passing `token` only
adds `Authorization: Bearer ...` to requests. Confirm the gateway's policy and
avoid printing `client.session.headers` in diagnostics.
