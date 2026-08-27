# Sparse Encoder API Reference

This reference covers the public sparse encoder surface that is useful for agent-authored code. It intentionally excludes dense `util.semantic_search` details except where needed for routing.

## Imports

```python
from sentence_transformers import SparseEncoder
from sentence_transformers.sparse_encoder.evaluation import SparseInformationRetrievalEvaluator
from sentence_transformers.sparse_encoder import losses
from sentence_transformers.sparse_encoder import search_engines
```

`SparseEncoder` is also available from `sentence_transformers.sparse_encoder`.

## `SparseEncoder` Construction

Common constructor shape:

```python
model = SparseEncoder(
    model_name_or_path,
    device=None,
    prompts=None,
    default_prompt_name=None,
    trust_remote_code=False,
    revision=None,
    local_files_only=False,
    token=None,
    model_kwargs=None,
    backend="torch",
    similarity_fn_name=None,
    max_active_dims=None,
)
```

Key decisions:

- `model_name_or_path`: local path or Hugging Face model id, such as a SPLADE model.
- `local_files_only=True`: avoids network access and fails fast if files are not cached.
- `trust_remote_code=True`: only use after reviewing the model repository because it can execute custom code.
- `backend`: supports `"torch"`, `"onnx"`, and `"openvino"`, but export/deployment details belong in `../backend-export-optimization/SKILL.md`.
- `similarity_fn_name`: sparse models default lazily to dot product when `model.similarity` is first accessed; valid names are `"dot"`, `"cosine"`, `"euclidean"`, and `"manhattan"`.
- `max_active_dims`: global cap on non-zero dimensions; must be positive when provided.

## Encoding

Main signature facts:

```python
embeddings = model.encode(
    inputs,
    prompt_name=None,
    prompt=None,
    batch_size=32,
    show_progress_bar=None,
    convert_to_tensor=True,
    convert_to_sparse_tensor=True,
    save_to_cpu=False,
    device=None,
    max_active_dims=None,
    pool=None,
    chunk_size=None,
)
```

Behavior and output:

- Accepts one string or a list/iterable of strings.
- Returns a torch tensor by default, usually sparse COO when `convert_to_sparse_tensor=True`.
- A single string returns a one-dimensional embedding; multiple strings return `[num_inputs, output_dimension]`.
- `convert_to_tensor=False` returns individual tensors instead of a stacked tensor, which can avoid sparse slicing pain.
- `save_to_cpu=True` moves outputs to CPU and is useful before indexing, serialization, or multiprocessing concatenation.
- `max_active_dims` passed to `encode` overrides the model-level cap for that call.
- Additional kwargs must be supported by the model, except `task` and `processing_kwargs`; unsupported kwargs raise `ValueError`.

For retrieval tasks with query/document asymmetry, prefer:

```python
query_embeddings = model.encode_query(queries, max_active_dims=64)
document_embeddings = model.encode_document(documents, max_active_dims=256)
```

These methods apply query/document prompts or router tasks when the model defines them. If the model has no prompts/routes, they can behave like `encode`.

## Similarity

`model.similarity(embeddings1, embeddings2)` returns a matrix of pairwise scores between both collections. Sparse SPLADE models normally use dot product by default.

```python
query_embeddings = model.encode_query(["weather in new york"])
document_embeddings = model.encode_document([
    "New York weather is rainy today.",
    "A recipe for tomato soup.",
])
scores = model.similarity(query_embeddings, document_embeddings)
```

`model.similarity_pairwise(embeddings1, embeddings2)` returns one score per aligned pair, not a full matrix.

Set `model.similarity_fn_name = "cosine"` only when cosine-normalized behavior is desired. Dot product is the usual sparse lexical retrieval score.

## Sparsity Diagnostics

Use `SparseEncoder.sparsity` or `model.sparsity` on a 1D or 2D torch tensor:

