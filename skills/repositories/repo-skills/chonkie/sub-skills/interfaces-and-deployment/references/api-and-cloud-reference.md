# Local API, Chonkie Cloud, logging, and deployment reference

This reference covers installed Chonkie `1.7.0` interface surfaces for serving and client/API work. The local OSS FastAPI API and Chonkie Cloud wrappers are different surfaces:

- **Local OSS FastAPI API**: self-hosted, no built-in auth, routes under a local process running `chonkie.api.main:app`.
- **Chonkie Cloud wrappers**: client classes that call `https://api.chonkie.ai` and require `CHONKIE_API_KEY` or an explicit `api_key`.

## Installation extras

| Use case | Install |
| --- | --- |
| CLI only | `pip install "chonkie[cli]"` |
| Local API server | `pip install "chonkie[api]"` |
| API with local semantic/code routes available | `pip install "chonkie[api,semantic,code]"` |
| API with provider embedding routes | Add provider extras such as `openai`, `cohere`, or `voyageai`; see `../embeddings-and-generative/`. |
| Docker image behavior | Reference build uses API, semantic, code, OpenAI, and Catsu-related extras. |

The `api` extra supplies FastAPI/Uvicorn plus async database support (`sqlalchemy`, `alembic`, `aiosqlite`) and recipe/JSON-schema helpers.

## FastAPI app basics

Import target:

```python
from chonkie.api.main import app
```

Server commands:

```bash
chonkie serve --host 127.0.0.1 --port 8000
uvicorn chonkie.api.main:app --host 0.0.0.0 --port 8000
```

App metadata and docs:

| Property | Value |
| --- | --- |
| Title | `Chonkie OSS API` |
| Swagger UI | `/docs` |
| ReDoc | `/redoc` |
| OpenAPI JSON | `/openapi.json` |
| Health | `GET /health` returns `{"status": "ok"}` |
| Info | `GET /` returns API metadata and route lists |

Startup lifespan initializes the configured database. The default database URL is `sqlite+aiosqlite:///./data/chonkie.db`; set `DATABASE_URL` to override it. For SQLite paths, the database directory is created automatically when possible.

CORS is permissive by default. Set `CORS_ORIGINS` to a comma-separated origin list for production, for example:

```bash
CORS_ORIGINS=https://app.example.com,https://admin.example.com chonkie serve
```

## Local API endpoints

All chunking endpoints accept a string or list of strings in the `text` field. A single string returns a flat list of chunk dictionaries; a list of strings returns a list of lists.

Chunk dictionary fields include at least:

| Field | Meaning |
| --- | --- |
| `text` | Chunk content. |
| `start_index` | Start character index in original input. |
| `end_index` | End character index in original input. |
| `token_count` | Token count according to the selected tokenizer/chunker. |

Routes:

| Method/path | Purpose | Main schema |
| --- | --- | --- |
| `GET /health` | Health check for probes/load balancers. | none |
| `GET /` | API information and route list. | none |
| `POST /v1/chunk/token` | Fixed token-window chunking. | `TokenChunkerRequest` |
| `POST /v1/chunk/sentence` | Sentence-boundary chunking. | `SentenceChunkerRequest` |
| `POST /v1/chunk/recursive` | Recursive structural chunking; chunkers are cached per `(recipe, lang, tokenizer)`. | `RecursiveChunkerRequest` |
| `POST /v1/chunk/semantic` | Semantic similarity chunking; requires semantic/model dependencies. | `SemanticChunkerRequest` |
| `POST /v1/chunk/code` | AST-aware code chunking; requires code/tree-sitter dependency. | `CodeChunkerRequest` |
| `POST /v1/refine/overlap` | Add overlap context to chunks without mutating input objects. | `OverlapRefineryRequest` |
| `POST /v1/refine/embeddings` | Attach embeddings to chunks through embedding models/providers. | `EmbeddingsRefineryRequest` |
| `POST /v1/pipelines` | Create a stored local API pipeline. | `PipelineCreateRequest` |
| `GET /v1/pipelines` | List stored pipelines. | none |
| `GET /v1/pipelines/{pipeline_id}` | Retrieve one stored pipeline. | path id |
| `PUT /v1/pipelines/{pipeline_id}` | Update name, description, or steps. | `PipelineUpdateRequest` |
| `DELETE /v1/pipelines/{pipeline_id}` | Delete a stored pipeline. | path id |
| `POST /v1/pipelines/{pipeline_id}/execute` | Execute a stored pipeline on text. | `PipelineExecuteRequest` |

