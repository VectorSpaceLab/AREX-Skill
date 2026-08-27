# Database Backends

| `database_type` | Vector DB | Connection env var | Optional dependency | Notes |
|---|---:|---|---|---|
| `postgres` | no | `DEEPFACE_POSTGRES_URI` | `psycopg[binary]` | Stores arrays in SQL tables; ANN needs FAISS and `build_index`. |
| `mongo` | no | `DEEPFACE_MONGO_URI` | `pymongo` | Document-store backend; ANN needs FAISS and stored index. |
| `weaviate` | yes | `DEEPFACE_WEAVIATE_URI` | `weaviate-client` | Requires running or hosted Weaviate. |
| `neo4j` | yes | `DEEPFACE_NEO4J_URI` | `neo4j` | Requires Neo4j vector index support and Graph Data Science plugin according to client checks. |
| `pgvector` | yes | `DEEPFACE_POSTGRES_URI` | `psycopg[binary]`, `pgvector` | Requires PostgreSQL with the `vector` extension enabled. |
| `pinecone` | yes | `DEEPFACE_PINECONE_API_KEY` | `pinecone` | Hosted vector service. |
| `milvus` | yes | `DEEPFACE_MILVUS_URI` | `pymilvus` | Requires a running Milvus endpoint. |

The API layer also reads `DEEPFACE_DATABASE_TYPE` and `DEEPFACE_CONNECTION_DETAILS`. `DEEPFACE_CONNECTION_DETAILS` can override the backend-specific env var in API mode.

Python calls can pass a string URI, backend-specific dict where supported, or an existing `connection=` object managed by the application.
