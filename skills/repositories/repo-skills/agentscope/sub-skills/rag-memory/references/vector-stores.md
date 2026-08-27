# Vector Stores

## Purpose

Read this when the RAG or memory workflow is correct but the vector backend or embedding dimension is wrong.

## Verified vector-store families

| Store | Verified notes |
| --- | --- |
| `QdrantStore` | Supports `location`, `url`, `path`, `api_key`, `distance`, and `client_kwargs`. The local in-memory form is the easiest way to smoke-test RAG. |
| `MilvusLiteStore` | Local persistent backend; useful when you want a file-backed store instead of in-memory Qdrant. |
| `MongoDBStore` | External MongoDB vector search backend; requires a reachable deployment and `filter_fields` for metadata filters. |
| `ElasticsearchStore` | External Elasticsearch vector backend; uses dense-vector search and flattened metadata. |

## Dimension rules

- The embedding model dimension must match the vector store collection.
- The tests and demos use `DashScopeEmbeddingModel` with `text-embedding-v4` and `dimensions=1024` for the local RAG walkthrough.
- `Mem0Middleware` uses a 1536-d local Qdrant path in the OSS demo.
- `ReMeMiddleware` uses a 1024-d embedding model in the demo.

## Backend selection notes

| Need | Good choice | Why |
| --- | --- | --- |
| Fast local demo | In-memory Qdrant | No external service needed |
| Local persistence | Milvus Lite | File-backed without a server |
| Existing MongoDB stack | MongoDB | Uses the team's current datastore |
| Existing Elasticsearch stack | Elasticsearch | Good when the team already runs Elastic |

## Practical advice

- If search returns nothing or the store rejects inserts, check the embedding dimension first.
- If you are changing backends only to fix a workflow bug, read the troubleshooting page before editing code.
- Use the RAG script helpers with in-memory Qdrant before moving to an external store.