## Local API request schemas

### Chunking schemas

| Schema | Required | Defaults / key fields |
| --- | --- | --- |
| `TokenChunkerRequest` | `text` | `tokenizer="character"`, `chunk_size=512`, `chunk_overlap=0`; `chunk_size >= 1`, `chunk_overlap >= 0`. |
| `SentenceChunkerRequest` | `text` | `tokenizer="character"`, `chunk_size=512`, `chunk_overlap=0`, `min_sentences_per_chunk=1`, `min_characters_per_sentence=12`, `approximate=False`, `delim=["\n", ". ", "! ", "? "]`, `include_delim="prev"`. |
| `RecursiveChunkerRequest` | `text` | `tokenizer="character"`, `chunk_size=512`, `recipe="default"`, `lang="en"`, `min_characters_per_chunk=24`. |
| `SemanticChunkerRequest` | `text` | `embedding_model="minishlab/potion-base-8M"`, `threshold=0.5`, `chunk_size=512`, `similarity_window=3`, `min_sentences_per_chunk=1`, `min_characters_per_sentence=12`, delimiters, skip/filter controls. |
| `CodeChunkerRequest` | `text` | `tokenizer="character"`, `chunk_size=512`, `language="python"`, `include_nodes=False`. |

Minimal deterministic request:

```json
{
  "text": "Chonkie makes chunking predictable.",
  "chunk_size": 128,
  "chunk_overlap": 0
}
```

Send it to `POST /v1/chunk/token` or use the recursive schema below for structured text:

```json
{
  "text": "# Heading\n\nA paragraph.",
  "chunk_size": 256,
  "recipe": "markdown",
  "min_characters_per_chunk": 24
}
```

### Refinery schemas

| Schema | Required | Defaults / key fields |
| --- | --- | --- |
| `OverlapRefineryRequest` | `chunks` | `tokenizer="character"`, `context_size=0.25`, `mode="token"`, `method="suffix"`, `merge=True`. The local API schema accepts `method="suffix"` or `"prefix"`. |
| `EmbeddingsRefineryRequest` | `chunks` | `embedding_model="text-embedding-3-small"` in the installed schema. Provider/model setup belongs to `../embeddings-and-generative/`. |

A chunk in `chunks` must contain at least `text`, `start_index`, `end_index`, and `token_count`; missing fields produce validation or 400-level errors.

### Stored local API pipeline schemas

`PipelineCreateRequest`:

| Field | Type | Meaning |
| --- | --- | --- |
| `name` | string | Unique pipeline name. Duplicate names produce 400 errors. |
| `description` | optional string | Human-readable description. |
| `steps` | list of `PipelineStepRequest` | Ordered steps to run. |

`PipelineStepRequest`:

| Field | Type | Meaning |
| --- | --- | --- |
| `type` | `"chunk"` or `"refine"` | Step type. |
| `chunker` | optional string | Required for `type="chunk"`. Valid local API execution names include `token`, `sentence`, `recursive`, `semantic`, `code`, `late`, `neural`, `slumber`, `table`, and `fast`. |
| `refinery` | optional string | Required for `type="refine"`. Valid names are `overlap` and `embeddings`. |
| `config` | object | Keyword arguments for the chunker/refinery constructor or recipe handling. |

Execution rules:

- The stored pipeline must contain at least one step.
- A `refine` step must follow a chunk step because it requires chunks as input.
- Bad step type, missing `chunker`, missing `refinery`, unknown component names, and invalid config produce 400 errors.
- Missing extras/model/provider errors generally appear as 500 errors.

## Local API error classes

| Status | Common cause |
| --- | --- |
| `200` / `201` / `204` | Successful read/create/delete. |
| `400` | Invalid chunk/refinery parameters, duplicate pipeline name, unknown component, bad pipeline order, or malformed chunk dicts. |
| `404` | Stored pipeline id not found. |
| `422` | Pydantic/FastAPI request body validation failed. |
| `500` | Runtime failure such as missing optional extra, model/provider initialization failure, or unexpected chunker/refinery exception. |

## Logging and environment variables

### Package logging

Set `CHONKIE_LOG` before importing Chonkie:

| Value | Effect |
| --- | --- |
| unset / empty | warnings and errors (`WARNING`) |
| `off`, `false`, `0`, `disabled`, `none` | disable Chonkie logging |
| `error`, `1` | `ERROR` |
| `warning`, `2` | `WARNING` |
| `info`, `3` | `INFO` |
| `debug`, `4` | `DEBUG` |
| `unconfigured` | leave logging unconfigured so a host/test framework can control the root logger |

