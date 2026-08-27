# Serving troubleshooting

Start with a timestamped `health_check()`, the exact workflow name, execution
ID, status response, and HTTP status/body. Redact Bearer tokens, Redis
passwords, AWS/Azure credentials, signed URLs, and private-key material.
Use the offline checker before contacting a service:

```bash
python path/to/earth2studio-skill/sub-skills/serving/scripts/check_service_config.py \
  --mode client --require-auth --nensemble 8 --batch-size 2
```

The checker never opens a socket or changes a service; a failure means the
local configuration contract is incomplete, not that the endpoint is down.

## Triage matrix

| Symptom | Likely boundary | Safe next step |
|---|---|---|
| ImportError for FastAPI/Redis/RQ/Hydra | `serve` extra absent or conflicting environment | Install the targeted `earth2studio[serve]` extra in the intended environment; run a minimal import check. Model extras are separate. |
| Connection/API error or timeout | URL, TLS/proxy, API process, or network boundary | Confirm the URL and authorized reachability with `/health`; tune `timeout`, `max_retries`, and `retry_backoff_factor`; do not retry indefinitely. |
| `/health` 503 or server startup fails | Redis, API/RQ workers, cleanup daemon, or service process unavailable | Give the operator the response and timestamp; verify the service prerequisite and worker set. Do not mutate Redis or start processes here. |
| `401`/`403` | External auth gateway or wrong/expired token | Obtain a fresh token through the deployment's auth flow and pass `token=...`; never put it in source or logs. The package client does not validate tokens itself. |
| `404` workflow | Name not registered, not exposed, or wrong URL route | Call `/v1/infer/workflows`; use the exact name and `/schema`; check `EXPOSED_WORKFLOWS` and discovery imports. |
| `409` from `POST /v1/infer` | More than one exposed workflow | Use the named `POST /v1/infer/{workflow_name}` route. |
| `422` on submission | Schema/Pydantic/typed parameter error | Fetch `/schema`, remove unknown keys, use JSON-compatible values, and supply date-times with a time component. |
| `429` on submission | Inference/result/object-storage/finalization queue full | Back off and retry after capacity recovers; reduce ensemble size or request rate. Do not delete queue entries. |
| `202` from results | Execution is queued/running or `pending_results` | Poll the status endpoint; do not call `get_request_results()` in a tight loop. |
| `failed` status with an error | Workflow model/data/backend error or downstream pipeline error | Preserve the error, parameters, and execution ID; validate model/data extras and worker logs with the operator, then submit a bounded corrected request. |
| `400` expired results | Results TTL/cleanup removed artifacts | Re-run the workflow; result files are not recoverable through the API. |
| `404` result file/zip | Failed execution, missing manifest, absent zip, or wrong manifest path | Fetch result metadata first and use an exact `output_files[].path`; confirm zip creation is enabled if the zip path is requested. |
| `as_dataset()` rejects a path | Result is not `.zarr`/`.nc`, no output, or unsupported storage type | Inspect `result_paths()`; use `download_result` for a supported file or an appropriate provider-specific reader. |
| S3 result says signed URL is missing | Upload succeeded without complete CloudFront signing config | Configure CloudFront domain/key pair/PEM through the deployment secret mechanism, or use server storage/provider-specific access. Never invent a URL. |
| Azure result cannot open in `RemoteEarth2WorkflowResult` | Client high-level reader has no Azure branch | Obtain Azure authorization and read `remote_path`/`blob_url` with an Azure-aware consumer, or request server storage. |
| `pending_results` becomes `failed` after object storage enabled | Missing bucket/identity/endpoint, invalid Azure container URL, or storage package | Check provider prerequisites and sanitized worker error; temporarily validate with server storage if allowed. |
| Zarr opens slowly or fails remotely | Unconsolidated/expired store, auth headers, async HTTP timeout, or URL path | Wait for `completed`, use the result object's `as_dataset()`, preserve its token/storage options, and set `xr_args` only for supported xarray options. |
| NetCDF read fails with missing `netcdf4` | Client-side NetCDF engine optional dependency absent | Install the needed NetCDF reader in the client environment or retrieve the file as bytes and use a supported local reader. |
| Custom workflow absent after adding a file | `WORKFLOW_DIR` not parsed, import failure, decorator/name/exposure error | Check the configured directory and its comma/colon separators, then query discovery/schema; a missing model extra can prevent module import. |
| Custom workflow fails only under API | API-only Redis context or worker environment differs from local shell | Keep permanent resources in `__init__`, ensure the same dependencies/data credentials are available to workers, and use `update_progress()`/`get_output_path()`. |
| Progress stuck at `queued` | No inference worker or Redis/RQ queue issue | Check readiness and queue-worker health with the operator; do not relabel it completed on the client. |

## Difficult synthetic case: incomplete remote ensemble setup

A caller asks for remote ensemble results with `nensemble=8` and `batch_size=2`,
but has no Redis settings, no S3 bucket/object-store configuration, and no
Bearer token although the endpoint requires auth. Handle it in this order:

1. Run the offline checker with `--require-redis --require-object-storage
   --require-auth --nensemble 8 --batch-size 2`; expect nonzero exit and
   secret-safe findings for each missing group.
2. Distinguish client from server ownership: Redis and S3 bucket/identity are
   service prerequisites; the token is a client/gateway prerequisite. Do not
   pass Redis credentials in `Earth2StudioClient`.
3. Ask the operator to establish Redis/RQ and object storage, or select server
   storage for a bounded test. For S3, require a bucket and, if the standard
   client reader is desired, CloudFront signed-URL configuration.
4. After prerequisites are confirmed, call `/health`, discover the ensemble
   workflow and schema, submit the exact schema fields, and keep the execution
   ID. A successful submission is not proof that the object-storage finalizer
   succeeded.
5. Poll through `pending_results`; only consume results after `completed` and
   inspect `storage_type`, `signed_url`, and `result_paths()` before opening.

The case is intentionally beyond a happy-path client example: it tests service
ownership, secret boundaries, queue/finalization timing, storage/client
compatibility, and schema-driven ensemble parameters.

## What not to do

- Do not use the old unnamed legacy `workflow_type` JSON schema from stale
  deployment notes.
- Do not report a local `device="cuda"` choice as proof that the server has a
  GPU; `RemoteEarth2Workflow.to()` changes only local tensor handling.
- Do not expose raw exception bodies that contain URLs with signed query strings
  or credentials.
- Do not start/stop API, Redis, RQ, or cleanup processes, flush queues, delete
  outputs, rotate credentials, or provision S3/Azure resources from this skill.
  Escalate those actions with the precise failing boundary.
