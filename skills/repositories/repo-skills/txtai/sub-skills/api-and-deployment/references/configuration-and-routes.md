# Configuration and Routes

This reference covers txtai `Application` and API configuration, route activation, request shapes, auth hooks, OpenAI-compatible routes, MCP, custom endpoints, and response formats.

## Application Loading

`Application(config, loaddata=True)` builds a configured txtai process from YAML or a Python dict.

- `config` can be a YAML file path, YAML string, or dict.
- `Application.read(path_or_yaml)` loads YAML from an existing file path, parses a YAML string, or raises `FileNotFoundError` for a plain missing path.
- `loaddata=True` loads an existing embeddings index from top-level `path` if one exists; `loaddata=False` loads models/config without loading persisted index data.
- Application creates pipelines first, workflows second, agents third, then initializes embeddings.
- Workflow actions named `index`, `upsert`, `search`, or `transform` resolve to application methods; other string actions resolve to configured pipelines/workflows or importable callable paths.
- Pipeline configs can request the application object with an `application:` key; this is useful for custom pipelines that need app state.

Minimal local Python application:

```python
from txtai import Application

app = Application("app.yml")
print(app.count())
print(app.search("climate policy", limit=3))
print(list(app.workflow("summarize", ["text"])))
```

## Top-Level YAML Keys

Core service keys:

```yaml
path: index-or-output-path
writable: false
reindex: false

embeddings:
  path: sentence-transformers/all-MiniLM-L6-v2
  content: true

workflow:
  echo:
    tasks:
      - task: console

openai: true
mcp: true
```

Key meanings:

- `path`: save/load location for a single embeddings index served by the API process.
- `writable`: enables mutation endpoints; defaults to read-only behavior when absent/false.
- `reindex`: enables `/reindex`; defaults to disabled and should stay disabled for untrusted clients.
- `cloud`: top-level cloud storage settings for index load/save.
- `embeddings`: all embeddings configuration supported by txtai; also enables search/count/index routes.
- `agent`: map of named agent configs; each name becomes callable by `/agent` and OpenAI chat model routing.
- Pipeline sections: lower-case pipeline names such as `summary`, `labels`, `translation`, `textractor`, `llm`, `rag`, `reranker`, `caption`, `tabular`, `segmentation`.
- `workflow`: map of named workflow definitions, each with `tasks` and optional `schedule` or `stream`.
- `openai`: boolean enabling OpenAI-compatible `/v1/...` routes.
- `mcp`: boolean or dict enabling `/mcp`.
- `cluster`: shard list for a distributed embeddings API aggregator.

## Workflow YAML in API Config

Workflow config belongs under top-level `workflow`:

```yaml
workflow:
  sumtranslate:
    tasks:
      - action: summary
      - action: translation
        args: [fr]
```

Task fields:

- `action`: a configured pipeline/workflow name, special action (`index`, `upsert`, `search`, `transform`), list of actions, or importable callable path.
- `task`: optional task type such as `file`, `retrieve`, `service`, or `console`.
- `args`: static argument list appended to workflow data when invoking the task.
- `schedule`: optional cron schedule block with `cron` and `elements`.
- Shorthand task strings become `action: <string>`.

Route workflow execution:

```bash
curl -X POST "http://127.0.0.1:8000/workflow" \
  -H "Content-Type: application/json" \
  -d '{"name":"sumtranslate","elements":["text to summarize"]}'
```

Design complex workflows in `../pipelines-and-workflows/SKILL.md`; use this reference only to expose already-designed workflows through the API.

## Route Activation

At FastAPI lifespan startup, txtai reads `CONFIG`, builds the API instance, scans bundled routers, and includes a router when its router name appears in the top-level config.

Examples:

- `embeddings:` enables embeddings routes plus similarity routes when no separate `similarity:` section exists.
- `summary:` enables summary routes.
- `workflow:` enables `/workflow`.
- `agent:` enables `/agent`.
- `openai: true` enables `/v1/...` OpenAI-compatible routes.
- `cluster:` without `embeddings:` still includes embeddings routes for aggregation.
- A missing top-level key means the corresponding route family is absent from `/docs`.

## Embeddings Route Family

Requires `embeddings:` or `cluster:`.

Common routes and shapes:

- `GET /search?query=<query>&limit=10&weights=0.5&index=name&parameters={...}&graph=false`
  - Returns `[{"id": value, "score": float}]` for vector-only results or dict rows when content/database query returns columns.
  - `limit` is bounded to `1..250`; default is `10`.
  - `parameters` may be JSON string query parameters for SQL bind variables.
- `POST /batchsearch` body fields: `queries`, optional `limit`, `weights`, `index`, `parameters`, `graph`.
- `POST /add` body: list of documents, usually `[{"id": 0, "text": "..."}]`.
- `POST /addobject` multipart fields: `data`, optional `uid`, optional `field`.
- `POST /addimage` multipart fields: `data`, `uid`, optional `field`.
- `GET /index`: builds an index from queued documents.
- `GET /upsert`: upserts queued documents into an existing index.
- `POST /delete` body: list of ids.
- `POST /reindex` body: `config` dict and optional `function` string.
- `GET /count`: returns index count.
- `POST /explain`, `POST /batchexplain`: token-importance explanations.
- `GET /transform`, `POST /batchtransform`: embedding vectors.

Mutation routes raise HTTP 403 when `writable` is false. `/reindex` also raises HTTP 403 when `reindex` is false.

For query syntax, row formats, SQL, graph, and result-shape details, use `../embeddings-search/SKILL.md`.

