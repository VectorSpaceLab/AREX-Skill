# Operations Troubleshooting

## Quick Triage

1. Confirm Python is `>=3.11,<3.13`.
2. Confirm the installed distribution is `InvokeAI` and the entry points exist: `invokeai-web`, `invoke-useradd`, `invoke-userdel`, `invoke-userlist`, `invoke-usermod`.
3. Run `invokeai-web --version` or `python scripts/inspect_cli_help.py --command invokeai-web` before attempting a full server start.
4. Resolve the intended root/config: CLI `--root`/`--config`, then `INVOKEAI_ROOT`, then virtualenv parent, then `~/invokeai`.
5. Use `python scripts/summarize_settings.py --category WEB` and `--category MULTIUSER` to confirm setting names and env vars.
6. For API questions, use a running server's `/openapi.json` or `python scripts/inspect_openapi_routes.py --fallback` when full deps are unavailable.

For broad installation, Torch, CUDA, and backend issues not specific to server/config/auth operations, read `../../references/troubleshooting.md`.

## Missing Runtime Dependencies

Symptoms:

- `ModuleNotFoundError` for `fastapi`, `uvicorn`, `torch`, `pydantic_settings`, `socketio`, `jose`, `passlib`, `bcrypt`, or model/backend packages.
- `inspect_openapi_routes.py` reports it cannot import the live app.
- Server import fails before uvicorn starts.

Actions:

- Do not infer that the server is broken from an inspection-only environment; this skill draft explicitly had package metadata/import facts but not full dependencies installed.
- Verify the app is installed with the normal runtime dependencies and exactly one backend extra appropriate to the platform when applicable.
- Use `--fallback` route inspection for high-level route routing until a full app environment is available.

## Root and Config Mistakes

Symptoms:

- App creates or reads an unexpected `invokeai.yaml`.
- User-management CLI changes the wrong database.
- Models, outputs, or custom nodes appear missing.

Actions:

- Reconstruct root selection: `invokeai-web --root ROOT --config CONFIG` wins for web startup; otherwise `INVOKEAI_ROOT`, then `VIRTUAL_ENV` parent, then `~/invokeai`.
- Remember user-management CLIs accept `--root` but not `--config`.
- Check relative path settings: `db_dir`, `models_dir`, `outputs_dir`, `custom_nodes_dir`, and cache directories resolve under the chosen root.
- External provider secrets may be in `api_keys.yaml`, not `invokeai.yaml`.
- If a YAML schema error appears, check `schema_version` and migration backups ending in `.yaml.bak`.

## Port and Host Issues

Symptoms:

- Requested port is already in use.
- Logs show the server is running on a different port.
- Browser cannot connect from another machine.

Actions:

- Startup searches for the first open port when `port` is occupied and updates the in-memory config for that process. Check logs for the final port.
- Use `host: 0.0.0.0` only when intentional LAN exposure is needed; default `127.0.0.1` is local-only.
- Ensure firewall and reverse proxy settings match the final host/port.

## CUDA Allocator and Torch Import Ordering

Symptoms:

- `pytorch_cuda_alloc_conf` appears ignored.
- CUDA allocator errors happen before server startup completes.

Actions:

- The app configures the Torch CUDA allocator before importing modules that import Torch. Preserve this ordering in diagnostics.
- Avoid snippets that import `torch` before loading/checking `pytorch_cuda_alloc_conf`.
- Route deeper VRAM/model-cache tuning to `../model-management/SKILL.md` after confirming the setting is present.

## CORS, SSL, and Logging

Symptoms:

- Browser blocked by CORS.
- HTTPS startup fails.
- Network logs are missing or too verbose.
- SQL logs flood output.

Actions:

- Check `allow_origins`, `allow_credentials`, `allow_methods`, and `allow_headers`. The app exposes `X-Refreshed-Token` for auth token refresh.
- Check `ssl_certfile` and `ssl_keyfile` paths relative to root unless absolute.
- Use `log_level_network` for uvicorn/network verbosity and `log_level` for application logging.
- `log_sql` only has effect with debug-level logging and can be extremely verbose.
- `log_handlers` can include console, file, syslog, or HTTP handlers; verify destination writability separately.

## Multiuser and Auth Mistakes

Symptoms and fixes:

- `403 Multiuser mode is disabled`: set `multiuser: true` or `INVOKEAI_MULTIUSER=true` before using login/setup flows.
- `setup_required: true`: create the first admin through `/api/v1/auth/setup` or controlled user CLI setup against the intended root.
- CLI mutates wrong users: pass `--root` explicitly and verify `db_dir` under that root.
- `Password must be at least 8 characters long` or `Password must contain uppercase, lowercase, and numbers`: strict password checking is active; use a compliant password or disable strict checking only if policy allows.
- Login succeeds but admin endpoint returns 403: token belongs to a non-admin user; update admin status with an admin token or controlled `invoke-usermod` run.
- Token refresh not visible on GET: refresh middleware only emits `X-Refreshed-Token` on successful mutating requests.
- `JWT secret has not been initialized`: auth token service is being used before normal app startup initialized dependencies and loaded the database secret.

## API/OpenAPI Import Failures

Symptoms:

- OpenAPI generation fails before routes are listed.
- Importing `invokeai.app.api_app` logs missing UI or backend warnings.

Actions:

- Use `python scripts/inspect_openapi_routes.py --fallback` for a safe bundled route-family summary.
- If exact schema is required, run route inspection in the same installed environment that can start `invokeai-web`.
- Use a running server's `/openapi.json` when app import has side effects or dependency gaps.
- Route workflow CRUD/session queue endpoint interpretation to `../workflows-queues/SKILL.md`, custom node runtime/import issues to `../workflow-nodes/SKILL.md`, and model install/cache endpoints to `../model-management/SKILL.md`.

## Unsafe or Excluded Maintenance

- Gallery maintenance was not bundled as an executable helper because it deletes orphan image files, removes orphan database rows, and regenerates thumbnails.
- Do not run mutating user-management commands for inspection. Prefer `--help`, `invoke-userlist --json` only against a disposable/confirmed root, or API reads with an authorized token.
- Do not start the full server just to answer route-family or setting-name questions; use bundled scripts first.
