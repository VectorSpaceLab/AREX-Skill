# Retrieval and GraphRAG

## Retrieval Entry Points

RAGFlow exposes retrieval through several REST paths that share the same retrieval core but differ in validation and field names.

- `POST /retrieval`: SDK compatibility endpoint. Requires `dataset_ids` and `question`.
- `POST /datasets/search`: multi-dataset search endpoint. Requires `dataset_ids` and `question`.
- `POST /datasets/{dataset_id}/search`: single-dataset search endpoint. Supplies the dataset id from the path.
- Chat, bot, OpenAI-compatible, agent, and search-bot routes call into the same retrieval service with their own search_config defaults.

When fixing retrieval, identify the entry point first. A bug in request validation may affect only one endpoint; a bug in `Dealer`/retriever ranking affects all callers.

## Hybrid Search Flow

The central search object is `Dealer`. It combines full-text and vector search over the document engine.

1. Request filters are built from dataset ids, document ids, availability, graph fields, and other indexed fields.
2. Pagination uses `page`, `page_size`/`size`, and `top_k`/`topk` depending on the route.
3. If `question` is empty, retrieval can return ordered chunks using chunk order, page number, top position, and creation timestamp.
4. If `question` is present, the query is tokenized into full-text match terms.
5. If an embedding model is provided, the question is encoded and searched against `q_{dimension}_vec` with cosine similarity.
6. Full-text and dense matches are fused with a weighted sum. Search callers pass vector similarity weight; full-text weight is effectively the complement.
7. The result set carries ids, fields, highlight data, aggregations, query vector, and keywords.
8. Retrieval can re-rank, prune deleted documents, expand child chunks, add TOC-related chunks, add KG content, and map fields for public output.

Document engine rows must contain both token fields and vector fields for best hybrid behavior. If vectors are missing or dimensions differ from the selected embedding model, vector retrieval will silently degrade or fail depending on backend.

## Ranking Inputs

Important ranking inputs include:

- `similarity_threshold`: minimum retrieval score threshold used by service-level retrieval.
- `vector_similarity_weight`: weight assigned to vector similarity; full-text weight is the complement in service code.
- `top_k`: candidate count requested from the document engine.
- `page` and `page_size`: public pagination controls.
- `rerank_id`: optional rerank model id.
- `keyword`: when enabled, query keywords can be generated and appended to the question.
- `cross_languages`: optional cross-language query expansion.
- `pagerank`: dataset-level ranking boost. It is engine-dependent and may be unavailable on non-Elasticsearch engines.
- `tag_kwd`/`tag_feas`: tag features can influence rank feature scores.
- `important_kwd` and `question_kwd`: chunk-level keyword/question fields added manually or by post-processing.

## Metadata and Document Filters

Retrieval can filter documents before searching chunks.

- `dataset_ids`/`kb_ids`: required for public retrieval and always used as index filters.
- `document_ids`/`doc_ids`: optional. If present, routes validate that every document belongs to the selected dataset(s).
- `metadata_condition`: structured metadata filter used by compatibility retrieval and other routes.
- `meta_data_filter`: search endpoint wrapper format that is converted by service code.
- `available_int`: chunk availability flag; disabled chunks should not be returned in normal retrieval.

A metadata condition with no matching documents can deliberately return zero chunks before document engine search. This is expected and should not be treated as an indexing bug.

## Retrieval Response Mapping

Internal chunk fields are remapped for public responses in compatibility endpoints.

Common mappings:

- `chunk_id` or document-engine row id -> `id`
- `content_with_weight` -> `content`
- `doc_id` -> `document_id`
- `docnm_kwd` -> `document_keyword`
- `kb_id` -> `dataset_id`
- `important_kwd` -> `important_keywords`
- `question_kwd` -> `questions`
- `img_id` -> `image_id`

Vector fields and tokenizer fields are stripped from public chunk responses. Do not expose `q_*_vec`, `*_tks`, `*_ltks`, or other runtime-only fields unless a low-level debug endpoint explicitly requires them.

## Child Chunk and TOC Retrieval

Child chunking and TOC enhancement improve context assembly after initial search.

