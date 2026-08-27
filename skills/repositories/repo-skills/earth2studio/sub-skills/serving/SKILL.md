---
name: serving
description: "Use Earth2Studio's optional REST server and Python client to
  register workflows, submit and monitor inference, retrieve results, configure
  storage and authentication boundaries, or diagnose serving failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Earth2Studio serving

Use this route when a task involves a remote Earth2Studio inference endpoint,
workflow registration/schema, asynchronous execution, result retrieval, Redis/RQ
service prerequisites, object storage, or serving diagnostics. This is an
optional capability of Earth2Studio 0.18.0a0, not a replacement for local
`run.*` workflows.

## Choose the interface

- Use `RemoteEarth2Workflow` for an Earth2Studio-compatible, lazy xarray/data
  source/model result. Read [client-workflows.md](references/client-workflows.md).
- Use `Earth2StudioClient` for explicit request IDs, polling, file manifests,
  downloads, health checks, and custom integrations.
- Use the server-side `Workflow` or `Earth2Workflow` contract only when authoring
  a workflow that the service will discover. Read
  [server-reference.md](references/server-reference.md).
- Use [configuration.md](references/configuration.md) before changing Redis,
  output, exposure, object-store, retention, or token settings.
- Use [troubleshooting.md](references/troubleshooting.md) for service boundaries
  and recovery. Run the safe offline checker when a configuration is incomplete:
  `python path/to/earth2studio-skill/sub-skills/serving/scripts/check_service_config.py --help`.

## Prerequisites and limits

1. Install the optional serving dependencies, for example
   `uv pip install 'earth2studio[serve]'`, in the environment used by the
   client or server. The extra includes FastAPI/Uvicorn, Pydantic, Redis/RQ,
   metrics, Hydra, HTTP requests, and object-storage packages; model/data
   extras remain separate.
2. A usable service needs an API process, Redis, RQ workers, result cleanup,
   writable output locations, and the model/data credentials required by the
   selected workflow. Do not start, stop, mutate Redis, or provision cloud
   services from this route; treat those as operator prerequisites.
3. Verify the endpoint first with `GET /health` (or `/readiness`), then discover
   the actual deployed workflow names with `GET /v1/infer/workflows` and its
   `.../{workflow_name}/schema` endpoint. Do not assume example workflow names
   are installed or exposed.
4. The current API is the named custom-workflow API:
   `POST /v1/infer/{workflow_name}`,
   `GET .../{execution_id}/status`, and
   `GET .../{execution_id}/results`. The unnamed `POST /v1/infer` route is only
   a narrow compatibility convenience when exactly one workflow is exposed;
   legacy `workflow_type` request bodies are not the current contract.
5. Client authentication is a Bearer token passed to `Earth2StudioClient(token=...)`
   or `RemoteEarth2Workflow(..., token=...)`. The package client sends the
   header; an authentication gateway or server deployment must enforce it.
   Never put credentials in a skill command, log, fixture, or committed file.

## Standard client route

1. Construct a client with the service URL and exact workflow name. Set a
   finite request timeout, retry count/backoff, and token only from a secure
   runtime source.
2. Call `health_check()`, construct `InferenceRequest(parameters={...})`, and
   call `submit_inference_request()`. Save the returned `execution_id`.
3. For asynchronous control, call `get_request_status(id)` until `COMPLETED`,
   then call `get_request_results(id)`. For a bounded synchronous operation,
   use `run_inference_sync(request, poll_interval=..., timeout=...)` or
   `wait_for_completion(id, ...)`.
4. Inspect `output_files` and `result_paths()` before opening data. Use
   `download_result(result, path)` for individual files or a high-level result
   object's `as_dataset()`, `as_data_source()`, or `as_model()`.
5. Preserve the execution ID and workflow name together: status/results URLs
   are workflow-scoped, and a result object can be reconstructed later with
   `RemoteEarth2WorkflowResult(workflow, execution_id)`.

## Supported serving concepts

The server can expose deterministic, diagnostic, ensemble, downscaling, or
user-defined computations, but the deployed registry—not this skill—defines
what is available. A workflow's Pydantic schema defines its required and
optional JSON parameters. Ensemble parameters commonly include `nensemble`,
`batch_size`, and a perturbation choice, but use the discovered schema rather
than copying an example blindly.

For a custom workflow, keep permanent resources in `__init__`, validate typed
parameters, write under the execution output directory, and report progress.
For an `Earth2Workflow`, `__call__` must accept `io: IOBackend`; its remaining
annotated arguments become the request schema. The server selects `zarr` or
`netcdf4` output, wraps IO for progress, and finalizes result metadata.

## Validation checkpoints

- Health is `HealthStatus(status, timestamp)`; unhealthy/readiness failures are
  service failures, not invalid forecast parameters.
- Submission should return an execution ID and an initial queued/accepted
  response. HTTP 422 indicates parameter validation; 404 can mean the workflow
  is absent or not exposed; 429 indicates admission queues are full.
- Status includes the request ID, enum status, optional progress, and an error
  message. `pending_results` means computation finished but result finalization
  is not yet ready.
- Results contain a file manifest and storage metadata. `as_dataset()` supports
  `.zarr` and `.nc`; it does not interpret arbitrary files. Large downloads are
  buffered in memory by `download_result`, so prefer lazy Zarr access where
  supported and bound result size operationally.

## Further reading

- [client-workflows.md](references/client-workflows.md) — exact client APIs,
  request/result models, polling, xarray access, and ensemble patterns.
- [server-reference.md](references/server-reference.md) — endpoints, custom
  workflow contracts, discovery, schema, status, and monitoring.
- [configuration.md](references/configuration.md) — optional install, config
  defaults, environment overrides, auth boundary, and S3/Azure prerequisites.
- [troubleshooting.md](references/troubleshooting.md) — symptoms, diagnosis,
  recovery, and intentional service/deployment omissions.
- [scripts/check_service_config.py](scripts/check_service_config.py) — offline,
  secret-safe parser and configuration readiness report; it never contacts a
  service, changes Redis, uploads data, or starts a process.
