# Retrieval and RAG Troubleshooting

## Install and import failures

- `ModuleNotFoundError: haystack`: install the `haystack-ai` distribution in the active Python environment and import with `import haystack`.
- Wrong package installed: avoid legacy package names; verify `python -c "import haystack; print(haystack.__version__)"` reports the expected Haystack 2 version.
- In the Haystack repo checkout, use Hatch-managed commands from the repository instructions rather than bare `python` or `pip`.

## Optional dependency failures

- Transformer readers/rankers and sentence-transformer embedders can require optional packages such as torch, transformers, sentencepiece, accelerate, or sentence-transformers.
- `ExtractiveReader` raises an import hint for `transformers[torch,sentencepiece]` if optional dependencies are unavailable.
- Provider-backed generators, hosted embedding APIs, and TEI rankers may need separate integration packages or reachable services. Prove retrieval locally before adding them.

## Credential and backend issues

- RAG retrieval should not require generator credentials; if credentials fail, replace the generator with a local placeholder and confirm `retriever.documents` first.
- Hugging Face private models require `HF_API_TOKEN` or `HF_TOKEN` through Haystack `Secret` handling; do not hard-code tokens.
- External document stores have their own connectivity, schema, and persistence requirements. Reproduce with `InMemoryDocumentStore` to isolate Haystack pipeline wiring from backend setup.

## API misuse

- `top_k must be greater than 0`: set positive `top_k` on retrievers, joiners, and rankers.
- `document_store must be an instance of InMemoryDocumentStore`: in-memory retrievers only work with `InMemoryDocumentStore`; use integration-specific retrievers for other stores.
- Empty BM25 query: pass non-empty query strings.
- Wrong run input name: BM25 uses `query`; embedding retrieval uses `query_embedding`; `FilterRetriever` uses `filters`; readers use `query` and `documents`.
- `FilterPolicy.MERGE` only shallow-merges dictionaries. For complex filters, build the full final filter explicitly.
- `DocumentJoiner` `weights` must match the number of input document lists for weighted modes and must not sum to zero.

## Data and configuration problems

- Empty store: check `count_documents()` immediately after writing.
- Duplicate IDs: choose `DuplicatePolicy.SKIP`, `OVERWRITE`, or `FAIL` intentionally; do not rely on default behavior in retryable ingestion.
- No documents from filters: run `store.filter_documents(filters)` and verify field paths such as `meta.lang` versus `lang`.
- BM25 misses expected docs: ensure document `content` is text, query tokens overlap after lowercasing/tokenization, and the target docs were written to the same `index`.
- Embedding retrieval misses expected docs: verify each document has an embedding, query and document vectors have the same length, the same model family was used, and `embedding_similarity_function` matches the model recommendation.
- Unexpected shared state in tests: `InMemoryDocumentStore(index="same")` instances share process-local storage; use unique indexes for isolated tests.

## Workflow-specific failures

- Pipeline connection error: connect output sockets explicitly, for example `retriever.documents` to `answerer.documents` or `prompt_builder.documents`.
- Generator answer is wrong but retrieval is correct: inspect retrieved document content and reroute prompt/model work to `../../generation-and-model-components/SKILL.md`.
- No RAG answer because no documents are retrieved: debug store count, filters, query text/vector, and `top_k` before changing prompt templates.
- Sentence-window errors: documents must include `source_id` and `split_id` metadata, or custom names passed as `source_id_meta_field` and `split_id_meta_field`; set `raise_on_missing_meta_fields=False` only when skipped context is acceptable.
- Auto-merging errors: matched leaf documents need `__parent_id`, `__level`, and `__block_size`; parent documents in the merger store need `__children_ids`; `threshold` must be between 0 and 1.
- Lost-in-the-middle ranker errors: all documents must be textual; set `top_k` and `word_count_threshold` to positive integers.
- Reader warm-up/model failures: call `warm_up()` before first reader use, ensure optional dependencies and model access, and note core `ExtractiveReader` deprecation when planning long-term code.

## Debug sequence

1. Import check: `import haystack` and the exact component classes.
2. Store check: `count_documents()` and one `filter_documents()` call.
3. Base retrieval check: BM25 or embedding retriever outside a pipeline.
4. Pipeline check: one retriever in `Pipeline` with `include_outputs_from` or direct component output.
5. Enrichment check: joiner/ranker/window/merger one at a time.
6. RAG check: connect prompt/generator only after retrieved documents are correct.
