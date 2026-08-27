# Serving configuration and prerequisites

This is a configuration map, not a deployment recipe. It describes values the
Earth2Studio serving code reads. Use a deployment's secret manager and operator
runbook for credentials, process startup, networking, TLS, cloud IAM, and
Redis administration.

## Optional dependency set

The package's `serve` extra contains the REST and queue stack: FastAPI,
Uvicorn, Pydantic 2, `redis`, `hiredis`, RQ, Prometheus client, `aiofiles`,
Hydra, dotenv support, HTTP clients, and object-storage support including
`multi-storage-client`, cryptography, Azure Blob, and Azure identity packages.
The low-level client additionally uses `requests`; remote Zarr access can use
`aiohttp`. Model, data-source, perturbation, diagnostic, and plotting extras
are not implied by `earth2studio[serve]`.

Use a package-compatible Python version (the current project metadata requires
Python >=3.11 and <3.15) and verify the exact optional extras for the deployed
workflow. A missing serving import should be reported as an optional dependency
problem, not “the model is unavailable.”

## Defaults and environment overrides

The server loads its structured configuration and applies these environment
variables. Empty/unset values leave the documented default in place. Boolean
conversion is intentionally simple: only case-insensitive `true` becomes true;
validate values before deployment.

| Area | Environment variable | Default / accepted form |
|---|---|---|
| Redis | `REDIS_HOST` | `localhost` |
| Redis | `REDIS_PORT` | `6379`, integer |
| Redis | `REDIS_DB` | `0`, integer |
| Redis | `REDIS_PASSWORD` | unset; secret, never log |
| Redis | `REDIS_RETENTION_TTL` | `604800` seconds |
| Queue | `MAX_QUEUE_SIZE` | configured queue default is 10 in the dataclass; bundled config may set 20 |
| Paths | `DEFAULT_OUTPUT_DIR` | `/outputs` |
| Paths | `RESULTS_ZIP_DIR` | `/outputs` |
| Paths | `OUTPUT_FORMAT` | `zarr` or `netcdf4` |
| Logging | `LOG_LEVEL` | `INFO` |
| API | `SERVER_PORT` | `8000`, integer |
| Retention | `RESULTS_TTL_HOURS` | `24`, integer |
| Cleanup | `CLEANUP_WATCHDOG_SEC` | `900`, integer |
| Exposure | `EXPOSED_WORKFLOWS` | comma-separated names; empty exposes all |
| Discovery | `WORKFLOW_DIR` | comma- or colon-separated Python directories |

`SERVER_PORT` overrides the port; the server host, docs URL (`/docs`), ReDoc
URL (`/redoc`), worker count, title, and CORS defaults come from the structured
server configuration. The API source does not use `EARTH2STUDIO_API_URL` or
`EARTH2STUDIO_API_TOKEN` as server settings; those are convenient client-side
conventions in examples. Pass the token explicitly to the client.

The server's configuration manager also supports object-storage overrides:

| Object storage field | Environment variable | Default / meaning |
|---|---|---|
| enabled | `OBJECT_STORAGE_ENABLED` | `false` |
| provider | `OBJECT_STORAGE_TYPE` | `s3` or `azure` |
| S3 bucket | `OBJECT_STORAGE_BUCKET` | unset; required for S3 upload |
| AWS region | `OBJECT_STORAGE_REGION` | `us-east-1` |
| remote prefix | `OBJECT_STORAGE_PREFIX` | `outputs` |
| explicit S3 key | `OBJECT_STORAGE_ACCESS_KEY_ID` | unset; prefer IAM role/profile |
| explicit S3 secret | `OBJECT_STORAGE_SECRET_ACCESS_KEY` | unset; secret |
| session token | `OBJECT_STORAGE_SESSION_TOKEN` | unset; temporary credential |
| S3-compatible endpoint | `OBJECT_STORAGE_ENDPOINT_URL` | unset |
| transfer acceleration | `OBJECT_STORAGE_TRANSFER_ACCELERATION` | true |
| parallelism | `OBJECT_STORAGE_MAX_CONCURRENCY` | 16 |
| multipart chunk bytes | `OBJECT_STORAGE_MULTIPART_CHUNKSIZE` | 8388608 |
| Rust client | `OBJECT_STORAGE_USE_RUST_CLIENT` | true |
| CloudFront domain | `CLOUDFRONT_DOMAIN` | unset |
| CloudFront key pair | `CLOUDFRONT_KEY_PAIR_ID` | unset |
| CloudFront PEM content | `CLOUDFRONT_PRIVATE_KEY` | unset; secret key content |
| signed URL TTL | `SIGNED_URL_EXPIRES_IN` | 86400 seconds |

