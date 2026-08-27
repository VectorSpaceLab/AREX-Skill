# API reference

## Defaults that matter

These defaults are the main retrieval behavior knobs exposed by the sub-skill:

- `DocChatAgentConfig.n_relevant_chunks = 3`
- `DocChatAgentConfig.n_similar_chunks = 3`
- `DocChatAgentConfig.use_bm25_search = True`
- `DocChatAgentConfig.use_fuzzy_match = True`
- `DocChatAgentConfig.hypothetical_answer = False`
- `DocChatAgentConfig.retrieve_only = False`
- `DocChatAgentConfig.conversation_mode = True`
- `DocChatAgentConfig.retain_context = False`
- `ParsingConfig.splitter = Splitter.MARKDOWN`
- `ParsingConfig.chunk_size = 1000` inside `DocChatAgentConfig.parsing`
- `PdfParsingConfig.library = "pypdfium2"`
- `VectorStoreConfig.full_eval = False`

## `DocChatAgentConfig`

`DocChatAgentConfig` bundles the retrieval pipeline:

| Field | Purpose | Notes |
| --- | --- | --- |
| `doc_paths` | Docs or URLs to ingest | Accepts local paths, URLs, folders, and bytes via the ingest methods |
| `vecdb` | Vector-store config | Usually `QdrantDBConfig`, but any supported backend config works |
| `parsing` | Parser and chunking config | Controls split strategy, PDF/DOCX library choice, and neighbor windows |
| `n_similar_chunks` | Retrieval width per method | Used by semantic, BM25, and fuzzy retrieval stages |
| `n_relevant_chunks` | Final returned passages | After reranking or fusion |
| `n_neighbor_chunks` | Context-window expansion at retrieval time | Adds neighboring chunks around a match |
| `use_bm25_search` | Lexical retrieval toggle | Default on |
| `use_fuzzy_match` | Approximate string match toggle | Default on |
| `use_reciprocal_rank_fusion` | Fuse multiple rank lists | Useful when multiple retrieval methods are enabled |
| `cross_encoder_reranking_model` | Optional reranker | Leave empty to skip cross-encoder reranking |
| `chunk_enrichment_config` | Chunk enrichment prompts | Adds retrieval-friendly keywords or questions |
| `relevance_extractor_config` | Verbatim passage extraction config | Defaults to `RelevanceExtractorAgentConfig(llm=None)` |
| `filter` | Retrieval filter | Used by vector-store and lexical search paths |
| `filter_fields` | Lance filter whitelist | Important for Lance RAG schema guidance |
| `add_fields_to_content` | Extra fields copied into text | Helps table-like or structured records match queries |
| `full_citations` | Citation detail level | Inherited from `ChatAgentConfig` |

## `DocChatAgent`

| Method | Purpose | Notes |
| --- | --- | --- |
| `ingest_docs(...)` | Ingest already-built `Document` objects | Splits, enriches, embeds, stores, and indexes chunks |
| `ingest_doc_paths(...)` | Ingest paths, URLs, bytes, or lists | Routes URLs through `URLLoader`, files through `RepoLoader` |
| `ingest_dataframe(...)` | Ingest tabular data | Promotes rows to `Document` objects and can preserve metadata columns |
| `get_relevant_chunks(...)` | Retrieve candidate passages | Combines semantic, BM25, fuzzy, fusion, and reranking logic |
| `get_relevant_extracts(...)` | Produce query + verbatim extracts | Uses `RelevanceExtractorAgent` when enabled |
| `answer_from_docs(...)` | Answer from retrieved extracts | Returns `ChatDocument` with citation metadata |
| `llm_response(...)` / `llm_response_async(...)` | Conversation entry point | Turns doc retrieval into an answer or summary |
| `retrieval_tool(...)` | Retrieval-only tool handler | Sets `retrieve_only=True` and returns extracts directly |
| `clear()` | Drop the active collection and local caches | For Qdrant local, also re-creates the store |
| `set_filter(...)` | Apply a retrieval filter | Rebuilds cached chunk views |
| `user_docs_ingest_dialog()` | Interactive ingest helper | Optional operator workflow |

## `LanceDocChatAgent`

`LanceDocChatAgent` extends `DocChatAgent` with LanceDB-specific filtering and FTS.

| Method | Purpose | Notes |
| --- | --- | --- |
| `ingest_dataframe(...)` | Lance-friendly dataframe ingest | Creates FTS indexes on `content` |
| `query_plan(...)` | Apply a `QueryPlanTool` | Handles filter + query + dataframe calculation |
| `get_similar_chunks_bm25(...)` | Lance full-text search | Uses LanceDB search plus the active filter |
| `_get_clean_vecdb_schema()` | Build schema guidance for the planner | Used by `LanceRAGTaskCreator` |

## `LanceRAGTaskCreator`

`LanceRAGTaskCreator.new(agent)` wires:

1. `LanceQueryPlanAgent`
2. `QueryPlanCritic`
3. `LanceDocChatAgent`

The planner emits a query plan with:

- `original_query`
- `filter`
- `query`
- `dataframe_calc`

## `FileAttachment`

Useful when you want to send files directly to a multimodal model instead of parsing them first.

| Constructor | Input |
| --- | --- |
| `from_path(...)` | Local file path or URL |
| `from_bytes(...)` | Raw bytes plus optional filename |
| `from_io(...)` | File-like object |
| `from_text(...)` | In-memory text |

`to_dict(model)` emits an OpenAI-style `file` or `image_url` payload.

## `VectorStoreConfig`

Common fields used by retrieval backends:

- `collection_name`
- `replace_collection`
- `storage_path`
- `cloud`
- `batch_size`
- `embedding`
- `embedding_model`
- `timeout`
- `host`
- `port`
- `document_class`
- `metadata_class`
- `full_eval`

`VectorStore.create(config)` dispatches by concrete config class, not by string.
