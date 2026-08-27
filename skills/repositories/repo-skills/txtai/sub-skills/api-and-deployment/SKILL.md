---
name: api-and-deployment
description: "Configure and deploy txtai Application/API services,
  OpenAI-compatible endpoints, MCP, auth, custom routes, clusters, containers,
  cloud patterns, observability, and console caveats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# API and Deployment

Use this sub-skill when the user wants to run txtai as a configured application, FastAPI service, OpenAI-compatible endpoint, MCP server, secured internal service, custom API, distributed embeddings cluster, container/cloud deployment, or console-driven index explorer.

Route away from this sub-skill when the user is asking for detailed index/query authoring, pipeline design, or agent prompting internals:

- Use `../embeddings-search/SKILL.md` for `Embeddings` indexing, SQL, hybrid, graph, object, and search-query design.
- Use `../pipelines-and-workflows/SKILL.md` for pipeline selection, workflow task authoring, scheduling, and generator consumption.
- Use `../agents-and-llm-orchestration/SKILL.md` for LLM, RAG, Agent tools, prompts, templates, and model backend behavior.

## Fast Path

1. Install API support in the target environment.
   ```bash
   pip install "txtai[api]"
   ```
2. Generate a safe starter config without launching a server.
   ```bash
   python skills/txtai/sub-skills/api-and-deployment/scripts/api_config_template.py \
     --template secure-readonly --output app.yml
   python skills/txtai/sub-skills/api-and-deployment/scripts/api_config_template.py --validate app.yml
   ```
3. Start FastAPI/Uvicorn from the directory that contains `app.yml`.
   ```bash
   CONFIG=app.yml uvicorn "txtai.api:app" --host 127.0.0.1 --port 8000
   ```
4. Inspect live route docs at `http://127.0.0.1:8000/docs` and smoke-test a route enabled by the config.
   ```bash
   curl "http://127.0.0.1:8000/count"
   ```

## Configuration Model

The API is backed by `Application(config, loaddata=True)`. The config can be a YAML file path, YAML string, or dict. When `loaddata=True`, a saved index at top-level `path` is loaded if it exists; otherwise models/components are constructed from config.

Core top-level YAML keys:

- `path`: saved embeddings index path for API load/save; one API process serves one primary index path.
- `writable`: `false` by default; required for `/add`, `/index`, `/upsert`, `/delete`, and `/reindex`.
- `reindex`: `false` by default; only enable for trusted admin clients because `/reindex` accepts new config.
- `embeddings`: creates/loads an embeddings index and enables embeddings/search routes.
- Pipeline keys such as `summary`, `labels`, `textractor`, `llm`, `rag`, `translation`: create matching pipeline instances and routes.
- `workflow`: defines named workflows and enables `/workflow`.
- `agent`: defines named agents and enables `/agent`.
- `openai`: `true` enables `/v1/...` OpenAI-compatible routes.
- `mcp`: `true` or a dict enables `/mcp` and exports enabled API routes as MCP tools.
- `cluster`: configures an API aggregator over shard URLs.

See `references/configuration-and-routes.md` for route families, request shapes, response formats, auth, MCP, custom endpoint hooks, and `Application` details.

## Safe Service Patterns

Prefer a two-process or two-config deployment for mutable indexes:

- Admin/build process: private network, `writable: true`, optional `/add` and `/index`, no public ingress.
- Public query service: `writable: false`, `reindex: false`, token auth, TLS at a reverse proxy, only route keys needed by clients.
- Treat `/reindex` as a trust boundary even when token auth is enabled; it accepts config and optional function names.
- Keep model and index caches on persistent volumes in containers/serverless to avoid repeated downloads and cold starts.

Token auth uses a SHA-256 digest in `TOKEN`, while clients send the raw token in the `Authorization` header:

```bash
TOKEN="$(python -c 'import hashlib; print(hashlib.sha256(b"change-me").hexdigest())')" \
CONFIG=app.yml uvicorn "txtai.api:app" --host 127.0.0.1 --port 8000

curl -H "Authorization: Bearer change-me" "http://127.0.0.1:8000/count"
```

