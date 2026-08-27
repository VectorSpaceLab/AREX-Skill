# Datastore Search Troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `Unsupported database type` | `database_type` or `DEEPFACE_DATABASE_TYPE` is not in the inventory. | Use one of `postgres`, `mongo`, `weaviate`, `neo4j`, `pgvector`, `pinecone`, `milvus`. |
| Optional dependency error | Backend client package is missing. | Install only the selected backend client; do not install all clients by default. |
| `connection information not found` | No `connection_details`, `connection`, or expected env var is set. | Provide explicit `connection_details` or set the backend env var. |
| `No embeddings found in the database for the criteria` | Search parameters do not match registered embeddings, or no data registered. | Register identities with the same `model_name`, `detector_backend`, `align`, and `l2_normalize`. |
| Duplicate registration | Same face/embedding hash already exists. | Treat zero inserted as idempotent if appropriate. |
| `faiss is not installed` | Non-vector backend ANN requires FAISS. | Install FAISS or use `search_method="exact"`. |
| pgvector/Neo4j extension or permission error | Service lacks required extension/plugin/privileges. | Ask an administrator to enable prerequisites or choose another backend. |
