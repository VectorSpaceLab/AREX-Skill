# Deployment

This reference covers safe service startup, Uvicorn, containers, cloud/serverless patterns, distributed clusters, model/index caching, observability, and console usage caveats.

## Local Uvicorn Service

Start from the directory that contains the config or pass an explicit config path:

```bash
CONFIG=app.yml uvicorn "txtai.api:app" --host 127.0.0.1 --port 8000
```

Production notes:

- Install API support with `pip install "txtai[api]"`.
- Keep the service bound to `127.0.0.1` behind a reverse proxy unless it is intentionally exposed.
- Use `--host 0.0.0.0` only inside a controlled container/network boundary.
- Uvicorn serves HTTP by default; use a TLS reverse proxy for HTTPS in most deployments.
- `/docs` exposes interactive OpenAPI docs for enabled route families.
- A missing route in `/docs` usually means the matching top-level YAML key is missing.

## Read-Only Public API Pattern

Use this pattern to expose search, count, OpenAI-compatible search, and MCP safely while avoiding untrusted mutation.

```yaml
path: /srv/txtai/index
writable: false
reindex: false

embeddings:
  path: sentence-transformers/all-MiniLM-L6-v2
  content: true

openai: true
mcp: true
```

Start with token auth:

```bash
TOKEN="$(python -c 'import hashlib; print(hashlib.sha256(b"replace-this-token").hexdigest())')" \
CONFIG=app.yml uvicorn "txtai.api:app" --host 127.0.0.1 --port 8000
```

Smoke checks:

```bash
curl -H "Authorization: Bearer replace-this-token" "http://127.0.0.1:8000/count"
curl -H "Authorization: Bearer replace-this-token" \
  -X POST "http://127.0.0.1:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"test query"}],"model":"embeddings"}'
```

Security notes:

- Token auth over plain HTTP exposes the raw bearer token to the network; put the service behind HTTPS.
- Keep `writable: false` and `reindex: false` for public services unless every caller is trusted.
- Build or update indexes in a separate private job, then deploy the saved index to read-only serving.

## Admin Build Service Pattern

For controlled indexing operations, run a private service or one-off job with mutation enabled:

```yaml
path: /srv/txtai/index
writable: true
reindex: false

embeddings:
  path: sentence-transformers/all-MiniLM-L6-v2
  content: true
```

Indexing sequence through API:

```bash
curl -X POST "http://127.0.0.1:8000/add" \
  -H "Content-Type: application/json" \
  -d '[{"id":0,"text":"first document"},{"id":1,"text":"second document"}]'

curl "http://127.0.0.1:8000/index"
curl "http://127.0.0.1:8000/count"
```

Operational notes:

- `/add` queues documents; `/index` builds and saves the index.
- `/upsert` updates an existing index and saves it when `path` is set.
- `/delete` deletes ids and saves when `path` is set.
- `/reindex` requires both `writable: true` and `reindex: true`; only expose it to trusted admin callers.

For document shape and query design, route to `../embeddings-search/SKILL.md`.

## Docker Patterns

txtai publishes CPU and GPU image families. CPU images are smaller and are recommended when no GPU is available. Base images do not bundle models, so first start may download models unless caches are mounted or baked into the image.

Model cache volume pattern:

```bash
docker run --rm -it \
  -p 8000:8000 \
  -v "$PWD/app.yml:/app/app.yml:ro" \
  -v "$PWD/index:/srv/txtai/index" \
  -v "$PWD/model-cache:/models" \
  -e CONFIG=/app/app.yml \
  -e TRANSFORMERS_CACHE=/models \
  txtai-api-image
```

Image build patterns from source decisions:

- API image: use an API Dockerfile pattern that copies `config.yml`, warms/caches models, and starts `uvicorn "txtai.api:app"`.
- Service image: use scheduled workflow config for long-running background jobs.
- Workflow image: run a named workflow once with command-line parameters.
- GPU image: use a GPU-capable base image and runtime, and verify driver/container CUDA compatibility before promising acceleration.
- Minimal image: install only needed extras instead of `txtai[all]` when image size matters.

Caveats:

- Mount a persistent index path if the service mutates or needs to load a prebuilt index.
- Mount model caches or bake models into the image to reduce cold starts.
- Do not store bearer tokens or cloud credentials in image layers; use runtime secrets.
- Ensure the container has enough memory for selected models and ANN/database backends.

## Cloud and Serverless Patterns

txtai applications are YAML-configured and can run locally, in containers, serverless functions, or Kubernetes/Knative.

Common cloud patterns:

- Docker Engine: run the same Uvicorn service in a container with mounted config, index, and cache volumes.
- Kubernetes: deploy the API as a service/deployment, mount persistent volumes, use secrets for tokens/credentials, and terminate TLS at ingress.
- Knative/serverless: package the API image for scale-to-zero with careful cold-start/model-cache planning.
- AWS Lambda/SAM: use a container-image Lambda with an ASGI adapter pattern and a config file copied into the image.

