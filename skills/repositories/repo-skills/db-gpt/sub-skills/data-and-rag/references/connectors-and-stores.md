# Connectors and stores

Use this reference to choose a structured datasource, vector store, full-text
store, or graph store without confusing a local smoke with a live integration.

## SQLite first

SQLite is the preferred CPU/local fixture because it is embedded, deterministic,
and supported by SQLAlchemy without a database service.

```python
from dbgpt_ext.datasource.rdbms.conn_sqlite import (
    SQLiteConnector,
    SQLiteConnectorParameters,
)

params = SQLiteConnectorParameters(
    path=":memory:",
    check_same_thread=False,
    driver="sqlite",
)
connector = SQLiteConnector.from_parameters(params)
# A file-backed option creates parent directories when needed:
file_connector = SQLiteConnector.from_file_path("./scratch/demo.db")
```

Verified parameter facts:

- `path` is required; a file path or `:memory:` is valid.
- `check_same_thread` defaults to `False`, allowing sharing across threads.
- `driver` defaults to `sqlite` and is reflected in `db_url()`.
- `from_file_path` uses SQLAlchemy and creates the parent directory if absent.
- `SQLiteTempConnector.create_temporary_db()` provides a temporary file and
  context-manager cleanup for package-level tests.

Safe schema checks include `get_table_names()`, `get_table_info()`,
`get_fields(table_name)`, `get_simple_fields(table_name)`, `get_indexes(table_name)`,
`get_show_create_table(table_name)`, `table_simple_info()`,
`get_table_comments()`, and `query_ex(...)`. Use parameterized SQL for values;
identifiers still need validation/quoting because several introspection helpers
construct SQL with table names.

Avoid write SQL against a user database during a smoke. Create a temporary
SQLite database and fixture tables, then close/delete it. A connector import or
empty database check does not prove that a remote dialect works.

## Other datasource families

The extension package includes connector families for common RDBMS/warehouses
such as MySQL, PostgreSQL, ClickHouse, DuckDB, Hive, MSSQL, Oracle, OceanBase,
GaussDB/openGauss, Doris, StarRocks, and Vertica, plus graph-oriented
connectors. Each has its own parameter dataclass, driver, optional dependency,
SQL dialect, authentication, and service availability. Use the corresponding
parameter class from the public package and inspect its signature in the target
environment; do not copy SQLite fields to another backend.

For every non-SQLite connector, validate in this order:

1. import the parameter class and connector module;
2. parse a redacted config without connecting;
3. verify host/port/database/user fields and TLS options;
4. perform a read-only ping or schema query only with explicit service access;
5. close the connector and record backend/version details.

Do not put passwords in a skill, command history, metadata, or error report.
Use environment/config secret interpolation owned by the setup/model/API route.

## Vector stores

The vector store contract is `IndexStoreBase`/`VectorStoreBase`: load chunks,
search similar chunks, optionally filter by metadata/score, test collection
existence, and delete/truncate an index. Choose one backend per validation case:

| Backend family | Use | Boundary |
|---|---|---|
| Chroma | Default embedded/local persistent vector store | Requires `chromadb` and an embedding function; use a disposable `persist_path` in tests. |
| Milvus | Distributed production vector service | Requires a running Milvus endpoint and matching client/extra; not CPU-local equivalent. |
| Qdrant | Remote or self-hosted vector service | Requires endpoint/client and embedding dimension agreement. |
| Weaviate | Remote vector service | Requires endpoint/client/auth depending on deployment. |
| PGVector | PostgreSQL extension-backed vector storage | Requires PostgreSQL plus extension and credentials. |
| OceanBase vector | Database-backed vector storage | Requires compatible OceanBase service/driver and dimension configuration. |
| Valkey vector | Key/value vector index | Requires Valkey service and its vector/index configuration. |
| Elasticsearch vector/full-text | Remote search service | Requires Elasticsearch client/service; do not confuse with BM25-only configuration. |

### Chroma configuration

```python
from dbgpt_ext.storage.vector_store.chroma_store import (
    ChromaStore,
    ChromaVectorConfig,
)

config = ChromaVectorConfig(
    persist_path="./scratch/chroma",
    collection_metadata={"hnsw:space": "cosine"},
)
store = ChromaStore(
    vector_store_config=config,
    name="tiny_fixture",
    embedding_fn=embeddings,
)
```

`ChromaVectorConfig` accepts `persist_path`, optional collection metadata, user,
password, `max_chunks_once_load`, and `max_threads`. `ChromaStore` requires a
config, a collection name, and `embedding_fn`; missing embeddings are a hard
configuration error. Chroma names are normalized when invalid for Chroma's
collection rules. Use a unique disposable collection and delete/truncate it
when a check finishes; persistent local state is still side effect.

Before constructing any vector store, verify the embedding function with a
probe and check its dimension against any existing collection. Dimension errors
must be rejected before `upsert`, `load_document`, collection creation, or
network access. Keep model name and dimension next to the collection identity.

## Full text/BM25

DB-GPT's `BM25Assembler` uses `ElasticsearchStoreConfig` and an Elasticsearch
client. A typical config shape is:

```toml
[rag.storage.full_text]
type = "elasticsearch"
uri = "127.0.0.1"
port = 9200
# user/password only through secret management
```

Configuration parsing is safe; assembler construction, index creation, refresh,
persistence, and retrieval are live service operations. BM25 is useful for
exact names, identifiers, and lexical matches; it does not remove the need for
chunking or metadata. The native Elasticsearch candidate is optional and should
be skipped when no service is explicitly available.

## Graph stores and graph RAG

Graph RAG is a separate optional backend. DB-GPT can build several graph views:
LLM triplets, document/paragraph structure, Markdown heading hierarchy, and
code AST structure. Retrieval can combine keyword, vector, Text2GQL, and graph
expansion depending on enabled features. Graph indexing usually requires an LLM
for entity/triplet extraction, an embedding function for similarity search, and
a graph service/store.

Supported adapters include TuGraph, Neo4j, and Memgraph-related implementations;
exact extras and config keys vary by adapter. A common configuration shape is:

```toml
[rag.storage.graph]
type = "tugraph"
host = "127.0.0.1"
port = 7687
username = "${env:GRAPH_USER}"
password = "${env:GRAPH_PASSWORD}"
```

Do not run graph setup, Docker, schema mutation, or deletion from a bundled
skill. Record graph service version, graph name, enabled graph families,
embedding/model identity, and cleanup policy when a user explicitly provisions
one. The package's in-memory graph primitives are suitable for algorithmic
unit checks but do not prove a TuGraph/Neo4j/Memgraph integration.

## Store selection matrix

- Need a local parser/chunk/schema check: stdlib fixture helper + SQLite.
- Need local semantic retrieval: Chroma + deterministic test embedding + a
  disposable path, if the Chroma extra is installed.
- Need exact lexical matching at service scale: Elasticsearch BM25.
- Need schema-aware table/field retrieval: SQLite or another connector +
  `DBSchemaAssembler` + table/field vector stores.
- Need entity/relationship traversal: graph store with explicit LLM,
  embeddings, graph service, and cleanup approval.

In every case, report whether the operation was import-only, local persistent,
or connected to an external service.
