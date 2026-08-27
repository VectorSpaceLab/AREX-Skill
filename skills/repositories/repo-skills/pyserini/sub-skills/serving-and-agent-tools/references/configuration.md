# Server Configuration

Pyserini REST and MCP servers share `SharedSearchBackend`, so `--config` YAML index aliases resolve the same way for both servers. The config is safe to validate before startup because the parser checks paths, types, API-key shape, and alias relationships without starting a server.

## YAML Shape

Top-level config must be a mapping. Both keys are optional, but `--no-prebuilt-indexes` requires a non-empty `indexes` mapping.

```yaml
indexes:
  sparse_alias: ./indexes/sparse-lucene
  dense_alias:
    path: ./indexes/dense-faiss
    index_type: faiss
    base_index: sparse_alias
    encoder: BAAI/bge-base-en-v1.5
  hnsw_alias:
    path: ./indexes/lucene-hnsw
    index_type: lucene_hnsw
    base_index: sparse_alias
    encoder: BAAI/bge-base-en-v1.5
    ef_search: 100
api_keys:
  - replace-with-a-high-entropy-secret
```

## Index Aliases

Each `indexes` key is a non-empty alias. The alias is what REST paths and MCP tools should use instead of a filesystem path.

| Form | Meaning |
| --- | --- |
| `alias: ./path/to/index` | Short form for a sparse Lucene TF index. Equivalent to `index_type: tf`. |
| `alias: {path: ./index, index_type: tf}` | Explicit sparse Lucene alias. |
| `alias: {path: ./dense, index_type: faiss, encoder: ..., base_index: sparse}` | Dense/Faiss/impact alias with its stored-document sparse base. |

Valid `index_type` values are:

- `tf` for sparse Lucene indexes opened by `LuceneSearcher`.
- `impact` for Lucene impact indexes.
- `lucene_flat` for Lucene flat dense indexes.
- `lucene_hnsw` for Lucene HNSW dense indexes.
- `faiss` for Faiss dense indexes.

Rules enforced by Pyserini config loading:

- `path` must be non-empty and point to an existing directory; relative paths resolve relative to the YAML file.
- `impact`, `faiss`, `lucene_flat`, and `lucene_hnsw` require a non-empty `encoder`.
- `ef_search`, when present, must be a positive integer.
- `base_index`, when present, must name another configured alias.
- A `base_index` target must be a `tf` alias, because document retrieval for dense/impact/Faiss search needs a sparse Lucene index with stored documents.

## API Keys and Auth

`api_keys` must be a list of non-empty strings. If present, REST protects all `/v1/*` routes. Clients can send either header:

```bash
-H "Authorization: Bearer replace-with-a-high-entropy-secret"
-H "X-API-Key: replace-with-a-high-entropy-secret"
```

MCP uses the same index config but does not use the REST API-key middleware for stdio tool calls.

## Startup Flags

REST server:

```bash
python -m pyserini.server.rest --host 127.0.0.1 --port 8081 --config server.yaml
```

Common REST flags:

| Flag | Default | Use |
| --- | --- | --- |
| `--host` | `0.0.0.0` | Bind address. Prefer `127.0.0.1` for local-only use. |
| `--port` | `8081` | HTTP port. |
| `--config` | none | YAML aliases and API keys. |
| `--no-prebuilt-indexes` | false | Accept only aliases from `--config`; disables arbitrary local paths and prebuilt names. |
| `--load-shedding-threshold` | `3000` ms | With API keys, shed busiest keys when rolling p99 latency exceeds this threshold. |
| `--search-cache-size` | `2048` | LRU size for string-query search results. |
| `--document-cache-size` | `4096` | LRU size for document fetches. |
| `--server-log-file` | none | Write uvicorn error/access logs to a file. |
| `--auth-log-file` | stderr | Write auth attribution logs with key fingerprints. |
| `--no-access-log` | false | Disable uvicorn access logs. |

MCP server:

```bash
python -m pyserini.server.mcp --config server.yaml
python -m pyserini.server.mcp --transport http --port 8000 --config server.yaml
```

MCP flags:

| Flag | Default | Use |
| --- | --- | --- |
| `--transport` | `stdio` | `stdio` for local client-managed processes, `http` for remote/forwarded access. |
| `--port` | `8000` | HTTP transport port. |
| `--config` | none | Same server YAML aliases as REST. |

## Safe Validation

Use the bundled validator before server startup:

```bash
python scripts/validate_server_config.py server.yaml
python scripts/validate_server_config.py server.yaml --json
```

The validator reports alias names, resolved path existence, index types, `base_index` relationships, `encoder` requirements, API-key count, and whether `--no-prebuilt-indexes` would be valid. It does not open indexes, load Java, start FastAPI, run MCP, or download prebuilt indexes.