- Child chunks are produced when parser config enables parent-child chunking and supplies `children_delimiter`/`enable_children` execution fields.
- A child chunk can carry a `mom`/parent reference so retrieval can recall parent content after precise child matching.
- TOC extraction creates a synthetic inactive TOC chunk with `toc_kwd` and ids pointing to source chunks.
- Retrieval can use `toc_enhance` to ask a chat model to supplement missing context based on TOC structure.

If a query finds child chunks but answers lack context, inspect parent-child fields and TOC fields before changing ranking thresholds.

## GraphRAG Retrieval

`KGSearch` extends `Dealer` for graph retrieval. It returns one synthetic chunk summarizing relevant entities, relations, and community reports.

Graph retrieval steps:

1. The question is rewritten into answer type keywords and entities using a chat model.
2. Entity candidates are searched by query entities against graph entity rows.
3. Entity type candidates are loaded by requested answer types and rank.
4. Relation candidates are searched by query text against relation rows.
5. N-hop relations from entity metadata are folded into relation candidates.
6. Entity/relation scores combine similarity and pagerank-like graph weights.
7. Community reports can be appended if configured and token budget remains.
8. The result is inserted at the front of normal retrieved chunks when `use_kg` is enabled and KG content is non-empty.

Important graph row fields include `knowledge_graph_kwd`, `entity_kwd`, `entity_type_kwd`, `from_entity_kwd`, `to_entity_kwd`, `rank_flt`, `weight_int`, `weight_flt`, `entities_kwd`, and `n_hop_with_weight`.

## GraphRAG Construction and Resume

GraphRAG construction is a task route, not a retrieval-time operation.

- The task route uses dataset parser config and may add default `graphrag` config if missing.
- `method` selects extractor style: `light`, `general`, or `ner`.
- `entity_types` must fit the dataset domain; defaults are generic.
- `resolution` and `community` are optional heavier phases.
- Redis checkpoints store phase payloads for community and resolution work with a bounded TTL.
- Phase markers record completed `resolution_done` and `community_done` phases for a dataset so a rerun can skip work after a crash/cancel.
- A Redis lock protects graph merge operations. Lock timeout problems usually indicate a still-running task, stale lock, or overloaded queue/worker.

If new document content changes the global graph, prior phase markers must be cleared so resolution/community outputs are not stale.

## RAPTOR Retrieval Impact

RAPTOR is generated at indexing time and surfaces during normal retrieval as additional summary chunks.

- It creates hierarchical summary chunks with `raptor_kwd` and method metadata.
- File-level and dataset-level scopes produce different summary ownership and cleanup behavior.
- Changing RAPTOR tree builder or clustering method should clean stale summaries for the affected document/fake document id.
- Duplicate summary chunks usually mean cleanup did not exclude or keep the right method.

RAPTOR does not require `use_kg`; it participates through the normal document engine search path once summary chunks are indexed.

## Debugging No-Chunk Retrieval

Use this order to avoid chasing the wrong layer:

1. Confirm selected datasets use the same embedding model when querying multiple datasets.
2. Confirm documents are `DONE`, enabled, and have nonzero chunk count/token count.
3. Confirm the document engine index exists for the tenant/dataset and contains rows for the document ids.
4. Confirm `dataset_ids`, `document_ids`, and metadata filters do not exclude all documents.
5. Confirm query is not empty after stripping, unless empty-query behavior is desired.
6. Lower similarity threshold and increase `top_k` to distinguish ranking from indexing failure.
7. Check vector field dimension against the active embedding model.
8. Disable rerank, `use_kg`, `toc_enhance`, and metadata filters to isolate base retrieval.
9. If only KG content is missing, verify GraphRAG task completion and graph row fields.
10. If only parent context is missing, verify child/TOC fields and parser_config flattening.

## Safe Verification Targets

Good native or synthetic targets for this area:

- Metadata filter tests that prove filtered document ids produce expected chunk inclusion/exclusion.
- Search pagination and `top_k` tests that assert stable public response shape.
- Rank feature score tests for tag features and pagerank interaction.
- GraphRAG checkpoint and phase-marker tests for resume/cleanup behavior.
- Task route tests for RAPTOR/GraphRAG index create, trace, cancel, and wipe/resume semantics.