For TLS, prefer a reverse proxy terminating HTTPS and forwarding to a loopback/internal Uvicorn service.

See `references/deployment.md` for Uvicorn, Docker, model caching, cloud/serverless, Kubernetes/Knative, clustering, and observability patterns.

## Route Activation Rules

Routes are included based on top-level config keys. If a key is absent, the corresponding route family is absent even though txtai is installed.

Common route groups:

- `embeddings`: `GET /search`, `POST /batchsearch`, `POST /add`, `GET /index`, `GET /upsert`, `POST /delete`, `POST /reindex`, `GET /count`, transform/explain/object routes.
- `workflow`: `POST /workflow` with `name` and `elements`.
- `agent`: `POST /agent` with `name`, `text`, optional `maxlength`, and optional `stream`.
- `llm` and `rag`: `/llm`, `/batchllm`, `/rag`, `/batchrag` when those pipeline keys are configured.
- Pipeline keys: route families such as `/summary`, `/label`, `/translate`, `/textract`, `/segment`, `/caption`, `/tabular`, `/rerank`, and batch variants.
- `openai`: `/v1/chat/completions`, `/v1/embeddings`, `/v1/audio/speech`, `/v1/audio/transcriptions`, `/v1/audio/translations`.
- `mcp`: `/mcp` mounted by FastApiMCP when configured.

`embeddings` also enables similarity routes if no separate `similarity` key is present. `cluster` without `embeddings` still includes embeddings routes for the aggregator.

## OpenAI-Compatible Use

Set `openai: true` to expose OpenAI-style routes. The actual backend still comes from txtai config:

- Chat `model` matching an `agent` name calls that agent.
- Chat `model: embeddings` searches the embeddings index and returns the best result text.
- Chat `model` matching a pipeline name calls that pipeline, except `llm` uses the default LLM pipeline path.
- Chat `model` matching a workflow name runs the named workflow on the first user message.
- `/v1/embeddings` uses the configured embeddings transformer; the `model` field is echoed in the response.

If an OpenAI client reports a missing model or route, check both `openai: true` and the backing `agent`, `workflow`, `llm`, `rag`, `embeddings`, or pipeline section.

## MCP, Custom Endpoints, and Auth

Use `mcp: true` for defaults or a dict with `clientargs` and `mcpargs`. MCP exposes enabled API endpoints as tools at `/mcp`; it does not design tools or prompts for you.

Use environment hooks for advanced service customization:

- `API_CLASS=package.module.CustomAPI` uses a subclass/factory target instead of the default API class.
- `DEPENDENCIES=package.module.Dependency` adds FastAPI dependencies such as custom auth or middleware.
- `EXTENSIONS=package.module.Extension` runs extension hooks that can include custom routers.

Keep extension modules importable from the service environment and avoid referencing local checkout-only paths.

## Console Caveat

The console is an index/application explorer, not a standard argparse CLI. `python -m txtai.console --help` treats `--help` as the initial index/config path and may fail trying to load it. Use the console with a saved index path or YAML config path:

```bash
python -m txtai.console path/to/index
python -m txtai.console app.yml
```

Inside the console, commands include `.load`, `.config`, `.limit`, `.highlight`, and `.workflow`; plain text runs a search query.

## Validation Checklist

Before handing an API deployment back to a user, verify:

- Config parses as YAML and expected top-level route keys are present.
- API extras are installed; `from txtai.api import app` succeeds.
- `CONFIG` points to the intended config file from the service working directory.
- Public configs keep `writable: false` and `reindex: false` unless explicitly trusted.
- Token auth uses a SHA-256 digest in `TOKEN` and raw bearer token in client requests.
- `/docs` shows the expected route families; missing routes usually mean missing config keys.
- `Accept: application/msgpack` clients unpack MessagePack; JSON clients handle base64 for bytes/images.
- Container/cloud deployments mount index/model caches and satisfy CPU/GPU/system-library requirements.

Use `references/troubleshooting.md` for symptom-driven fixes covering extras, config paths, auth, OpenAI model routing, MCP dependencies, serialization, clusters, console path semantics, and cloud caveats.
