# Retrieval Evaluation Troubleshooting

Use this reference when a BEIR retrieval/evaluation workflow fails after data is loaded. For data schemas and loader issues, route to `../data-loading/SKILL.md`. For reranking-specific failures, route to `../reranking/SKILL.md`.

## Quick Triage

1. Run `python scripts/retrieval_smoke.py` to prove BEIR evaluation and dense exact retrieval work offline.
2. Run `python scripts/inspect_optional_backends.py --json` to inspect optional packages and CUDA without contacting services.
3. Verify `corpus`, `queries`, `qrels`, and `results` shapes match the contracts in [api-reference.md](api-reference.md).
4. Reduce `batch_size` and `corpus_chunk_size` before changing model code for memory errors.
5. Distinguish import-level optional dependency readiness from runtime services, credentials, model downloads, and hardware.

## Invalid `score_function`

Symptoms:

- Dense exact retrieval raises `ValueError: score function: ... must be either (cos_sim) ... or (dot) ...`.
- FAISS retrieval raises an assertion failure for unsupported score functions.

Causes:

- Typo such as `cosine`, `ip`, `l2`, or `bm25`.
- Passing a dense score function to a backend that does not use it the same way.

Fix:

- Use `score_function="cos_sim"` or `score_function="dot"` for dense exact and FAISS retrieval.
- Use `"cos_sim"` for cosine-trained models when embeddings are not already normalized.
- Use `"dot"` for dot-product-trained models or normalized embeddings intended for inner product.

## Identical Query and Document IDs

Symptoms:

- Expected self-match is missing from results or metrics.
- Metrics are lower than expected when query ids intentionally equal document ids.

Causes:

- `DenseRetrievalExactSearch.search()` skips results where `corpus_id == query_id`.
- `EvaluateRetrieval.evaluate(..., ignore_identical_ids=True)` removes identical query/doc ids by default.

Fix:

- Prefer distinct query and document ids for evaluation datasets.
- If self-matches are intentional and present in `results`, call `EvaluateRetrieval.evaluate(qrels, results, k_values, ignore_identical_ids=False)`.
- If dense exact search removed self-matches before evaluation, use distinct corpus ids or a custom search implementation.

## Qrels / Results Mismatch

Symptoms:

- Metric evaluation errors from `pytrec_eval`.
- Metrics are unexpectedly zero.
- Custom metric functions fail with missing query ids.

Causes:

- `results` contains query ids not present in `qrels`.
- `qrels` contains query ids that were not retrieved.
- Document ids in results do not match corpus/qrels ids due to string/int conversion or external index mapping.
- Reusing a runfile or FAISS index from a different dataset/split.

Fix:

```python
missing_qrels = set(results) - set(qrels)
missing_results = set(qrels) - set(results)
unknown_docs = {doc_id for docs in results.values() for doc_id in docs if doc_id not in corpus}
```

- Repair ids before evaluation.
- Keep document ids as strings consistently.
- When using FAISS save/load, keep the `.faiss` index and `.tsv` mapping files together and from the same corpus.

## Custom Model Returns Wrong Shape

Symptoms:

- Torch matrix multiplication errors.
- FAISS dimension mismatch errors.
- `topk` failures or nonsensical rankings.
- Retrieval works for queries but fails when encoding corpus chunks.

Causes:

- `encode_queries()` or `encode_corpus()` returns a 1-D vector for one input instead of a 2-D matrix.
- Query and corpus embedding dimensions differ.
- Returned rows do not match input count.
- Returned object is a ragged list or object dtype array.
- Model ignores BEIR's `convert_to_tensor` or `normalize_embeddings` kwargs in an incompatible way.

Fix:

- Run `python scripts/retrieval_smoke.py` and compare the toy encoder protocol.
- Add explicit checks in the custom model wrapper:

