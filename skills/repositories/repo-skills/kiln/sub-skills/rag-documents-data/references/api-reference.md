# API reference

This reference collects the public document and RAG routes and the main Python entry points that own them.

## Document route families

| Route family | Common paths | Purpose | Notes |
|---|---|---|---|
| Documents | `/api/projects/{project_id}/documents`, `/documents/bulk`, `/documents/{document_id}`, `/documents/{document_id}/download`, `/documents/{document_id}/open_enclosing_folder`, `/documents/edit_tags`, `/documents/delete`, `/check_library_state` | Create, list, patch, delete, and inspect documents | Bulk upload infers MIME from filename. Delete/open/download endpoints are not suitable for autonomous agent use. |
| Extractions | `/extractor_configs/{extractor_config_id}/extractions`, `/documents/{document_id}/extractions`, `/documents/{document_id}/extractions/{extraction_id}`, `/documents/{document_id}/download_extraction/{extraction_id}`, `/documents/{document_id}/extract` | Inspect and run document extraction | `extract` is the workflow entry point for a single document. Deleting an extraction also clears extractor cache when possible. |
| Extractor configs | `/create_extractor_config`, `/extractor_configs`, `/extractor_configs/{extractor_config_id}`, `/extractor_configs/{extractor_config_id}/run_extractor_config`, `/extractor_configs/{extractor_config_id}/progress` | Create, list, patch, and run extractor configs | Config creation validates provider/model support and doc-extraction capability. |
| Chunker configs | `/create_chunker_config`, `/chunker_configs` | Create and list chunker configs | Semantic chunkers require a valid embedding config reference. |
| Embedding configs | `/create_embedding_config`, `/embedding_configs`, `/embedding_configs/{embedding_config_id}` | Create and list embedding configs | Creation validates model availability and optional dimension overrides. |
| Vector store configs | `/create_vector_store_config`, `/vector_store_configs` | Create and list vector store configs | Current store types are LanceDB FTS/vector/hybrid. |
| Reranker configs | `/create_reranker_config`, `/reranker_configs` | Create and list reranker configs | Current reranker type is Cohere-compatible through LiteLLM. |
| RAG configs | `/rag_configs/create_rag_config`, `/rag_configs`, `/rag_configs/{rag_config_id}`, `/rag_configs/{rag_config_id}/run`, `/rag_configs/{rag_config_id}/search`, `/rag_configs/progress`, `/rag_configs/{rag_config_id}` (PATCH) | Build, inspect, run, and search RAG configs | `run` streams progress. `search` returns formatted search results. Archived configs are rejected for run/search. |
| Ephemeral split | `/extractor_configs/{extractor_config_id}/documents/{document_id}/ephemeral_split` | Split an extraction without persisting a chunked document | Useful for previewing chunk boundaries. `chunk_size=None` returns one chunk with the full extraction output. |

## Request models and their validation focus

| Request model | Important fields | Validation focus |
|---|---|---|
| `CreateExtractorConfigRequest` | provider/model, output format, passthrough MIME list, extractor prompts | Model must exist and support document extraction. |
| `PatchExtractorConfigRequest` | name, description, archived flag | At least one field is required. |
| `CreateChunkerConfigRequest` | chunker type and typed properties | Semantic chunkers require an existing embedding config. |
| `CreateEmbeddingConfigRequest` | provider/model, optional dimensions | Dimensions must not exceed model dimensions. |
| `CreateVectorStoreConfigRequest` | store type and typed properties | Store-specific defaults are filled in. |
| `CreateRerankerConfigRequest` | top_n, provider/model, properties | Model must exist. |
| `CreateRagConfigRequest` | tool name/description, config ids, optional reranker, tags | Every referenced sub-config must exist. |
| `UpdateRagConfigRequest` | name, description, archived flag | All fields are optional; the route updates only the provided fields. |
| `RagSearchRequest` | query | Blank query returns an empty result list. |
| `GetRagConfigProgressRequest` | rag_config_ids | Empty or missing ids means all configs. |
| `EphemeralSplitRequest` | chunk_size, chunk_overlap | `chunk_overlap` defaults to 0 when omitted. |

## Code entry points

These are the main Python functions and classes a Researcher should inspect or extend when working on document and RAG behavior:

- `kiln_ai.datamodel.extraction.Document`
- `kiln_ai.datamodel.extraction.Extraction`
- `kiln_ai.datamodel.chunk.ChunkerConfig`
- `kiln_ai.datamodel.embedding.EmbeddingConfig`
- `kiln_ai.datamodel.vector_store.VectorStoreConfig`
- `kiln_ai.datamodel.rag.RagConfig`
- `kiln_ai.datamodel.reranker.RerankerConfig`
- `kiln_ai.adapters.extractors.extractor_adapter_from_type()`
- `kiln_ai.adapters.chunkers.chunker_adapter_from_type()`
- `kiln_ai.adapters.embedding.embedding_adapter_from_type()`
- `kiln_ai.adapters.vector_store.vector_store_adapter_for_config()`
- `kiln_ai.adapters.rerankers.reranker_adapter_from_config()`
- `kiln_ai.adapters.rag.progress.compute_current_progress_for_rag_config()`
- `kiln_ai.adapters.rag.rag_runners.RagWorkflowRunner`
- `kiln_ai.tools.rag_tools.RagTool`
- `kiln_server.document_api.connect_document_api()`
- `kiln_server.document_api.build_rag_workflow_runner()`
- `kiln_server.document_api.get_documents_filtered()`

## Search and tool behavior

`RagTool` is the canonical search tool id path. Its tool id format is:

```text
kiln_tool::rag::<rag_config_id>
```

Search behavior depends on the selected vector store type:

- FTS: query string only
- vector: query string plus query embedding
- hybrid: query string plus query embedding

If a reranker is configured, `RagTool` reranks after search and before it formats the output.
The output format is the same metadata block format described in [data formats](data-formats.md).

## Route notes that matter in practice

- RAG run and search routes reject archived configs.
- RAG config creation requires the extractor, chunker, embedding, and vector store configs to exist first.
- document extraction and RAG run routes stream progress through SSE.
- some file-opening and delete routes are deny-listed for agentic use in the server layer; do not rely on them for autonomous workflows.
- route and request validation should prefer the model layer over ad hoc checks in future changes.

## Evidence notes

Source evidence used here includes `libs/server/kiln_server/document_api.py`, `libs/core/kiln_ai/tools/tool_registry.py`, `libs/core/kiln_ai/tools/rag_tools.py`, `libs/core/kiln_ai/adapters/rag/rag_runners.py`, `libs/core/kiln_ai/adapters/rag/progress.py`, and the document/RAG API tests under `libs/server/kiln_server/test_document_api.py`.
