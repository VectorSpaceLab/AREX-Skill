# Vector Database, Knowledge Base, and Storage Reference

This reference covers Nexent knowledge-base storage, vector indexing/search, chunk management, summaries, and the `knowledge_base_search` tool.

## Vector Database Core

Nexent uses a `VectorDatabaseCore` abstraction with Elasticsearch and DataMate implementations.

| Capability | Core methods |
| --- | --- |
| Index management | `create_index`, `delete_index`, `get_user_indices`, `check_index_exists` |
| Document/chunk indexing | `vectorize_documents`, `delete_documents`, `get_index_chunks`, `create_chunk`, `update_chunk`, `delete_chunk`, `count_documents` |
| Search | `accurate_search`, `semantic_search`, `hybrid_search`, `search`, `multi_search` |
| Reporting | `get_documents_detail`, `get_indices_detail` |

### Elasticsearch Behavior

- New indices include fields such as `id`, `title`, `filename`, `path_or_url`, `language`, `author`, `date`, `content`, `process_source`, `embedding_model_name`, `file_size`, `create_time`, and dense-vector embedding fields.
- `vectorize_documents` chooses small-batch insertion for fewer than 64 documents unless `large_mode=True`. Large batches adjust index refresh settings temporarily, sub-batch embedding calls, retry embedding API failures, then bulk insert and refresh.
- Text embedding models skip chunks whose `process_source` is `UniversalImageExtractor`; multimodal models embed both text and image metadata chunks and use a separate multimodal embedding field.
- Bulk indexing surfaces specific JSON error codes where possible, especially `es_dim_mismatch` for embedding dimension mismatch and `es_bulk_failed` for other fatal bulk errors.
- `get_index_chunks` excludes vector embeddings from returned payloads and can paginate or scroll all chunks.

### DataMate Behavior

DataMate is selected through the vector database type and requires a tenant-scoped service URL. It implements the same high-level interface for index, document, chunk, and hybrid-search operations but should be treated as externally managed/read-only in some backend permission paths.

## Backend Knowledge-Base Lifecycle

Backend API routes for knowledge bases live under `/indices` and `/summary`.

| Operation | Route shape | Key behavior |
| --- | --- | --- |
| Existence check | `POST /indices/check_exist` | Checks uniqueness for the current tenant, with optional exclusion during rename. |
| Create knowledge base | `POST /indices/{index_name}` | Creates vector index plus knowledge metadata, group visibility, source-file preservation, quota, and selected embedding model. |
| Update knowledge base | `PATCH /indices/{index_name}` | Edits name, in-group permission, groups, summary frequency, quota, or embedding model depending on route. |
| Delete knowledge base | `DELETE /indices/{index_name}` | Deletes index, metadata, source objects, Redis task records, and storage charges where applicable. |
| Index documents | `POST /indices/{index_name}/documents` | Vectorizes chunks with the knowledge base's saved embedding model; returns submitted/indexed counts. |
| List files | `GET /indices/{index_name}/files` | Merges vector data, source ledger, task progress, source availability, and chunk counts. |
| Delete document | `DELETE /indices/{index_name}/documents` | Supports full document delete or source-only delete depending on `scope`. |
| Chunk CRUD | `/indices/{index_name}/chunks`, `/chunk`, `/chunk/{chunk_id}` | Read, create, update, and delete individual chunks. |
| Hybrid search | `POST /indices/search/hybrid` | Requires read permission for every requested knowledge base. |
| Summary | `/summary/{index_name}/auto_summary` and `/summary/{index_name}/summary` | Generate, change, and retrieve knowledge-base summary text. |

Permission rules matter. Creator/admin-like roles can edit broadly; ordinary users may have creator, edit, read, or no access depending on tenant, group visibility, and in-group permission. DataMate knowledge is treated as read-only. Search routes and tools must filter inaccessible indices before querying vector storage.

## Knowledge-Base Search Tool

`KnowledgeBaseSearchTool` is the SDK tool that agents use for local knowledge retrieval.

| Setting | Meaning |
| --- | --- |
| `top_k` | Number of results returned to the model; rerank over-fetches internally. |
| `index_names` | Default internal index names. User-facing display names are converted through `display_name_to_index_map`. |
| `search_mode` | `hybrid`, `accurate`, or `semantic`. Invalid modes raise a clear error. |
| `rerank` / `rerank_model` | Optional reranking; failures keep original vector results. |
| `embedding_model` | Required for semantic/hybrid vector branches. |
| `vdb_core` | Injected vector database client. |
| `document_paths` | Internal filter restricting results to selected source documents. |
| `allowed_index_names` | Backend-computed read-permission whitelist; fabricated LLM index names are silently dropped. |

Result formatting normalizes `local` and `minio` source types to `file`, emits observer search-content cards, includes citation indices, and emits picture events for image chunks whose content contains image metadata. Image filtering calls the data-process service with a short timeout and falls back safely if filtering fails.

## Storage and MinIO

Nexent storage uses an abstract storage client plus a MinIO/S3-compatible implementation.

| API | Behavior |
| --- | --- |
| `MinIOStorageConfig(endpoint, access_key, secret_key, region=None, default_bucket=None, secure=True)` | Validates endpoint/access/secret and identifies storage type as MinIO. |
| `upload_file` / `upload_fileobj` | Uploads local files or file objects; returns `(success, path_or_error)` where success paths are bucket/object-style paths for later presigning. |
| `download_file`, `get_file_stream`, `get_file_range` | Read whole objects or byte ranges. |
| `get_file_url` | Returns a presigned URL with configurable expiration. |
| `get_file_size` vs `get_file_size_strict` | `get_file_size` hides not-found/errors as `0`; strict mode raises service/permission errors and returns `None` for not found. |
| `list_files`, `delete_file`, `exists`, `copy_file` | Object management primitives. |

The backend file-management service resolves upload folders by user/tenant, commits source objects to the knowledge storage ledger, handles quota checks, preserves original filenames, and renames duplicate filenames within a knowledge base. Preview for Office files uses cached PDF conversion through the data-process service.

## Configuration Checklist

For code changes, use the backend constants module as the only environment-variable source. Important knowledge-stack configuration names include:

- Vector/search: `ELASTICSEARCH_HOST`, `ELASTICSEARCH_API_KEY`, `ELASTICSEARCH_SERVICE`, DataMate URL config, model records for embedding/rerank models.
- Data process: `DATA_PROCESS_SERVICE`, `REDIS_URL`, `REDIS_BACKEND_URL`, `DP_FILE_SPLIT_SIZE_MB`, `DP_PART_PROCESSOR_COUNT`, split wait/retry settings, Ray/Celery settings.
- Storage: `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_REGION`, `MINIO_DEFAULT_BUCKET`, `MINIO_SECURE`.
- Conversion/image: `MAX_CONCURRENT_CONVERSIONS`, `CLIP_MODEL_PATH`, `IMAGE_FILTER`, table-transformer/unstructured model-cache variables.

Live values are deployment concerns. This sub-skill helps identify the names and code paths; use [deployment-operations](../../deployment-operations/SKILL.md) to change deployed services or env files.

## Safe Test Strategy

- Test vector core behavior with mocked Elasticsearch clients and fake embedding models.
- Test `knowledge_base_search` with a fake `vdb_core`, fake reranker, observer spy, display-name mapping, `document_paths`, and `allowed_index_names`.
- Test backend knowledge routes with dependency/mocker patches at import sites; do not require live Elasticsearch, MinIO, Redis, or model providers for unit coverage.
- Test chunk CRUD with small dictionaries and verify embedding is regenerated only when expected.
