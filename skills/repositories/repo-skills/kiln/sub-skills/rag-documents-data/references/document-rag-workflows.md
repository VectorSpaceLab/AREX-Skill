# Document and RAG workflows

This reference describes the canonical order for Kiln document ingestion and RAG search.

## 1) Ingest a document

A `Document` belongs to a project and stores:

- `name` and optional `name_override`
- `description`
- `original_file` metadata plus attachment
- `kind`
- `tags`

The document's `original_file.mime_type` must map to a supported `Kind` family. The supported families are document, image, video, and audio.

### Key checks

- `get_kind_from_mime_type()` must return a kind.
- unsupported MIME values should fail before extraction.
- `friendly_name` resolves to `name_override` when present, otherwise `name`.

## 2) Extract content

Extraction produces an `Extraction` under a `Document`.

- `source` is `processed` or `passthrough`
- `extractor_config_id` selects the config
- `output` stores the extracted text attachment
- `output_content()` reads UTF-8 text from the attachment path

### Passthrough behavior

`BaseExtractor.extract()` checks `ExtractorConfig.passthrough_mimetypes` first.
If the MIME type is listed there, the extractor returns the file text as-is and marks the result as passthrough.

### LiteLLM extractor behavior

`LitellmExtractor`:

- selects a prompt by `Kind`
- supports document, image, video, and audio prompts
- splits PDFs page by page
- caches PDF page results when a filesystem cache is available
- special-cases OpenRouter audio/video payload shapes

### Important failure modes

- passthrough content must be readable as UTF-8 text
- missing or unsupported MIME types should fail early
- a deleted extraction may need cache cleanup before the next extraction run

## 3) Chunk extracted text

Chunking produces a `ChunkedDocument` under an `Extraction`.

- `chunker_config_id` selects the chunker config
- `chunks` store text attachments
- `load_chunks_text()` reads each chunk as UTF-8 text

### Fixed-window chunking

- uses `SentenceSplitter`
- runs `clean_up_text()` first
- returns empty chunks for empty or whitespace-only input

### Semantic chunking

- resolves the embedding config from the parent project
- wraps the embedding adapter in `KilnEmbeddingWrapper`
- uses `SemanticSplitterNodeParser`
- requires `embedding_config_id`, `buffer_size`, and `breakpoint_percentile_threshold`

### Important failure modes

- `chunk_overlap` must be smaller than `chunk_size`
- semantic chunking requires a parent project and a valid embedding config
- tiny or whitespace-only fixtures may legitimately produce zero chunks

## 4) Generate embeddings

`ChunkEmbeddings` stores one vector per chunk.
The vector at index `i` corresponds to the chunk at index `i` in the parent `ChunkedDocument`.

`LitellmEmbeddingAdapter`:

- batches inputs up to the adapter's batch limit
- can request lower dimensional embeddings when the model supports it
- expects a provider/model pair that Litellm can resolve

### Important failure modes

- embedding generation depends on the configured provider and model
- vector lengths must remain consistent for later indexing
- query embeddings are required for vector and hybrid search

## 5) Index into a vector store

Indexing collects `DocumentWithChunksAndEmbeddings` records and writes them to the selected vector store.

`RagIndexingStepRunner`:

- filters documents by rag tags when tags are configured
- deduplicates extractions, chunked documents, and embeddings by config id
- infers vector dimensionality from the first record
- batches writes to the vector store
- reconciles stale rows by deleting nodes not in the current target set

`LanceDBAdapter`:

- uses deterministic chunk IDs derived from `document_id::chunk_idx`
- replaces stale rows when the chunk set changes
- returns empty results when the table has not been created yet
- performs table-level locking during search to avoid concurrent FTS index churn

### Important failure modes

- indexing should happen before search is expected to be useful
- stale rows can remain if indexing is bypassed instead of using the workflow runner
- LanceDB reconciliation uses a pandas conversion path

## 6) Search with `RagTool`

`RagTool` is the public search tool for RAG configs.
It resolves the project, vector store config, embedding config, and optional reranker from the `RagConfig`.

### Search behavior

- FTS stores search directly with the query string
- vector and hybrid stores embed the query first
- if a reranker is configured, it reranks after the vector-store search
- the final tool output is formatted as metadata blocks separated by `=========`

### Result formatting

Each result is rendered as:

```text
[document_id: <id>, chunk_idx: <idx>]
<chunk text>
```

### Important failure modes

- vector and hybrid search require a working embedding adapter
- RAG search will not be meaningful until the index exists
- a missing reranker config should not block plain search

## 7) Stream progress

`RagProgress` tracks the full pipeline:

- total documents
- extracted documents and errors
- chunked documents and errors
- embedded documents and errors
- indexed chunks and errors
- log messages

`RagWorkflowRunner` yields the initial progress snapshot, then updates progress per stage.
The indexing stage sets `total_chunk_count` before chunk completion can be measured.

## 8) Use the document API route families

The document API owns the end-user route families for:

- documents
- extraction and extraction configs
- chunker configs
- embedding configs
- vector store configs
- reranker configs
- RAG configs
- RAG progress, RAG runs, and RAG search

The route details live in [API reference](api-reference.md).

## Evidence notes

Source evidence used here includes `libs/core/kiln_ai/adapters/rag/rag_runners.py`, `progress.py`, `deduplication.py`, `chunk.py`, `extraction.py`, `embedding.py`, `vector_store.py`, `tools/rag_tools.py`, `adapters/vector_store/lancedb_adapter.py`, and `libs/server/kiln_server/document_api.py`.
