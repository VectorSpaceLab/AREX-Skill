# Ingestion Pipeline

## Mental Model

RAGFlow ingestion turns uploaded or linked files into searchable chunk records in the document engine. The common path is:

1. Dataset or document REST endpoint receives public fields such as `chunk_method`, `parser_config`, `document_ids`, or `pipeline_id`.
2. Public fields are normalized into internal database fields such as `parser_id`, `parser_config`, `embd_id`, and task rows.
3. Task routing decides between standard built-in chunking, a user dataflow pipeline, RAPTOR, GraphRAG, memory, or placeholder task types.
4. Standard tasks read the stored file, call the parser/chunker for `parser_id`, post-process chunks, embed them, insert them into the document engine, and update document counters/status.
5. Retrieval reads only the document engine plus database metadata; parsed-but-not-indexed documents are invisible to retrieval.

## REST Entry Points

Dataset routes handle default configuration and higher-level index operations:

- `POST /datasets`: creates a dataset. If no ingestion pipeline is selected, the default parser is `naive`.
- `PUT /datasets/{dataset_id}`: updates dataset fields and deep-merges `parser_config` into the existing dataset config. If `chunk_method` changes without a config, default config for the new method is generated.
- `GET /datasets/{dataset_id}/ingestions` and `GET /datasets/{dataset_id}/ingestions/{log_id}`: inspect ingestion logs.
- `POST /datasets/{dataset_id}/index?type=raptor|graphrag`: starts index-building tasks for auxiliary indexes.
- `GET /datasets/{dataset_id}/index?type=...`: traces index status.
- `DELETE /datasets/{dataset_id}/index?type=...&wipe=false`: cancels/removes index work; `wipe=false` preserves existing progress where supported.
- `GET /datasets/{dataset_id}/graph`: returns the dataset knowledge graph view.
- `POST /datasets/{dataset_id}/embedding` and `/embedding/check`: reembedding/check flows.

Document routes bridge uploads, per-document config, and parsing:

- `POST /datasets/{dataset_id}/documents`: uploads files. Multipart `parser_config` is parsed from JSON and only allowed keys are kept.
- `PATCH /datasets/{dataset_id}/documents/{document_id}`: updates document name, `parser_config`, `chunk_method`, `pipeline_id`, enabled flag, and metadata fields. Changing `chunk_method` resets the document for reparse when needed.
- `POST /datasets/{dataset_id}/documents/parse`: queues parsing for `document_ids`, clears old chunks for completed docs, and deletes old document-engine rows before queueing new work.
- `POST /datasets/{dataset_id}/documents/stop`: cancels running parsing for `document_ids`.
- `POST /documents/ingest`: compatibility endpoint that sets document run state and may apply KB metadata config before queueing work.

Chunk routes expose manual chunk lifecycle and compatibility parsing controls:

- `POST /datasets/{dataset_id}/chunks`: reparse `document_ids` through the chunk API compatibility route.
- `DELETE /datasets/{dataset_id}/chunks`: stop parsing and delete indexed chunks for running docs.
- `GET/POST/PATCH/DELETE /datasets/{dataset_id}/documents/{document_id}/chunks`: list, add, update, enable/disable, or delete individual chunks.

## Built-In Chunking Path

The built-in standard path is selected when task type is not dataflow/RAPTOR/GraphRAG and not another special route.

- The task handler binds the embedding model first and probes vector size with a small encode call.
- It initializes the dataset index in the document engine using the tenant index name, dataset id, vector size, and parser id.
- It fetches the stored file binary and calls the parser selected by `parser_id`.
- Parser selection maps methods such as `naive`/`general`, `paper`, `book`, `presentation`, `manual`, `laws`, `qa`, `table`, `resume`, `picture`, `one`, `audio`, `email`, `tag`, and `knowledge_graph` to parser modules.
- Parser config is merged for table parser metadata before chunking.
- Chunks may carry text, metadata, page/position fields, image/table markers, keywords/questions, and parser-specific fields.
- Embedding combines chunk content with filename/title weighting, writes a `q_{dimension}_vec` field, and records token consumption.
- Optional TOC extraction for the naive parser creates an extra inactive `toc_kwd` chunk with ids that point back to source chunks.
- Post-processing can add table metadata, keyword tokens, question tokens, auto-generated metadata, and auto-tags.
- The document engine insert must succeed before document counters are incremented and task progress reaches done.

## RAG Flow Pipeline Path

A dataset can use a user-defined ingestion pipeline instead of a built-in parser.

Pipeline components are graph nodes. The default graph starts with `File` and can include components such as `Parser`, `TokenChunker`, `Tokenizer`, and `Extractor`.

