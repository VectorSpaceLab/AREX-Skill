# Install and Extras

## When to read

Read this before installing Langroid, choosing optional extras, or debugging an
import that says a feature needs a specific extra.

## Python and base install

Langroid `0.65.16` declares Python `>=3.10,<3.14`.

Common installs:

```bash
pip install langroid
pip install -e .
pip install -e ".[dev]"
```

Use editable install only when working inside a Langroid checkout. For ordinary
package use, prefer the PyPI install.

Minimal import check:

```bash
python - <<'PY'
import langroid as lr
import langroid.language_models as lm
print(lr.ChatAgent, lr.Task, lr.ToolMessage)
print(lm.OpenAIGPTConfig().chat_model)
PY
```

The bundled root helper performs the same style of no-network checks:

```bash
python scripts/check_langroid_environment.py --json
```

## Public optional extras

Install the smallest extra set needed for the workflow:

| Need | Suggested extra(s) | Notes |
| --- | --- | --- |
| Document chat with PDF/DOCX/OCR parser choices | `doc-chat`, `pdf-parsers`, `docx`, `markitdown`, `marker-pdf`, `docling`, `pymupdf4llm` | Parser extras can pull native tools, OCR binaries, or model downloads. |
| HuggingFace or transformer embeddings | `hf-embeddings`, `hf-transformers`, `transformers` | May install Torch and download models. Verify CPU/GPU availability separately. |
| Vector stores beyond base Qdrant support | `vecdbs`, `lancedb`, `chromadb`, `weaviate`, `pinecone`, `postgres`, `meilisearch`, `fastembed` | Some backends need services, credentials, or persistent storage. |
| SQL agents | `sql`, `postgres`, `mysql` | PostgreSQL source builds may need `pg_config`; `psycopg2-binary` can be easier for local inspection. |
| Graph agents | `neo4j`, `arango` | A running database service is still required for live graph Q&A. |
| Provider/gateway extras | `litellm`, `google-genai`, `tavily`, `exa`, `seltz` | Many provider packages are base dependencies; live calls still need keys. |
| Chainlit UI | `chainlit` | Starts an interactive web app; do not use as a unit-test smoke by default. |
| Local document crawling | `crawl4ai`, `scrapy`, `firecrawl` | Browser crawling or remote services can require extra binaries or credentials. |

Avoid `all` unless the task explicitly requires broad optional coverage. The
`all` extra is convenient for demos but much larger than most focused workflows.

## No console entry points

The package metadata does not define a top-level `langroid` console script.
Most runnable workflows are Python scripts or direct API usage through package
classes. Use the sub-skill scripts for no-network smoke checks.

## Development checks

For repository maintenance, common commands are:

```bash
pip install -e ".[dev]"
make check
make lint
make type-check
pytest <focused-test-selection>
```

These are maintainer checks, not required for using the package in an agent app.
