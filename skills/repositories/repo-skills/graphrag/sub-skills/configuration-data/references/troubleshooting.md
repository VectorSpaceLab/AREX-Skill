# Configuration and Data Troubleshooting

## `.env` Interpolation Fails

Symptom: loading config raises `Environment variable not found: 'NAME'`.

Checks:

- Confirm the placeholder uses `${NAME}` syntax, not shell-only forms.
- Put `.env` beside `settings.yaml`, or export the variable before loading config.
- If a value is optional for the selected auth/provider mode, remove the placeholder instead of leaving an unresolved `${...}`.
- Remember that parsing happens before Pydantic validation, so even an unused placeholder can fail loading.

## Missing API Key

Symptom: model validation says `api_key must be set when auth_method=api_key.`

Checks:

- For OpenAI-style API key auth, set `api_key: ${GRAPHRAG_API_KEY}` and define `GRAPHRAG_API_KEY`.
- Ensure `.env` is loaded from the config directory, not from the shell's current directory.
- If using Azure managed identity, switch `auth_method` and remove `api_key` from that model block.

## Azure Managed Identity Conflicts with API Key

Symptom: validation says `api_key should not be set when using Azure Managed Identity.`

Fix:

```yaml
completion_models:
  default_chat_model:
    model_provider: azure
    model: gpt-4o
    azure_deployment_name: gpt-4o
    api_base: ${AZURE_OPENAI_ENDPOINT}
    api_version: 2024-06-01
    auth_method: azure_managed_identity
```

Do not keep `api_key: null`, `api_key: ""`, or `api_key: ${GRAPHRAG_API_KEY}` unless testing confirms the exact Pydantic behavior for that release. The safe pattern is to omit the key.

## `azure_deployment_name` on Non-Azure Provider

Symptom: validation says `azure_deployment_name should not be specified for non-Azure model providers.`

Fix:

- For `model_provider: openai`, remove `azure_deployment_name`, `api_base`, and Azure-specific fields.
- For Azure OpenAI, set `model_provider: azure`, provide `api_base`, and keep `azure_deployment_name` if the deployment name differs or needs to be explicit.

## Azure Provider Missing Endpoint

Symptom: validation says `api_base must be specified with the 'azure' model provider.`

Fix:

- Set `api_base` to the Azure OpenAI endpoint value.
- Keep the endpoint in `.env` if it should not be committed.
- Pair it with `api_version` expected by the deployed model and LiteLLM provider.

## Nested Structured Columns Fail

Symptom: CSV/JSON/JSONL/parquet input fails with `Property '...' not found` or documents have empty/wrong text.

Checks:

- `text_column`, `id_column`, and `title_column` can use dot paths such as `metadata.title` only through nested dictionaries.
- Arrays, stringified JSON, and parquet object cells are not flattened automatically.
- For CSV, nested values are usually strings; preprocess them into flat columns before indexing.
- For parquet, confirm the loaded row objects preserve dictionaries where dot paths expect dictionaries.
- Always set `text_column` explicitly when the source field is not named `text`.

## Optional Reader Dependencies Missing

Symptoms: MarkItDown or parquet reader creation/import fails.

Checks:

- `markitdown` support depends on the MarkItDown package and optional extras for formats such as PDFs or Office documents.
- `parquet` support depends on pandas plus a parquet engine such as `pyarrow`.
- Use `scripts/smoke_input_readers.py` to distinguish core reader readiness from optional dependency gaps.
- If optional dependencies are unavailable, convert inputs to `text`, `csv`, `json`, or `jsonl` before indexing.

## LanceDB URI or Schema Problems

Symptoms: LanceDB path errors, unexpected database location, or vector schema validation failures.

Checks:

- `vector_store.type: lancedb` uses `db_uri`; if relative, GraphRAG resolves it from the config directory.
- Ensure the process can create/write the `db_uri` directory.
- Do not set unsafe `id_field` or `vector_field` names; they must start with a letter or underscore and contain only letters, digits, and underscores.
- Match `vector_size` to the embedding model output dimension. Defaults are not guaranteed to match custom embedding models.

## Azure AI Search Vector Issues

Symptoms: authentication errors, index creation failures, or field incompatibilities.

Checks:

- Use `url` for the search endpoint.
- Provide `api_key` for key auth or configure identity/audience when using token auth.
- Keep index names and schema fields valid for Azure AI Search.
- Avoid changing schema for an existing index without planning migration or recreation.

## Cosmos DB Storage/Table/Vector Issues

Symptoms: missing container/database errors, partition/batch errors, or local emulator-specific failures.

Checks:

- Cosmos-backed storage needs service settings such as `connection_string` or `account_url`, `container_name`, and `database_name` where applicable.
- `table_provider.type: cosmosdb` is separate from `output_storage.type`; make both sides explicit when writing tables to Cosmos.
- Batch-oriented table writes have provider limits; reduce `table_provider.batch_size` if batch validation fails.
- Local Cosmos emulator availability is platform-dependent; do not assume it exists for runtime checks.

## Docs Drift Around JSONL, Parquet, and MarkItDown

Symptom: docs say only `text`, `csv`, or `json` are supported, or that JSONL is unsupported.

Resolution:

- Trust the package code for GraphRAG 3.1.0 behavior: `InputType` includes `csv`, `text`, `json`, `jsonl`, `markitdown`, and `parquet`.
- Mention doc drift in review notes when verifying a generated skill.
- Prefer smoke checks against installed package imports when deciding what a future agent can safely use.

## Avoid Secret Leakage

When debugging config:

- Redact `api_key`, `connection_string`, `token`, `credential`, `password`, and similar keys.
- Do not print full `.env` content.
- Prefer `scripts/inspect_config.py`, which emits a redacted JSON summary.
