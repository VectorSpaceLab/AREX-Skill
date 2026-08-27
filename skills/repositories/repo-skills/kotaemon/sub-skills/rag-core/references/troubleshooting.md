# Kotaemon RAG Core Troubleshooting

Use this guide for programmatic RAG failures after imports succeed. If the failure is about app startup, provider credentials, local model servers, parser dependencies, or UI configuration, route to the relevant sibling skill instead of patching RAG core.

## Fast Triage

1. Run the inspector: `python skills/kotaemon/sub-skills/rag-core/scripts/inspect_pipeline_components.py --repo-root <repo-root>`.
2. Confirm the class exists and whether inspection used `import` or `ast` mode.
3. Identify the failing layer: schema, component invocation, indexing, vectorstore, docstore, retrieval, reranking, evidence formatting, QA/citation, prompt template, or reasoning helper.
4. Build a provider-free reproduction with fake embeddings or fake QA before changing provider configuration.
5. Preserve and print `doc_id`, `score`, `metadata`, and `retrieval_metadata` across each step.

## Provider Object Missing

Symptoms:

- A class has a `Node(default_callback=...)` that tries to access app-level managers.
- QA classes fail while looking up default LLMs.
- `BaseLLM.invoke`, `BaseLLM.stream`, or provider-specific methods raise `NotImplementedError`.

Likely cause:

- The component expects an explicit provider object or a running ktem app context. Core code does not create API credentials or local model servers.

Fix:

- Pass explicit `llm`, `embedding`, `citation_pipeline`, or `qa_pipeline` objects during construction.
- For core tests, use deterministic fake embeddings or fake QA components.
- For API keys, endpoint URLs, local model compatibility, or concrete provider constructor details, route to `model-providers`.

## Embedding and Vectorstore Mismatch

Symptoms:

- Vectorstore query returns no ids or unexpected ids.
- Similarity scores are empty or inconsistent.
- Vectorstore complains about dimensions, ids, or node types.
- Retrieval fails after indexing appeared to succeed.

Checks:

- Confirm `embedding(text)` returns `list[DocumentWithEmbedding]` with vector lengths matching stored vectors.
- Confirm `VectorIndexing` and `VectorRetrieval` share the same embedding object or compatible embedding dimensions.
- Confirm `vector_store.add(..., ids=[doc.doc_id])` and `doc_store.add(docs)` use the same ids.
- Confirm `vector_store.query(...)` returns `(embeddings, scores, ids)` in that order.
- Check whether a concrete vectorstore normalizes vectors or requires UUID ids.

Fix:

- Use stable `Document(id_=...)` values when debugging.
- Re-index after changing embedding models or vector dimensions.
- Use a tiny in-memory reproduction before trying Chroma, LanceDB, Milvus, or Qdrant.
- If a provider-backed embedding class fails to initialize, route provider setup to `model-providers`.

## Empty Retrieval

Symptoms:

- `VectorRetrieval(...)` returns `[]`.
- Hybrid mode prints zero vectorstore/docstore hits.
- Text mode returns no results with `InMemoryDocumentStore`.

Checks:

- `doc_store` must be present; `VectorRetrieval` raises when it is missing.
- `doc_store.count()` should match indexed document count.
- Query `scope` should contain ids that exist in both stores.
- `top_k` should be greater than zero.
- `retrieval_mode="text"` requires a docstore with real text search; in-memory docstore `query(...)` returns an empty list.
- `do_extend=True` multiplies the first round by `first_round_top_k_mult`, but final output is still filtered to `top_k`.

Fix:

- Start with `retrieval_mode="vector"` and no `scope`.
- Print raw vectorstore ids/scores directly before `VectorRetrieval` post-processing.
- Remove rerankers temporarily; `LLMReranking` can filter aggressively, though it falls back to first `top_k` when all are rejected.
- Check thumbnail metadata only after text documents retrieve correctly.

## Metadata Lost

Symptoms:

- QA output lacks source names or page labels.
- Citations cannot map back to documents.
- Evidence shows `Content from -`.
- `RetrievedDocument` objects have scores but missing metadata.

Likely cause:

- A custom component created new `Document` objects without copying metadata.
- The vectorstore stored embeddings but the docstore did not store full documents.
- The embedding wrapper returned new documents without preserving ids/metadata.

Fix:

- Prefer `RetrievedDocument(**doc.to_dict(), score=doc.score)` when cloning retrieved docs.
- Explicitly copy `metadata` and `retrieval_metadata` in filters/rerankers.
- Store full source docs in `doc_store`, not only vectors.
- Keep `file_name`, `page_label`, `section`, `type`, `window`, `table_origin`, and `image_origin` when they are relevant to QA.

## Low-Confidence or Missing Citation

Symptoms:

