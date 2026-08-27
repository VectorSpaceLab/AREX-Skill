# Troubleshooting

Use this checklist when document ingestion, RAG indexing, search, or imports fail.

## Import and dependency checks

Start with the bundled import checker:

```bash
python skills/disco/kiln/sub-skills/rag-documents-data/scripts/check_rag_imports.py
```

The script imports document/RAG modules only. It does not call providers, start servers, read external services, or make network requests.

| Symptom | Likely cause | Action |
|---|---|---|
| Missing `pandas` while importing or using LanceDB paths | LanceDB reconciliation calls a `to_pandas()` path when deleting stale nodes | Install or restore `pandas` in the Python environment used for RAG checks. |
| Missing `llama_index` or LanceDB modules | chunking, vector-store loaders, and LanceDB adapters depend on LlamaIndex/LanceDB packages | Install the Kiln RAG/vector-store dependency set before running RAG indexing or loader checks. |
| Missing `litellm` | extractor, embedding, and reranker adapters are LiteLLM-backed | Install the core AI adapter dependency set before running provider-backed extraction/embedding/reranking. |
| MCP tool imports fail after dependency refresh | current tool imports were verified with lock-compatible `mcp` 1.10.1 | Do not upgrade MCP blindly; restore the lock-compatible version before debugging higher-level code. |
| server import fails after Starlette change | Starlette 1.6 is incompatible with current server code; 0.52.1 worked in verification | Restore a compatible Starlette/FastAPI stack before debugging document routes. |

## Search returns empty results

Check these in order:

1. The `RagConfig` exists and is not archived.
2. The referenced extractor, chunker, embedding, and vector store configs exist under the same project path.
3. The documents matched by `RagConfig.tags` have extraction, chunking, and embeddings for the matching config IDs.
4. The RAG indexing workflow has run after the latest document/tag/chunk changes.
5. The selected vector store type matches the query: FTS needs text only; vector/hybrid need query embeddings.
6. Provider credentials or local services are available when query embeddings are required.

An uninitialized LanceDB table can return an empty list rather than an exception. Treat empty search as an indexing or query-precondition issue first, not immediately as a relevance failure.

## Indexing or LanceDB problems

| Symptom | Likely cause | Action |
|---|---|---|
| `No records to index` log | no documents matched tags, or upstream extraction/chunking/embedding has not produced records | inspect the document tags and the config-id chain before changing vector-store code. |
| stale chunks appear in search | indexing was bypassed or interrupted before reconciliation | rerun the RAG workflow runner so `delete_nodes_not_in_set()` can clean stale rows. |
| embedding/chunk count mismatch | a `ChunkEmbeddings` object does not align one vector per chunk | regenerate embeddings for that chunked document before indexing. |
| table not initialized | search ran before any successful index write | run the RAG config and confirm indexed chunk counts in `RagProgress`. |
| too many file handles or flaky FTS creation | concurrent LanceDB/FTS index creation | use the existing vector-store locking path; do not add parallel raw LanceDB searches without locks. |

## Extraction problems

| Symptom | Likely cause | Action |
|---|---|---|
| unsupported MIME type | MIME is not in the document validator's supported set | fix the filename/MIME source or add explicit support in the datamodel and API together. |
| passthrough fails on a text file | file is not UTF-8 text or MIME is not exactly in `passthrough_mimetypes` | use UTF-8 fixtures and `text/plain` or `text/markdown` passthrough values. |
| extraction unexpectedly calls a model | passthrough MIME list does not match the actual document MIME | inspect `original_file.mime_type`, not only the extension. |
| PDF extraction is slow | PDFs are split page by page and pages can be processed in parallel | use small fixtures for tests; rely on cache behavior only when a filesystem cache is configured. |
| OpenRouter rejects audio/video extraction | provider requires special audio/video payload shapes | use the existing LiteLLM extractor encoding path rather than hand-building file blocks. |

Paid/provider/Ollama/cloud/Copilot flows require credentials or services and are optional for normal import/static verification. Do not convert missing credentials into a hard skill failure unless the downstream task explicitly requires a live provider.

## Chunking problems

| Symptom | Likely cause | Action |
|---|---|---|
| fixed-window config validation fails | `chunk_overlap >= chunk_size` | reduce overlap or increase chunk size. |
| semantic chunker cannot initialize | missing parent project path or missing embedding config | persist the embedding config under the project before creating the semantic chunker. |
| whitespace-only fixture yields zero chunks | `clean_up_text()` removed all content | assert zero chunks intentionally or use a non-whitespace fixture. |
| chunk count changes after dependency updates | splitter implementation changed | update downstream retrieval expectations only after validating that search relevance remains acceptable. |

## RAG tool and reranker problems

| Symptom | Likely cause | Action |
|---|---|---|
| `Vector store config not found` | `RagConfig.vector_store_config_id` does not resolve under the parent project path | repair the RAG config or recreate it after the vector store config exists. |
| `Embedding config not found` during vector/hybrid search | query embedding config does not resolve | repair `RagConfig.embedding_config_id`; FTS search is the only store type that skips query embeddings. |
| `No embeddings generated` | embedding provider returned no vectors | check provider config, credentials, service status, and dimensions settings. |
| reranker config not found | optional reranker id points to a missing config | remove the reranker id or recreate the reranker config; base search can still work without reranking. |
| tool output is empty string | no search results | check indexing and query preconditions before changing output formatting. |

## Tiny fixture cautions

- Use file extensions that match the MIME being tested.
- Use short but non-empty text for chunking and search fixtures.
- Use deterministic small vectors for vector-store fixtures.
- Keep fixture documents small; provider-backed extraction and embedding should be mocked unless credentials are explicitly supplied.
- Do not treat zero results from an unindexed vector store as proof that retrieval ranking is broken.

## Evidence notes

Source evidence used here includes `libs/core/kiln_ai/adapters/vector_store/lancedb_adapter.py`, `libs/core/kiln_ai/adapters/extractors/base_extractor.py`, `litellm_extractor.py`, `libs/core/kiln_ai/adapters/chunkers/*`, `libs/core/kiln_ai/tools/rag_tools.py`, `libs/server/kiln_server/document_api.py`, and related document/RAG tests.
