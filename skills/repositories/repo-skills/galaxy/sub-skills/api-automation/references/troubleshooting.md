# API Troubleshooting

Use this reference to diagnose common Galaxy API failures while keeping automation safe and secrets out of logs.

## First Checks

1. Confirm the base URL. If the user provides `https://host/galaxy`, API routes are usually under `https://host/galaxy/api/...`; do not append `/api` twice.
2. Probe `GET /api/version` to confirm the service and route prefix.
3. Probe `GET /api/whoami` with credentials to confirm the API key user before writes.
4. Redact keys from logs, URLs, exceptions, shell history, and reproduction snippets.
5. Treat non-local URLs as production-like unless the user says the instance is disposable.

## Missing or Wrong API Keys

Symptoms:

- `401 Unauthorized`.
- `403 Forbidden` on routes that should work for the user.
- `GET /api/whoami` returns no user or a different user than expected.
- HTML login page returned instead of JSON.

Actions:

- Ask the user for an API key through a secure channel or environment variable; do not request that they paste it into a committed file.
- Confirm the key belongs to the intended Galaxy instance.
- Prefer an API-key header if the user's client supports it; otherwise carefully redact query-string `key` values.
- Do not use browser cookies as a substitute for API keys in standalone automation unless the user explicitly asks for session-based debugging.

## 401 Unauthorized

Likely causes:

- Key missing, malformed, expired/revoked, or attached to the wrong instance.
- The route requires authentication and anonymous access is disabled.
- A reverse proxy, subpath, or base URL sent the request to the wrong service.

Fixes:

- Re-run the same request against `/api/version` and `/api/whoami`.
- Check that the request is JSON/API traffic, not redirected HTML.
- Confirm key placement and redaction.

## 403 Forbidden and ADMIN_REQUIRED

Likely causes:

- The key is valid but not allowed for the resource.
- The route requires admin privileges.
- The object exists but is owned by another user or restricted by roles.
- `run-as` was supplied without an admin key.

Actions:

- If the response includes `ADMIN_REQUIRED`, do not try to bypass it. Choose one: use an admin key, ask for an allowed non-admin route/source mode, or redesign the operation.
- For tests, assert both `403` and the error code/name when exercising permission boundaries.
- For workflow imports, avoid server-side path imports unless the task is explicitly admin/deployment oriented.
- For shared resources, inspect sharing/roles instead of assuming the object ID is invalid.

## 400 Bad Request and Payload Validation

Likely causes:

- Missing required fields.
- More than one mutually exclusive source field, especially on workflow create/import routes.
- Wrong content type: JSON endpoint received form/multipart or vice versa.
- Dataset references use the wrong source discriminator (`hda`, `hdca`, `ldda`) or an ID from another user/history.
- Pydantic validation rejected field names, types, or nested structures.

Actions:

- Compare payload fields against the OpenAPI schema for the target Galaxy version.
- For negative API tests, use raw helper methods and assert a stable status/error/message fragment.
- Log a redacted minimal payload shape, not full dataset content or keys.
- Reduce to a disposable history plus one dataset before expanding to workflows or collections.

## Wrong Base URL or Server Not Running

Symptoms:

- Connection refused, timeout, proxy error, TLS error, HTML page, or `404` on all `/api/...` routes.
- `GET /api/version` fails while the UI URL works.

Actions:

- Ask whether Galaxy is mounted under a subpath.
- Normalize the URL and remove duplicate `/api` components.
- Confirm the server is running; route to `../configuration-and-admin/SKILL.md` for startup/configuration.
- If using a public production URL, stop before writes and ask for confirmation.

## Async Job, History, and Workflow States

Symptoms:

- Submit response succeeds but outputs are empty or not ready.
- Workflow invocation appears stuck.
- Dataset content reads fail or show incomplete data.

Actions:

- Poll invocation, job, history content, and dataset state endpoints with a bounded timeout.
- Treat `ok` as success and `error` as a failure requiring job/tool details.
- Remember that queued/running states can be normal on a busy instance.
- For tests, prefer `DatasetPopulator.wait_for_tool_run(...)` and `WorkflowPopulator.wait_for_invocation_and_completion(...)`.

## OpenAPI Inspection Problems

- Importing Galaxy's OpenAPI schema generator requires Galaxy's Python package context and optional dependencies. If that environment is unavailable, inspect an exported schema file or use offline route guidance instead.
- Schema generation describes routes and models but does not validate a live user's permissions or the existence of object IDs.
- If schema output differs from examples, trust the schema for the checked-out Galaxy version and treat older scripts as conceptual examples.

## Production Safety Checklist

Before any write operation:

- The user explicitly supplied `--execute`-equivalent authorization.
- The URL is confirmed as intended and not accidentally production.
- The key user is confirmed with `whoami`.
- The target history/workflow/dataset IDs are disposable or explicitly named by the user.
- The command output redacts credentials.
- A dry-run plan has been shown first.
