---
name: configuration-data
description: "Initialize, inspect, and troubleshoot GraphRAG settings,
  environment interpolation, auth, input readers, storage/cache/table providers,
  vector stores, and offline data readiness before indexing or querying."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# GraphRAG Configuration and Data

Use this sub-skill when a task mentions `settings.yaml`, `.env`, `GraphRagConfig`, Azure/OpenAI auth, LiteLLM model settings, input file schemas, `input_storage`, `output_storage`, `cache`, `table_provider`, `vector_store`, LanceDB, Azure AI Search, Cosmos DB, or safe checks before running an index.

## Route Boundaries

- Stay here for initialization, config loading, schema validation, provider selection, secret-safe summaries, and offline input reader checks.
- Route full index execution, update runs, workflow selection, and interpreting `PipelineRunResult` outputs to `../indexing/`.
- Route completed-index DataFrame loading and search calls to `../querying/`.
- Route prompt generation and `graphrag prompt-tune` usage to `../prompt-tuning/`.
- Route custom reader/provider implementation, factory registration, and package-extension design to `../package-extensions/`.

## Fast Workflow

1. Create or locate a project root containing `settings.yaml`, `settings.yml`, or `settings.json`; `graphrag init --root <project>` generates the default `settings.yaml` and `.env` skeleton.
2. Fill `completion_models` and `embedding_models` with LiteLLM-compatible `model_provider`, `model`, `auth_method`, and either `api_key` or Azure managed identity fields.
3. Set `input.type` and reader columns, then match `input_storage.type` and `input_storage.base_dir` or remote storage settings to the data source.
4. Choose local or remote `output_storage`, `cache.storage`, `table_provider`, and `vector_store` providers before indexing.
5. Validate without network calls:
   ```bash
   python scripts/inspect_config.py --root <project>
   python scripts/smoke_input_readers.py
   ```
6. If config and readers pass, continue with indexing in `../indexing/`; do not run indexing just to validate settings.

## Key APIs and Commands

- `from graphrag.config.load_config import load_config` loads `settings.[yaml|yml|json]` from a root and returns `GraphRagConfig`.
- `load_config(root_dir, cli_overrides={...})` recursively overlays CLI-style nested dictionaries before Pydantic validation.
- `GraphRagConfig` validates file base directories, resolves file paths, expands LanceDB `db_uri`, and overlays default vector schemas for GraphRAG embeddings.
- `graphrag init --root <project>` writes default config content with `${GRAPHRAG_API_KEY}` interpolation and common prompt file paths.
- `graphrag index --root <project>` belongs to `../indexing/` after this sub-skill has checked prerequisites.

## Provider Matrix

- Inputs: `text`, `csv`, `json`, `jsonl`, `markitdown`, and `parquet` through `graphrag_input.create_input_reader`.
- Storage: `file`, `memory`, `blob`, and `cosmosdb` via `StorageConfig`, depending on the section using it.
- Cache: `json`, `memory`, and `none`; JSON cache uses a nested `storage` block.
- Tables: `parquet`, `csv`, and `cosmosdb` through `table_provider.type`.
- Vectors: `lancedb`, `azure_ai_search`, and `cosmosdb` through `vector_store.type`.

## References

- See `references/config-schema-and-env.md` for `GraphRagConfig`, model auth, `.env`, and validation behavior.
- See `references/input-storage-cache-vector.md` for reader schemas and storage/cache/table/vector provider settings.
- See `references/troubleshooting.md` for common validation failures and doc/code drift traps.

## Bundled Offline Checks

- `scripts/inspect_config.py` loads a project config and prints a JSON summary with secret-like values redacted.
- `scripts/smoke_input_readers.py` creates tiny temporary `text`, `csv`, `json`, `jsonl`, and optional `parquet` inputs and reports local reader readiness without credentials or network access.