Programmatic controls:

```python
import chonkie

chonkie.logger.configure("debug")
chonkie.logger.configure("off")
chonkie.logger.enable("info")
chonkie.logger.disable()
```

### API server environment

| Variable | Default | Purpose |
| --- | --- | --- |
| `LOG_LEVEL` | `INFO` for direct API import/server; `chonkie serve` defaults to `info` and sets `LOG_LEVEL` to uppercase | Configures API logging/Uvicorn level. |
| `CORS_ORIGINS` | `*` | Comma-separated local API CORS allow-list. |
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/chonkie.db` | Async SQLAlchemy database URL for stored API pipelines. |
| `HF_HOME` | deployment-dependent | Useful in containers so model caches are writable by the runtime user. |

### Credential boundaries

| Credential | Applies to | Notes |
| --- | --- | --- |
| `CHONKIE_API_KEY` | Chonkie Cloud client wrappers | Required for `chonkie.cloud` objects unless an explicit `api_key` argument is passed. |
| Provider keys such as `OPENAI_API_KEY`, `COHERE_API_KEY`, `VOYAGE_API_KEY`, `MISTRAL_API_KEY` | Embedding/generative/OCR providers | Route details to `../embeddings-and-generative/`. |
| Vector DB credentials/URLs | Storage handshakes | Route to `../integrations-and-storage/`. |

## Chonkie Cloud wrappers

Cloud wrappers call `https://api.chonkie.ai/v1` and should be treated as external network/credential operations. Constructors generally read `CHONKIE_API_KEY` or accept `api_key=...`; many chunker constructors also perform an API availability check, so do not instantiate them in offline diagnostics.

Import surface:

```python
from chonkie.cloud import (
    Pipeline, PipelineStep, FileManager,
    TokenChunker, SentenceChunker, RecursiveChunker, SemanticChunker,
    CodeChunker, LateChunker, NeuralChunker, SlumberChunker,
    OverlapRefinery, EmbeddingsRefinery,
)
```

### Cloud pipeline

`chonkie.cloud.Pipeline(slug, description=None, api_key=None)` requires a slug containing only lowercase letters, numbers, dashes, and underscores. It raises if no API key is provided.

Methods:

| Method | Purpose |
| --- | --- |
| `Pipeline.get(slug, api_key=None)` | Fetch an existing cloud pipeline. |
| `Pipeline.list(api_key=None)` | List cloud pipelines. |
| `Pipeline.validate(steps, api_key=None)` | Validate a list of cloud pipeline steps; returns `(is_valid, errors)`. |
| `.chunk_with(chunker_type, **kwargs)` | Add a cloud chunking step and return `self`. |
| `.refine_with(refinery_type, **kwargs)` | Add a cloud refinery step and return `self`. |
| `.process_with(chef_type, **kwargs)` | Add a cloud processing step and return `self`. |
| `.update(description=None)` | Update an existing pipeline. |
| `.delete()` | Delete the cloud pipeline. |
| `.run(text=None, file=None)` | Save if necessary and execute with either text or one file. Exactly one of `text` or `file` is required. |
| `.to_config()` | Return step dictionaries. |
| `.describe()` | Return a `chunk(token) -> refine(overlap)`-style description. |
| `.reset()` | Clear steps. |

Cloud `PipelineStep(type, component, params={})` converts to/from dictionaries with `type`, `component`, and parameter keys.

### Cloud files

`FileManager(api_key=None)` requires `CHONKIE_API_KEY` or an explicit key. `upload(path)` posts the file to cloud storage and returns a `File(name, size)` object. Cloud pipeline and chunker `.run(..., file=...)` / `.chunk(..., file=...)` paths upload before execution.

### Cloud chunkers

