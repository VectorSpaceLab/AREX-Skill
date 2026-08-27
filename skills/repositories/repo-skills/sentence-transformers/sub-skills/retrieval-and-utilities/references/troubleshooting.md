# Retrieval and Utilities Troubleshooting

## Install and import failures

- `ModuleNotFoundError: sentence_transformers`: install the package in the active Python environment and verify with `python -c "import sentence_transformers"`.
- `ImportError: Please install datasets`: `mine_hard_negatives` requires the `datasets` package; install the training/dev dependency set or `datasets` explicitly.
- `ModuleNotFoundError: faiss` or `usearch`: FAISS/USearch search helpers are optional; install the backend you actually use or fall back to in-memory `semantic_search`.
- Torch/transformers import errors usually indicate an incompatible environment; check Python version, PyTorch build, and `transformers` version constraints.
- Hosted or private model loading failures can be authentication, revision, cache, or network issues; use a local model path and `local_files_only=True` when offline.

## `semantic_search` misuse

- Shape mismatch: query and corpus embeddings must share the same embedding dimension.
- Empty corpus: `top_k` becomes invalid if there are no corpus rows; validate corpus size before search.
- Wrong ID mapping: `corpus_id` is positional in the embedding matrix, not necessarily an external document ID.
- Bad ranking with `dot_score`: dot product only behaves like cosine when embeddings are normalized.
- Unexpected low scores with Euclidean/Manhattan: helpers return negative distances, so less negative values rank higher.
- Out-of-memory errors: lower `query_chunk_size`, lower `corpus_chunk_size`, move tensors to CPU, reduce `top_k`, or use an index backend.
- Device mismatch symptoms: keep query and corpus tensors on compatible devices; `semantic_search` moves queries to the corpus device but model encoding choices may still allocate elsewhere.

## Retrieve-and-rerank failures

- Candidate-relative IDs: `CrossEncoder.rank` IDs refer to the candidate document list passed to the reranker; map back through dense hits to recover original corpus IDs.
- Reranking too slow: reduce first-stage `top_k`, increase reranker batch size if memory allows, or cache dense retrieval results.
- Poor recall after reranking: increase first-stage `top_k`; rerankers cannot recover documents the retriever did not return.
- Score confusion: retriever scores and reranker scores are not calibrated to each other; sort final output by reranker score after reranking.
- Long documents: chunk documents before dense retrieval and keep metadata linking chunks back to source documents.

## Hard-negative mining failures

- Wrong columns selected: set `anchor_column_name` and `positive_column_name`; otherwise the function falls back to the first two dataset columns.
- No or too few negatives: loosen `relative_margin`, `absolute_margin`, `max_score`, `min_score`, `range_min`, or increase `range_max`.
- False negatives: increase `range_min`, filter near-duplicate positives, group duplicate queries, or use a CrossEncoder to rescore candidates.
- Invalid `output_format`: use only `triplet`, `n-tuple`, `labeled-pair`, or `labeled-list`.
- Deprecated arguments: replace `as_triplets` with `output_format` and `margin` with `absolute_margin` or `relative_margin`.
- FAISS retrieval depth cap: GPU FAISS can limit per-query depth; reduce expectations or run CPU/exact search for deeper candidate ranges.
- Cache surprises: if text/model inputs changed but cache files remain, clear the configured cache folder and recompute embeddings.

## Quantization failures

- Unstable int8/uint8 quality: provide `calibration_embeddings` or explicit `ranges`; avoid calibrating from tiny query batches.
- `ValueError` in FAISS/USearch helpers: pass exactly one of `corpus_embeddings` or `corpus_index`.
- Rescoring warning: rescoring only helps when query embeddings are float32 and the corpus/index is quantized.
- Backend precision mismatch: use the precision and dtype expected by the vector backend (`uint8`, signed `int8`, packed binary, or unsigned packed binary).
- Quality drop with binary embeddings: increase `rescore_multiplier`, retrieve more candidates, keep float32 queries, or use int8 scalar quantization.
- Confusing model quantization with embedding quantization: embedding quantization changes stored vectors; model-weight quantization/export is a backend optimization topic.

## Backend and service limits

- Search services may return distances where lower is better; normalize result interpretation before merging with `semantic_search` results.
- Approximate indexes trade recall for latency; evaluate recall@k before relying on reranker improvements.
- Vector DBs can reorder, compact, or shard internal IDs; store stable document IDs in metadata.
- External services require batching, retry, timeout, and rate-limit handling in production code.
- Do not place API keys, service URLs, or local cache paths in reusable public skill files or checked-in scripts.

## Demo script issues

- `--toy-tensors` requires only `torch` and `sentence-transformers`; it does not download a model.
- `--model` may download unless the model exists locally or `--local-files-only` is set.
- If `encode_query`/`encode_document` are unavailable for a custom model, use regular `encode` consistently for queries and documents.
- The script is intentionally tiny and exact; use it to validate API wiring, not to benchmark production retrieval.
