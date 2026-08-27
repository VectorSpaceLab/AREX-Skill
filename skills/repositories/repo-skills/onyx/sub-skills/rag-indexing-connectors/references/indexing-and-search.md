# Indexing and Search

Use this reference when a change affects docfetching, docprocessing, chunking, embeddings, contextual RAG, the document index factory, or OpenSearch retrieval behavior.

## Pipeline shape

1. A connector yields `Document`, `HierarchyNode`, or `SlimDocument` records.
2. The document indexing adapter prepares DB state, resolves access control, document sets, ancestor hierarchy ids, and the previous chunk count.
3. Image sections are materialized through the file store and summarized with a vision model when image analysis is enabled.
4. `Chunker` turns each `IndexingDocument` into `DocAwareChunk` objects via the text, image, and tabular chunkers.
5. Optional contextual RAG adds a document summary and per-chunk context within the reserved token budget.
6. The embedder produces title and passage embeddings, including mini-chunk embeddings when multipass is enabled.
7. Chunks are written to every active vector backend through `write_chunks_to_vector_db_with_backoff()`.
8. The post-index step updates chunk counts, timestamps, last-modified markers, and the stored content hash.
9. Optional document push is fire-and-forget and must never fail the batch.

## Document gating and hashes

- `get_docs_to_update()` applies two gates: timestamp first, then content hash.
- If `doc_updated_at` advanced, the new document must be indexed even if the content hash is identical.
- If the timestamp did not advance, the content hash can skip unchanged documents.
- Only persist the new content hash after a successful vector write.
- Never stamp a FUTURE / secondary write with the PRESENT content hash, or the shared hash can suppress the other index.
- `DocumentBase.content_hash()` covers title, text content, image file ids, metadata, and owners. It intentionally excludes derived summaries.

## Chunking, images, and tabular files

- `process_image_sections()` reads image bytes from the file store and stores the image summary text back onto the section.
- If image analysis is disabled or no vision model is available, the image section is still converted to a base section so the rest of the pipeline can proceed.
- `DocumentChunker` dispatches by section type: text, image, and tabular.
- `TabularSection.csv_file_id` points to a staged CSV in the file store; the tabular chunker streams it instead of materializing the whole sheet in memory.
- `Document.file_id` is the persisted raw file id used by downstream file-handling flows. For tabular files, it must be preserved so later consumers can find the original bytes.
- `generate_enriched_content_for_chunk_embedding()` and `generate_enriched_content_for_chunk_text()` add title, metadata, doc summary, and chunk context around the raw chunk text.

## Contextual RAG

- Contextual RAG is controlled by search settings plus the global enable flag.
- The chunker reserves tokens for document summary and chunk context only when the document does not already fit in one chunk.
- If the title and metadata consume too much of the chunk budget, the chunker drops them before it drops the raw content.
- The document summary and chunk context are search-time augmentations only; they must be stripped from user-facing chunks when results are returned.

## Document index factory

- `get_default_document_index()` returns the active retrieval backend for the current search settings.
- `get_all_document_indices()` returns every backend that should receive writes.
- OpenSearch and Vespa are selected by the search settings / migration state, not by connector type.
- If you change chunk fields, inspect the document index schema as well as the indexing pipeline so the write path and the retrieval path stay aligned.

## OpenSearch hybrid caveats

- OpenSearch hybrid search runs separate keyword and vector search phases, then combines them with normalization.
- The normalization pipeline can be min-max or z-score; the weights must match the subquery order and sum to 1.
- Title text is already mixed into the content, so title scoring is a boost, not a separate main signal.
- Time-based boosting is intentionally not pushed into the OpenSearch query because the hybrid normalization stage cannot safely recover missing candidates.
- Hybrid recall depends on enough candidates being fetched from each subquery; too-small candidate counts can hide good matches before normalization.

## When to inspect which layer

- Change in connector output shape: inspect the adapter and chunker first.
- Change in attachment, image, or tabular handling: inspect the file store and section materialization flow.
- Change in search ranking or filters: inspect the document index factory and OpenSearch query builder.
- Change in summary behavior: inspect the contextual RAG section and the chunk-content cleanup path.
