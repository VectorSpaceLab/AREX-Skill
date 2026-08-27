# Package Overview

Kotaemon is a workspace-style Python repository for a document-QA/RAG application and reusable RAG library.

## Packages

| Distribution | Import | Role | Evidence |
| --- | --- | --- | --- |
| `kotaemon-app` | root app files | top-level application distribution depending on `kotaemon[all]` and `ktem` | root `pyproject.toml`, `app.py`, `flowsettings.py` |
| `kotaemon` | `kotaemon` | core RAG library: components, schemas, loaders, LLMs, embeddings, indexes, retrieval, ranking, QA, prompts, reasoning | `libs/kotaemon/pyproject.toml`, `libs/kotaemon/kotaemon/` |
| `ktem` | `ktem` | Gradio document-QA app framework: settings, pages, resources, file index, managers, DB models, extensions, MCP | `libs/ktem/pyproject.toml`, `libs/ktem/ktem/` |

Public package metadata in this checkout declares Python `>=3.10`. The repository documentation uses Python 3.10 examples and recommends `uv sync --python 3.10` for local checkout setup.

## Main Entry Points

| Entry point | Use | Notes |
| --- | --- | --- |
| `python app.py` | launch the Gradio document-QA app from a configured checkout | reads `flowsettings.py`, `.env`, app data dirs, and Gradio env variables |
| `kotaemon` console script | core `kotaemon.cli:main` group | includes `promptui` export/run developer utilities |
| `scripts/run_*` | release-style app startup helpers | reference-only in this skill because they can install/update/launch environments |
| `scripts/serve_local.py` | llama-cpp-python OpenAI-compatible local LLM server helper | reference-only; use model-provider/local-model guidance before running |
| `scripts/migrate/migrate_chroma_db.py` | Chroma migration helper | use the bundled app-deployment preflight before any mutating migration |

## Install Variants

| Variant | Best for | Guidance |
| --- | --- | --- |
| Docker images | end users who want the web app with fewer local dependency conflicts | choose lite/full/ollama image based on parser and local-model needs |
| `uv sync --python 3.10` | source checkout development | matches repository docs and lockfile intent |
| editable package installs | focused library/app development | install `libs/kotaemon` and `libs/ktem`; add optional extras only for selected workflows |
| optional parser/provider packages | Docling, PaddleOCR, unstructured, Mathpix, Azure Document Intelligence, GraphRAG, local model servers | install only when the task needs that integration and credentials/hardware are available |

Avoid broad extras unless required. The `kotaemon[all]` path can pull provider SDKs, document-processing packages, vector stores, and dev tools; it is useful for full application parity but slow and conflict-prone in constrained environments.

## Sub-Skill Ownership

- `app-deployment` owns launch, app configuration, data dirs, migration preflight, PDF.js, login/setup, and operation troubleshooting.
- `document-ingestion` owns loaders, parsers, splitters, and document metadata before indexing.
- `rag-core` owns programmatic pipeline composition, schema, vector retrieval, reranking, QA, prompts, and citations.
- `model-providers` owns LLM/embedding/reranking/web-search/local-model/GraphRAG provider setup and offline env validation.
- `extensions` owns custom components, index/retriever classes, settings/pages, pluggy packages, and templates.

## Optional Dependency Surfaces

| Surface | Examples | Read |
| --- | --- | --- |
| Document parsing | `unstructured`, Docling, PaddleOCR, Mathpix, Azure Document Intelligence, Adobe, OCR/VLM helpers | `sub-skills/document-ingestion/SKILL.md` |
| Vector/doc stores | ChromaDB, LanceDB, Milvus, Qdrant, Elasticsearch, in-memory stores | `sub-skills/rag-core/SKILL.md` and `sub-skills/app-deployment/SKILL.md` |
| Model providers | OpenAI, Azure OpenAI, Anthropic, Google, Mistral, Groq, Cohere, VoyageAI, Ollama, TEI, HuggingFace/FastEmbed | `sub-skills/model-providers/SKILL.md` |
| Graph RAG | MS GraphRAG, NanoGraphRAG, LightRAG | `sub-skills/model-providers/references/graphrag.md` |
| UI/extensions | Gradio, pluggy, ktem settings/pages, project templates | `sub-skills/extensions/SKILL.md` |

## Inspection Caveat

During skill creation, package metadata and top-level imports were verified in a partial read-only environment, but a full dependency install was not completed because provider/app wheels downloaded very slowly. Runtime guidance therefore relies on repository docs, source, tests, package metadata, and safe import/signature inspection, and avoids claiming provider connectivity or full app launch validation.
