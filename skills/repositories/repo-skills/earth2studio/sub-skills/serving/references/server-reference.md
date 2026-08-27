# REST server and custom workflow reference

Read this when a service owner needs to understand the API contract or expose a
new workflow. This reference describes the current named custom-workflow API;
it intentionally does not provide process-start, shutdown, Redis mutation, or
cloud deployment procedures.

## Endpoint contract

The FastAPI application exposes:

| Method | Endpoint | Contract |
|---|---|---|
| `GET` | `/health`, `/readiness` | Checks Redis, API workers, RQ workers, and cleanup daemon; returns `status` and `timestamp`, or 503 when unhealthy. |
| `GET` | `/liveness` | Returns `{"status": "alive"}` for a process liveness probe. |
| `GET` | `/metrics` | Prometheus text exposition. |
| `GET` | `/v1/infer/workflows` | Exposed workflow names and descriptions. |
| `GET` | `/v1/infer/{workflow_name}/schema` | Pydantic JSON Schema for that workflow's request parameters. |
| `POST` | `/v1/infer/{workflow_name}` | Enqueues `{"parameters": {...}}`; returns workflow name, execution ID, status, queue position, message, and timestamp. |
| `GET` | `/v1/infer/{workflow_name}/{execution_id}/status` | Returns status, progress, timestamps, execution time, error, metadata, and queue position when queued. |
| `GET` | `/v1/infer/{workflow_name}/{execution_id}/results` | Returns finalized JSON result metadata and output manifest. |
| `GET` | `/v1/infer/{workflow_name}/{execution_id}/results/{filepath}` | Streams a specific file or the complete zip when the filepath is `workflow_name:execution_id`. |

The unnamed `POST /v1/infer` compatibility route is accepted only when exactly
one workflow is exposed; it has the same `{"parameters": ...}` body and returns
409 for multiple exposed workflows or 503 for none. Prefer named routes so a
caller cannot accidentally target a different workflow after exposure changes.
The old request shape containing `workflow_type`, `prognostic`, `data`, and
`io` is not the current server contract.

A minimal read-only HTTP probe, when a service is authorized for access, is:

```bash
curl -fsS "$EARTH2STUDIO_API_URL/health"
curl -fsS "$EARTH2STUDIO_API_URL/v1/infer/workflows"
curl -fsS "$EARTH2STUDIO_API_URL/v1/infer/<name>/schema"
```

Do not treat an HTTP health success as proof that a model can run: health checks
cover service plumbing, not data availability, model packages, GPU memory, or
workflow-specific credentials.

## Two workflow base classes

### `Workflow`

Subclass `earth2studio.serve.server.workflow.Workflow` for full control:

```python
from typing import Any
from earth2studio.serve.server.workflow import (
    Workflow, WorkflowParameters, WorkflowProgress, WorkflowRegistry,
)

class Parameters(WorkflowParameters):
    # Declare typed Pydantic fields and constraints here.
    pass

@WorkflowRegistry.instance().register
class MyWorkflow(Workflow):
    name = "my_workflow"
    description = "A concise service description"
    Parameters = Parameters

    @classmethod
    def validate_parameters(cls, parameters: dict[str, Any] | Parameters):
        return Parameters.validate(parameters)

    def run(self, parameters: dict[str, Any] | Parameters, execution_id: str):
        parameters = self.validate_parameters(parameters)
        self.update_execution_data(execution_id, {"metadata": {"parameters": parameters.model_dump()}})
        self.update_execution_data(
            execution_id,
            WorkflowProgress(progress="running", current_step=1, total_steps=1),
        )
        output_dir = self.get_output_path(execution_id)
        # Write only files that the result pipeline should expose under output_dir.
        return {"status": "success"}
```

The base parameter model forbids unknown fields. `WorkflowParameters` validates
`forecast_times` and `start_time` values when those fields exist; string values
must include a date-time separator (`T` or a space) and parse as ISO-8601.
Implement `validate_parameters()` as a class method and raise a useful
`ValueError` for workflow-specific constraints.

Use `update_execution_data(execution_id, dict_or_WorkflowProgress)` for progress
or metadata. The service owns the lifecycle status; workflow code must not set
or overwrite `status`. `get_output_path(execution_id)` creates the standard
per-execution directory. The execution's `run()` exception is captured as a
failed status and error message.

### `Earth2Workflow`

Subclass `earth2studio.serve.server.e2workflow.Earth2Workflow` when a normal
Earth2Studio recipe should also run as a Python call. The metaclass derives
Pydantic `Config` from `__init__` and `Parameters` from `__call__`:

