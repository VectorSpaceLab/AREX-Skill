# Remote Service Troubleshooting

## Missing Service URL

Symptoms:

- `docling convert-remote` exits with code `2` and reports no service URL.
- SDK construction code has no `url` value or fails before any network request.

Fix:

- Pass `--service-url` for CLI calls, or set `DOCLING_SERVICE_URL`.
- For `.env` usage, put `.env` in the current working directory from which the command runs.
- Use a base URL such as `https://docling.example.com` or `http://localhost:5001`; do not include `/v1` because the client appends versioned API paths.
- Run `scripts/check_service_config.py` for no-network validation.

## Authentication Failures

Symptoms:

- HTTP 401 or 403.
- Service errors mentioning missing, invalid, or unauthorized API key.

Fix:

- Pass `--api-key` or set `DOCLING_SERVICE_API_KEY` when the service requires authentication.
- The SDK sends the key as `X-Api-Key`; raw REST calls must do the same.
- Do not log API keys or include them in bug reports.
- Confirm that the key belongs to the target service URL, especially when switching between local, staging, managed, or production services.

## Service Unreachable Or Health Fails

Symptoms:

- CLI exits with code `1` and reports `Cannot reach service`.
- SDK `health()` raises a service or transport error.

Fix:

- First validate config without network: `python scripts/check_service_config.py --service-url ...`.
- With user approval, call health only: `python scripts/check_service_config.py --service-url ... --ping`.
- Check that proxies, TLS inspection, VPNs, and container networking allow the client to reach the service.
- For a local server, the default service URL is commonly `http://localhost:5001`; inside containers, `localhost` means the container itself, not the host machine.

## Timeouts And Long Tasks

Symptoms:

- `TaskTimeoutError` from job waiting.
- CLI times out while the service continues working.
- Large PDFs, OCR-heavy documents, VLM, ASR, or advanced enrichment jobs fail late.

Fix:

- Increase SDK `job_timeout` and per-call `job.result(timeout=...)`.
- Increase CLI `--timeout`; use `--document-timeout` when the service should allow longer per-document processing.
- Reduce `max_concurrency` or `--max-concurrency` if the service is capacity constrained.
- For task APIs, keep the `task_id` and poll later if the service retains task results.
- Distinguish client wait timeout from server-side execution timeout in user-facing guidance.

## Websocket Problems

Symptoms:

- Status updates fail through `/v1/status/ws/{task_id}`.
- Corporate proxies, ingress controllers, or firewalls break websocket upgrades.

Fix:

- Use polling: CLI `--watcher polling`; SDK `status_watcher=StatusWatcherKind.POLLING`.
- Leave websocket fallback enabled unless diagnosing a websocket-specific issue.
- Tune polling cadence with `poll_server_wait` and `poll_client_interval` in SDK clients.

## Quota, Capacity, And Usage Limits

Symptoms:

- `UsageLimitExceededError` with current usage and limit.
- HTTP 429-like service response, queue admission failure, or policy/capacity failure category.

Fix:

- Reduce concurrency and retry later only if the error is retryable.
- Surface quota details without exposing credentials.
- For managed services, check account limits or task quotas.
- For self-hosted services, check queue/compute backend capacity and service configuration.

## Task Not Found, Result Not Ready, Result Expired

Symptoms:

- `TaskNotFoundError`: unknown task id.
- `ResultNotReadyError`: result fetched before terminal status.
- `ResultExpiredError`: completed task result no longer retained.

Fix:

- Poll or watch until status is terminal before fetching results.
- Ensure the task id is from the same service URL and environment.
- Fetch results promptly; services may expire task results.
- Preserve `task_id`, `submitted_at`, and watcher mode in logs, but do not log document content or credentials.

## Private Artifact URLs

Symptoms:

- Presigned result conversion submits successfully, but artifact materialization fails.
- Error mentions artifact download, unsafe/private URL, redirect, size limit, or expired URL.

Fix:

- Prefer `InBodyTarget()` for clients that cannot reach the service's artifact storage.
- Use `ZipTarget()` when a zip payload is more appropriate and the service supports it.
- Ensure presigned artifact URLs are globally routable from the client runtime and have not expired.
- Do not bypass the artifact URL safety guard for arbitrary services. Only consider private artifact access when the user controls the service and storage network boundary.
- Increase `artifact_download_timeout` or `max_artifact_download_bytes` only when the artifact is expected and trusted.

## Response Schema Mismatch

Symptoms:

- `ResponseSchemaMismatchError` when parsing an otherwise successful service response.

Fix:

- Treat it as likely client/server version skew.
- Upgrade `docling-slim[service-client]` and the service together, or inspect the service `/version` endpoint.
- If raw REST calls succeed but the SDK fails, compare the live OpenAPI schema with the installed client version.

## Remote Pipeline Boundaries

Remote conversion through `docling-serve` is different from local pipeline options that call external model APIs. If a local pipeline or service-side pipeline needs remote model calls, the service must explicitly enable remote services for those pipeline internals. Route model API setup, VLM/GPU/MLX requirements, ASR extras, ffmpeg, and model prefetching to the pipeline/backend guidance unless the failure is the service-client connection itself.

## Safe Escalation Pattern

1. Validate URL/API-key presence and URL shape without network.
2. If authorized, call `/health` only.
3. If authorized, call `/version` for client/server version diagnosis.
4. Only then run a minimal conversion against a non-sensitive sample document.
5. Avoid uploading private documents while diagnosing credentials, routing, websocket, or timeout settings.