```python
stats = model.sparsity(embeddings)
print(stats["active_dims"], stats["sparsity_ratio"])
```

The result contains:

- `active_dims`: mean number of non-zero dimensions per embedding.
- `sparsity_ratio`: mean fraction of zero dimensions.

Use this to detect output blow-ups, collapsed models, poor regularization, or an overly aggressive `max_active_dims` cap.

## Decoding Token Weights

SPLADE-style vocabulary-sized embeddings can be decoded to token weights:

```python
decoded = model.decode(embeddings, top_k=10)
```

Use decoded weights for inspection, service adapters that require token-weight pairs, or debugging unexpected matches. `top_k` must be positive when provided. CSR sparse models are not vocabulary-aligned in the same interpretable way.

## Sparse Search Engines

The sparse search adapters are in `sentence_transformers.sparse_encoder.search_engines` and are optional-service helpers, not mandatory for in-memory search.

- `semantic_search_qdrant(query_embeddings, corpus_embeddings=None, corpus_index=None, top_k=10, output_index=False, **kwargs)` expects sparse COO tensors and imports `qdrant-client`.
- `semantic_search_elasticsearch(query_embeddings_decoded, corpus_embeddings_decoded=None, corpus_index=None, top_k=10, output_index=False, **kwargs)` expects decoded `[[("token", weight), ...], ...]` data and imports `elasticsearch`.
- `semantic_search_opensearch(query_embeddings_decoded, corpus_embeddings_decoded=None, corpus_index=None, top_k=10, output_index=False, **kwargs)` expects decoded token-weight lists and imports `opensearch-py`.
- `semantic_search_seismic(query_embeddings_decoded, corpus_embeddings_decoded=None, corpus_index=None, top_k=10, output_index=False, index_kwargs=None, search_kwargs=None)` expects decoded token-weight lists and imports `pyseismic-lsr`.

All service helpers can create a temporary index from corpus embeddings when `corpus_index` is absent, or reuse an existing index tuple. Do not assume a service is running; catch `ImportError`, connection errors, and schema/index failures.

## Sparse IR Evaluation

`SparseInformationRetrievalEvaluator` measures retrieval metrics over dictionaries:

```python
evaluator = SparseInformationRetrievalEvaluator(
    queries={"q1": "weather today"},
    corpus={"d1": "sunny weather", "d2": "financial report"},
    relevant_docs={"q1": {"d1"}},
    name="tiny-sparse-ir",
    batch_size=16,
    main_score_function="dot",
    max_active_dims=128,
)
results = evaluator(model)
```

It reports IR metrics such as MRR, recall, NDCG, MAP, and sparse diagnostics such as query/corpus sparsity and average FLOPS. Use `write_predictions=True` when predictions will feed `ReciprocalRankFusionEvaluator` for hybrid or multi-system evaluation.

## Sparse Losses and Training Concepts

Sparse model training is covered broadly in `../evaluation-and-training/SKILL.md`, but sparse-specific routing matters:

- Use `losses.SpladeLoss(model, loss=..., document_regularizer_weight=..., query_regularizer_weight=...)` for SPLADE architectures; it wraps a main sparse loss and adds FLOPS-style sparsity regularization.
- Use `losses.CSRLoss` for CSR sparse autoencoder architectures.
- `losses.SparseMSELoss` can be used independently for embedding-level sparse distillation.
- Main sparse losses include `SparseMultipleNegativesRankingLoss`, `SparseMarginMSELoss`, `SparseDistillKLDivLoss`, `SparseTripletLoss`, `SparseCosineSimilarityLoss`, `SparseCoSENTLoss`, and `SparseAnglELoss`.
- `CachedSpladeLoss` is relevant when caching helps fit larger effective batches.
- For inference-free SPLADE routers, configure `router_mapping` in `SparseEncoderTrainingArguments` and often use a higher `learning_rate_mapping` for `SparseStaticEmbedding` than for the transformer path.
