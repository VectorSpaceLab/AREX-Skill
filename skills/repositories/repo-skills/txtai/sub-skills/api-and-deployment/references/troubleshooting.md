# Troubleshooting

Use this guide to diagnose txtai API, Application, OpenAI-compatible, MCP, deployment, cluster, serialization, and console issues.

## API Extra or Import Failure

Symptoms:

- `ImportError: API is not available - install "api" extra to enable`
- `ModuleNotFoundError` for `fastapi`, `uvicorn`, `fastapi_mcp`, `aiohttp`, or API response dependencies.
- `uvicorn "txtai.api:app"` fails before serving routes.

Likely causes:

- The environment has base `txtai` but not API extras.
- MCP or cluster dependencies are missing in a minimal environment.
- The service runs under a different Python interpreter than the one where txtai was installed.

Fixes:

```bash
python -m pip install "txtai[api]"
python -c "from txtai.api import app; print(app)"
python -m uvicorn "txtai.api:app" --help
```

If only a specific capability is missing, install the smallest matching extra or package set rather than `txtai[all]` when deployment size matters.

## CONFIG Path and YAML Load Issues

Symptoms:

- Startup fails with `FileNotFoundError: Unable to load file ...`.
- `/docs` loads but expected routes are absent.
- A config works locally but not in Docker/systemd/Kubernetes.

Likely causes:

- `CONFIG` points to a path relative to a different working directory.
- The config file is not mounted into the container.
- YAML parsed successfully but lacks the top-level key that activates a route.
- A string intended as a YAML body is interpreted as a missing file path.

Fixes:

```bash
CONFIG=/absolute/container/path/app.yml uvicorn "txtai.api:app"
python skills/txtai/sub-skills/api-and-deployment/scripts/api_config_template.py --validate app.yml
```

Checks:

- Confirm `CONFIG` is set in the service process, not only in an interactive shell.
- Confirm top-level keys such as `embeddings`, `workflow`, `agent`, `llm`, `rag`, `openai`, or `mcp` are present.
- Confirm the service user can read the file and mounted index path.

## Missing Route Family

Symptoms:

- `/docs` does not show `/workflow`, `/agent`, `/v1/chat/completions`, `/mcp`, or pipeline routes.
- Client gets 404 for a route expected from docs or examples.

Likely causes:

- Route families are activated by top-level config keys, not by installed packages alone.
- `openai: true` or `mcp: true` is missing.
- Pipeline/workflow/agent sections are nested under the wrong key.

Fixes:

- Add `workflow:` for `/workflow`.
- Add `agent:` for `/agent`.
- Add `openai: true` for `/v1/...` routes.
- Add `mcp: true` for `/mcp`.
- Add the needed pipeline key (`summary:`, `translation:`, `llm:`, `rag:`, etc.) for pipeline routes.
- Add `embeddings:` or `cluster:` for embeddings routes.

## Read-Only, Writable, and Reindex Failures

Symptoms:

- `POST /add`, `GET /index`, `GET /upsert`, `POST /delete`, or `POST /reindex` returns HTTP 403.
- Error detail contains `writable != True`.
- `/reindex` returns HTTP 403 with `reindex != True`.

Likely causes:

- API config is read-only, which is the safer default.
- `/reindex` is disabled even though `writable` is true.
- Caller expects a public service to mutate the index.

Fixes:

- For public query services, keep `writable: false` and use a private build/update job instead.
- For trusted admin jobs, set `writable: true` and run on private network.
- Enable `reindex: true` only when all callers and provided configs/functions are trusted.

Trust boundary:

- `/reindex` accepts new config and an optional function name; never expose it to untrusted clients.
- Token auth is not a substitute for network isolation when tokens are shared broadly.

## Index Load and Persistence Problems

Symptoms:

- `/count` returns `null` or `0` unexpectedly.
- Search returns empty results after restart.
- Updates work until container restarts, then disappear.

Likely causes:

- No `embeddings:` section, so no embeddings instance exists.
- Top-level `path` points to a nonexistent or wrong index.
- `path` is inside ephemeral container/serverless storage.
- `/add` queued documents but `/index` or `/upsert` was not called.
- `loaddata=False` was used in local Python and skipped saved index data.

Fixes:

- Set a persistent top-level `path`.
- Mount the index directory into containers.
- Call `/index` after `/add` for initial builds, or `/upsert` for updates.
- Confirm `Application(config, loaddata=True)` for serving saved indexes.

## Auth Token Mismatch

Symptoms:

- HTTP 401 with `Invalid Authorization Token`.
- Missing auth fails as expected, but a seemingly correct token also fails.

Implementation facts:

- Server `TOKEN` must be the SHA-256 hex digest of the expected token.
- Client sends the raw token, optionally with `Bearer ` prefix.
- txtai strips `Bearer ` and hashes the remainder before comparison.

Fixes:

```bash
python - <<'PY'
import hashlib
print(hashlib.sha256(b"secret").hexdigest())
PY
```

Server:

```bash
TOKEN=<sha256-of-secret> CONFIG=app.yml uvicorn "txtai.api:app"
```

Client:

```bash
curl -H "Authorization: Bearer secret" "http://127.0.0.1:8000/count"
```

Security reminder: bearer tokens sent over HTTP are clear text. Use HTTPS through a reverse proxy or a secure internal network.

## OpenAI-Compatible Model Routing Issues

Symptoms:

- OpenAI client gets a response from the wrong backend.
- `model` name appears ignored.
- `/v1/embeddings` echoes a model name but uses a different embedding model.
- Chat route errors because a configured backend is missing.

Implementation facts:

- `openai: true` enables routes but does not create LLMs, agents, workflows, or embeddings by itself.
- Chat model names are logical txtai names: agent name, workflow name, pipeline name, `embeddings`, or fallback `llm`.
- `/v1/embeddings` uses the configured embeddings transformer; request `model` is echoed, not used to switch models.
- `max_completion_tokens` maps to txtai `maxlength`.
- `stream: true` streams chat chunks with `data: ...` lines and a final `data: [DONE]`.

Fixes:

- Ensure `openai: true` is top-level.
- Add the backing section: `agent:`, `workflow:`, `embeddings:`, `llm:`, or the pipeline key.
- Use `model: embeddings` only when `embeddings:` exists and content search returns `text`.
- Use an agent/workflow name exactly as defined in YAML.
- For auth-enabled deployments, confirm the OpenAI client sends the raw token as bearer auth.

## MCP Route or Tool Export Problems

Symptoms:

- `/mcp` is missing from route list.
- MCP inspector cannot connect.
- Tool list is empty or missing expected API tools.

Likely causes:

- `mcp` top-level key is absent or false.
- API/MCP dependencies are missing.
- No API route families are enabled for tools to export.
- Client timeout/base URL assumptions need tuning.

Fixes:

```yaml
mcp: true
```

Or:

```yaml
mcp:
  clientargs:
    timeout: 100
  mcpargs:
    name: txtai
```

Checks:

- Confirm `/mcp` appears in `app.routes` or `/docs`-adjacent inspection.
- Confirm the route families you want exported are enabled in YAML.
- Keep MCP behind the same auth/TLS posture as the regular API.

## Serialization and MessagePack Confusion

Symptoms:

- Image or bytes fields are base64 strings.
- Client receives binary content it tries to parse as JSON.
- MessagePack response unpacking fails.

Implementation facts:

- Default JSON serializes bytes/images as base64 text.
- `Accept: application/msgpack` returns MessagePack and preserves bytes for binary payloads.
- The response class is selected from the exact `Accept` header value.

Fixes:

- For normal JSON clients, do not send `Accept: application/msgpack`; base64-decode binary fields if needed.
- For MessagePack clients, send `Accept: application/msgpack` and unpack with a MessagePack decoder.
- Avoid mixed proxy/client headers that override `Accept` unexpectedly.

