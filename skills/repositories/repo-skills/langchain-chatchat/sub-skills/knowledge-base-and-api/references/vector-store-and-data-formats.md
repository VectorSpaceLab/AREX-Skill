# Vector Store and Data Formats

## Core concepts

Langchain-Chatchat stores knowledge-base files and metadata under `CHATCHAT_ROOT`. `kb_settings.yaml` controls chunking, vector-store selection, retrieval thresholds, and supported text splitters.

Important fields:

| Setting | Meaning |
| --- | --- |
| `DEFAULT_KNOWLEDGE_BASE` | Default KB name, commonly `samples` after initialization. |
| `DEFAULT_VS_TYPE` | Default vector-store backend, inspected default `faiss`. |
| `VECTOR_SEARCH_TOP_K` | Number of retrieved chunks. |
| `SCORE_THRESHOLD` | Similarity cutoff; lower scores are more relevant for many vector stores. |
| `CHUNK_SIZE`, `OVERLAP_SIZE` | Chunking parameters for document ingestion. |
| `TEXT_SPLITTER_NAME` | Text splitter implementation, e.g. Chinese recursive, recursive character, markdown header. |
| `ZH_TITLE_ENHANCE` | Chinese title enhancement for chunking/indexing. |
| `PDF_OCR_THRESHOLD` | OCR behavior for PDFs with large embedded images. |

## Supported vector stores

Inspected settings list these choices: `faiss`, `milvus`, `zilliz`, `pg`, `es`, `relyt`, and `chromadb`.

- `faiss` is the default CPU/local vector store path and is included in base dependencies.
- `milvus` and `zilliz` need running services and connection credentials.
- `pg` and `relyt` use PostgreSQL-style connection URIs.
- `es` needs Elasticsearch host/port/auth/cert settings.
- `chromadb` is a configured option but still needs dependency/service validation for the user's deployment.

Do not treat a successful FAISS smoke as proof that external vector DB backends work.

## Document ingestion modes

| Mode | API/CLI | Notes |
| --- | --- | --- |
| Copy files to KB content and rebuild | `chatchat kb -r` or `recreate_vector_store` | Batch-oriented; requires embedding provider; can be slow. |
| API upload to persistent KB | `/knowledge_base/upload_docs` | Can upload and vectorize in one request when `to_vector_store=True`. |
| API update existing docs | `/knowledge_base/update_docs` | Use when file content changed. |
| Temporary docs | `/knowledge_base/upload_temp_docs` | Returns a `knowledge_id` for temp-file chat. |
| Direct search | `/knowledge_base/search_docs`, `/search_temp_docs` | Useful for retrieval debugging. |

## File and parser notes

The package includes document-loader and OCR-related dependencies such as unstructured, PyMuPDF, rapidocr_onnxruntime, opencv, and python-docx. Actual supported behavior depends on installed optional system libraries and file type.

Common safe checks:

- Confirm the file appears in `list_files` after upload or indexing.
- Search for an exact phrase from the document.
- For PDFs/images, distinguish text extraction/OCR failures from vector-store failures.
- For Markdown, check splitter behavior if headers should be retained as metadata.

## Rebuild decision guide

Run full vector rebuild when:

- The embedding model changed.
- Chunking/splitter settings changed.
- Files were copied manually into KB content directories.
- The vector-store type changed.

Prefer targeted update/increment operations when only a few files changed. Avoid destructive prune/clear operations until the KB root and backup are confirmed.
