# API Server Troubleshooting

Start with non-mutating checks:

```bash
python scripts/check_api_entrypoints.py
lightrag-server --help
curl http://localhost:9621/health
curl http://localhost:9621/openapi.json
```

Do not use uploads, deletes, graph mutation, or model-backed queries as generic liveness probes.

## Default Guest-Mode JWT Warning

Symptom:

```text
TOKEN_SECRET not set and AUTH_ACCOUNTS is not configured. Falling back to the default guest-mode JWT secret.
```

Meaning:

- Login auth is disabled because `AUTH_ACCOUNTS` is empty.
- The server still needs a JWT secret to issue guest tokens for WebUI/session behavior.
- This is acceptable for local development only when another layer is not expected to enforce auth.

Fix for exposed deployments:

```bash
lightrag-hash-password --username admin 'replace-with-a-strong-password'
```

Then configure:

```bash
AUTH_ACCOUNTS='admin:{bcrypt}...'
TOKEN_SECRET='replace-with-a-long-random-secret'
JWT_ALGORITHM=HS256
```

Restart the server process after changing `.env`.

## Auth Account Setup Fails

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `TOKEN_SECRET must be explicitly set...` | `AUTH_ACCOUNTS` is set with no secret or the built-in default secret. | Set a long non-default `TOKEN_SECRET`. |
| `AUTH_ACCOUNTS must use comma-separated user:password pairs` | One entry lacks `:` or has an empty username/password. | Use `user:password,user2:password2`; quote the whole value if needed. |
| Login always returns `Invalid username or password` | Wrong plaintext password or malformed bcrypt value. | Regenerate with `lightrag-hash-password --username USER PASSWORD`; preserve the `{bcrypt}` prefix. |
| `JWT_ALGORITHM` rejected | Algorithm is empty or `none`. | Use `HS256` unless deployment policy requires another secure supported algorithm. |
| API key returns `403` | Missing or wrong `X-API-Key` header. | Send the exact configured key in `X-API-Key`, or use a valid JWT. |
| JWT returns `401` | Expired, invalid, guest token used after auth became enabled, or user token used after auth disabled. | Log in again after auth-mode changes. |

If both login auth and API key are configured, either a valid non-guest JWT or the configured API key can satisfy protected routes.

## Missing API Extra Or Console Scripts

Symptoms:

- `lightrag-server: command not found`
- Import errors for `fastapi`, `uvicorn`, `gunicorn`, `python-multipart`, `jwt`, or `bcrypt`
- Upload routes fail before reaching LightRAG code because multipart support is absent

Fix:

```bash
pip install 'lightrag-hku[api]'
python scripts/check_api_entrypoints.py
```

If storage or local provider dependencies are missing after the API server starts, route those issues to `../../storage-backends/SKILL.md` or `../../llm-providers/SKILL.md` rather than treating them as API entrypoint failures.

## `.env` Not Taking Effect

Checklist:

- The `.env` file must be in the current startup directory where `lightrag-server` or `lightrag-gunicorn` is launched.
- Already-exported OS environment variables take precedence over `.env` values.
- Restart the process after changing `.env`; long-running workers do not reload it automatically.
- Command-line flags override env-backed defaults for that run.
- Use `/health` to confirm effective non-secret settings such as bind mode, provider names, storage names, workspace, auth mode, worker mode, and parser routing.

For generated setups, prefer rerunning `make env-base`, `make env-storage`, or `make env-server` instead of manually merging host and Docker settings.

## Upload, Scan, Delete, Or Graph Mutation Returns Busy/409

Common messages include `Pipeline is busy`, scan skipped because the pipeline is active, or delete/clear refusing while work is in progress.

Safe recovery sequence:

1. Poll `GET /documents/pipeline_status` and `GET /health` to identify whether the pipeline is busy, scanning, destructive, or has pending enqueue requests.
2. Wait for normal processing to finish when possible; do not retry destructive clear/delete in a tight loop.
3. If the job is intentionally stuck and the server supports it for the situation, call `POST /documents/cancel_pipeline`, then inspect status again.
4. Retry upload/text enqueue only after scan classification or destructive operations finish.
5. Retry scan only after `busy=false`, `scanning=false`, and `pending_enqueues=0`.
6. Retry graph mutation only after pipeline activity is idle, because graph edits are protected from concurrent document-derived graph writes.

Operational rule:

- Upload/text enqueue may overlap normal processing through pipeline request nudging.
- Scan classification and destructive delete/clear are exclusive windows; they reject conflicting writes to avoid losing files or writing into storage that is being removed.
- Detailed pipeline state-machine semantics belong to `../../document-pipeline/SKILL.md`.

