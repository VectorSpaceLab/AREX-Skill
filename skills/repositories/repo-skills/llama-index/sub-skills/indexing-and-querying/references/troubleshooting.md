# Indexing and Querying Troubleshooting

## Missing Embedding Model

Symptoms:

- Index construction fails while embedding documents or nodes.
- Retrieval fails when the vector store query mode requires embeddings.
- The code unexpectedly tries to use a remote provider.

Fixes:

- Set `Settings.embed_model` before constructing a `VectorStoreIndex`.
- Or pass `embed_model=...` to `VectorStoreIndex(...)`, `VectorStoreIndex.from_vector_store(...)`, or `VectorIndexRetriever(...)`.
- For local smoke tests, use `MockEmbedding(embed_dim=...)`.
- For text-only retrieval modes, confirm the active vector store supports the chosen mode before assuming embeddings are unnecessary.

## Missing LLM or API Key

Symptoms:

- `as_query_engine` retrieval works but response synthesis fails.
- Router, fusion query generation, sub-question decomposition, or summarization fails.
- Errors mention provider credentials even though indexing succeeded.

Fixes:

- Set `Settings.llm` or pass `llm=...` explicitly to query engines, synthesizers, routers, and fusion retrievers.
- For retrieval debugging, use `response_mode="no_text"` or call `retriever.retrieve(...)` to avoid synthesis.
- For no-network tests, use `MockLLM` and keep `QueryFusionRetriever(num_queries=1)` unless testing query generation.

## Constructor Receives Documents Instead of Nodes

Symptoms:

- `VectorStoreIndex(documents)` or `VectorStoreIndex(nodes=documents)` raises a message saying constructors now take node objects.

Fixes:

- Use `VectorStoreIndex.from_documents(documents)` for `Document` objects.
- Use `VectorStoreIndex(nodes=nodes)` only after documents have been transformed into `BaseNode` objects.
- Route loading, parsing, chunking, and transformation choices to `ingestion-and-loading`.

## Persistence Path Confusion

Symptoms:

- `load_index_from_storage` raises `No index in storage context`.
- Reloaded retrieval differs from pre-persist retrieval.
- Multiple index error appears during reload.

Fixes:

- Persist with `index.storage_context.persist(persist_dir=...)` or the exact `storage_context` used to build the index.
- Reload with `StorageContext.from_defaults(persist_dir=same_dir)`.
- If more than one index was persisted, set stable ids with `index.set_index_id(...)`, persist after setting ids, then call `load_index_from_storage(storage_context, index_id=...)`.
- Do not mix an old local storage directory with a newly created external vector-store collection unless they intentionally describe the same indexed nodes.

## Vector Store Stores Text vs Nodes

Symptoms:

- Retrieval returns ids but cannot reconstruct text nodes.
- Reloaded index has missing source nodes.
- `VectorStoreIndex.from_vector_store(...)` raises because the vector store does not store text.

Fixes:

- If the vector store has `stores_text=False`, persist the docstore and index store with the vector store boundary.
- Use `store_nodes_override=True` when building if you want nodes recorded locally even when the vector store stores text.
- Only use `VectorStoreIndex.from_vector_store(vector_store)` with vector stores that store text.
- Provider-specific vector-store setup belongs in `integrations-and-storage`; this sub-skill owns the LlamaIndex storage boundary pattern.

## Empty Retrieval Results

Symptoms:

- `retriever.retrieve(...)` returns `[]`.
- Query engine response has no sources or generic empty-context behavior.

Diagnosis checklist:

- Confirm documents/nodes were non-empty before indexing.
- Inspect `len(index.index_struct.nodes_dict)` for vector indexes or stored node ids for summary indexes.
- Temporarily increase `similarity_top_k`.
- Remove `filters`, `doc_ids`, and `node_ids`; add them back one at a time.
- Use `response_mode="no_text"` to separate retrieval from synthesis.
- Verify the query text matches the indexed language/domain and the embedding model used at query time matches the one used at index time.

## `similarity_top_k` and Filter Misuse

Symptoms:

- Too few or zero nodes return after adding filters.
- Hybrid search parameters appear ignored.
- Backend-specific errors mention unsupported filters or query modes.

Fixes:

- Treat `similarity_top_k` as the final candidate count requested from the retriever, not as a guarantee after filters/postprocessors.
- Ensure metadata keys and values exist on nodes before indexing.
- Use `MetadataFilters` / `MetadataFilter` objects for standard filters.
- Use hybrid knobs such as `alpha`, `sparse_top_k`, and `hybrid_top_k` only with vector stores that document support for those modes.
- Pass backend-specific query options through `vector_store_kwargs={...}`.

## Router Tool Metadata Errors

Symptoms:

- Router chooses the wrong retriever/query engine.
- Selector errors mention missing or malformed tool metadata.
- `SubQuestionQueryEngine` cannot map generated sub-questions to tools.

Fixes:

- Wrap targets with `RetrieverTool.from_defaults(...)` or `QueryEngineTool.from_defaults(...)`.
- Give every tool a unique `name`; sub-question routing uses tool metadata names as keys.
- Write descriptions with domain, data source, strengths, and exclusions.
- Avoid vague descriptions like `answers questions`; selectors need discriminating metadata.
- For deterministic tests, pass an explicit selector or question generator instead of relying on provider defaults.

## Query Fusion Issues

Symptoms:

- Fusion calls an LLM unexpectedly.
- Async retrieval fails or sync methods are called in the wrong context.
- Result scores look unintuitive.

Fixes:

- Set `num_queries=1` to disable generated query variants.
- Pass `llm=...` when `num_queries > 1`.
- Set `use_async=False` in sync-only environments.
- Try `mode="reciprocal_rerank"` for rank-based fusion or `mode="relative_score"` for score-normalized fusion.
- Verify `retriever_weights` length matches the number of retrievers; weights are normalized internally.

## Router and Sub-Question Async/Synthesis Problems

Symptoms:

- `AsyncStreamingResponse not supported in sync code` from router combination.
- Nested event-loop or async execution errors.
- Sub-question execution drops failed sub-questions and produces incomplete final answers.

Fixes:

- Align `use_async` between sub-question engines, synthesizers, and the runtime environment.
- Avoid sync router combination over async streaming responses; use async query paths or disable streaming.
- For `SubQuestionQueryEngine.from_defaults`, pass `use_async=False` in simple scripts and notebooks that already manage event loops poorly.
- Inspect verbose sub-question output to find failed tool names or bad decomposition.

## Response Mode Problems

Symptoms:

- Context window errors in summarization.
- Too many LLM calls or slow responses.
- Retrieved nodes are good but final answer ignores them.

Fixes:

- Use `compact` for a balanced default.
- Use `tree_summarize` for broad summarization or combining router multi-select outputs.
- Avoid `simple_summarize` on large retrieved contexts.
- Use `no_text` or `context_only` to debug retrieval without answer generation.
- If structured outputs are needed, route prompt/output schema design to `customization-and-structured-outputs`.

## Optional Vector-Store Dependency Failures

Symptoms:

- Imports for a provider vector store fail, but `llama_index.core` imports fine.
- Errors mention missing database clients, cloud SDKs, or integration packages.

Fixes:

- Keep core index/query code provider-neutral until the integration dependency is installed.
- Use `SimpleVectorStore` or default in-memory storage for local smoke tests.
- Route package installation, credentials, collection creation, and provider-specific persistence to `integrations-and-storage`.
- After provider setup, return to this sub-skill for `StorageContext`, index construction, retriever, query engine, and reload patterns.