| Class | Main constructor defaults | Operation |
| --- | --- | --- |
| `TokenChunker` | `tokenizer="gpt2"`, `chunk_size=512`, `chunk_overlap=0` | `chunk(text=... | file=...)` posts to `/chunk/token`. |
| `SentenceChunker` | `tokenizer="gpt2"`, `chunk_size=512`, `chunk_overlap=0`, `min_sentences_per_chunk=1`, `min_characters_per_sentence=12`, `approximate=True`, delimiter controls | Posts to `/chunk/sentence`. |
| `RecursiveChunker` | `tokenizer="gpt2"`, `chunk_size=512`, `min_characters_per_chunk=12`, `recipe="default"`, `lang="en"` | Posts to `/chunk/recursive`. |
| `SemanticChunker` | `embedding_model="minishlab/potion-base-32M"`, `threshold=0.8`, `chunk_size=512`, similarity/filter controls | Posts to `/chunk/semantic`. |
| `CodeChunker` | `tokenizer="gpt2"`, `chunk_size=512`, `language="auto"` | Posts to `/chunk/code`; cloud response does not expose tree-sitter nodes. |
| `LateChunker` | `embedding_model="nomic-ai/modernbert-embed-base"`, `chunk_size=512`, `min_characters_per_chunk=24`, recipe/lang controls | Posts to `/chunk/late`. |
| `NeuralChunker` | model default `mirth/chonky_modernbert_large_1`, `min_characters_per_chunk=10` | Posts to `/chunk/neural`; validates supported model names client-side. |
| `SlumberChunker` | `tokenizer="gpt2"`, `chunk_size=1024`, `recipe="default"`, `lang="en"`, `candidate_size=128`, `min_characters_per_chunk=24` | Posts to `/chunk/slumber`. |

Cloud chunkers return `Chunk` objects for single input and lists of lists for batch input where supported.

### Cloud refineries

| Class | Defaults | Operation |
| --- | --- | --- |
| `OverlapRefinery` | `tokenizer="gpt2"`, `context_size=0.25`, `mode="token"`, `method="suffix"`, `recipe="default"`, `lang="en"`, `merge=True` | Posts chunk dicts to `/refine/overlap` and deserializes back to the original chunk type. |
| `EmbeddingsRefinery` | `embedding_model="minishlab/potion-retrieval-32M"` | Posts chunk dicts to `/refine/embeddings`, converts returned embeddings to NumPy arrays on chunk objects. |

Both cloud refineries require all input chunks to have the same type.

## Login/load token helpers

`chonkie.utils` exposes helpers for the public Chonkie API token config file:

```python
from chonkie.utils import login, load_token

login("ck_...")       # writes the API key into ~/.chonkie/config.json
token = load_token()  # prefers CHONKIE_API_KEY, then config file
```

Behavior:

- `login(api_key)` creates the user config directory if needed and writes `api_key` into `~/.chonkie/config.json`.
- `load_token()` first returns `CHONKIE_API_KEY` when set.
- If the environment variable is absent, `load_token()` reads `~/.chonkie/config.json` and returns `api_key`.
- Missing config or missing `api_key` raises `ValueError` with a message suggesting login.
- The installed CLI command list does not expose an active `chonkie login` command; use the Python helper or environment variable.

## Deployment guidance

### Local process

For development:

```bash
pip install "chonkie[api,semantic,code]"
CHONKIE_LOG=info chonkie serve --host 127.0.0.1 --port 8000
```

For a production process manager, prefer direct Uvicorn or your ASGI supervisor, set a fixed `DATABASE_URL`, restrict `CORS_ORIGINS`, and put a reverse proxy/TLS layer in front if exposing the service beyond localhost.

### Container behavior distilled from packaged deployment files

The reference container setup uses:

- Python 3.11 slim multi-stage build.
- Builder installs Chonkie with API, semantic, code, OpenAI, and Catsu-capable extras.
- Runtime stage copies only the virtual environment, installs the small runtime system library set needed by numerical/model dependencies, creates `/app/data`, runs as a non-root `chonkie` user, exposes port `8000`, and starts `uvicorn chonkie.api.main:app --host 0.0.0.0 --port 8000`.
- Health check performs an HTTP GET to `http://localhost:8000/health`.
- `HF_HOME` is pointed into the writable data volume so model caches are available to the non-root user.

Compose-style settings to preserve conceptually:

| Setting | Purpose |
| --- | --- |
| Port `8000:8000` | Expose the API server. |
| Data volume mounted at app data directory | Persist SQLite database and optional model cache. |
| Optional `.env` file | Keep environment configuration outside the image. |
| `LOG_LEVEL`, `CORS_ORIGINS`, `DATABASE_URL` | Server logging, browser access, and stored pipeline database. |
| Provider API keys | Only for provider-backed embedding/refinery routes. |
| Restart policy and health check | Keep service available and detect unhealthy containers. |

Production tips:

- Restrict `CORS_ORIGINS`; do not keep `*` for browser-facing production services.
- Add authentication or a trusted reverse proxy if exposing the local OSS API publicly; the API itself is unauthenticated.
- Persist the database volume if using stored API pipelines.
- Warm up model-backed routes such as semantic chunking after deploy if first-request latency matters.
- Route vector database service/container decisions to `../integrations-and-storage/`.
