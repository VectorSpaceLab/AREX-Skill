# Troubleshooting

Use this reference for deployment and operator failures. If the symptom is a
model-family mismatch, backend extra problem, or per-model launch issue, route
that case to the model or launch sub-skill instead.

## Fast triage

| Symptom | Likely cause | What to check | Safe recovery |
| --- | --- | --- | --- |
| Cannot reach the service from another machine | The server is bound to loopback or the port is not published | Host binding, port mapping, ingress, and firewall rules | Bind to a public interface only when intended, then publish the port correctly. |
| `401` after turning on auth | Missing login or wrong bearer token | Auth mode, token header, and token lifetime | Log in again or use a valid API key. |
| Setup page loops or bootstrap fails | First admin not created yet, or someone else already completed setup | `/v1/admin/setup/status` and the setup response | Create the initial admin once, then switch to normal login. |
| Need to recover a lost admin | Admin password was forgotten or a bootstrap race was lost | Offline reset command and the auth database path | Reset the admin password offline and revoke stale refresh tokens. |
| OIDC startup fails | One or more required OIDC variables are missing | Issuer, client ID, client secret, redirect URI, and enabled flag | Provide the full OIDC set or disable OIDC before startup. |
| `/metrics` is missing | Metrics were disabled, or you are querying the wrong exporter | `XINFERENCE_DISABLE_METRICS`, supervisor `/metrics`, and worker exporter host/port | Re-enable metrics or query the correct endpoint. |
| Web UI is not served | No static export is available, or the export path is wrong | `XINFERENCE_FRONTEND_DIST_DIR` and the presence of the built export | Point the server at a valid static export or rely on the bundled export. |
| Audit Center is empty | Audit search is reading the wrong backend | `XINFERENCE_ES_URL`, `XINFERENCE_AUDIT_ES_INDEX`, and local audit logs | Point search at the intended backend or inspect the local audit file. |
| Requests are rejected by IP | IP restrictions or proxy trust are too strict | `XINFERENCE_ALLOWED_IPS` and `XINFERENCE_TRUSTED_PROXIES` | Adjust the allow-list or the trusted proxy list. |
| Slow or large requests time out | Request timeout or concurrency limits are too low | `XINFERENCE_HTTP_REQUEST_TIMEOUT` and `XINFERENCE_HTTP_LIMIT_CONCURRENCY` | Tune the limits upward only when the traffic pattern justifies it. |
| Model downloads fail in a container | Cache mounts, model source, or external access are missing | `XINFERENCE_HOME`, model caches, and the selected model source | Mount persistent caches or point the deployment at the intended source. |

## Common checks

- Confirm whether advanced auth is enabled before looking for a login bug.
- Confirm whether the deployment expects Hugging Face, ModelScope, or another
  model source.
- Verify that the auth database, logs, and caches all live under the intended
  persistent root.
- If a worker exporter is missing, confirm that metrics are actually enabled.
- Remember that permissive CORS is not access control; use the network
  boundary and IP rules instead.

## Escalation boundary

If the error mentions a model engine, backend package, custom model schema, or
launch flags, switch to the model/backend or serving/CLI sibling skill rather
than treating it as an operations bug.