```python
embeddings = np.asarray(embeddings, dtype="float32")
if embeddings.ndim != 2 or embeddings.shape[0] != len(inputs):
    raise ValueError(f"expected ({len(inputs)}, dim), got {embeddings.shape}")
```

- Make `encode_queries` and `encode_corpus` accept `**kwargs` and ignore unsupported BEIR options.

## Missing FAISS

Symptoms:

- `NameError: name 'faiss' is not defined` when using FAISS classes.
- `ModuleNotFoundError: No module named 'faiss'`.
- `encode_and_retrieve()` fails during `search_from_files`.

Causes:

- No compatible FAISS package is installed.
- CPU/GPU FAISS package does not match the runtime platform.
- Code path imports FAISS conditionally, so failures can appear later at class construction or search time.

Fix:

- Run `python scripts/inspect_optional_backends.py --json` and check the `faiss` entry.
- Install a compatible FAISS package such as `faiss-cpu` for CPU-only usage, or a GPU-compatible build when needed.
- Fall back to `DenseRetrievalExactSearch.retrieve()` when FAISS is not required.

## Elasticsearch / BM25 Failures

### Package Present but No Service

Symptoms:

- `elasticsearch` imports, but BM25 connection times out or refuses connection.
- User says BEIR/BM25 is installed but retrieval cannot connect.

Cause:

- `BM25Search` requires both the Python package and a running Elasticsearch-compatible service at `hostname`.

Fix:

- Use `scripts/inspect_optional_backends.py` only for package readiness.
- Separately verify the service outside BEIR according to the user's environment policy.
- Set `hostname` to the reachable service URL.

### Invalid Index Name

Symptoms:

- `ValueError` about invalid Elasticsearch index.

Causes and fixes:

- Index contains illegal characters: remove `#:\/*?"<>|,`.
- Index starts with `_`, `-`, or `+`: choose a lowercase alphanumeric prefix.
- Index is `.` or `..`: use a real name.
- Index has uppercase letters: lowercase it.

### Wrong Language Analyzer

Symptoms:

- `ValueError: Invalid Language ... not supported by Elasticsearch`.

Fix:

- Use one of BEIR's supported Elasticsearch analyzer names, such as `english`, `german`, `french`, `spanish`, `cjk`, or another listed in `ElasticSearch.languages`.

### Wrong Field Keys

Symptoms:

- Documents index but retrieval returns poor or empty results.
- Existing index search uses different field names than BEIR expects.

Fix:

- For new indexes, keep `keys={"title": "title", "body": "txt"}` or choose explicit field names and use them consistently.
- Remember BEIR documents have `title` and `text`; BM25 maps `text` into the configured `body` field.
- With `initialize=False`, confirm the existing index uses the same field names.

### Index Refresh / Shard Issues

Symptoms:

- Retrieval immediately after indexing misses recently indexed documents.
- Small corpora behave oddly with default shard settings.

Fix:

- Increase `sleep_for` or refresh the index according to the service tools.
- For small corpora, set `number_of_shards=1`.

## API Credential or Network Failures

Symptoms:

- Cohere or Voyage wrapper logs `Error while encoding texts`.
- Empty or malformed embeddings cause downstream tensor errors.
- Requests fail with authentication, quota, rate-limit, or network errors.

Causes:

- Missing provider package.
- Missing credentials such as `COHERE_API_KEY`.
- Network is unavailable or blocked.
- Provider model name is invalid or unavailable.
- Rate limits or billing restrictions.

Fix:

- Run `scripts/inspect_optional_backends.py --json` for package and environment-variable signals.
- Confirm credentials and network permission before running provider-backed retrieval.
- Use small `batch_size` and provider-recommended model names.
- Cache embeddings with `encode_and_retrieve()` to avoid repeated calls.

## Embedding Cache and Overwrite Problems

Symptoms:

- Results do not change after model/prompt changes.
- `search_from_files` loads stale `corpus.*.pkl` shards.
- FAISS file search errors after changing embedding dimensions.

Causes:

- `overwrite=False` reuses existing query/corpus embedding files.
- Cache directory name does not encode model, prompts, normalization, dataset, or split.
- Old corpus shards remain after reducing corpus size or chunk count.

Fix:

- Use a fresh cache directory for each model/dataset/split/prompt combination.
- Set `overwrite=True` when intentionally replacing embeddings.
- Delete old `corpus.*.pkl` shards before rerunning with fewer chunks.
- Do not reuse FAISS indexes across different embedding dimensions or corpora.

## Huge Corpus, Batch Size, or GPU Memory Issues

Symptoms:

- CUDA out-of-memory.
- Process killed during corpus encoding or similarity scoring.
- Very slow retrieval with large corpora.

Causes:

- `batch_size` too large for model/GPU memory.
- `corpus_chunk_size` too large for dense exact similarity matrix.
- Model downloads or inference exceed local hardware.
- Attempting exact dense search where FAISS/indexing is more appropriate.

Fix:

- Reduce `batch_size` first.
- Reduce `corpus_chunk_size` for dense exact search.
- Use `encode_and_retrieve()` or FAISS index persistence for repeated runs.
- Use `FlatIPFaissSearch` as a first FAISS migration path.
- For large LLM embeddings, confirm GPU memory, dtype, max length, and cache directory before retrieval.

## vLLM, LoRA, NVEmbed, LLM2Vec, and PEFT Issues

Symptoms:

- Optional import failure for `vllm`, `peft`, or `llm2vec`.
- Model download or trust-remote-code errors.
- CUDA or dtype errors.
- LoRA rank/path mismatch.

Causes:

- Optional extras are not installed.
- Model weights require large downloads, GPU, or custom code.
- Runtime package versions are incompatible with torch/CUDA.
- `VLLMEmbed` LoRA parameters do not match the adapter.

Fix:

- Inspect packages and CUDA with `scripts/inspect_optional_backends.py --json`.
- Test a tiny subset before full BEIR retrieval.
- Reduce `max_length` and `batch_size`.
- Use explicit cache directories for model downloads.
- Confirm LoRA adapter path, `lora_r`, pooling, prompt prefixes, and dtype.

## Sparse Search Issues

Symptoms:

- `SparseSearch` fails with shape mismatch or sparse matrix dot errors.
- SPARTA and UniCOIL return poor or empty rankings.

Causes:

- Using `query_weights=True` for SPARTA-style token ids or omitting it for UniCOIL-style weighted query vectors.
- Sparse matrix orientation differs from what `SparseSearch` expects.
- Model/tokenizer downloads or dtype aliases are incompatible with current numpy/torch versions.

Fix:

- SPARTA: call `retriever.retrieve(corpus, queries)` with default `query_weights=False`.
- UniCOIL: call `retriever.retrieve(corpus, queries, query_weights=True)`.
- SPLADE: prefer wrapping with `DenseRetrievalExactSearch` and `score_function="dot"`.
- Test on a few documents before full-corpus retrieval.

## Metric Interpretation Surprises

Symptoms:

- `Hole@k` is high despite good recall.
- `R_cap@k` differs from standard recall.
- `Accuracy@k` seems too coarse.

Explanations:

- `Hole@k` counts unannotated retrieved docs, not incorrect docs.
- `R_cap@k` caps denominator by `min(number_of_relevant_docs, k)`.
- `Accuracy@k` only checks whether at least one relevant document appears in top-k.
- BEIR metrics average over qrels query ids, so missing or extra query coverage changes interpretation.

## When to Route Elsewhere

- Dataset files cannot be read or qrels schema is wrong: route to `../data-loading/SKILL.md`.
- First-stage results are ready but user asks for cross-encoder or MonoT5 reranking: route to `../reranking/SKILL.md`.
- User asks to train retriever models: route to the training sub-skill when present.
- User asks for query generation, passage expansion, or answer generation: route to generation-focused sub-skills when present.