- `answer.metadata["citation"]` is `None`.
- `answer.metadata["qa_score"]` is `None` or very low.
- Cited spans cannot be found in retrieved documents.
- Cited docs are lower-scoring than uncited docs.

Checks:

- `CitationPipeline` returns `None` when tool-call parsing or provider invocation fails.
- `qa_score` is derived from token logprobs when available; many providers do not return logprobs.
- Inline citations require exact copied start/end phrases.
- `PrepareEvidencePipeline` may trim long evidence; confirm the cited phrase remains after trimming.
- Table/image/chatbot metadata changes evidence formatting and mode.

Fix:

- Compare citation quotes or inline start/end phrases against `doc.text`, not just rendered HTML.
- Increase `max_context_length` or provide a custom trim function for debugging.
- Log retrieval scores, reranker scores, and final evidence text together.
- If citation extraction relies on unsupported tool calling for the provider, route provider compatibility to `model-providers` or disable citation for the reproduction.

## Prompt Template Variable Mismatch

Symptoms:

- `ValueError: Missing keys in template: ...`.
- Warnings about keys provided but not in template.
- Template placeholders such as `{0day}` warn or raise.

Checks:

- Inspect `PromptTemplate(...).placeholders`.
- Confirm `BasePromptComponent` attributes include every placeholder.
- Confirm values are supported types: string, int, `Document`, or callable returning one of those.
- Use `partial_populate(...)` only when unresolved placeholders are intended.

Fix:

- Rename placeholders to valid Python identifiers.
- Pass exact kwargs expected by the template.
- Keep `safe=True` during development to fail fast.
- When combining templates with `+`, re-check the merged placeholder set.

## Optional Reranker Missing

Symptoms:

- Import fails for a reranking module.
- Reranker constructor needs a provider, SDK, or API key.
- Retrieval works until `rerankers=[...]` is added.

Checks:

- `BaseReranking` is provider-agnostic; concrete rerankers may not be.
- `LLMReranking` and `LLMScoring` need an LLM object and may require logprobs.
- Third-party rerankers can require optional packages.

Fix:

- Remove rerankers and confirm base retrieval first.
- Use a small deterministic `BaseReranking` subclass for local tests.
- Add provider-backed rerankers only after the LLM/provider path is validated through `model-providers`.
- Preserve document metadata and scores when reranking.

## `BaseComponent.run` vs Callable Invocation

Symptoms:

- Calling `run(...)` works but normal component execution behaves differently.
- Calling `invoke(...)` raises `NotImplementedError`.
- Streamed QA returns chunks but direct invocation fails.

Rules:

- Implement `run(...)` in custom `BaseComponent` subclasses.
- Call `component(...)` for normal execution through TheFlow.
- Use `invoke(...)` only when the concrete class implements it.
- Use `stream(...)` for QA classes whose `invoke(...)` is intentionally not implemented.
- Do not rely on `flow()` unless `inflow` is set to another `BaseComponent`.

Fix:

- Inspect the concrete class for implemented methods with the bundled inspector.
- Replace `component.run(...)` with `component(...)` in normal pipelines unless you are deliberately bypassing middleware.
- Replace `component.invoke(...)` with `component(...)` if `invoke` is not implemented.

## QA Evidence Mode Confusion

Symptoms:

- Text question gets image or table prompt.
- Figure answers ignore images.
- Table markup leaks into answer unexpectedly.

Checks:

- `PrepareEvidencePipeline` chooses figure mode if any image evidence exists, then table mode if any table exists, otherwise text.
- It reads `metadata["type"]` to choose table/chatbot/image handling.
- Image evidence uses `image_origin` and captions from document content.

Fix:

- Normalize `metadata["type"]` before QA.
- Separate text/table/image retrieval paths if mixed evidence hurts answer quality.
- For parser-specific metadata issues, route to `document-ingestion`.

## Inspector Problems

Symptoms:

- The inspector reports AST mode for many modules.
- Imports fail with optional dependency errors.
- A module is listed as missing.

Interpretation:

- AST mode is acceptable for skill usage; it means the script avoided executing a module whose imports are unavailable or unsafe in the current environment.
- Missing modules can indicate repo layout drift or a changed package structure.

Fix:

- Use `--module` to inspect a narrower module list.
- Use `--json` for machine-readable class/function inventories.
- Add `--import-mode never` when you only want AST inspection.
- If public classes moved, update API references before relying on old import paths.

## When to Route Away

- App launch, Docker, Gradio auth, PDF.js, migration, or environment variables: `app-deployment`.
- API keys, endpoint URLs, local model servers, provider SDK versions, embedding provider credentials, reranker provider credentials, GraphRAG providers: `model-providers`.
- PDF/table/OCR/docx/html/xlsx/txt/web loading, splitters, parser optional dependencies, malformed source document metadata: `document-ingestion`.
- ktem custom pages, extensions, templates, component registration, project scaffolding: `extensions`.