AWS-specific API/workflow launcher patterns are reference-only for this skill because they depend on cloud account setup, SAM/Lambda runtime behavior, credentials, and packaging choices. Use the architectural pattern, not a copied account-specific helper, for runtime deployments.

Serverless caveats:

- Cold starts are dominated by model downloads, model load time, and index load time.
- Function memory/time limits must fit the selected model and index.
- Writable indexes are usually a poor fit for ephemeral serverless storage; build externally and serve read-only.
- Cloud object storage settings may be appropriate for index load/save, but credentials must be provided by the deployment platform.

## Kubernetes and Clustered Embeddings

A txtai embeddings cluster aggregates multiple API shard URLs into one logical index:

```yaml
cluster:
  shards:
    - http://txtai-shard-0:8000
    - http://txtai-shard-1:8000
```

Behavior:

- Data is split across shards at index time.
- Search queries are sent to all shards in parallel and aggregated/sorted.
- `count` sums shard counts.
- `delete`, `reindex`, `index`, and `upsert` are forwarded to shards.
- String ids are hashed to choose a shard; missing ids are assigned randomly.
- Clusters are recommended only for very large datasets where a single ANN backend is insufficient.
- New shards cannot be added after building the initial index without rebuilding the cluster.

Kubernetes notes:

- Use stable service names for shard URLs.
- Keep shard count and routing stable for the lifetime of an index.
- Add health checks for every shard; partial shard outages can produce failed requests or incomplete behavior depending on the failing action.
- Run query aggregator separately from shard services when possible.

## OpenAI-Compatible Deployment

Minimal search-backed OpenAI-compatible config:

```yaml
path: /srv/txtai/index
writable: false

embeddings:
  path: sentence-transformers/all-MiniLM-L6-v2
  content: true

openai: true
```

Client example:

```python
from openai import OpenAI

client = OpenAI(base_url="http://127.0.0.1:8000/v1", api_key="not-used-by-txtai")
response = client.chat.completions.create(
    model="embeddings",
    messages=[{"role": "user", "content": "feel good story"}],
)
print(response.choices[0].message.content)
```

If token auth is enabled, use a client mechanism that sends `Authorization: Bearer <raw-token>` to the txtai server. Some OpenAI clients use the API key as bearer token automatically; confirm the raw token matches the digest configured in `TOKEN`.

## MCP Deployment

Minimal MCP config:

```yaml
embeddings:
  path: sentence-transformers/all-MiniLM-L6-v2

mcp: true
```

Smoke checks:

```bash
curl "http://127.0.0.1:8000/mcp"
```

Operational notes:

- `/mcp` appears only when `mcp` is configured and MCP dependencies import successfully.
- MCP exports enabled API routes; keep config minimal if you want a small tool surface.
- Use auth/TLS just as for normal API routes.
- MCP clients may have their own timeout and transport expectations; tune `mcp.clientargs` and `mcp.mcpargs` when needed.

## Observability

For tracing, install the MLflow plugin and enable autologging in the process that creates/runs txtai components:

```bash
pip install mlflow-txtai
mlflow server --host 127.0.0.1 --port 8000
```

```python
import mlflow

mlflow.set_tracking_uri("http://127.0.0.1:8000")
mlflow.set_experiment("txtai")
mlflow.txtai.autolog()
```

Deployment advice:

- Keep tracing service endpoints internal or protected.
- Use tracing for development, debugging, evaluation, and controlled staging first; evaluate overhead before enabling in production.
- Trace-sensitive payloads may contain prompts, retrieved context, user text, or generated outputs.
- Observability applies to embeddings, pipelines, workflows, RAG, and agents; detailed RAG/agent interpretation belongs in `../agents-and-llm-orchestration/SKILL.md`.

## Console Deployment Caveat

Install console support when needed:

```bash
pip install "txtai[console]"
```

Correct usage:

```bash
python -m txtai.console path/to/saved-index
python -m txtai.console app.yml
```

Console semantics:

- The first positional argument is treated as an index path or YAML config path.
- `python -m txtai.console --help` is not standard argparse help; it attempts to load `--help` as a path/config and can fail.
- Inside the console, `.load <path>` loads an index or YAML application.
- `.workflow <name> <args...>` runs a configured workflow only when the loaded object is an `Application`.
- Plain text is treated as a search query.

## Release Handoff Checklist

Before treating a deployment as ready:

- Verify `python -c "from txtai.api import app"` succeeds in the service environment.
- Validate YAML with the bundled helper script or `Application.read` before launch.
- Confirm `/docs` contains only expected route families.
- Confirm a successful read route such as `/count` or `/search`.
- Confirm mutation routes return HTTP 403 in public read-only deployments.
- Confirm auth rejects missing/wrong tokens and accepts the intended bearer token.
- Confirm OpenAI clients use the intended `model` name and send auth headers correctly.
- Confirm MCP `/mcp` exists only when intended.
- Confirm MessagePack clients unpack `application/msgpack`; JSON clients handle base64 binary fields.
- Confirm container/cloud config mounts persistent index and model caches.
- Record optional dependency/GPU/cloud features that were documented but not natively verified.
