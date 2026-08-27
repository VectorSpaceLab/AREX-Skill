# Inference Workflows

These recipes are distilled from the package API, examples, and tests. They are
written as reusable patterns: replace `MODEL_NAME_OR_PATH` with an approved local
path or model id and choose devices explicitly for the environment.

## Dense Embedder With Auto Loader

Use this when the checkpoint is in the built-in mapping or when you provide a
custom `model_class`.

```python
from FlagEmbedding import FlagAutoModel

model = FlagAutoModel.from_finetuned(
    MODEL_NAME_OR_PATH,
    model_class=None,  # set for unmapped checkpoints
    normalize_embeddings=True,
    use_fp16=False,
    devices="cpu",
    query_instruction_for_retrieval="Represent this sentence for searching relevant passages:",
)

queries = ["what is vector search?", "how do rerankers work?"]
passages = [
    "Vector search compares dense embeddings for semantic retrieval.",
    "A reranker scores query and passage pairs after candidate retrieval.",
]

q_vecs = model.encode_queries(queries, batch_size=2)
p_vecs = model.encode_corpus(passages, batch_size=2)
scores = q_vecs @ p_vecs.T
```

Expected observations:

- `q_vecs.shape[0] == len(queries)`.
- `p_vecs.shape[0] == len(passages)`.
- With normalized embeddings, `scores` is a cosine-similarity matrix.

## Custom Local Embedder Checkpoint

Use this when auto mapping cannot infer the model class. Choose the class from
the architecture that produced the checkpoint.

```python
from FlagEmbedding import FlagAutoModel

model = FlagAutoModel.from_finetuned(
    LOCAL_CHECKPOINT,
    model_class="encoder-only-base",
    pooling_method="cls",
    normalize_embeddings=True,
    use_fp16=False,
    devices="cpu",
    trust_remote_code=False,
    query_instruction_for_retrieval="Represent this sentence for searching relevant passages:",
    query_instruction_format="{}{}",
    truncate_dim=None,
)
```

Decision points:

- Use `encoder-only-base` with `pooling_method="cls"` for BGE-style encoder
  checkpoints and `pooling_method="mean"` for E5-style checkpoints.
- Use `decoder-only-base` for last-token pooled LLM embedding checkpoints.
- Use `encoder-only-m3` only for M3-compatible checkpoints that expose dense,
  sparse, and ColBERT heads.
- Keep `trust_remote_code=False` unless the checkpoint includes custom model
  code that has been reviewed.
- Set `truncate_dim` only for Matryoshka-style checkpoints trained for
  dimensional truncation.

## Concrete Encoder Embedder

Use the concrete class when you already know it is an encoder-only dense model.

```python
from FlagEmbedding import FlagModel

model = FlagModel(
    MODEL_NAME_OR_PATH,
    normalize_embeddings=True,
    use_fp16=False,
    devices="cpu",
    pooling_method="cls",
    query_instruction_for_retrieval="Represent this sentence for searching relevant passages:",
)

q_vecs = model.encode_queries(["query text"])
p_vecs = model.encode_corpus(["candidate passage"])
score = float((q_vecs @ p_vecs.T)[0, 0])
```

## M3 Dense And Sparse Retrieval

Use `BGEM3FlagModel` or `model_class="encoder-only-m3"` when you need dense,
sparse, or ColBERT outputs.

```python
from FlagEmbedding import BGEM3FlagModel

model = BGEM3FlagModel(
    MODEL_NAME_OR_PATH,
    normalize_embeddings=True,
    use_fp16=False,
    devices="cpu",
    pooling_method="cls",
)

queries = ["what is multilingual retrieval?"]
passages = [
    "Multilingual retrieval searches relevant text across languages.",
    "A reranker can improve candidate ordering.",
]

q = model.encode_queries(
    queries,
    return_dense=True,
    return_sparse=True,
    return_colbert_vecs=False,
)
p = model.encode_corpus(
    passages,
    return_dense=True,
    return_sparse=True,
    return_colbert_vecs=False,
)

dense_scores = q["dense_vecs"] @ p["dense_vecs"].T
sparse_scores = model.compute_lexical_matching_score(
    q["lexical_weights"],
    p["lexical_weights"],
)
```

Validate that `q["dense_vecs"]` and `p["dense_vecs"]` are not `None` before
matrix multiplication. Validate that `lexical_weights` is not `None` before
calling `compute_lexical_matching_score`.

## M3 Pair Scoring

Use `compute_score` when the task is pairwise scoring rather than retrieving
all passage candidates by matrix multiplication.

```python
pairs = [
    ("what is multilingual retrieval?", "Multilingual retrieval searches text across languages."),
    ("what is multilingual retrieval?", "A GPU accelerates tensor operations."),
]

scores = model.compute_score(
    pairs,
    batch_size=2,
    max_query_length=512,
    max_passage_length=512,
    weights_for_different_modes=[1.0, 0.3, 1.0],
)

dense = scores["dense"]
sparse = scores["sparse"]
colbert = scores["colbert"]
combined = scores["colbert+sparse+dense"]
```

