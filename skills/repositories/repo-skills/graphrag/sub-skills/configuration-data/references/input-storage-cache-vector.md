# Input, Storage, Cache, Table, and Vector Configuration

## Input Readers

`input.type` is dispatched by `graphrag_input.create_input_reader(InputConfig, storage)`. Current built-in types are:

- `text`: reads text files; default pattern matches text-style inputs.
- `csv`: reads rows with Python CSV parsing; each row becomes a document.
- `json`: reads one object or an array of objects per file.
- `jsonl`: reads one JSON object per line.
- `markitdown`: uses MarkItDown to convert supported file types such as HTML, Office, and PDF formats; some formats require optional dependencies.
- `parquet`: reads parquet rows; requires parquet-capable dependencies such as `pyarrow`.

The older input docs may say only text/csv/json are supported or that JSONL is unsupported. Prefer the package code and tests when they disagree: `InputType` includes `jsonl`, `markitdown`, and `parquet`.

## Structured Reader Columns

CSV, JSON, JSONL, and parquet share structured-file behavior:

```yaml
input:
  type: jsonl
  file_pattern: .*\.jsonl$
  id_column: id
  title_column: metadata.title
  text_column: body
```

- `text_column` defaults to `text`; it can be a dot path into nested dictionaries, such as `payload.body`.
- `id_column` is optional; without it, GraphRAG hashes the text into an id.
- `title_column` is optional; without it, GraphRAG uses the filename plus row number.
- Dot-path lookup only traverses dictionaries. It does not flatten arrays or parse JSON strings stored inside a cell.
- Nested columns from parquet or CSV may need preprocessing if they arrive as stringified JSON or list-valued cells.

## Storage Blocks

GraphRAG uses `StorageConfig` in multiple places. Common fields are:

```yaml
input_storage:
  type: file
  base_dir: input

output_storage:
  type: file
  base_dir: output

update_output_storage:
  type: file
  base_dir: update_output
```

Supported storage types include `file`, `memory`, `blob`, and `cosmosdb`, depending on the section and factory path. Remote providers typically require `connection_string` or `account_url`, `container_name`, and for Cosmos DB, `database_name`.

Use file storage for offline validation and local development. Use `blob` or `cosmosdb` only when credentials and network access are intentionally available.

## Cache Configuration

Cache config uses a cache type plus optional nested storage:

```yaml
cache:
  type: json
  storage:
    type: file
    base_dir: cache
```

- `json` stores cache entries through the nested `storage` provider.
- `memory` is process-local and useful for tests or one-off runs.
- `none` disables cache persistence.
- For remote JSON cache, make the nested storage settings complete; missing container/database fields fail later when the provider is created.

## Table Provider

`table_provider.type` controls indexed table persistence, separately from the raw storage blocks:

```yaml
table_provider:
  type: parquet
```

Built-ins include:

- `parquet`: default table output for GraphRAG artifacts.
- `csv`: table output as CSV files.
- `cosmosdb`: Cosmos DB table provider; use with appropriate Cosmos storage settings and container naming.

Route questions about consuming completed tables for query APIs to `../querying/`.

## Vector Store

`vector_store.type` controls embedding/vector persistence:

```yaml
vector_store:
  type: lancedb
  db_uri: output/lancedb
  vector_size: 3072
```

Built-ins are:

- `lancedb`: local LanceDB; `db_uri` is resolved from the project config directory if relative.
- `azure_ai_search`: remote Azure AI Search; uses `url`, optional `api_key`, optional `audience`, and generated or explicit index schema.
- `cosmosdb`: remote Cosmos DB vector store; uses `connection_string`, `database_name`, and related service settings.

GraphRAG ensures a schema exists for each core embedding. `IndexSchema` fields include `index_name`, `id_field`, `vector_field`, `vector_size`, and a typed `fields` mapping. Field names for id/vector must be safe identifiers matching `^[A-Za-z_][A-Za-z0-9_]*$`, which matters for Cosmos DB and search-index compatibility.

Example explicit schema:

```yaml
vector_store:
  type: azure_ai_search
  url: ${AZURE_AI_SEARCH_ENDPOINT}
  api_key: ${AZURE_AI_SEARCH_API_KEY}
  vector_size: 3072
  index_schema:
    text_unit_text:
      index_name: text_unit_text
      id_field: id
      vector_field: vector
      vector_size: 3072
      fields:
        title: str
        community: int
```

## Offline Readiness Checks

Use `scripts/smoke_input_readers.py` before indexing when the task is only to confirm local readers. It writes tiny files in a temporary directory, instantiates built-in readers against file storage, and reports whether each reader can be created and invoked without credentials. It skips parquet if pandas/pyarrow support is unavailable.
