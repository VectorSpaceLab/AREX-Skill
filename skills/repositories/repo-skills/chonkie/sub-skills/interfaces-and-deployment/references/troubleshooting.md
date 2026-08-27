# Interfaces and deployment troubleshooting

Use this guide for Chonkie CLI, local FastAPI API, Chonkie Cloud, logging, and deployment issues. When the issue belongs to another capability family, route rather than duplicating deep guidance.

## Routing matrix

| Symptom or task | Primary owner |
| --- | --- |
| CLI command construction, `chonkie serve`, API routes, `CHONKIE_API_KEY`, `CHONKIE_LOG`, Docker/compose serving | this sub-skill |
| Local chunker choice, chunk object fields, deterministic fallback behavior | `../chunking-and-types/` |
| Python fluent pipeline API, chefs, refineries inside local Python workflows | `../pipelines-and-processing/` |
| OpenAI/Cohere/Voyage/Gemini/LiteLLM/Catsu/provider embeddings or model cache/download issues | `../embeddings-and-generative/` |
| Qdrant/Chroma/Pinecone/Milvus/MongoDB/Pgvector/Weaviate/Elastic/Turbopuffer/LanceDB storage services | `../integrations-and-storage/` |

## CLI issues

### `chonkie: command not found`

Likely causes:

- Chonkie is not installed in the active environment.
- The `cli` extra or console-script entry point is missing.
- The environment's `bin`/`Scripts` directory is not on `PATH`.

Checks:

```bash
python -c "import chonkie; print(chonkie.__version__)"
python -m pip show chonkie
python -m pip install "chonkie[cli]"
```

Then re-open/activate the environment or invoke the command from the environment that installed Chonkie.

### `chonkie chunk` unexpectedly needs model dependencies

Installed help defaults `--chunker` to `semantic`. Semantic chunking may need optional dependencies and model downloads. For safe local CLI examples, override the default:

```bash
chonkie chunk "Some text." --chunker recursive --chunk-size 256
chonkie chunk "Some text." --chunker token --chunk-size 256 --chunker-params tokenizer=character
```

If the user explicitly needs semantic/late/neural/slumber behavior, route model/dependency planning to `../embeddings-and-generative/`.

### `--chunker-params` or other `*-params` did not parse as expected

Repeat the option for multiple values:

```bash
chonkie chunk text.txt --chunker recursive \
  --chunker-params recipe=markdown \
  --chunker-params min_characters_per_chunk=24
```

Parsing rules:

- `key=value` becomes a keyword argument.
- Bare `flag` becomes `flag=True`.
- `true`, `false`, `none`, and `null` are coerced.
- Numbers are converted to `int` or `float` when possible.
- Explicit flags like `--chunk-size` override the same key supplied in `--chunker-params`.

### A file path is treated as raw text, or raw text is treated as a file

`chonkie chunk` and `chonkie pipeline` check whether the text argument is an existing file path. Existing files are read as UTF-8; non-existing paths are treated as raw text. If you intended a file, verify the path exists from the current shell:

```bash
test -f notes.txt && echo ok
```

Invalid UTF-8 or read errors are reported as file-read failures.

### Unknown chunker or handshaker

Use help to inspect installed names:

```bash
chonkie chunk --help
```

Known chunker names from installed help include `code`, `fast`, `late`, `neural`, `recursive`, `semantic`, `sentence`, `slumber`, `table`, `teraflopai`, and `token`.

Known handshaker names from installed help include `chroma`, `elastic`, `lancedb`, `milvus`, `mongodb`, `pgvector`, `pinecone`, `qdrant`, `turbopuffer`, and `weaviate`. Handshakers usually require optional packages and live services; route setup to `../integrations-and-storage/`.

### `chonkie pipeline` says input is missing

One of these is required:

```bash
chonkie pipeline "raw text" --chunker recursive
chonkie pipeline notes.txt --chunker recursive
chonkie pipeline --d ./docs --ext .md --chunker recursive
```

If using `--d`, the directory must exist. Repeat `--ext` for multiple extensions.

## `chonkie serve` and local API issues

### API server dependency errors

If `chonkie serve` reports missing FastAPI/Uvicorn/API support, install the API extra:

```bash
python -m pip install "chonkie[api]"
```

If serving semantic or code endpoints, add the selected optional extras:

```bash
python -m pip install "chonkie[api,semantic,code]"
```

Provider-backed embeddings still require provider extras and keys; route to `../embeddings-and-generative/`.

### The command hangs after `Starting Chonkie API server`

That is expected: `chonkie serve` starts a long-running server. For diagnostics that should exit, use help/import/schema checks instead:

```bash
chonkie serve --help
python -c "from chonkie.api.main import app; print(app.title)"
python scripts/cli_api_smoke.py --skip-cli
```

### Port already in use

Choose another port or stop the conflicting process:

```bash
chonkie serve --host 127.0.0.1 --port 3000
```

### API docs not reachable

Check:

- Server is running and bound to the expected host/port.
- Use `http://localhost:8000/docs` when bound to `0.0.0.0:8000` locally.
- Firewalls/container port mappings expose the port.
- Reverse proxies forward to the correct backend.

