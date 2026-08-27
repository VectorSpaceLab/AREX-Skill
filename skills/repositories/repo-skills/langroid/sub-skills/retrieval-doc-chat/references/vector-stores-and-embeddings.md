# Vector stores and embeddings

## Dispatch model

`VectorStore.create(config)` chooses a backend from the concrete config class.
There is no string-based routing at this layer.

## Common config fields

`VectorStoreConfig` carries the shared retrieval-store settings:

- `collection_name`
- `replace_collection`
- `storage_path`
- `cloud`
- `batch_size`
- `embedding`
- `embedding_model`
- `timeout`
- `host`
- `port`
- `document_class`
- `metadata_class`
- `full_eval`

`full_eval` defaults to `False`. Keep it that way unless the input is fully trusted.

## Embeddings

Langroid retrieves with vector search, so the embedding dimension must match the backend index.

### Common embedding configs

- `OpenAIEmbeddingsConfig`
- `SentenceTransformerEmbeddingsConfig`
- `LlamaCppServerEmbeddingsConfig` in examples and advanced setups

### DocChat defaults

`DocChatAgent` chooses an embedding default based on availability:

- if `sentence_transformers` is available, it prefers a Hugging Face sentence-transformer config
- otherwise it falls back to OpenAI embeddings

The built-in Hugging Face default is `BAAI/bge-large-en-v1.5`.
The built-in OpenAI default is `text-embedding-3-small`.

## Backend overview

| Backend | Mode | Strengths | Notes |
| --- | --- | --- | --- |
| `QdrantDBConfig` | local / cloud / docker | Default doc-chat store, hybrid options | `close()` matters for local storage locks |
| `LanceDBConfig` | local | Fast local tables and dataframe workflows | Best match for Lance RAG and FTS |
| `ChromaDBConfig` | local | Simple persistent local store | Good lightweight fallback |
| `PostgresDBConfig` | docker / cloud | SQL-backed retrieval with pgvector | Needs SQLAlchemy + pgvector and DB access |
| `WeaviateDBConfig` | embedded / local / docker / cloud | Flexible schema-backed retrieval | Cloud mode needs endpoint and key |
| `PineconeDBConfig` | cloud | Managed serverless vector store | Requires API key and valid index naming |
| `MeiliSearchConfig` | local / cloud | Lexical search and filtering | Better as a search store than a vector primary |

## Qdrant

Qdrant is the default doc-chat backend in many flows.
Useful fields include:

- `cloud`
- `docker`
- `collection_name`
- `storage_path`
- `use_sparse_embeddings`
- `sparse_embedding_model`
- `sparse_limit`
- `distance`

Local Qdrant uses a storage lock. Call `close()` or use a context manager.

## LanceDB

LanceDB is the natural backend for dataframe-heavy retrieval.
`LanceDocChatAgent` adds LanceDB full-text search and schema-aware filtering.

Good fit when you need:

- document rows with filterable fields
- FTS plus semantic retrieval
- dataframe calculations over filtered retrieval results

## Chroma

Chroma is a simple persistent local store.
It is useful when you want a lightweight backend and do not need cloud features.

## Postgres / pgvector

Use `PostgresDBConfig` when your store already lives in PostgreSQL.
Connection setup depends on whether you use Docker or a cloud connection string.

## Weaviate

Weaviate can run embedded, local, dockerized, or in cloud mode.
Cloud mode requires the API URL and API key.

## Pinecone

Pinecone is cloud-only in this sub-skill.
It requires `PINECONE_API_KEY` and a valid serverless index name.

## MeiliSearch

MeiliSearch is included for fast lexical search.
It is helpful when retrieval quality depends on exact or approximate term matching.

## Practical defaults

- start with Qdrant for general RAG
- use LanceDB when the documents behave like rows
- use Chroma for small local experiments
- use Postgres, Weaviate, or Pinecone only when the deployment already wants them
