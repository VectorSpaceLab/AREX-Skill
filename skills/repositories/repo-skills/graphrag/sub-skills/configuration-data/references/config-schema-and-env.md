# Configuration Schema and Environment

## Load Order

GraphRAG configuration is loaded with `load_config(root_dir, cli_overrides=None)`. The root can be a directory containing `settings.yaml`, `settings.yml`, or `settings.json`, or a path to one of those files. The loader:

1. Locates the settings file.
2. Loads `.env` from the settings file directory when present.
3. Expands `${VARIABLE}` placeholders using environment variables.
4. Parses YAML or JSON.
5. Recursively merges any `cli_overrides` dictionary.
6. Builds a `GraphRagConfig` Pydantic model.
7. Changes the current working directory to the config file directory, so relative paths in config are resolved from the project root.

If a placeholder such as `${GRAPHRAG_API_KEY}` is present and the variable is not defined in the environment or `.env`, loading fails before model validation with a config parsing error.

## Top-Level Sections

`GraphRagConfig` includes these high-value sections for setup checks:

- `completion_models` and `embedding_models`: model dictionaries keyed by model id.
- `input`: reader type and column mapping.
- `input_storage`, `output_storage`, and `update_output_storage`: source/output storage blocks.
- `chunking`: chunk size, overlap, encoding model, and metadata prepending.
- `cache`: cache type plus nested cache storage.
- `reporting`: status/error reporting location.
- `table_provider`: output table provider, usually parquet, csv, or Cosmos DB.
- `vector_store`: LanceDB, Azure AI Search, or Cosmos DB vector settings.
- `embed_text`, `extract_graph`, `summarize_descriptions`, `community_reports`, and query sections: model ids and prompt paths consumed later by indexing/querying.

GraphRAG validates that file-based `input_storage`, `output_storage`, `update_output_storage`, and file reporting have base directories. It resolves those directories and LanceDB `vector_store.db_uri` to absolute paths in memory. Do not copy those resolved local paths into public skill content or shared examples.

## Model Auth Rules

GraphRAG uses LiteLLM model config through `ModelConfig`. For each completion or embedding model:

- `model_provider` and `model` are required for LiteLLM-backed providers.
- `auth_method: api_key` requires a non-empty `api_key` value after environment interpolation.
- `auth_method: azure_managed_identity` must not include `api_key`.
- `model_provider: azure` requires `api_base`; `api_version` is commonly needed for Azure endpoints.
- `azure_deployment_name` is valid for Azure model providers and rejected for non-Azure providers.
- If Azure deployment name equals model name, it may be omitted in common setups, but explicit deployment names are safer for diagnosing endpoint routing.

Secret-safe examples:

```yaml
completion_models:
  default_chat_model:
    model_provider: openai
    model: gpt-4o
    auth_method: api_key
    api_key: ${GRAPHRAG_API_KEY}

embedding_models:
  default_embedding_model:
    model_provider: azure
    model: text-embedding-3-large
    azure_deployment_name: text-embedding-3-large
    api_base: ${AZURE_OPENAI_ENDPOINT}
    api_version: 2024-06-01
    auth_method: azure_managed_identity
```

For managed identity, remove `api_key` entirely rather than leaving `api_key: ${GRAPHRAG_API_KEY}` in the block.

## CLI Overrides

`load_config(root_dir, cli_overrides={...})` recursively merges dictionaries. Use the same nested shape as `settings.yaml`:

```python
from graphrag.config.load_config import load_config

config = load_config(
    "my-project",
    cli_overrides={
        "input": {"type": "jsonl", "text_column": "body"},
        "vector_store": {"type": "lancedb", "db_uri": "output/lancedb"},
    },
)
```

Overrides replace lists and scalar values. They merge nested dictionaries, so overriding one model field does not require resupplying the whole model block.

## Secret Hygiene

When summarizing or debugging config, redact keys whose names contain `key`, `secret`, `token`, `credential`, `connection_string`, or `password`. Also avoid printing full endpoint URLs if they encode tenant, account, or database names that should not be shared.

Use `scripts/inspect_config.py` when a future agent needs a quick model/provider summary without leaking secrets.