## Custom API Class, Dependencies, or Extensions Fail

Symptoms:

- Startup import error for `API_CLASS`, `DEPENDENCIES`, or `EXTENSIONS`.
- Custom route is missing.
- Custom auth dependency rejects every request.

Likely causes:

- Import path is not available on `PYTHONPATH` in the service process.
- Extension class does not include a router on the passed FastAPI app.
- Dependency callable signature does not match FastAPI expectations.
- Configured custom pipeline key is missing or misspelled.

Fixes:

- Package custom code with the deployment or install it into the environment.
- Use comma-separated fully qualified import paths in environment variables.
- In extensions, call `app.include_router(...)`.
- Smoke-test custom imports with `python -c "import package.module"` from the service environment.

## Cluster Partial Failures

Symptoms:

- Aggregator requests fail when one shard is down.
- Counts/search results are lower than expected.
- String ids appear on unexpected shards.
- Adding a new shard after initial indexing breaks distribution assumptions.

Implementation facts:

- Cluster uses shard URLs from `cluster.shards`.
- Search and batch search fan out to all shards and aggregate results.
- `count` sums shard counts.
- String ids are hashed with Adler-32; missing ids are randomly assigned.
- Shard count should remain stable after the initial index build.

Fixes:

- Add health checks and readiness probes for each shard.
- Keep shard URLs stable with service DNS names.
- Rebuild the cluster when changing shard count.
- Use cluster only for very large indexes where single-node ANN/database backends are insufficient.
- Record partial outage behavior in deployment runbooks; do not silently treat partial shard results as complete.

## Docker, Cloud, GPU, and Network Caveats

Symptoms:

- Container cold start is slow.
- Models redownload on every start.
- GPU is not used or service crashes on CUDA errors.
- Cloud/serverless function times out.
- API works locally but not behind ingress/proxy.

Likely causes:

- No persistent model cache or index volume.
- GPU image/runtime/driver mismatch.
- Serverless memory/time limits too low for the model/index.
- `CONFIG` or index path not mounted in the container.
- Proxy strips auth or `Accept` headers.

Fixes:

- Mount model cache and index directories; optionally bake models into image layers.
- Prefer CPU images when GPUs are unavailable; they are smaller and simpler.
- Verify container GPU runtime separately from txtai before debugging model code.
- Use runtime secrets for tokens/cloud credentials.
- Configure reverse proxy to preserve `Authorization`, `Content-Type`, and `Accept` headers.
- For serverless, serve read-only indexes and avoid runtime index mutation.

## Observability Issues

Symptoms:

- No traces appear in MLflow.
- Tracing works in a script but not in the API service.
- Sensitive user prompts or retrieved context appear in traces.

Likely causes:

- `mlflow-txtai` is not installed in the service environment.
- `mlflow.txtai.autolog()` is not called in the process that creates/runs txtai components.
- Tracking URI is unreachable from the service container.
- Tracing is enabled in an environment with sensitive traffic.

Fixes:

- Install and configure MLflow in the same environment/process.
- Call autologging before exercising components.
- Keep tracking services internal/protected.
- Review trace payload retention policy before enabling in production.

## Console Path Semantics

Symptoms:

- `python -m txtai.console --help` fails trying to load `--help`.
- Console starts but `.workflow` does nothing.
- Plain query raises `AttributeError`.

Implementation facts:

- The console entrypoint treats the first positional argument as an index/config path.
- It is not a standard argparse CLI and does not implement `--help`.
- `.workflow` runs only when the loaded object is an `Application`, not a bare `Embeddings` instance.
- Plain text is treated as a search query against `console.app`.

Correct usage:

```bash
python -m txtai.console path/to/index
python -m txtai.console app.yml
```

Inside console:

```text
.load app.yml
.config
.limit 5
.workflow workflow-name arg1 arg2
plain search query
```

If the console import fails, install `txtai[console]` and confirm `rich` is available.