```python
from datetime import datetime
from earth2studio import run
from earth2studio.data import GFS
from earth2studio.io import IOBackend
from earth2studio.models.px import FCN
from earth2studio.serve.server.e2workflow import Earth2Workflow
from earth2studio.serve.server.workflow import WorkflowRegistry

@WorkflowRegistry.instance().register
class ForecastWorkflow(Earth2Workflow):
    name = "forecast_workflow"
    description = "A typed forecast recipe"

    def __init__(self, model_type: str = "fcn"):
        super().__init__()
        package = FCN.load_default_package()
        self.model = FCN.load_model(package)
        self.data = GFS()

    def __call__(
        self,
        io: IOBackend,
        start_time: list[datetime] | None = None,
        num_steps: int = 6,
    ) -> None:
        run.deterministic(start_time or [datetime(2024, 1, 1)], num_steps, self.model, self.data, io)
```

The `io` argument is reserved and excluded from the generated request schema;
the server supplies it. Every other argument needs a type hint and must be
Pydantic/JSON compatible. Use lists instead of NumPy arrays or PyTorch tensors
in the REST request. Arguments without defaults are required; `__init__`
arguments become service configuration and are instantiated once per worker.
`num_steps`/`nsteps` receive generated bounds of 1 through 1000 in the automatic
parameter model.

`Earth2Workflow.run()` chooses `zarr` or `netcdf4` from server configuration,
allows a declared `output_format` parameter to override the default, wraps the
backend with progress reporting, consolidates Zarr metadata, and finalizes
metadata. `update_progress(WorkflowProgress(...))` is a no-op in an ordinary
local call and updates Redis when the object is running under the server.

## Registration and discovery

Decorate a workflow **class**, not an instance:

```python
@WorkflowRegistry.instance().register
class MyWorkflow(Workflow):
    ...
```

The registry rejects non-classes, non-`Workflow` subclasses, duplicate names,
and the reserved name `workflows`. Registration is active in API mode; when a
module is run as a local script or outside the API process, the decorator leaves
the class usable without adding it to the server registry.

At API/worker initialization, built-in example workflows are discovered and
then Python files in `WORKFLOW_DIR` are imported non-recursively. Set
`WORKFLOW_DIR` to one directory or comma/colon-separated directories. Keep
workflow modules importable and do not depend on an unavailable working
 directory. A missing directory is logged and skipped; import errors are
counted and logged. The `EXPOSED_WORKFLOWS` setting can restrict public routes;
an empty list exposes all registered workflows, while warmup-only names remain
callable for warmup but are not included in the public list.

When debugging a missing custom route, check in order: directory exists,
`WORKFLOW_DIR` is parsed as intended, module import has no missing model/data
extra, class has the decorator and a unique name, and exposure includes it.
Use `/v1/infer/workflows` and `/schema` rather than assuming registration.

## Lifecycle, queue, and output semantics

The normal lifecycle is:

```text
queued → running → pending_results → completed
   └──────────────→ failed or cancelled
completed → expired after the configured retention period
```

The server persists execution state in Redis and queues work through RQ. A
queued response may include a zero-based `position`; once a worker claims it,
position disappears. `pending_results` means inference finished but manifest,
object storage, or final metadata work is still in progress.

Submission validates parameters before enqueueing. Relevant responses include:

- `404`: workflow/route is absent, not exposed, or execution is unknown.
- `422`: Pydantic/workflow parameter validation failed.
- `409`: unnamed route has more than one exposed workflow.
- `429`: admission control found a full inference/result/object-storage or
  metadata queue; retry after capacity recovers.
- `503`: no exposed workflow or service dependency is unavailable.
- `500`: enqueue, execution, result finalization, or server error.

Results are written beneath the configured output directory. The result
metadata includes a file manifest (`path`, `size`), status, timestamps,
parameters, execution time, and storage metadata. The complete zip is available
under the `{workflow_name}:{execution_id}` path only when zip creation is
configured; individual files are guarded against path traversal and support
HTTP range requests. Expired or cleaned-up results are not recoverable through
this API.

## Monitoring boundary

`/health` and `/readiness` run in-process checks for Redis connectivity and the
presence of API, RQ, and cleanup-daemon processes. `/liveness` only proves that
the API process responds. `/metrics` is a scrape endpoint, not an inference
status API. For a failed health result, give operators the failing component,
queue name, timestamp, and execution ID; do not attempt to repair Redis or
process state from a client workflow.