## Query Route Surprises

| Symptom | Explanation | Fix |
| --- | --- | --- |
| `/query` does not stream | It is intentionally JSON-only and forces `stream=false`. | Use `POST /query/stream` for NDJSON streaming. |
| `/query/stream` returns one line | Request set `stream=false`, response came from cache, or provider returned a non-streaming result. | Still parse as NDJSON; one line is valid. |
| Streaming works locally but buffers behind proxy | Proxy buffering is enabled. | Disable response buffering for streaming routes; honor `X-Accel-Buffering: no` where supported. |
| Rerank warning appears | `enable_rerank=true` but no reranker is configured. | Configure rerank provider via `RERANK_*` or send `enable_rerank=false`. |
| `only_need_context` or `only_need_prompt` surprises users | These diagnostic flags bypass normal answer generation. | Remove them for end-user answers. |

Provider errors during query are usually provider-binding issues; route to `../../llm-providers/SKILL.md`.

## Path Prefix, CORS, And WebUI Routing

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `/site01/docs` works but OpenAPI paths look unprefixed | Expected root-path behavior. | Do not duplicate the prefix in route definitions; clients use browser-visible prefix, OpenAPI path keys stay natural. |
| WebUI loads but API calls hit the wrong base URL | Runtime prefix injection missing or proxy strips/adds a different prefix than `LIGHTRAG_API_PREFIX`. | Set `LIGHTRAG_API_PREFIX` to the browser-visible stripped prefix and restart. |
| Direct backend `/test-prefix/...` works in tests but proxy fails | Proxy forwarding/path stripping differs from FastAPI root-path assumptions. | Align proxy rewrite rules with `LIGHTRAG_API_PREFIX`; backend routes remain natural. |
| Browser CORS errors | `CORS_ORIGINS` does not include the WebUI/dev origin, or credentials/header policy mismatches deployment. | Set `CORS_ORIGINS` to explicit allowed origins for non-same-origin dev/proxy setups. |
| Dev WebUI prefix differs from production | Vite dev runtime config not set. | Use `VITE_DEV_API_PREFIX` and `VITE_DEV_WEBUI_PREFIX` for dev parity. |

When possible, prefer same-origin WebUI served by the API server at `/webui/`; it avoids most CORS issues.

## WebUI Build Or Serve Issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `/webui/` returns unavailable or fallback response | Packaged WebUI assets are not present in the installed package/source build. | Build from source with `cd lightrag_webui && bun install --frozen-lockfile && bun run build`, then restart/reinstall as appropriate. |
| Built assets not included in a normal package install | Assets were built after package installation. | Build before creating/installing the package, or use editable install for development. |
| `bun: command not found` | Bun is not installed. | Install Bun for project tests; `npm run build` can build/lint when dependencies are installed, but tests still use Bun. |
| Frontend tests fail under Vitest/Jest | Wrong test runner. | Use `bun test`. |
| Browser automation waits forever on `networkidle` | Vite dev server keeps long-lived connections. | Wait for `domcontentloaded` plus a stable selector. |
| Build fails on path aliases in old versions | Tooling cannot resolve frontend alias config. | Use the current package or run the project’s configured build script rather than ad-hoc bundler commands. |

## Docker And Setup Wizard Issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `make env-storage` or `make env-server` says `.env` is missing | Base setup was not run. | Run `make env-base` first. |
| Host `.env` contains container-only hostnames after manual edits | Host and Docker layers were merged by hand. | Rerun the relevant `make env-*` target; keep container overrides in generated compose. |
| Generated stack lacks updated service blocks | Existing wizard-managed blocks were preserved. | Use `make env-base-rewrite` or `make env-storage-rewrite` when full regeneration is intended. |
| Compose fails because required variables are missing | Some service credentials are resolved at compose startup, not snapshotted into generated YAML. | Export or set the required variables before `docker compose -f docker-compose.final.yml up -d`. |
| Security audit reports weak auth or unsafe whitelist | Deployment is not hardened. | Run `make env-server`, set strong auth/API key/JWT values, then rerun `make env-security-check`. |

## Difficult Usability Cases To Test

1. Safe auth hardening: start from guest-mode warning, generate a bcrypt admin account, set a non-default `TOKEN_SECRET`, verify `/auth-status` changes to enabled mode, confirm invalid JWT/API key failures are distinct, and ensure no secret appears in reusable notes.
2. Busy-conflict recovery: while ingestion is active, reason through why graph mutation gets HTTP `409`, scan refuses overlapping work, and destructive document delete/clear must wait; use `/documents/pipeline_status` and `/health` to decide when retry is safe without deleting files or losing uploads.
