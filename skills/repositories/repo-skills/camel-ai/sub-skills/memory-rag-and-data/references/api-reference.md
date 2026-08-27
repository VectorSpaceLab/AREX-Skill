# API Reference

This reference summarizes the CAMEL memory, retrieval, embedding, storage, loader, datahub, and dataset APIs most useful to future coding agents. Confirm exact signatures in the installed package with `../scripts/inspect_rag_components.py` when dependency versions matter.

## Memory APIs

- `ChatHistoryMemory(context_creator, storage=None, window_size=None, agent_id=None)`: wraps `ChatHistoryBlock`; stores chronological chat records in key-value storage; preserves an initial system/developer message when windowing.
- `VectorDBMemory(context_creator, storage=None, retrieve_limit=3, agent_id=None)`: wraps `VectorDBBlock`; embeds user topics and retrieves similar prior records from vector storage; does not support rollback/pop.
- `LongtermAgentMemory(context_creator, chat_history_block=None, vector_db_block=None, agent_id=None)`: combines recent chat history with semantic vector recall when both short-term and long-term context are needed.
- `ChatHistoryBlock(storage=None, keep_rate=0.9)`: `write_records`, `retrieve(window_size=None)`, `clear`, `pop_records`, and `remove_records_by_indices` over `BaseKeyValueStorage`.
- `VectorDBBlock(storage=None, embedding=None)`: defaults to `OpenAIEmbedding` and Qdrant; writes non-empty message content as `VectorRecord(payload=record.to_dict())`.
- `MemoryRecord(message, role_at_backend, uuid=..., timestamp=..., agent_id='', extra_info=None)`: serializable memory unit with `to_dict`, `from_dict`, and OpenAI-message conversion helpers.
- `ScoreBasedContextCreator(token_counter, token_limit)`: creates token-bounded context from scored `ContextRecord` values; pair it with a token counter matching the target model.

## Attaching Memory To Agents

`ChatAgent` accepts `memory=` in its constructor and also exposes `agent.memory` assignment. For persisted chat memory, use `ChatHistoryMemory` with `JsonStorage` or use `agent.save_memory(path)` and `agent.load_memory_from_path(path)` when the full agent memory format is desired. If using multiple agents, set `agent_id` so records can be attributed and filtered consistently.

## Retriever APIs

- `VectorRetriever(embedding_model=None, storage=None)`: defaults to `OpenAIEmbedding()` and Qdrant. `process(content, chunk_type='chunk_by_title', max_characters=500, embed_batch=50, should_chunk=True, extra_info=None, metadata_filename=None, chunker=None, **kwargs)` parses/chunks content and stores embeddings. `query(query, top_k=..., similarity_threshold=...)` returns dictionaries with similarity, content path, metadata, extra info, and text.
- `AutoRetriever(url_and_api_key=None, vector_storage_local_path=None, storage_type=None, embedding_model=None)`: one-call RAG helper. `run_vector_retriever(query, contents, top_k=..., similarity_threshold=..., return_detailed_info=False, max_characters=500)` initializes storage per content and runs ingestion/query.
- `HybridRetriever(embedding_model=None, vector_storage=None)`: combines `VectorRetriever` and `BM25Retriever`; `process(content_input_path)` ingests both; `query(..., vector_weight=0.8, bm25_weight=0.2, rank_smoothing_factor=60, ...)` fuses results using reciprocal rank fusion.
- `BM25Retriever`: keyword retrieval using rank-bm25; useful for exact terms and deterministic small corpora.
- `JinaRerankRetriever` and `CohereRerankRetriever`: hosted rerankers; require provider credentials and should be guarded in CI.

## Embedding APIs

All embedding classes implement `embed(obj)`, `embed_list(objs)`, and `get_output_dim()` through `BaseEmbedding`.

- `OpenAIEmbedding(model_type=TEXT_EMBEDDING_3_SMALL, url=None, api_key=None, dimensions=NOT_GIVEN)`: reads `OPENAI_API_KEY` and optional base URL; `dimensions` can override output size for compatible models.
- `OpenAICompatibleEmbedding(model_type, api_key=None, url=None, output_dim=None)`: use for OpenAI-compatible servers; set output dimension explicitly if the backend cannot report it.
- `AzureEmbedding(model_type, url=None, api_key=None, api_version=None, dimensions=NOT_GIVEN)`: Azure OpenAI text embeddings.
- `MistralEmbedding`, `GeminiEmbedding`, `JinaEmbedding`, `TogetherEmbedding`: provider-specific text embeddings; require matching API keys.
- `SentenceTransformerEncoder(model_name='intfloat/e5-large-v2', **kwargs)`: local sentence-transformers embeddings; useful for offline CI fixtures but model download/cache may still be needed.
- `VisionLanguageEmbedding(model_name=...)`: multimodal/image embeddings; keep separate from text-only vector collections unless dimensions and payload schema are explicit.

## Vector Storage APIs

