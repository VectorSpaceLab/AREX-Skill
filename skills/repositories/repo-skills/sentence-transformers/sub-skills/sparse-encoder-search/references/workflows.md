# Sparse Encoder Workflows

## Sparse Embedding Smoke Workflow

1. Choose a sparse model and decide whether network downloads are allowed.
2. Load with `SparseEncoder(model_id, local_files_only=True)` in offline environments.
3. Encode representative text with `convert_to_tensor=True` and `convert_to_sparse_tensor=True`.
4. Print `embeddings.shape`, `embeddings.is_sparse`, `model.sparsity(embeddings)`, and top decoded tokens.
5. Re-run with `max_active_dims` when active dimensions are too high.

Use the bundled script for a safe pattern:

```bash
python scripts/sparse_encoder_smoke.py --model naver/splade-cocondenser-ensembledistil --sentences "weather today" "sunny outside" --max-active-dims 32
```

The script is adapted from the sparse computing-embeddings example, but adds argparse, `--local-files-only`, and no dependency on repository files.

## Query/Document Retrieval Workflow

Use query/document methods when a model has prompts or a router:

```python
model = SparseEncoder("naver/splade-v3")
queries = ["what causes skin aging"]
documents = [
    "UV-A light can contribute to tanning and skin aging.",
    "A sports club opened downtown.",
]
query_embeddings = model.encode_query(queries, max_active_dims=64)
document_embeddings = model.encode_document(documents, max_active_dims=256)
scores = model.similarity(query_embeddings, document_embeddings)
```

Decision points:

- Use `encode_query` and `encode_document` for IR; use `encode` for symmetric similarity or generic diagnostics.
- Keep query and document `max_active_dims` separate when latency differs: queries often need stricter caps than offline-indexed documents.
- Keep dot product unless the task explicitly requires cosine or another metric.
- Decode top tokens when results look lexical, off-topic, or too dependent on artifacts such as punctuation.

## Sparse Search Without External Services

For small corpora or validation tests, keep everything in memory:

1. Encode queries and documents as sparse tensors.
2. Compute `scores = model.similarity(query_embeddings, document_embeddings)`.
3. Use `torch.topk` or sorting to map scores back to document IDs.
4. Check `model.sparsity` and decoded tokens before blaming model quality.

This is the safest path for CI, notebooks, and agent-generated smoke tests because it has no service dependency.

## Search Service Integration

Use service helpers only after confirming optional dependencies and a running service.

- Qdrant: pass sparse COO tensors to `search_engines.semantic_search_qdrant`; install `qdrant-client` and provide connection kwargs if not using the default local URL.
- Elasticsearch: decode embeddings with `model.decode` and pass token-weight lists to `semantic_search_elasticsearch`; install `elasticsearch`; the helper maps tokens to `rank_features`.
- OpenSearch: decode embeddings and pass token-weight lists to `semantic_search_opensearch`; install `opensearch-py`; OpenSearch neural sparse models may use inference-free query routing.
- Seismic: decode embeddings and pass token-weight lists to `semantic_search_seismic`; install `pyseismic-lsr`; tune `index_kwargs` and `search_kwargs` only after baseline correctness works.

Service cautions:

- Do not assume a local service is available on default ports.
- Keep index creation separate from query-time search in production; helper-created temporary indexes are useful for demos, not durable deployment architecture.
- Cap active dimensions or top decoded tokens when payload size, index size, or rank-feature field counts become too large.
- Validate score ordering against a tiny in-memory baseline before trusting a service adapter.

## Hybrid Sparse + Dense Retrieval

Sparse and dense retrieval are complementary. A robust hybrid plan usually has:

1. Sparse candidate generation using `SparseEncoder` for lexical expansion and exact-token sensitivity.
2. Dense candidate generation using `SentenceTransformer` or existing dense index for semantic paraphrases.
3. Score fusion such as reciprocal rank fusion, weighted normalized scores, or service-native hybrid features.
4. Optional reranking with `CrossEncoder` for the final top candidates.
5. Separate monitoring of sparse active dimensions, dense embedding norms, recall@k, and latency.

Keep this sub-skill focused on the sparse side. Dense semantic search details belong in `../retrieval-and-utilities/SKILL.md`, and reranking belongs in `../reranking-cross-encoder/SKILL.md`.

## Sparse IR Evaluation Workflow

Use `SparseInformationRetrievalEvaluator` when you have query IDs, corpus IDs, and relevance judgments:

```python
evaluator = SparseInformationRetrievalEvaluator(
    queries=queries,
    corpus=corpus,
    relevant_docs=relevant_docs,
    main_score_function="dot",
    max_active_dims=128,
    write_predictions=True,
)
results = evaluator(model)
```

Checklist:

- `queries`: `dict[qid, query_text]`.
- `corpus`: `dict[cid, document_text]`.
- `relevant_docs`: `dict[qid, set[cid]]`.
- Use a small evaluation slice during training to control runtime.
- Inspect primary metric, recall@k/NDCG@k, query sparsity, corpus sparsity, and FLOPS.
- Use `write_predictions=True` when evaluating fusion with `ReciprocalRankFusionEvaluator`.

## Sparse Training Routing

For SPLADE fine-tuning, wrap a sparse ranking/distillation loss in `SpladeLoss`:

```python
from sentence_transformers.sparse_encoder import losses

loss = losses.SpladeLoss(
    model=model,
    loss=losses.SparseMultipleNegativesRankingLoss(model=model),
    query_regularizer_weight=5e-5,
    document_regularizer_weight=3e-5,
)
```

Guidance:

- Use `SpladeLoss` for SPLADE; use `CSRLoss` for CSR architectures.
- Use `SparseMSELoss` for embedding-level distillation from sparse teacher embeddings.
- Match dataset columns to the inner loss before tuning sparsity regularizers.
- Track active dimensions during training; regularizer weights that are too weak can make retrieval expensive, while overly strong weights can collapse useful terms.
- For inference-free SPLADE, set `router_mapping` so query/document columns take the intended route and consider `learning_rate_mapping` for `SparseStaticEmbedding`.

## Difficult Usability Cases

### Diagnose collapsed sparsity or too many active dimensions

User symptom: sparse embeddings have thousands of active dimensions, service indexing is slow, or retrieval quality collapses after aggressive caps.

Plan:

1. Run `scripts/sparse_encoder_smoke.py` on representative query/document texts without a cap.
2. Record `active_dims`, `sparsity_ratio`, top decoded tokens, and similarity ordering.
3. Re-run with candidate `max_active_dims` values such as 32, 64, 128, and 256.
4. Compare top-token coverage and ranking changes, not just memory savings.
5. If training is involved, adjust `SpladeLoss` regularizer weights gradually and evaluate with `SparseInformationRetrievalEvaluator`.

### Plan hybrid sparse+dense retrieval without assuming services

User symptom: wants Qdrant, Elasticsearch, OpenSearch, or hybrid retrieval, but the environment has no running service.

Plan:

1. Build a tiny in-memory sparse baseline with `SparseEncoder` and `model.similarity`.
2. Build or reference a dense baseline through `../retrieval-and-utilities/SKILL.md` only if dense embeddings are in scope.
3. Define a service-independent fusion contract: inputs are ranked lists of `(doc_id, score)`; output is a fused ranked list.
4. Add service adapters behind optional dependency checks and connection probes.
5. Keep CI tests limited to in-memory baselines and `--help`; mark service integration tests as opt-in.