## Pipeline Route Families

Top-level pipeline keys activate matching routes. Common examples:

- `summary`: `GET /summary`, `POST /batchsummary`.
- `labels`: `POST /label`, `POST /batchlabel`.
- `translation`: `GET /translate`, `POST /batchtranslate`.
- `textractor`: `GET /textract`, `POST /batchtextract`.
- `segmentation`: `GET /segment`, `POST /batchsegment`.
- `similarity`: `POST /similarity`, `POST /batchsimilarity`.
- `llm`: `GET /llm`, `POST /batchllm` with optional `maxlength`, `stream`, `stripthink`.
- `rag`: `GET /rag`, `POST /batchrag` with optional `maxlength`, `stream`, `stripthink`.
- `reranker`: `GET /rerank`, `POST /batchrerank`.
- `caption`, `entity`, `tabular`, `transcription`, `texttospeech`, and object/upload routes depend on matching sections and extras.

Pipeline input/output contracts vary by pipeline. Use `../pipelines-and-workflows/SKILL.md` for authoring and `../agents-and-llm-orchestration/SKILL.md` for `llm`, `rag`, and agent internals.

## Agent Route

Requires top-level `agent:`.

```bash
curl -X POST "http://127.0.0.1:8000/agent" \
  -H "Content-Type: application/json" \
  -d '{"name":"researcher","text":"Write a short answer","maxlength":512,"stream":false}'
```

Fields:

- `name`: configured agent name under `agent`.
- `text`: instructions to run.
- `maxlength`: optional maximum sequence length.
- `stream`: optional streaming response flag.

Agent tool configuration, RAG templates, and backend choices belong in `../agents-and-llm-orchestration/SKILL.md`.

## OpenAI-Compatible Routes

Enable with:

```yaml
openai: true
```

Routes:

- `POST /v1/chat/completions`
- `POST /v1/embeddings`
- `POST /v1/audio/speech`
- `POST /v1/audio/transcriptions`
- `POST /v1/audio/translations`

Chat request body:

```json
{
  "messages": [{"role": "user", "content": "Hello"}],
  "model": "llm",
  "max_completion_tokens": 512,
  "stream": false
}
```

Chat model routing:

- If `model` matches a configured agent name, txtai calls `app.agent(model, message, **kwargs)`.
- If `model` is exactly `embeddings`, txtai runs search and returns the top result text.
- If `model` matches a configured pipeline name other than `llm`, txtai calls that pipeline.
- If `model` matches a configured workflow name, txtai runs the workflow on the first message.
- Otherwise txtai falls back to the configured `llm` pipeline.

Embeddings request body:

```json
{"input": "text to embed", "model": "embedding-model-name"}
```

`/v1/embeddings` returns an OpenAI-style object with `data[].embedding` vectors and echoes the request `model`; it does not switch model based on that field.

Audio routes require matching text-to-speech or transcription pipeline configuration and optional dependencies.

## MCP

Enable with a boolean:

```yaml
mcp: true
```

Or with options:

```yaml
mcp:
  clientargs:
    timeout: 100
  mcpargs:
    name: txtai
```

Behavior:

- Mounts a new `/mcp` route using FastApiMCP.
- Exports the currently enabled FastAPI routes as MCP tools.
- `clientargs` are passed to an internal HTTPX async client; defaults include `base_url: http://apiserver` and `timeout: 100`.
- `mcpargs` are passed to FastApiMCP.

If `/mcp` is absent, confirm `mcp` is a top-level key and the API extra includes MCP dependencies.

## Auth and Service Hooks

Default token auth:

```bash
TOKEN="$(python -c 'import hashlib; print(hashlib.sha256(b"secret").hexdigest())')" \
CONFIG=app.yml uvicorn "txtai.api:app"
```

Client:

```bash
curl -H "Authorization: Bearer secret" "http://127.0.0.1:8000/count"
```

Implementation details:

- `TOKEN` must be the SHA-256 hex digest of the expected client token.
- Client `Authorization` may include `Bearer `; txtai strips the prefix before hashing.
- Missing or mismatched auth returns HTTP 401 with `Invalid Authorization Token`.
- Without `TOKEN` or custom dependencies, the default API is open HTTP.

Customization environment variables:

- `API_CLASS`: import path to a custom API class, usually subclassing `txtai.api.API`.
- `DEPENDENCIES`: comma-separated import paths to FastAPI dependency classes/callables.
- `EXTENSIONS`: comma-separated import paths to extension classes; each receives the FastAPI `app` and can include routers.

Minimal extension pattern:

```python
from fastapi import APIRouter
from txtai.api import Extension, application

class MyRouter:
    router = APIRouter()

    @staticmethod
    @router.get("/lower")
    def lower(text: str):
        return application.get().pipeline("my.pipeline", (text,))

class MyExtension(Extension):
    def __call__(self, app):
        app.include_router(MyRouter().router)
```

## Response Formats

All bundled routers use an encoding-aware route class.

- Default response is JSON.
- `Accept: application/msgpack` returns MessagePack when possible.
- JSON responses base64-encode bytes, byte streams, and images.
- MessagePack responses preserve bytes for binary payloads.
- Clients requesting MessagePack must explicitly unpack it.

Examples:

```bash
curl -H "Accept: application/msgpack" "http://127.0.0.1:8000/count" --output count.msgpack
```

If binary/image results look like base64 strings, the client likely requested JSON. If a client sees binary bytes it cannot decode, it likely requested MessagePack or reused headers from a binary-capable client.
