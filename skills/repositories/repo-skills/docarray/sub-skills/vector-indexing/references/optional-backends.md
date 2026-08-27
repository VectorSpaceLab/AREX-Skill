# Optional vector backends

These integrations are public DocArray capabilities, but they were not service-verified in the selected minimum CPU environment. Read this table before installing or launching a service.

| Class | Import trigger | Extra/dependency | Runtime prerequisite | Selection notes |
| --- | --- | --- | --- | --- |
| `HnswDocumentIndex` | `from docarray.index import HnswDocumentIndex` | `docarray[hnswlib]` | Local compiled `hnswlib`; writable `work_dir` | Local ANN with SQLite for non-vector fields; useful for small/medium local datasets. |
| `QdrantDocumentIndex` | `from docarray.index import QdrantDocumentIndex` | `docarray[qdrant]` | Qdrant local/in-memory/cloud endpoint; API key for cloud | Supports vector, filter, text, and hybrid operations according to Qdrant query types. |
| `WeaviateDocumentIndex` | `from docarray.index import WeaviateDocumentIndex` | `docarray[weaviate]` | Weaviate endpoint, embedded runtime, or service; auth as configured | A vector field generally needs backend-specific `Field(is_embedding=True)` configuration. |
| `ElasticDocIndex` | `from docarray.index import ElasticDocIndex` | `docarray[elasticsearch]` plus Elastic v8-compatible client | Elasticsearch v8 service and connection config | Native ANN support in documented v8 path; uses Elasticsearch Query DSL for filters. |
| `ElasticV7DocIndex` | `from docarray.index import ElasticV7DocIndex` | `docarray[elasticsearch]` with v7-compatible client constraints | Elasticsearch 7.10 service | Stores vectors but does not provide native ANN in the documented v7 path. |
| `RedisDocumentIndex` | `from docarray.index import RedisDocumentIndex` | `docarray[redis]` | Redis Stack/RediSearch service | Requires Redis vector/text query syntax and service configuration. |
| `MilvusDocumentIndex` | `from docarray.index import MilvusDocumentIndex` | `docarray[milvus]` | Milvus service, often containerized | Vector fields commonly use `Field(is_embedding=True)` and Milvus index/metric config. |
| `MongoDBAtlasDocumentIndex` | `from docarray.index import MongoDBAtlasDocumentIndex` | `docarray[mongo]` | MongoDB Atlas cluster, credentials, vector-search setup | Requires Atlas connection and server-side vector index configuration. |
| `EpsillaDocumentIndex` | `from docarray.index import EpsillaDocumentIndex` | `docarray[epsilla]` | Epsilla client/service as documented by the installed version | Verify client API and service availability before use. |

## Common selection process

1. Define the schema and dimensions in a backend-neutral `BaseDoc` first.
2. Prototype `index`, `find`, and `filter` with `InMemoryExactNNIndex`.
3. Install only the chosen backend extra.
4. Prepare the actual service and credentials separately; DocArray does not generally start a database for you.
5. Run a tiny index/find/filter smoke against a disposable collection/index name.
6. Compare backend query-builder support before relying on text or hybrid search.
7. Record the backend, client, service, schema, index name, and metric configuration for reproducibility.

## Important backend differences

- HNSWLib is local and approximate; its `space="cosine"` represents cosine distance, unlike the in-memory backend's default cosine similarity terminology.
- Qdrant, Redis, Elasticsearch, Weaviate, and Milvus have backend-specific filter query objects or strings. Do not reuse the in-memory `{"field": {"$lte": value}}` syntax blindly.
- Weaviate and Milvus documented examples require explicit embedding-field configuration for vector search.
- Elasticsearch v7 and v8 are not interchangeable dependency/service variants; v7 lacks the documented native ANN path.
- External services may require Docker, network access, API keys, TLS, or server-side schema/index creation. These are optional verification blockers, not reasons to silently claim CPU verification.
