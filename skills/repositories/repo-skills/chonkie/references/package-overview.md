# Chonkie package overview

## Purpose

Read this to orient a future agent to Chonkie's public package surface, install extras, and safe operating boundaries before loading a focused sub-skill.

## Verified baseline

This skill was produced for Chonkie distribution `chonkie` version `1.7.0`, import root `chonkie`, Python `>=3.10`, and console script `chonkie`.

The minimum verified environment covered:

- Base dependencies: `tqdm`, `numpy`, `chonkie-core`, `tenacity`, `httpx`, `tokie`.
- Selected local extras: `cli`, `api`, `table`, and `code`.
- Safe checks: package metadata/import, deterministic chunkers, pipeline smoke, CLI help, FastAPI app/schema import, table/code tiny smokes, optional-dependency probes.

The skill did **not** verify live cloud/provider calls, vector datastore writes, model downloads, model caches, external services, or accelerator backends.

## Public surfaces by task

| Task | Primary route | Key APIs / commands | Boundary |
| --- | --- | --- | --- |
| Local text chunking | `sub-skills/chunking-and-types/` | `TokenChunker`, `SentenceChunker`, `RecursiveChunker`, `FastChunker` | Deterministic and CPU-local by default. |
| Code/table chunking | `sub-skills/chunking-and-types/` | `CodeChunker`, `TableChunker`, `TableChef` | Needs `code` or `table` extras for full use. |
| Semantic/model chunking | `sub-skills/embeddings-and-generative/` plus chunking route | `SemanticChunker`, `LateChunker`, `NeuralChunker`, `SlumberChunker`, `TeraflopAIChunker` | Optional dependencies, model downloads, provider APIs, or credentials may be required. |
| Document pipelines | `sub-skills/pipelines-and-processing/` | `Pipeline().fetch_from().process_with().chunk_with().refine_with().run()` | Use deterministic pipeline first; add optional refineries/exporters deliberately. |
| File/text processing | `sub-skills/pipelines-and-processing/` | `TextChef`, `MarkdownChef`, `TableChef`, `LiteParse`, `MistralOCR`, `FileFetcher` | OCR/provider parsers need optional extras and possibly credentials. |
| Embeddings/refinement | `sub-skills/embeddings-and-generative/` | `AutoEmbeddings`, provider embeddings, `EmbeddingsRefinery` | Distinguish local models from third-party API providers. |
| CLI use | `sub-skills/interfaces-and-deployment/` | `chonkie chunk`, `chonkie pipeline`, `chonkie serve` | The CLI's default chunker may be semantic; choose deterministic flags for no-network runs. |
| Local API server | `sub-skills/interfaces-and-deployment/` | `chonkie serve`, `chonkie.api.main:app`, Pydantic request schemas | Treat server startup as long-running; smoke with imports/schema inspection first. |
| Chonkie Cloud | `sub-skills/interfaces-and-deployment/` | `chonkie.cloud.Pipeline`, cloud chunkers/refineries/file manager | Requires `CHONKIE_API_KEY` or explicit `api_key`; do not confuse with provider keys. |
| JSON/datasets export | `sub-skills/integrations-and-storage/` | `JSONPorter`, `DatasetsPorter`, `Pipeline.export_with(...)` | JSON is base/offline; `datasets` extra for Hugging Face Dataset workflows. |
| Vector/datastore handshakes | `sub-skills/integrations-and-storage/` | Chroma, Qdrant, LanceDB, Milvus, MongoDB, Pgvector, Pinecone, Turbopuffer, Weaviate, Elastic handshakes | Optional client packages and live services/credentials; no writes without explicit scope. |

## Install extras matrix

Use extras only for the requested capability. Avoid `all` and `dev` unless the user specifically asks for a broad development environment.

| Extra | Enables | Notes |
| --- | --- | --- |
| `cli` | Typer CLI | Needed for the `chonkie` console command. |
| `api` | FastAPI local API, Uvicorn, SQLAlchemy, schema validation | Needed for `chonkie serve` and API-route imports. |
| `table` | table parsing/conversion dependencies | Includes pandas/tabulate/openpyxl/lxml-style table support. |
| `code` | tree-sitter language pack | Needed for robust `CodeChunker`; first grammar setup can be expensive. |
| `semantic`, `model2vec` | local model2vec semantic chunking | May require model downloads/cache. |
| `st` | sentence-transformer embeddings/late chunking | Pulls sentence-transformers/accelerate and often torch. |
| `neural` | neural chunker | Pulls transformers/torch and model weights. |
| `openai`, `azure-openai`, `gemini`, `jina`, `cohere`, `voyageai`, `litellm`, `catsu` | provider embeddings | Require provider SDKs and API credentials. |
| `genie`, `genies`, `groq`, `cerebras` | LLM/genie wrappers | Require provider SDKs, credentials, and live API authorization. |
| `mistral`, `liteparse` | OCR/document parsing chefs | May require credentials, server URLs, or native/parser dependencies. |
| `datasets` | Hugging Face Dataset export | Offline dataset creation is possible; hub upload remains a separate network task. |
| datastore extras such as `chroma`, `qdrant`, `lancedb`, `milvus`, `mongodb`, `pgvector`, `pinecone`, `tpuf`, `weaviate`, `elastic` | vector/datastore handshakes | Client package installation is not permission to write to a live service. |

## Data and object contracts

- Most chunkers return a list of `Chunk`-like objects with `text`, `start_index`, `end_index`, and `token_count`.
- Pipeline `run(texts="...")` returns one `Document`; `run(texts=[...])` or directory fetch returns `list[Document]`.
- Markdown processing can preserve modality-specific structures such as code blocks, tables, and images.
- Refineries and handshakes generally consume existing chunks; create/validate chunks before storing or exporting.

## Operating rules

- Prefer source-backed/public APIs and verified signatures. If an API is optional, test imports before constructing it.
- Use bundled scripts for diagnostics rather than original source tests or docs.
- Do not leak local environment paths, API keys, or service credentials into prompts or outputs.
- For live external calls or writes, require explicit user-provided resources and scope.