Health check:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status": "ok"}
```

### Browser CORS failures

Default `CORS_ORIGINS=*` is permissive but not production-safe. For production, set explicit comma-separated origins:

```bash
CORS_ORIGINS=https://app.example.com,https://admin.example.com chonkie serve
```

If a browser still fails, confirm the exact scheme, hostname, and port match the origin value.

### Stored pipeline database problems

The default local API database is SQLite at `./data/chonkie.db` relative to the server working directory. If the server cannot create or write it:

- Set an explicit writable `DATABASE_URL`.
- Ensure the parent data directory exists or is creatable by the runtime user.
- In containers, mount a writable data volume and keep the database path inside it.

Example:

```bash
DATABASE_URL=sqlite+aiosqlite:///./data/chonkie.db chonkie serve
```

### Local API returns 422

422 is FastAPI/Pydantic validation failure. Check request JSON field names and types:

- Every chunking request needs `text` as a string or list of strings.
- Refinery requests need `chunks`, a list of chunk dicts with at least `text`, `start_index`, `end_index`, and `token_count`.
- Numeric fields such as `chunk_size` must satisfy minimum constraints.

### Local API returns 400

Common causes:

- Duplicate stored pipeline name.
- Unknown chunker/refinery name in a stored pipeline.
- A `refine` step appears before any `chunk` step.
- A step is missing its required `chunker` or `refinery` field.
- Chunk dictionaries are malformed for a refinery.

### Local API returns 500

Common causes:

- Missing optional extra for the selected route, for example semantic or code.
- Model/provider initialization failure.
- Unexpected chunker/refinery runtime exception.

Use a deterministic route to isolate server health:

```bash
curl -X POST http://localhost:8000/v1/chunk/token \
  -H "Content-Type: application/json" \
  -d '{"text":"hello world", "chunk_size": 20}'
```

If token chunking works but semantic/code/embeddings fail, route optional dependency or provider setup to the appropriate sibling sub-skill.

## Logging issues

### Too much or too little Chonkie logging

Set `CHONKIE_LOG` before import:

```bash
CHONKIE_LOG=off python your_script.py
CHONKIE_LOG=info python your_script.py
CHONKIE_LOG=debug python your_script.py
```

Accepted values include `off`, `error`, `warning`, `info`, `debug`, numeric `1` through `4`, and `unconfigured`.

### Duplicate logs under tests or host applications

Set:

```bash
CHONKIE_LOG=unconfigured
```

This prevents Chonkie from attaching its own non-propagating handler so the host logging/test framework can capture logs.

### API server log level differs from package logging

`chonkie serve --log-level debug` controls server/Uvicorn/API log level through `LOG_LEVEL`. Package logging is controlled by `CHONKIE_LOG`. Set both when you need both behaviors:

```bash
CHONKIE_LOG=debug chonkie serve --log-level debug
```

## Chonkie Cloud issues

### `No API key provided`

Chonkie Cloud wrappers require `CHONKIE_API_KEY` or an explicit `api_key` argument:

```bash
export CHONKIE_API_KEY=ck_...
```

```python
from chonkie.cloud import Pipeline
pipeline = Pipeline(slug="my-pipeline", api_key="ck_...")
```

Do not confuse this with provider keys such as `OPENAI_API_KEY`; those are for embedding/generative providers and belong to `../embeddings-and-generative/`.

### Cloud constructor fails while offline

Many cloud chunker constructors check `https://api.chonkie.ai/` during initialization and will fail when offline, blocked, or when the service is unavailable. In offline diagnostics, inspect class signatures rather than instantiating cloud clients.

### Invalid cloud pipeline slug

Cloud `Pipeline(slug=...)` accepts lowercase letters, numbers, dashes, and underscores only. Examples:

| Valid | Invalid |
| --- | --- |
| `rag_pipeline` | `RAG Pipeline` |
| `rag-pipeline-1` | `rag.pipeline` |

### Cloud `run` file/text argument errors

Cloud `Pipeline.run` and cloud chunker `.chunk` calls require exactly one of `text` or `file` where documented. Passing neither or both raises a value error before or during request construction.

### Cloud response parsing errors

If a cloud call returns invalid JSON or an unexpected shape, wrappers raise value errors. Check:

- Correct endpoint capability for the selected class.
- Input text/file shape and batch expectations.
- Credential validity and account/API availability.
- Network/proxy configuration.

Use mocked tests or dry signature inspection unless the user explicitly authorizes live cloud calls.

## Deployment and container issues

### Container starts but `/health` fails

Check:

- Port `8000` is mapped from container to host.
- The process command starts `uvicorn chonkie.api.main:app` on `0.0.0.0`.
- The image includes `chonkie[api]` dependencies.
- Logs show no database permission or import failure.

### SQLite data disappears after restart

Mount a persistent data volume and keep `DATABASE_URL` inside it. Without a persistent volume, stored API pipelines are ephemeral.

### Model-backed routes fail in a non-root container

For semantic/model-backed routes, model caches must be writable by the runtime user. Set a writable cache directory such as `HF_HOME` inside the mounted data volume, and warm up the model-backed route after deployment if cold starts matter.

### Public exposure without auth

The OSS local API has no built-in authentication. Do not expose it directly to the public internet without a trusted reverse proxy, network policy, or separate auth layer. Restrict CORS for browser clients.

## Safe first-response checklist

When asked to diagnose an interface/deployment problem:

1. Identify surface: CLI, local API server, Chonkie Cloud, logging, or container.
2. Ask whether live servers/cloud calls are allowed if the requested action would start a service or use credentials.
3. For no-network/no-credential diagnostics, run help/import/schema checks only.
4. Avoid semantic defaults until optional model/provider dependencies are confirmed.
5. Route provider, vector DB, and Python pipeline details to sibling sub-skills.
