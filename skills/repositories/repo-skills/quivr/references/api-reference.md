# API Reference

This file distills the live public APIs that matter most for the Quivr skill.
Use the root `SKILL.md` to choose the right sub-skill, then use this reference
for exact object names and signatures.

## Brain

### Construction

- `await Brain.afrom_langchain_documents(name, langchain_documents, vector_db=None, storage=TransparentStorage(), llm=None, embedder=None)`
- `await Brain.afrom_files(name, file_paths, vector_db=None, storage=TransparentStorage(), llm=None, embedder=None, skip_file_error=False, processor_kwargs=None)`
- `Brain.from_files(...)` is the synchronous wrapper around `afrom_files(...)`.

### Retrieval and QA

- `await Brain.asearch(query, n_results=5, filter=None, fetch_n_neighbors=20) -> list[SearchResult]`
- `await Brain.aask(run_id, question, system_prompt=None, retrieval_config=None, rag_pipeline=None, list_files=None, chat_history=None, **input_kwargs) -> ParsedRAGResponse`
- `async for chunk in Brain.ask_streaming(run_id, question, system_prompt=None, retrieval_config=None, rag_pipeline=None, list_files=None, chat_history=None, **input_kwargs)`
- `Brain.ask(run_id, question, ...)` is the synchronous wrapper around `aask(...)`.

### Introspection and persistence

- `Brain.info() -> BrainInfo`
- `Brain.print_info()` prints the brain tree.
- `await Brain.save(folder_path)` serializes a brain to `brain_<id>/config.json` plus the vector store.
- `Brain.load(folder_path)` reconstructs a brain from the saved config and storage.

## Ingestion primitives

- `load_qfile(brain_id, path)` creates a `QuivrFile` from a path and computes metadata.
- `QuivrFile.metadata` includes `original_file_name`, `qfile_path`, `file_sha1`, and `file_size`.
- `SimpleTxtProcessor(splitter_config=SplitterConfig())` is the safe text processor.
- `await SimpleTxtProcessor.process_file(file) -> ProcessedDocument`
- `ProcessedDocument.chunks` is the list of `langchain_core.documents.Document` chunks.
- `SplitterConfig(chunk_size=400, chunk_overlap=100)` controls character-based splitting.

## Storage

- `TransparentStorage()` keeps files in memory and is the safest default for smoke checks.
- `LocalStorage(dir_path=None, copy_flag=True)` stores files on disk and defaults to `QUIVR_LOCAL_STORAGE` or `~/.cache/quivr/files`.
- `StorageBase` is the common abstraction behind storage implementations.

## Chat and retrieval

- `ChatHistory(chat_id, brain_id)` stores alternating human/AI messages.
- `ChatHistory.append(...)`, `get_chat_history(...)`, `iter_pairs()`, and `to_list()` are the key helpers.
- `RetrievalConfig(...)` collects RAG, reranker, workflow, and LLM settings.
- `WorkflowConfig(...)` validates node graphs and tool availability.
- `RerankerConfig(...)` resolves the reranker supplier and requires the matching API key when a supplier is selected.
- `LLMEndpointConfig(...)` stores the LLM provider, model, base URL, key, and token budget.
- `LLMEndpoint.from_config(config)` builds the provider-specific chat model wrapper.
- `LLMEndpoint.supports_func_calling()` reflects the model-name heuristic used by the RAG layer.
- `QuivrKnowledge`, `SearchResult`, `ParsedRAGResponse`, `ParsedRAGChunkResponse`, and `RAGResponseMetadata` are the main data objects returned by QA and search paths.

## Lower-level RAG engines

- `QuivrQARAG(retrieval_config, llm, vector_store, reranker=None)` provides the older synchronous/streaming RAG interface.
- `QuivrQARAGLangGraph(retrieval_config, llm, vector_store=None)` provides the graph-based pipeline used by the brain QA path.
- `QuivrQARAGLangGraph.answer_astream(...)` is the streaming engine behind `Brain.ask_streaming`.
- `model_supports_function_calling(model_name)` is the helper that decides whether tool-calling is available.