Expected keys are `dense`, `sparse`, `colbert`, `sparse+dense`, and
`colbert+sparse+dense`. For a batch, each value is a list of floats with the
same length as `pairs`. For one pair, values may be scalars.

## M3 With ColBERT Vectors

Use ColBERT vectors only when the downstream scorer expects token-level
multivectors. They consume more memory than dense vectors.

```python
q = model.encode_queries(
    ["query text"],
    return_dense=True,
    return_sparse=True,
    return_colbert_vecs=True,
)
p = model.encode_corpus(
    ["candidate passage"],
    return_dense=True,
    return_sparse=True,
    return_colbert_vecs=True,
)

token_interaction = model.colbert_score(
    q["colbert_vecs"][0],
    p["colbert_vecs"][0],
)
```

If a single string was encoded instead of a one-item list, the corresponding
`colbert_vecs` value is one array rather than a list. Normalize the input shape
before indexing in reusable code.

## Decoder-Only LLM Embedder

Decoder-only embedders use last-token pooling. Do not set `pooling_method` to
`cls` or `mean` for these classes.

```python
from FlagEmbedding import FlagLLMModel

model = FlagLLMModel(
    MODEL_NAME_OR_PATH,
    query_instruction_for_retrieval="Given a question, retrieve passages that answer the question.",
    query_instruction_format="<instruct>{}\n<query>{}",
    normalize_embeddings=True,
    use_fp16=False,
    devices="cpu",
)

q_vecs = model.encode_queries(["how much protein should a person eat?"])
p_vecs = model.encode_corpus(["Protein needs vary by age, activity, and health status."])
scores = q_vecs @ p_vecs.T
```

For long LLM inputs, tune `query_max_length`, `passage_max_length`, and
`batch_size` together. CPU smoke checks should use tiny inputs and batch size 1.

## ICL Embedder

Use `FlagICLModel` when the model supports few-shot task examples.

```python
from FlagEmbedding import FlagICLModel

examples = [
    {
        "instruct": "Given a web search query, retrieve relevant passages that answer the query.",
        "query": "what is a virtual interface",
        "response": "A virtual interface is a software-defined network interface abstraction.",
    }
]

model = FlagICLModel(
    MODEL_NAME_OR_PATH,
    query_instruction_for_retrieval="Given a question, retrieve passages that answer the question.",
    query_instruction_format="<instruct>{}\n<query>{}",
    examples_for_task=examples,
    examples_instruction_format="<instruct>{}\n<query>{}\n<response>{}",
    use_fp16=False,
    devices="cpu",
)

q_vecs = model.encode_queries(["summit definition"])
p_vecs = model.encode_corpus(["A summit is the highest point of a mountain."])
```

ICL query encoding uses a separate query multiprocessing pool. In long-running
processes, delete the model or call cleanup helpers after switching between
large query and corpus jobs.

## Pseudo-MoE Embedder

Use `FlagPseudoMoEModel` or `model_class="decoder-only-pseudo_moe"` for
checkpoints that expose a domain router.

```python
from FlagEmbedding import FlagAutoModel

model = FlagAutoModel.from_finetuned(
    MODEL_NAME_OR_PATH,
    model_class="decoder-only-pseudo_moe",
    query_instruction_for_retrieval="Given a question, retrieve passages that answer the question.",
    query_instruction_format="Instruct: {}\nQuery: {}",
    domain_for_pseudo_moe="reasoning",
    use_fp16=False,
    use_bf16=True,
    trust_remote_code=True,
    devices="cpu",
)

q_vecs = model.encode_queries(["why does the sky appear blue?"], domain_for_pseudo_moe="reasoning")
p_vecs = model.encode_corpus(["Short wavelengths scatter more in the atmosphere."])
```

Only pass a domain when the checkpoint was trained to support it. Unsupported
models may ignore the domain or fail in custom remote code.

## Encoder Reranker

Use this after an embedder retrieves a candidate set.

```python
from FlagEmbedding import FlagAutoReranker

reranker = FlagAutoReranker.from_finetuned(
    MODEL_NAME_OR_PATH,
    model_class=None,  # set for unmapped checkpoints
    use_fp16=False,
    devices="cpu",
    batch_size=8,
    query_max_length=256,
    max_length=512,
    normalize=False,
)

query = "what is vector search?"
candidates = [
    "Vector search compares dense embeddings for semantic retrieval.",
    "The capital city is a seat of government.",
]
pairs = [(query, passage) for passage in candidates]
scores = reranker.compute_score(pairs)
ranked = sorted(zip(candidates, scores), key=lambda item: item[1], reverse=True)
```

Use `normalize=True` only if the next component expects 0-1 sigmoid scores.
Raw reranker logits are valid for sorting candidates from the same model.

