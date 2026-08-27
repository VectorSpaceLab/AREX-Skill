# Vector Store Reference

## When to Read

Read this when configuring vector storage, debugging vector DB credentials, or
choosing the right backend for resources/knowledge.

## Enum Values

`VectorStoreType` recognizes:

- `redis`
- `pinecone`
- `chroma`
- `weaviate`
- `qdrant`
- `LanceDB`

The enum is broader than the factory coverage in this checkout; verify the
factory path before promising a backend is implemented end to end.

## Main Factory Behavior

`VectorFactory.get_vector_storage(vector_store, index_name, embedding_model)`
implements these paths:

- Pinecone: reads `PINECONE_API_KEY` and `PINECONE_ENVIRONMENT`, initializes
  Pinecone, creates the index if needed using a sample embedding dimension, and
  returns a Pinecone wrapper.
- Weaviate: reads embedded/url/api-key settings and creates a client through the
  Weaviate helper.
- Qdrant: creates a Qdrant client, creates a collection using sample embedding
  length, and returns a Qdrant wrapper.
- Redis: uses a fixed index name and creates the Redis-backed index.

`VectorEmbeddingFactory.build_vector_storage` turns chunk JSON into vector store
payload arrays and supports Pinecone, Qdrant, and Weaviate wrappers.

## Backend Requirements

| Backend | Requirements |
|---|---|
| Redis | Redis server reachable from the app configuration. |
| Pinecone | API key, environment, network, index permissions. |
| Weaviate | Embedded or remote Weaviate configuration plus optional API key. |
| Qdrant | Qdrant URL/port/api-key or local service setup depending on helper config. |
| Chroma/LanceDB | Enum support exists, but full factory support must be checked in the target checkout. |

## Common Pitfalls

- A vector DB enum value can parse successfully but still fail if the factory
  branch is absent or incomplete.
- Index dimension depends on the embedding model output length.
- Factory methods can create remote indexes/collections; ask before running live
  operations.
- A missing provider key can surface as a vector-store error when the sample
  embedding cannot be generated.
