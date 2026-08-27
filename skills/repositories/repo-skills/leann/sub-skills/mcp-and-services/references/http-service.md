# HTTP service

## Start and dependency contract

LEANN exposes a minimal FastAPI search service through either entry point:

```bash
leann serve
python -m leann.server
```

The CLI accepts:

```text
leann serve [--host HOST] [--port PORT]
```

Defaults are `127.0.0.1` and `8000`. The environment equivalents are
`LEANN_SERVER_HOST` and `LEANN_SERVER_PORT`; explicit CLI options override them
for that process. Generate and review a command without starting the service:

```bash
python scripts/generate_service_config.py http
python scripts/generate_service_config.py http --host 127.0.0.1 --port 9000
```

The optional server dependencies are FastAPI, Pydantic 2+, and Uvicorn. A
package-extra installation is:

```bash
uv pip install 'leann-core[server]'
```

No endpoint builds or mutates an index. However, `LeannCLI` initializes its
project-local index directory, so start from a writable project root that owns
`.leann/indexes`.

## Endpoint catalog

| Method and path | Request | Success | Important failures |
|---|---|---|---|
| `GET /health` | none | `200 {"status":"ok"}` | Connection/bind failure occurs before the route is reachable. |
| `GET /indexes` | none | `200` JSON array for indexes discovered in the current project | Empty array means no current-project index; it does not perform global registry listing. |
| `POST /indexes/{index_name}/search` | JSON `SearchRequest` | `200` JSON array of search results | Missing index -> 404; invalid body -> FastAPI 422; unhandled search/backend failure -> 500. |

`GET /indexes` items have this shape:

```json
{
  "name": "project-docs",
  "type": "cli",
  "status": "...",
  "size_mb": 1.25,
  "project_path": "/path/to/current/project"
}
```

`project_path` is absolute and may be sensitive. Do not expose or paste this
response without reviewing it.

## Search request and response

Request model and defaults:

| Field | Type | Required/default |
|---|---|---|
| `query` | string | required |
| `top_k` | integer | `5` |
| `complexity` | integer | `64` |
| `beam_width` | integer | `1` |
| `prune_ratio` | float | `0.0` |
| `recompute_embeddings` | boolean | `true` |
| `pruning_strategy` | string | `"global"` |
| `use_grep` | boolean | `false` |

Example:

```bash
curl --fail-with-body \
  -H 'Content-Type: application/json' \
  -d '{"query":"request authentication","top_k":5,"complexity":64}' \
  http://127.0.0.1:8000/indexes/project-docs/search
```

Success is a JSON array; each item is normalized to:

```json
{
  "id": "passage-id",
  "score": 0.812,
  "text": "matching passage text",
  "metadata": {"source": "docs/example.md"}
}
```

The service constructs `LeannSearcher` for the index base path and forwards all
request fields to `search`. Detailed parameter semantics belong to
`api-and-indexing`.

A missing index returns:

```json
{
  "detail": "Index 'project-docs' not found in current project. Build it with: leann build project-docs --docs ./your_docs"
}
```

The index base is resolved as
`.leann/indexes/<index_name>/documents.leann`, and existence is determined by
`documents.leann.meta.json`.

## Current-project behavior

The service derives its project from the process working directory:

```bash
cd /path/to/project
leann serve --host 127.0.0.1 --port 8000
```

Starting from a home directory, GUI launch directory, or service manager's
default directory points the API at the wrong `.leann/indexes` tree. Set the
service manager's working directory explicitly; do not use shell interpolation
for private paths.

Unlike MCP `leann_list`, `GET /indexes` intentionally lists only the current
project. There is no endpoint to choose an arbitrary project directory and no
HTTP build endpoint.

## Exposure and deployment boundary

The HTTP application has no authentication, authorization, TLS, CORS policy,
rate limit, request-size policy, or tenant isolation in this implementation.
Search responses return raw passage text and metadata; `/indexes` returns an
absolute project path.

- Keep the default loopback bind for local use.
- The bundled generator rejects non-loopback hosts unless
  `--allow-network-exposure` is supplied. That flag records intent; it does not
  add security controls.
- Before any LAN/public bind, place the service behind a separately configured
  authenticated TLS reverse proxy, firewall it, restrict the process account,
  and decide whether response metadata must be redacted.
- Do not expose private indexes on a shared workstation or multi-user service.
- Treat queries and returned passage text as potentially sensitive logs.
- Stop the Uvicorn process cleanly; do not launch duplicate workers against
  unknown embedding-daemon state without reviewing backend behavior.

## Health and smoke sequence

After an authorized launch, validate in this order:

```bash
curl --fail-with-body http://127.0.0.1:8000/health
curl --fail-with-body http://127.0.0.1:8000/indexes
curl --fail-with-body \
  -H 'Content-Type: application/json' \
  -d '{"query":"smoke test","top_k":1}' \
  http://127.0.0.1:8000/indexes/project-docs/search
```

A passing health route proves only that FastAPI/Uvicorn is listening. It does
not prove the working directory, index, embedding runtime, or search backend;
the index list and one bounded search are separate checks.
