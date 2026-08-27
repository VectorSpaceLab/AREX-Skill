# SDK/API Server Troubleshooting

Use this guide for SDK request lifecycle, API server health, login, dashboard, deployment, and compatibility failures. Route cloud credential/resource failures to `infrastructure-storage`; route task YAML schema errors to `task-yaml`; route cluster/jobs/serve behavior to the owning operational sub-skill.

## Request ID Was Not Awaited

Symptoms:

- Code prints a request ID string instead of a launch/status result.
- A tuple unpack fails because `sky.launch(...)` returned `RequestId[...]`.
- A later operation runs before launch/status has finished.

Fix:

```python
request_id = sky.launch(task, cluster_name='demo')
job_id, handle = sky.get(request_id)
```

Use `sky.stream_and_get(request_id)` when the user expects logs. In async code, await both submitter and result calls:

```python
request_id = await sky_async.status(['demo'])
clusters = await sky_async.get(request_id)
```

## API Server Not Running

Symptoms:

- CLI/SDK reports that the SkyPilot API server is unavailable.
- `sky.api_status()` returns an empty list for a local server that is not running.
- SDK calls hang while trying to connect.

Fix:

- Check status with `sky api info` or `sky api status`.
- Start a local server with `sky api start` or `sky.api_start()` if local operation is intended.
- If a remote endpoint is configured, do not use `sky api start`; login/logout or clear the endpoint first.
- Inspect logs with `sky api logs --tail 200` or `sky.api_server_logs(follow=False, tail=200)`.

## Local Start Fails Because a Remote Endpoint Is Set

Symptoms:

- `sky.api_start()` says it cannot start a local API server because the endpoint is set.
- Login/logout complains that `SKYPILOT_API_SERVER_ENDPOINT` is set.

Fix:

- For persistent remote usage, keep using `sky api login -e <endpoint>` and do not start a local server.
- For local usage, logout from the remote server or remove the configured API server endpoint.
- If `SKYPILOT_API_SERVER_ENDPOINT` is set, unset it before persistent login/logout or local server management.

## Remote Login or Relogin Fails

Symptoms:

- Browser flow does not complete.
- Service account token is rejected.
- Health check returns `NEEDS_AUTH` or an unhealthy status.

Fix:

- Confirm the endpoint includes `http://` or `https://` and has no stale trailing path.
- Use `sky api login -e <endpoint> --no-browser` when the browser is on a different machine or callback ports are unavailable.
- For service account tokens, ensure the token starts with `sky_` and belongs to the target server.
- Use `sky.api_login(endpoint=..., relogin=True)` or `sky api login -e <endpoint> --relogin` when cached cookies are stale.
- Run `sky api info` after login and verify the dashboard URL and user identity.

## Old Server/New Client Mismatch

Symptoms:

- `APINotSupportedError` for an SDK function or argument.
- Warning that a flag is ignored because the server does not support it.
- Error says the API server or client version is too old.

Fix:

- Run `sky api info` or `sky.api_info()` to inspect `api_version`, SkyPilot version, and commit.
- If the remote server is too old, ask the administrator to upgrade the remote API server, or downgrade the client to the server's compatible package version.
- If the local client is too old for the server, upgrade the local SkyPilot package.
- Avoid adding code that depends on a newer argument unless the remote server version is checked or the code has a fallback.

## Dashboard Is Blank, Missing, or Stale

Symptoms:

- API server is healthy but `/dashboard` is blank or static assets fail.
- Dashboard changes are not visible after source edits.

Fix:

- In a source checkout, rebuild dashboard assets before restarting the server: `npm --prefix sky/dashboard install` and `npm --prefix sky/dashboard run build`.
- Restart after rebuilding: `sky api stop` then `sky api start`.
- For container/Kubernetes deployment, ensure the image build includes dashboard output and the pod runs the intended image.
- Use the dashboard URL reported by `sky api login`, `sky api start`, or `sky.api_info()`-derived server URL.

## PostgreSQL or Kubernetes Upgrade Cautions

Symptoms:

- Requests or configuration disappear after a Helm upgrade.
- API server pod restarts but state is missing.
- Auth, database, storage, or dashboard settings are unexpectedly reset.

Fix:

- Preserve values on existing Helm releases with `helm upgrade ... --reuse-values` and only override the values being changed.
- Keep PostgreSQL connection settings stable for high-availability deployments; losing the configured database changes server state persistence.
- Do not replace credential/auth config during upgrades unless intentionally rotating credentials.
- Confirm `sky api login -e <endpoint>` still points at the upgraded server after deployment changes.

## Streaming the Wrong Request

Symptoms:

- Logs belong to an unexpected request.
- A shared remote server streams another user's or process's latest request.

Fix:

- Always retain and pass the explicit request ID returned by the SDK call.
- Avoid `sky.stream_and_get(None)` except in a single-user local debugging session.
- Use `sky.api_status(limit=...)` or `sky api status` to find a request prefix before calling `get`, `logs`, `cancel`, or `stream_and_get`.

## API Request Cancel Did Not Clean Up Cloud Resources

Symptoms:

- `sky api cancel` succeeds but clusters, jobs, or services still exist.
- A cancelled request left partial infrastructure for debugging.

Fix:

- Treat API request cancellation as request-level abort, not a universal cleanup command.
- Use workflow-specific cleanup after checking status: `sky.down(...)` for clusters, `sky.jobs.cancel(...)` for managed jobs, or `sky.serve.down(...)` for services.
- Confirm destructive cleanup with the user and route detailed behavior to the owning operational sub-skill.

## Inspection Helper Fails

Symptoms:

- `inspect_sdk_surface.py` cannot import `sky`.
- Signatures are missing or import errors mention optional providers.

Fix:

- Run the helper in an environment where SkyPilot is installed.
- The helper does not start the API server and does not require cloud credentials.
- If import fails, first solve package installation/import issues; provider credential checks belong to `infrastructure-storage`.
