# Package Overview

## What R2R is

R2R is a Retrieval-Augmented Generation system with:

- a Python package named `r2r`
- a JavaScript package named `r2r-js`
- an R2R server entry point exposed through `r2r.serve`
- document ingestion, retrieval/RAG, graph, collection, conversation, user, prompt, index, and system APIs

## Public Python surface

- `from r2r import R2RClient, R2RAsyncClient, get_version`
- `R2RClient(base_url: str | None = None, timeout: float = 300.0, custom_client=None)`
- `R2RAsyncClient(base_url: str | None = None, timeout: float = 300.0, custom_client=None)`
- `R2RResults.results` wraps the typed result
- `PaginatedR2RResult.results` and `PaginatedR2RResult.total_entries` expose paged data

## Public server surface

- `r2r.serve.create_app(config_name=None, config_path=None, full=False)`
- `r2r.serve.run_server(host=None, port=None, config_name=None, config_path=None, full=False)`
- `r2r.serve.main()`

## Main client groups

- `system` — health, status, settings
- `users` — login, refresh, API keys, profile, collections, verification
- `documents` — ingest, retrieve, list, download, export, metadata, filters, extraction
- `chunks` — chunk retrieval, search, update, list-by-document
- `collections` — create, list, add/remove users or documents, extract
- `retrieval` — search, rag, agent, completion, embedding
- `graphs` — build, pull, reset, entity, relationship, community operations
- `prompts` — create, retrieve, update, delete, list
- `indices` — create, list, retrieve, delete
- `conversations` — conversation and message lifecycle plus export

## How to choose a sub-skill

- User wants to call the Python SDK directly: go to `sub-skills/python-sdk/`.
- User wants to ingest documents, transform metadata, or validate filters: go to `sub-skills/ingestion-documents/`.
- User wants search, RAG, streaming citations, or agent/research flows: go to `sub-skills/retrieval-rag/`.
- User wants graph extraction or graph CRUD: go to `sub-skills/graph-workflows/`.
- User wants server install/config/Docker/provider troubleshooting: go to `sub-skills/server-configuration/`.
- User wants the JavaScript client or browser/Node differences: go to `sub-skills/javascript-sdk/`.

## Common conventions

- `R2R_API_BASE` sets the client base URL when not passed directly.
- `R2R_API_KEY` supplies API-key auth for the Python client.
- If both an access token and API key are set, the Python client raises an error.
- `x-project-name` is used when a project name is set on the client.
