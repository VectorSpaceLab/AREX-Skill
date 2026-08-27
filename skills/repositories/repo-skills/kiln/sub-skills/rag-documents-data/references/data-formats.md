# Data formats

Use these shapes when creating, validating, or debugging Kiln document and RAG data.

## Core document tree

| Entity | Parent | Important fields | Validation and runtime notes |
|---|---|---|---|
| `Document` | `Project` | `name`, `name_override`, `description`, `original_file`, `kind`, `tags` | `tags` cannot be empty strings and cannot contain spaces. `friendly_name` is `name_override` or `name`. |
| `FileInfo` | embedded in `Document` | `filename`, `size`, `mime_type`, `attachment` | MIME type must be supported. Browser-provided content type is not trusted by the bulk API; filename-based guessing is used there. |
| `Extraction` | `Document` | `source`, `extractor_config_id`, `output` | `source` is `processed` or `passthrough`. `output_content()` requires the extraction path and reads UTF-8 text. |
| `ChunkedDocument` | `Extraction` | `chunker_config_id`, `chunks` | `load_chunks_text()` requires the chunked document path and reads each chunk attachment as UTF-8 text. |
| `Chunk` | embedded in `ChunkedDocument` | `content` | `content` is an attachment whose serialized filename prefix is `content`. |
| `ChunkEmbeddings` | `ChunkedDocument` | `embedding_config_id`, `embeddings` | `embeddings[i]` corresponds to `chunks[i]`. Indexing rejects count mismatches. |
| `Embedding` | embedded in `ChunkEmbeddings` | `vector` | Vector values are floats. Dimensionality is inferred during indexing from the first vector. |

## Config entities

| Config | Key discriminator | Required data | Notes |
|---|---|---|---|
| `ExtractorConfig` | `extractor_type` | `model_provider_name`, `model_name`, `output_format`, `passthrough_mimetypes`, `properties` | Current type is `litellm`. Properties include `prompt_document`, `prompt_image`, `prompt_video`, `prompt_audio`, and a matching `extractor_type`. |
| `ChunkerConfig` | `chunker_type` | `properties` | `fixed_window` uses `chunk_size` and `chunk_overlap`; `semantic` uses `embedding_config_id`, `buffer_size`, `breakpoint_percentile_threshold`, `include_metadata`, and `include_prev_next_rel`. |
| `EmbeddingConfig` | provider/model pair | `model_provider_name`, `model_name`, `properties` | `properties.dimensions` is optional and must be a positive integer when present. API creation checks it against the selected model dimensions. |
| `VectorStoreConfig` | `store_type` | `properties` | Supported store types are `lancedb_fts`, `lancedb_vector`, and `lancedb_hybrid`. Vector and hybrid configs include `nprobes`. |
| `RagConfig` | config-id chain | `tool_name`, `tool_description`, extractor/chunker/embedding/vector store IDs, optional reranker ID, optional `tags` | `tags=None` means all documents. A non-None tag list must be non-empty and have no blank or space-containing tags. |
| `RerankerConfig` | `properties.type` | `top_n`, `model_provider_name`, `model_name` | Current type is `cohere_compatible`. `top_n` is positive. |

## MIME support

`Document.kind` is broad; exact support is checked by MIME type.

| Kind | Supported MIME types |
|---|---|
| `document` | `application/pdf`, `text/plain`, `text/markdown`, `text/html`, `text/md` |
| `image` | `image/png`, `image/jpeg` |
| `video` | `video/mp4`, `video/quicktime` |
| `audio` | `audio/wav`, `audio/mpeg`, `audio/ogg` |

The LiteLLM extractor also recognizes some provider-facing aliases such as `text/csv`, `image/jpg`, and `video/mov`. Treat those as adapter concerns, not as guaranteed persisted `FileInfo` MIME values unless the document validator accepts them.

## Passthrough details

`passthrough_mimetypes` is stored as a list of `OutputFormat` values even though it behaves like a MIME list.
The current values are:

- `text/plain`
- `text/markdown`

When passthrough matches, `BaseExtractor.extract()` reads the source file as text and returns:

- `is_passthrough=True`
- `content` equal to file text
- `content_format` equal to the extractor config's `output_format`

Use passthrough for text-like files that should not incur model extraction. Do not passthrough binary images, PDFs, audio, or video unless the code has been changed to handle those bytes safely.

## Vector-store data

| Shape | Fields | Notes |
|---|---|---|
| `DocumentWithChunksAndEmbeddings` | `document_id`, `chunked_document`, `chunk_embeddings` | Internal indexing bundle. Convenience properties expose `chunks` and `embeddings`. |
| `VectorStoreQuery` | `query_string`, `query_embedding` | FTS requires only `query_string`; vector requires `query_embedding`; hybrid requires both. |
| `SearchResult` | `document_id`, `chunk_idx`, `chunk_text`, optional `similarity` | `similarity` can be `None` for non-scored contexts or adapter-specific cases. |
| LanceDB node metadata | `kiln_doc_id`, `kiln_chunk_idx` | Used to reconstruct `SearchResult` and delete stale rows by document. |
| Global chunk id | `document_id::chunk_idx` | Used before reranking; reranking output is split back into document id and chunk index. |
| Deterministic node id | UUID from `document_id::chunk_idx` | LanceDB nodes need UUID-like ids, so the helper maps global chunk ids to stable UUIDs. |

## Progress and API response shapes

| Shape | Important fields | Notes |
|---|---|---|
| `RagProgress` | document totals, stage counts, chunk counts, per-stage error counts, `logs` | `total_document_completed_count` is the minimum of extracted/chunked/embedded counts. `total_chunk_completed_count` mirrors indexed chunks. |
| `RagStepRunnerProgress` | `success_count`, `error_count`, `logs` | Step-local counts are merged into `RagProgress`. Indexing success counts chunks; other stages count documents. |
| `ExtractionSummary` | extraction id, timestamps, source, `output_content`, extractor summary, truncation flag | API summaries truncate very large output content. |
| `RagConfigWithSubConfigs` | RAG config fields plus all referenced config objects | Used by RAG config list/get routes so callers do not have to resolve sub-configs manually. |
| `RagSearchResponse` | `results` | Search returns a list of `SearchResult`. Blank search query returns an empty list. |
| `EphemeralSplitResponse` | `chunks` | If `chunk_size` is `None`, the response contains one chunk with the full extraction output. |

## Tiny fixture implications

Tiny fixtures are useful for import and local behavior checks, but interpret them carefully:

- MIME fixtures should use a real extension because the bulk document API guesses MIME from the filename.
- Text passthrough fixtures must contain UTF-8 text.
- whitespace-only extraction output should produce zero chunks; this is valid behavior.
- fixed-window chunk counts are implementation-sensitive because `SentenceSplitter` changes can alter boundaries.
- semantic chunking fixtures may need mocked embedding adapters unless provider credentials are intentionally supplied.
- vector-store fixtures can use one or two documents, a few chunks, and deterministic small vectors, but chunk count must match embedding count.
- search fixtures should index before asserting retrieval, or explicitly assert the empty-result behavior of an uninitialized table.

## Evidence notes

Source evidence used here includes `libs/core/kiln_ai/datamodel/extraction.py`, `chunk.py`, `embedding.py`, `vector_store.py`, `rag.py`, `reranker.py`, `utils/rag_utils.py`, `adapters/vector_store/base_vector_store_adapter.py`, `lancedb_helpers.py`, and related tests under `libs/core/kiln_ai/adapters/` and `libs/server/kiln_server/test_document_api.py`.
