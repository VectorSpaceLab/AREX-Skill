---
name: rag-documents-data
description: "Manage Kiln document ingestion, extraction, chunking, embeddings,
  vector stores, rerankers, and RAG search."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# RAG Documents Data

Use this skill for Kiln document upload, extraction, chunking, embedding, vector-store indexing, reranking, progress, search, and document API work.

## Owns
- `Document`, `Extraction`, `ExtractorConfig`, `ChunkerConfig`, `EmbeddingConfig`, `VectorStoreConfig`, `RagConfig`, and `RerankerConfig`
- MIME classification, extraction passthrough behavior, and document attachment loading
- `RagTool`, RAG workflow runners, and RAG progress accounting
- document API route families that manage documents, extractions, config trees, RAG runs, progress, and search
- LanceDB/vector-store loading notes and chunk indexing reconciliation

## Route away
- task invocation, provider selection, or agent tool execution -> `task-execution-providers-tools`
- UI route mechanics or presentation concerns -> `server-desktop-web-api`
- synthetic data, evals, prompt optimization, or dataset splits -> `evals-optimization-finetuning`

## Use this sequence
1. Validate the document kind and MIME family before you reason about extraction.
2. Choose the extractor config. If the MIME type is configured for passthrough, the extractor should return UTF-8 file text directly.
3. Chunk only after extraction output exists. Semantic chunking requires a valid embedding config and a parent project path.
4. Embed chunk text before indexing. Keep chunk and embedding counts aligned.
5. Index into the vector store before search. The search tool is not a substitute for indexing.
6. Search with `RagTool`. Vector and hybrid stores need a query embedding; FTS does not.
7. Rerank only after vector-store search and before final formatting.

## Validation checklist
- MIME kind matches the supported family.
- `passthrough_mimetypes` contains the expected text MIME values.
- `chunk_overlap < chunk_size` for fixed-window chunking.
- semantic chunking has a parent project and a resolved embedding config.
- embedding vectors are present before indexing.
- vector-store, extractor, chunker, and embedding config IDs all resolve under the same project.
- the target vector store has been indexed before search is expected to return useful results.
- tiny fixtures still leave at least one non-whitespace chunk, or the zero-chunk case is intentional.

## Bundled references
- [Document and RAG workflows](references/document-rag-workflows.md)
- [Data formats](references/data-formats.md)
- [API reference](references/api-reference.md)
- [Troubleshooting](references/troubleshooting.md)

## Bundled scripts
- [check_rag_imports.py](scripts/check_rag_imports.py)

## Evidence notes
Source evidence used here includes `libs/core/kiln_ai/datamodel/extraction.py`, `chunk.py`, `embedding.py`, `vector_store.py`, `rag.py`, `reranker.py`, `libs/core/kiln_ai/adapters/*`, `libs/core/kiln_ai/tools/rag_tools.py`, and `libs/server/kiln_server/document_api.py`.