## Custom Local Reranker Checkpoint

```python
from FlagEmbedding import FlagAutoReranker

reranker = FlagAutoReranker.from_finetuned(
    LOCAL_CHECKPOINT,
    model_class="encoder-only-base",
    use_fp16=False,
    trust_remote_code=False,
    devices="cpu",
    query_max_length=256,
    max_length=512,
)
```

For LLM rerankers, choose `decoder-only-base`, `decoder-only-layerwise`, or
`decoder-only-lightweight` and review whether `trust_remote_code=True` is
required by the checkpoint.

## Decoder-Only Reranker

```python
from FlagEmbedding import FlagLLMReranker

reranker = FlagLLMReranker(
    MODEL_NAME_OR_PATH,
    use_fp16=False,
    devices="cpu",
    query_max_length=256,
    max_length=512,
)

scores = reranker.compute_score([
    ("what is a reranker?", "A reranker scores retrieved candidates with a cross-encoder."),
])
```

Decoder-only rerankers pack inputs as query A, passage B, and a yes/no prompt.
Use smaller `batch_size` than encoder rerankers when memory is tight.

## Layerwise Reranker

```python
from FlagEmbedding import LayerWiseFlagLLMReranker

reranker = LayerWiseFlagLLMReranker(
    MODEL_NAME_OR_PATH,
    use_fp16=False,
    use_bf16=False,
    trust_remote_code=True,
    devices="cpu",
    query_max_length=256,
    max_length=512,
)

scores = reranker.compute_score(
    [("what is M3?", "M3 combines dense, sparse, and multi-vector retrieval modes.")],
    cutoff_layers=[28],
)
```

With multiple cutoff layers, for example `cutoff_layers=[16, 28]`, validate
whether the return is `[scores_for_layer_16, scores_for_layer_28]` before
combining with other ranking signals.

## Lightweight Reranker

```python
from FlagEmbedding import LightWeightFlagLLMReranker

reranker = LightWeightFlagLLMReranker(
    MODEL_NAME_OR_PATH,
    use_fp16=False,
    use_bf16=False,
    trust_remote_code=True,
    devices="cpu",
    query_max_length=256,
    max_length=512,
)

scores = reranker.compute_score(
    [("what is compression?", "Compression reduces intermediate token work in the model.")],
    cutoff_layers=[28],
    compress_ratio=2,
    compress_layers=[24, 40],
)
```

Keep compression settings tied to the checkpoint family. Arbitrary layer numbers
can produce poor scores or runtime failures.

## Retrieval Pipeline With M3 Plus Reranker

```python
embedder = FlagAutoModel.from_finetuned(
    EMBEDDER_NAME_OR_PATH,
    model_class="encoder-only-m3",
    use_fp16=False,
    devices="cpu",
)

encoded_query = embedder.encode_queries(
    [query],
    return_dense=True,
    return_sparse=True,
    return_colbert_vecs=False,
)
encoded_corpus = embedder.encode_corpus(
    passages,
    return_dense=True,
    return_sparse=True,
    return_colbert_vecs=False,
)

dense_scores = (encoded_query["dense_vecs"] @ encoded_corpus["dense_vecs"].T)[0]
sparse_scores = embedder.compute_lexical_matching_score(
    encoded_query["lexical_weights"],
    encoded_corpus["lexical_weights"],
)[0]

candidate_ids = sorted(
    range(len(passages)),
    key=lambda i: dense_scores[i] + 0.3 * sparse_scores[i],
    reverse=True,
)[:TOP_K]

rerank_pairs = [(query, passages[i]) for i in candidate_ids]
rerank_scores = reranker.compute_score(rerank_pairs)
assert len(rerank_scores) == len(candidate_ids)

final = sorted(
    zip(candidate_ids, rerank_scores),
    key=lambda item: item[1],
    reverse=True,
)
```

The assertion prevents a common failure: treating a layerwise nested score shape
or a scalar M3 score as if it were a flat reranker score list.

## Batching And Multi-Device Recipes

For smoke checks:

```python
devices = "cpu"
batch_size = 1
use_fp16 = False
use_bf16 = False
```

For one GPU:

```python
devices = "cuda:0"
batch_size = 16  # tune upward only after a successful small run
use_fp16 = True
```

For multiple GPUs:

```python
devices = ["cuda:0", "cuda:1"]
```

Multi-device encode and score methods use multiprocessing pools. Start with a
small batch, verify output shapes, then increase batch size. If OOM occurs, the
concrete classes try to reduce batch size internally, but explicit conservative
batching is easier to debug.

## Cache And Download Control

Loading from a local path should not need network access if all model files are
present. Loading from a model id can download through Hugging Face. To control
cache placement, pass `cache_dir` from caller configuration or rely on standard
Hugging Face cache environment variables. Do not embed user-specific cache paths
in reusable scripts or skills.
