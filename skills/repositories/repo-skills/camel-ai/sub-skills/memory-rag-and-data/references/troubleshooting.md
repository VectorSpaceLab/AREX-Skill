# Troubleshooting

Use this when memory, retrieval, storage, loader, or dataset code fails or returns surprising results.

## Optional Extras Are Missing

Symptoms:

- `ImportError` from `qdrant_client`, `chromadb`, `faiss`, `unstructured`, `rank_bm25`, `neo4j`, `nebula3`, `redis`, `markitdown`, `docx2txt`, `fitz`, or cloud SDKs.
- CAMEL dependency wrappers report that a dependency is required.

Fixes:

- Install the narrow extra that matches the workflow: `pip install 'camel-ai[rag]'`, `pip install 'camel-ai[storage]'`, or `pip install 'camel-ai[document_tools]'`.
- Avoid installing every extra unless the environment is disposable and broad dependency changes are acceptable.
- Run `scripts/inspect_rag_components.py --json` to list installed optional modules without making network calls.

## Python 3.13 Loader/Storage Caveats

CAMEL metadata allows Python `>=3.10,<3.15`, but some optional packages are version-gated:

- `unstructured==0.16.20` is constrained to Python `<3.13` in RAG/document extras.
- `pyobvector` and related OceanBase/SQL parsing dependencies are constrained to Python `<3.13`.
- `markitdown` is included for Python `>=3.13` under `document_tools`.

If a Python 3.13 environment cannot import `UnstructuredIO`, prefer `MarkItDownLoader`, `BaseIO` file parsing, or a lower-Python ingestion environment for unstructured parsing.

## Vector Dimension Mismatch

Symptoms:

- Qdrant reports an existing collection dimension differs from the embedding dimension.
- Vector DB add/query fails with shape/dimension errors.
- Retrieval returns nonsense after changing embedding providers.

Fixes:

- Always set `vector_dim=embedding.get_output_dim()`.
- Name persistent collections with embedding family and dimension.
- Never mix embeddings with different output dimensions in one collection.
- Re-embed source chunks into a new collection when changing model or dimensions.
- For OpenAI embeddings, remember that `dimensions=` can change output size for supported models.

## Missing Embedding Credentials

Symptoms:

- `OpenAIEmbedding`, `MistralEmbedding`, `GeminiEmbedding`, `JinaEmbedding`, `TogetherEmbedding`, or hosted rerankers fail during initialization or first call.
- Local tests accidentally attempt hosted embedding calls.

Fixes:

- Use environment variables or application config for provider keys; do not hard-code keys in skill content or payloads.
- For CI, inject a deterministic fake `BaseEmbedding` or use a cached local `SentenceTransformerEncoder` only when model artifacts are available.
- Construct embeddings lazily in code paths that actually need them so non-RAG commands can run without credentials.

## Persistent Vs In-Memory Storage Confusion

Symptoms:

- Records disappear after process restart.
- Tests contaminate each other through reused local collection paths.
- Remote collections retain stale chunks.

Fixes:

- For Qdrant, no `path` and no remote URL means in-memory; `path` means local persistent; `url_and_api_key` means remote.
- For Chroma, `client_type='ephemeral'` is in-memory, `persistent` uses local disk, and `http`/`cloud` uses a service.
- For FAISS, persistence requires `storage_path`.
- Clear or delete test collections explicitly; do not depend only on object destructors.
- Use unique collection names per test run when remote services are unavoidable.

## Loader API Keys Or Network Failures

Symptoms:

- Web/API loaders return empty content, HTTP errors, auth errors, or timeouts.
- Tests fail offline.

Fixes:

- Keep tests on local files, raw bytes, or in-memory text elements.
- Treat `Apify`, `Firecrawl`, `JinaURLReader`, `ChunkrReader`, `MistralReader`, `MinerU`, `Crawl4AI`, and `ScrapeGraphAI` as integration paths requiring explicit credentials/network permission.
- Validate source permissions, API key names, rate limits, and response schema before embedding content.
- Store loader name, URL/file name, and extraction timestamp/version in metadata.

## Graph DB Connection Or Auth Fails

Symptoms:

- `Neo4jGraph` or `NebulaGraph` initialization fails.
- Schema is empty or stale.
- Triplet add/delete/query commands silently hit the wrong database/space.

Fixes:

- Verify URL/host/port, username, password, database/space, and network access outside the agent workflow.
- Call `refresh_schema()` after schema changes.
- Use small non-destructive `query` probes before adding triplets.
- Keep graph credentials in environment/application config, not in prompts or persisted memory.

## Token Budget And Context Creator Issues

Symptoms:

- Agent responses ignore older memory.
- `memory.get_context()` drops records unexpectedly.
- Long tool traces consume the context budget.

Fixes:

- Use a token counter aligned with the target model and set `token_limit` below the full model limit to leave space for new prompts and completions.
- Increase `window_size` or switch from pure chat history to vector/long-term memory when older facts matter.
- Use `clean_tool_calls()` for chat memory when tool/function messages do not need to be retained.
- Inspect `(context, token_count)` before passing memory to a live agent.

## Retrieval Returns Empty Results

Symptoms:

- `VectorRetriever.query` raises `ValueError: Query result is empty`.
- Query result payload is `None`.
- Hybrid retrieval returns irrelevant or duplicate snippets.

Diagnosis:

1. Check ingestion did not produce zero elements or chunks.
2. Check `storage.status().vector_count` after `process` or `add`.
3. Query with exact text known to exist in the fixture.
4. Temporarily lower `similarity_threshold` to `0.0`.
5. Print payload keys and confirm every record has a non-empty `text` field.
6. Confirm embedding dimensions and collection name match the current run.
7. For hybrid retrieval, inspect vector and BM25 results separately before fusion.

Fixes:

- Adjust chunking: set `should_chunk=False` for short fixtures or increase `max_characters` for fragmented documents.
- Preserve metadata and `content path` so retrieved chunks can be traced.
- Rebuild the vector collection after changing loaders, chunkers, embeddings, or filters.
- Use explicit payload filters only after unfiltered retrieval works.

## Loader Produces No Documents

Symptoms:

- `UnstructuredIO.parse_file_or_url` returns `[]` or warns.
- `create_file_from_raw_bytes` raises unsupported type or missing dependency.
- `MarkItDownLoader.convert_file` raises file-not-found, unsupported format, or conversion errors.

Fixes:

- Confirm file exists and extension is supported.
- For BaseIO, install the document parsing dependency required by the extension.
- For UnstructuredIO, verify Python version and `unstructured` availability.
- For MarkItDown, check `MarkItDownLoader.SUPPORTED_FORMATS` and use `skip_failed=True` for batch conversion when partial success is acceptable.
- For URL parsing, separate network fetch failures from parser failures.

## Reranker Problems

Symptoms:

- Jina/Cohere reranker imports or calls fail.
- Results are slower or different from base vector retrieval.

Fixes:

- Validate provider credentials and model names.
- Keep reranking optional; preserve a non-reranked retrieval path for CI and fallback.
- Log pre-rerank and post-rerank result IDs/scores when debugging ranking changes.

## Dataset/Datahub Issues

Symptoms:

- Hugging Face access fails due to auth/cache/network.
- Generated samples are missing fields or fail verifier checks.

Fixes:

- Use local `StaticDataset` fixtures when network is not explicitly allowed.
- Define required row fields and types before generation.
- Validate a small sample before running larger generation.
- Route complex datagen/evaluation loops to the sibling datagen/evaluation sub-skill.