- `File` loads the document name from the document row when running on a stored document, or uses the uploaded file object in debug/free-run mode.
- `Parser` normalizes file formats into `json`, `markdown`, `text`, `html`, or other configured outputs. Keep parser implementation work in the document parsing sub-skill.
- `TokenChunker` converts parser output into chunk dictionaries. It supports token-size, delimiter, or one-chunk modes, optional overlap, child chunks, and table/image context windows.
- `Tokenizer` tokenizes title/content/keywords/questions and optionally creates embedding vectors.
- `Extractor` can add LLM-derived fields such as TOC, keyword-like outputs, or other configured destination fields.
- Pipeline output is normalized to chunks before document-engine insertion. If output chunks lack vector fields, the dataflow service embeds them before indexing.
- Pipeline progress logs are stored separately and can be inspected through pipeline operation logs.

When debugging dataflow, verify the output format first. Empty `chunks`, `json`, `markdown`, `text`, or `html` output can be valid but will lead to zero indexed chunks.

## Parser Config Defaults and Merge Rules

`parser_config` is not a flat schema owned by one endpoint. It is normalized and merged in several places.

- Dataset create/update uses default config for the selected `chunk_method` and deep-merges user config.
- Empty parser config dictionaries may be treated as omitted config.
- Dataset update flattens `parent_child` into `children_delimiter` and `enable_children` for execution.
- Document update can merge nested `ext` fields into the document parser config.
- Document ingest with `apply_kb` copies selected KB metadata fields into the document parser config before queueing parsing.
- The execution layer sees both `parser_config` and `kb_parser_config` in task rows.

Important defaults for `naive` include `layout_recognize`, `chunk_token_num`, `delimiter`, `auto_keywords`, `auto_questions`, `html4excel`, `topn_tags`, `raptor`, `graphrag`, and `parent_child`. Other methods often disable RAPTOR and GraphRAG by default unless explicitly configured.

## Task Routing

Task routing occurs in the task handler after embedding model binding and index initialization.

- `memory`: saves memory task content and returns early.
- `dataflow` and related task types: run the user pipeline path.
- `raptor`: run RAPTOR summary generation and insert generated summary chunks.
- `graphrag`: run knowledge graph construction and insert graph chunks/metadata.
- `mindmap`, `evaluation`, `reembedding`, `clone`: currently lightweight or placeholder paths.
- default: run standard built-in chunking.

Cancellation is checked at multiple points. On cancellation cleanup, indexed rows for the document may be removed from the document engine.

## RAPTOR Boundaries

RAPTOR is an indexing-time augmentation that creates summary chunks from existing chunks. It is not a parser and should not replace normal chunk creation.

- Config lives under `parser_config.raptor`.
- The task route enables default RAPTOR config if missing when a RAPTOR task is requested.
- File-level scope summarizes per document; dataset-level scope can summarize across a fake dataset-level document id.
- Summary chunks use fields such as `raptor_kwd`, `extra.raptor_method`, `raptor_layer_int`, and generated chunk ids.
- Stale RAPTOR chunks are cleaned up when methods or scope change.
- RAPTOR requires a chat model, embedding model, and existing source chunks; empty source chunks should short-circuit rather than generate summaries.

## GraphRAG Boundaries

GraphRAG is also an indexing-time augmentation. It extracts entities, relations, and optional community/resolution outputs from already parsed chunks.

- Config lives under `parser_config.graphrag`.
- Default method is `light`; other extractor methods include `general` and `ner`.
- Common config keys include `use_graphrag`, `entity_types`, `method`, `batch_chunk_token_size`, retry/backoff settings, per-phase timeouts, merge/resolution/community timeouts, and lock acquisition timeout.
- GraphRAG work is protected by a dataset-scoped Redis lock to avoid concurrent graph merges.
- Checkpoints can cache community and resolution phase work. Phase markers let re-runs skip completed resolution/community phases after cancellation or crash.
- Clearing or regenerating graph content must invalidate stale phase markers and, when requested, graph rows.

## Adding a New Chunk Method

When adding a chunk method, trace all seams:

1. Add the public validation enum and error messages for dataset/document endpoints.
2. Add default parser config for dataset creation/update.
3. Map the method to a parser module in the task executor parser factory.
4. Decide whether RAPTOR/GraphRAG should default to enabled or disabled.
5. Decide file-type compatibility and parser_config keys.
6. Update frontend forms and SDK/API docs in their own sub-skills.
7. Add REST tests for create/update, upload/parse, and retrieval compatibility.

Do not add a parser method only in the UI or only in the backend; mismatched enums produce hard-to-debug parser_config/chunk_method failures.