Use `VectorRecord(vector, id=..., payload=None)`, `VectorDBQuery(query_vector, top_k)`, and `VectorDBQueryResult(record, similarity)` across vector stores. Each backend implements `add(records)`, `query(query, **kwargs)`, `delete(ids, **kwargs)`, `status()`, `clear()`, `load()`, and a `client` property.

- `QdrantStorage(vector_dim, collection_name=None, url_and_api_key=None, path=None, distance=VectorDistance.COSINE, delete_collection_on_del=False, **kwargs)`: in-memory by default, local persistent with `path`, remote with `(url, api_key)`. Existing collection dimensions must match.
- `ChromaStorage(vector_dim, collection_name=None, client_type='ephemeral', path='./chroma', host='localhost', port=8000, ssl=False, headers=None, api_key=None, tenant=None, database=None, distance=..., **kwargs)`: use `ephemeral` for tests, `persistent` for local disk, `http`/`cloud` for services.
- `FaissStorage(vector_dim, index_type='Flat', collection_name=None, storage_path=None, distance=VectorDistance.COSINE, nlist=100, m=16, **kwargs)`: local vector index; exact `Flat` is safest for tests; persistent only when `storage_path` is set.
- `MilvusStorage(vector_dim, url_and_api_key, collection_name=None, **kwargs)`, `TiDBStorage(vector_dim, collection_name, url_and_api_key, **kwargs)`, `PgVectorStorage(vector_dim, conn_info, table_name, distance=..., **kwargs)`, `WeaviateStorage(...)`, `SurrealStorage(...)`, and `OceanBaseStorage(...)`: production/service-oriented stores; require backend packages and connection settings.

## Key-Value, Object, And Graph Storage APIs

- `InMemoryKeyValueStorage()`: transient dict/list store for tests and short-lived memory.
- `JsonStorage(path)`: persistent JSON file store; good for local chat memory and small records.
- `RedisStorage(sid, url, loop=None, **kwargs)`: Redis-backed key-value storage; requires network/service availability.
- `Mem0Storage(agent_id=None, api_key=None, user_id=None, metadata=None)`: hosted memory storage; requires Mem0 credentials.
- `AmazonS3Storage(bucket_name, create_if_not_exists=False, access_key_id=None, secret_access_key=None, anonymous=False)`, `AzureBlobStorage(...)`, `GoogleCloudStorage(...)`: object storage for files/blobs, not vector search.
- `Neo4jGraph(url, username, password, database='neo4j', timeout=None, truncate=False)` and `NebulaGraph(host, username, password, space, port=9669, timeout=...)`: graph stores with `get_schema`, `refresh_schema`, `add_triplet`, `delete_triplet`, and `query`.

## Loader APIs

- `create_file_from_raw_bytes(raw_bytes, filename)` and `create_file(BytesIO, filename)`: parse supported local file types into `File(name, file_id, metadata, docs, raw_bytes)` where `docs` contains dictionaries such as `{'page_content': ...}`.
- `UnstructuredIO.create_element_from_text(text, ...)`: create an in-memory `Element` for no-network tests and RAG fixtures.
- `UnstructuredIO.parse_file_or_url(input_path, **kwargs)` and `parse_bytes(file, **kwargs)`: parse files/URLs into unstructured elements; URL mode is networked.
- `UnstructuredIO.clean_text_data`, `extract_data_from_text`, `chunk_elements`, and `stage_elements`: clean/chunk/stage extracted elements for retrieval payloads.
- `MarkItDownLoader(llm_client=None, llm_model=None)`: convert files to Markdown with `convert_file` or `convert_files`; supports many document/media formats when optional package constraints are satisfied.
- `Apify`, `ChunkrReader`, `Crawl4AI`, `Firecrawl`, `JinaURLReader`, `MinerU`, `MistralReader`, and `ScrapeGraphAI`: API-backed or browser/network loaders; require credentials, external services, or heavier runtime dependencies.

## Datahub And Dataset APIs

- `HuggingFaceDatasetManager(token=None)`: hub-oriented dataset operations; use for authorized Hugging Face workflows, not offline tests unless cached data is available.
- `StaticDataset(data, seed=None, min_samples=..., strict=..., **kwargs)`: wrap fixed examples for deterministic generation/testing.
- `FewShotGenerator(seed_dataset, verifier, model=None, seed=None, **kwargs)` and `SelfInstructGenerator(seed_dataset, verifier, instruction_agent=None, rationale_agent=None, seed=None, **kwargs)`: synthetic-data generation surfaces; cross-link to the datagen/evaluation sub-skill for full generation pipelines.

## Data Schemas To Validate

- Vector payloads from `VectorRetriever.process` should include `text`, `metadata`, `extra_info`, and `content path` when generated by the built-in retriever.
- Manual vector records should use `VectorRecord(vector=list[float], payload=dict)` with vector length equal to storage `vector_dim`.
- Loader `File.docs` should be a list of dictionaries with `page_content`; preserve source metadata under `metadata` rather than mixing it into text.
- Memory payloads should round-trip through `MemoryRecord.to_dict()` and `MemoryRecord.from_dict()` before being stored in JSON or vector storage.