The offline checker at
[../scripts/check_service_config.py](../scripts/check_service_config.py) can
validate names, types, and required relationships without displaying secrets.

## Redis/RQ service boundary

Redis is not optional for the API lifecycle: startup pings both async and sync
clients, execution state is stored with a retention TTL, and RQ queues carry
inference plus result-finalization stages. A healthy API process without a
reachable Redis or workers cannot deliver a forecast. Queue capacity checks
can reject requests with HTTP 429. The serving skill does not start Redis,
create queues, flush data, edit Redis keys, or prescribe a process supervisor.

For an operator handoff, report:

- Redis host/port/database and whether authentication is needed;
- queue names and configured max size;
- output/results directories and writable capacity;
- whether API, inference, result, object-storage, metadata, and cleanup workers
  are present; and
- the endpoint health/readiness response and timestamp.

Do not put a password, cloud key, PEM body, or bearer token in this handoff.

## Object storage choices

With `OBJECT_STORAGE_ENABLED=false`, result metadata reports `storage_type` as
`server` and reads use the API's result-file routes. For S3, the server uploads
to `OBJECT_STORAGE_BUCKET` under `{prefix}/{workflow_name}/{execution_id}`.
CloudFront signed URLs require all three of `CLOUDFRONT_DOMAIN`,
`CLOUDFRONT_KEY_PAIR_ID`, and `CLOUDFRONT_PRIVATE_KEY`; when absent, an upload
may succeed but the client cannot use the S3 high-level reader without a signed
URL. An S3-compatible `OBJECT_STORAGE_ENDPOINT_URL` is supported, but its
credentials and acceleration behavior are deployment-specific.

For Azure, set `OBJECT_STORAGE_TYPE=azure` and provide the HTTPS `container_url`
per workflow request. The server parses a URL of the form
`https://<account>.blob.core.windows.net/<container>...` and uses
`DefaultAzureCredential`/managed identity or an equivalent Azure environment.
`geo_catalog_url` is an optional per-request value for GeoCatalog ingestion;
it is not a general server credential. Azure result metadata has no server-
generated signed URL. The current Python client model/high-level result reader
supports `server` and `s3` branches only, so an Azure consumer needs its own
Azure-authorized blob reader or server-side result access.

Object storage is a pipeline stage after inference and result manifest work.
Missing bucket, cloud identity, endpoint access, container URL, or signed URL
configuration therefore commonly appears as `pending_results` followed by
`failed` rather than as an immediate submission error.

## Auth and exposure boundary

`Earth2StudioClient` puts `Authorization: Bearer <token>` on requests when its
`token` argument is truthy. `RemoteEarth2Workflow` forwards `token` through to
that client. The package server code does not define a built-in token validator;
use the deployment's auth gateway/middleware and confirm whether `/health`,
`/schema`, metrics, and result-file paths are protected. A 401/403 is an auth
boundary failure, not a workflow parameter failure.

`EXPOSED_WORKFLOWS` controls which registered names are routable. An empty list
means all registered names are exposed; a non-empty list is an allowlist. The
warmup list can keep a name callable for warmup while omitting it from the
public list. Use discovery and schema endpoints as the source of truth.
