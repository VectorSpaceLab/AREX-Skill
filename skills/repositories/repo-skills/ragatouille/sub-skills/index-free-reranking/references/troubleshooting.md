# Troubleshooting: Index-Free Reranking

## Import or Environment Fails Before Model Use

Symptoms:

- `ModuleNotFoundError` mentions `langchain.retrievers.document_compressors.base`.
- Imports fail around `fast_pytorch_kmeans` or `psutil`.

Likely causes and fixes:

- RAGatouille `0.0.9post2` expects a legacy-compatible LangChain stack; latest LangChain `1.x` removed import paths used by RAGatouille integrations.
- Install or use an environment with compatible `langchain` and `langchain_core` versions for this package generation baseline.
- Ensure `psutil` is present when `fast-pytorch-kmeans` imports require it.

## Model Download, Network, or Hardware Is Unavailable

`RAGPretrainedModel.from_pretrained()` may download a checkpoint such as `colbert-ir/colbertv2.0`. Real `rerank()`, `encode()`, and `search_encoded_docs()` calls can be CPU/GPU intensive.

For lightweight verification:

- Do not run model-loading examples unless the environment explicitly permits downloads and compute.
- Use the bundled `scripts/check_result_shapes.py` to validate JSON shape contracts offline.
- Treat the source notebooks as evidence-only when downloads or external pipelines are unsafe.

## `k` Is Larger Than the Document Count

For `rerank()`:

- If `k > len(documents)`, RAGatouille prints `k value cannot be larger than the number of documents! aborting...` and returns `None`.
- Fix by capping `k = min(requested_k, len(documents))` before calling.

For `search_encoded_docs()`:

- The encoded-search path calls `torch.topk()` directly and may raise when `k` exceeds the number of encoded documents.
- Track the number of encoded documents in your application and cap `k` before searching.

## More Than 1000 Documents Are Passed to `rerank()`

RAGatouille prints a warning that in-memory ranking is not optimized for large document counts and recommends building an index instead.

Fix:

- First-stage retrieve to a smaller candidate set, then `rerank()`.
- Or use a persisted index through `../../pretrained-indexing-search/SKILL.md` for repeated or large-scale retrieval.

## Duplicate Documents Produce a Warning

`rerank()` warns when `len(set(documents)) != len(documents)`. Duplicate text slows scoring and can produce confusing repeated results.

Fix:

- Deduplicate candidate strings before reranking when duplicates are accidental.
- If duplicates are intentional because metadata differs, keep a side table keyed by original position and decide how to merge or display repeated content.

## Results Have Unexpected Rank Values

The public docstring describes one-based ranks by default, but the index-free implementation enumerates ranks from `0`; with `zero_index_ranks=True`, it subtracts one again.

Fix:

- Prefer list order as the authoritative ranking for index-free results.
- If exporting rank values, normalize them in application code after receiving results.

## `search_encoded_docs()` Is Called Before `encode()`

Symptoms:

- Attribute errors involving `in_memory_collection`, `in_memory_embed_docs`, or `doc_masks`.

Cause:

- Encoded search only uses transient attributes created by `encode()` on the same model instance.

Fix:

- Call `encode()` before `search_encoded_docs()`.
- After `clear_encoded_docs()`, call `encode()` again before searching.

## Metadata Does Not Appear or Looks Misaligned

Expected behavior:

- `rerank()` does not accept `document_metadatas`; it returns `result_index` so callers can rejoin metadata from the external candidate list.
- `encode()` accepts `document_metadatas`, and single-query `search_encoded_docs()` can return `document_metadata` for each result.

Pitfalls:

- RAGatouille `0.0.9post2` does not robustly validate `document_metadatas` length in `encode()`. Provide exactly one metadata dict per document.
- Keep metadata usage consistent across appended batches. Appending no-metadata documents after metadata exists can hit a source typo (`in_memory_metadatas`) instead of cleanly adding `None` metadata entries.
- Multi-query `search_encoded_docs()` metadata injection is fragile because the implementation treats top-level results as if they are flat dicts.

Fix:

- Validate lengths before `encode()`.
- Prefer one query at a time when metadata is required.
- Keep external IDs in metadata, and verify returned metadata against `result_index` in tests or fixtures.

## Encoded State Is Stale

Symptoms:

- Results include documents from previous application state.
- New documents appear together with old documents unexpectedly.

Cause:

- Every `encode()` call appends to the model's in-memory collection.

Fix:

- Call `clear_encoded_docs(force=True)` before encoding a replacement collection.
- Use one `RAGPretrainedModel` instance per independent transient collection if isolation is simpler.

## `clear_encoded_docs()` Waits Before Returning

By default, `clear_encoded_docs(force=False)` prints a warning and sleeps for 10 seconds.

Fix:

- Use `clear_encoded_docs(force=True)` in scripts, tests, services, and automated agents.
- Use the default only when a human should have time to interrupt an accidental clear.

## Long Documents Slow Encoding or Reranking

`encode()` does not split documents. The example notebook describes dynamic max-token behavior; the inspected `0.0.9post2` source uses the base model maximum for `max_document_length="auto"`, and only the explicit-length path computes a capped 90th-percentile estimate that can print a slowdown warning.

Fix:

- Chunk long documents before `encode()` or `rerank()`.
- Lower `max_document_length` only if truncation is acceptable.
- Use GPU when available and safe, or switch to a persisted index for larger repeated workloads.
