# Inference API Reference

This reference captures the FlagEmbedding inference API surface needed by this
sub-skill. It is self-contained and uses only runtime names exposed by the
installed package.

## Public Imports

```python
from FlagEmbedding import (
    FlagAutoModel,
    FlagAutoReranker,
    FlagModel,
    BGEM3FlagModel,
    FlagLLMModel,
    FlagICLModel,
    FlagPseudoMoEModel,
    FlagReranker,
    FlagLLMReranker,
    LayerWiseFlagLLMReranker,
    LightWeightFlagLLMReranker,
)
```

`FlagModel` is the public alias for the encoder-only base embedder.
`BGEM3FlagModel` is the public alias for the M3 embedder. `FlagLLMModel`,
`FlagICLModel`, and `FlagPseudoMoEModel` are decoder-only embedder classes.
`FlagReranker` is the encoder-only reranker. `FlagLLMReranker`,
`LayerWiseFlagLLMReranker`, and `LightWeightFlagLLMReranker` are decoder-only
rerankers.

## Verified Loader Signatures

```python
FlagAutoModel.from_finetuned(
    model_name_or_path,
    model_class=None,
    normalize_embeddings=True,
    use_fp16=True,
    use_bf16=False,
    query_instruction_for_retrieval=None,
    devices=None,
    pooling_method=None,
    trust_remote_code=None,
    query_instruction_format=None,
    truncate_dim=None,
    **kwargs,
)
```

```python
FlagAutoReranker.from_finetuned(
    model_name_or_path,
    model_class=None,
    use_fp16=False,
    trust_remote_code=None,
    **kwargs,
)
```

`**kwargs` are forwarded to the concrete class. Common forwarded kwargs include
`cache_dir`, `batch_size`, `query_max_length`, `passage_max_length` for
embedders, and `devices`, `batch_size`, `query_max_length`, `max_length`,
`normalize`, `cutoff_layers`, `compress_ratio`, and `compress_layers` for
rerankers.

## Core Method Signatures

```python
AbsEmbedder.encode_queries(
    queries,
    batch_size=None,
    max_length=None,
    convert_to_numpy=None,
    **kwargs,
)
```

```python
AbsEmbedder.encode_corpus(
    corpus,
    batch_size=None,
    max_length=None,
    convert_to_numpy=None,
    **kwargs,
)
```

```python
AbsReranker.compute_score(sentence_pairs, **kwargs)
```

```python
BGEM3FlagModel.compute_score(
    sentence_pairs,
    batch_size=None,
    max_query_length=None,
    max_passage_length=None,
    weights_for_different_modes=None,
    **kwargs,
)
```

## Auto Mapping Behavior

Auto loaders extract an effective model name from `model_name_or_path` with
this behavior:

- For `BAAI/bge-base-en-v1.5`, the effective name is `bge-base-en-v1.5`.
- For a local path ending in `checkpoint-1000`, the effective name is the
  parent directory name.
- The effective name is checked against the built-in mapping. If it is missing,
  auto loading raises a model-not-found `ValueError`.

For unmapped local checkpoints, supply `model_class` explicitly. For embedders,
also supply `pooling_method`, `query_instruction_format`, and
`trust_remote_code` if the checkpoint differs from standard encoder-only BGE
defaults. For rerankers, supply `model_class` and class-specific kwargs such as
`cutoff_layers` or compression options.

Some mapping entries are provider-qualified remote ids, while the loader still
uses `os.path.basename(...)` for lookup. If a remote id that appears supported
still misses the mapping, pass the concrete `model_class` instead of assuming
the checkpoint is unusable.

## Embedder Model Classes

| `model_class` id | Concrete class | Default behavior | Use when |
|---|---|---|---|
| `encoder-only-base` | `FlagModel` | Dense embeddings from encoder hidden states. Default concrete pooling is `cls`; auto mapping may choose `cls` or `mean`. | BGE, E5, GTE, BCE, or local encoder-only dense checkpoints. |
| `encoder-only-m3` | `BGEM3FlagModel` | M3 dense, sparse lexical weights, and ColBERT vectors. Default pooling is `cls`. | `bge-m3` or compatible M3 checkpoints. |
| `decoder-only-base` | `FlagLLMModel` | Last-token pooled decoder-only embeddings. | LLM embedding checkpoints such as BGE multilingual Gemma or E5/GTE instruct LLM variants. |
| `decoder-only-icl` | `FlagICLModel` | Last-token pooled decoder-only embeddings with optional few-shot examples. | ICL embedding checkpoints. |
| `decoder-only-pseudo_moe` | `FlagPseudoMoEModel` | Decoder-only embeddings with optional domain routing. Defaults favor bf16 and remote code. | Pseudo-MoE checkpoints that expose domain selection. |

Known embedder mapping families include BGE, Qwen3-Embedding, E5, GTE, SFR,
Linq, and BCE. Common mapped BGE names include `bge-en-icl`, `bge-m3`,
`bge-multilingual-gemma2`, and BGE English/Chinese base, small, and large
variants.

## Reranker Model Classes

| `model_class` id | Concrete class | Default behavior | Use when |
|---|---|---|---|
| `encoder-only-base` | `FlagReranker` | Cross-encoder sequence-classification scores. | BGE reranker base/large/v2-m3 or compatible encoder rerankers. |
| `decoder-only-base` | `FlagLLMReranker` | Decoder-only yes-token style relevance scores. | LLM reranker checkpoints such as Gemma-style rerankers. |
| `decoder-only-layerwise` | `LayerWiseFlagLLMReranker` | Scores from selected hidden layers. | Layerwise MiniCPM-style rerankers. |
| `decoder-only-lightweight` | `LightWeightFlagLLMReranker` | Layerwise scores with token compression. | Lightweight Gemma2-style rerankers with compression. |

Known reranker mappings include `bge-reranker-base`, `bge-reranker-large`,
`bge-reranker-v2-m3`, `bge-reranker-v2-gemma`,
`bge-reranker-v2-minicpm-layerwise`, and
`bge-reranker-v2.5-gemma2-lightweight`.

## Embedder Parameter Notes

- `normalize_embeddings`: normalizes dense embeddings before output. With
  normalized embeddings, inner product is cosine similarity. Set false only
  when downstream scoring expects raw vectors.
- `use_fp16`: half precision for speed on supported accelerators. Use false
  for CPU smoke checks and when numerical stability matters more than speed.
- `use_bf16`: bfloat16 for supported accelerators. If `convert_to_numpy=True`,
  non-CPU bf16 tensors are upcast to float32 before NumPy conversion.
- `query_instruction_for_retrieval`: instruction applied by `encode_queries`.
  It is not automatically applied by `encode_corpus`.
- `query_instruction_format`: template with two `{}` placeholders:
  instruction, then query. String values containing literal `\n` are converted
  to newlines by the base helpers.
- `devices`: `None` auto-selects all CUDA devices, then NPU, MUSA, MPS, then
  CPU. A string pins one device. A list enables multiprocessing across devices.
- `pooling_method`: `cls` and `mean` are typical encoder options;
  decoder-only embedders require `last_token` and raise if another pooling
  method is used.
- `trust_remote_code`: auto mapping can set this per mapped checkpoint. When
  `model_class` is supplied manually, auto embedder defaults it to false unless
  you pass a value.
- `truncate_dim`: slices final embedding dimensions to `[..., :truncate_dim]`.
  Use it only for checkpoints trained to support dimensional truncation.
- `batch_size`: default 256. Concrete embedders attempt to reduce batch size on
  runtime or OOM errors, but this should not replace choosing a sane starting
  batch size.
- `query_max_length` and `passage_max_length`: defaults are 512 for base
  embedders. Decoder-only LLM embedders often need larger values only when the
  model and memory budget support them.
- `cache_dir`: forwarded to Hugging Face `from_pretrained`. Prefer a caller
  supplied cache directory or standard Hugging Face cache environment variables;
  do not hard-code a machine-specific cache path in reusable code.

## M3 Output Contract

`BGEM3FlagModel.encode`, `encode_queries`, and `encode_corpus` return a dict:

```python
{
    "dense_vecs": numpy_array_or_none,
    "lexical_weights": list_or_dict_or_none,
    "colbert_vecs": list_or_array_or_none,
}
```

Set `return_dense`, `return_sparse`, and `return_colbert_vecs` per call. Keys
are always present; disabled modes have `None` values.

M3 helper methods:

- `convert_id_to_token(lexical_weights)`: maps sparse token-id weights back to
  decoded token strings.
- `compute_lexical_matching_score(weights_1, weights_2)`: computes sparse
  lexical matching for one pair of dicts or all pairs from two lists.
- `colbert_score(q_reps, p_reps)`: computes one ColBERT token interaction
  score from query and passage multivectors.
- `compute_score(sentence_pairs, ...)`: returns per-pair scores for `dense`,
  `sparse`, `colbert`, `sparse+dense`, and `colbert+sparse+dense`.

`weights_for_different_modes` is ordered `[dense_weight, sparse_weight,
colbert_weight]`. When omitted, all three weights default to `1.0`.

## Reranker Parameter Notes

- `sentence_pairs`: use `("query", "passage")` or a list of two-item pairs.
  A single pair still returns a list from standard rerankers.
- `query_max_length`: max token length for the query side. If omitted,
  concrete rerankers use their instance value or `max_length * 3 // 4`.
- `max_length`: max token length for passages and packed reranker inputs.
  Some prose examples use the name `passage_max_length`, but the verified
  reranker constructors and compute methods use `max_length`.
- `normalize`: applies a sigmoid to scores and maps them to 0-1. Use false
  when comparing raw logits or reproducing model-native scores.
- `cutoff_layers`: for layerwise and lightweight rerankers, choose which layers
  produce scores. One cutoff layer returns one score list; multiple cutoff
  layers return a list of score lists.
- `compress_ratio`: lightweight reranker compression ratio. Supported ratios
  are documented by the class as `1`, `2`, `4`, and `8`.
- `compress_layers`: lightweight reranker layers selected for compression.
- `use_bf16`: layerwise and lightweight classes accept it even though the auto
  reranker signature does not list it; pass through `**kwargs` when needed.
- `peft_path`: concrete decoder-only reranker classes can merge a PEFT adapter
  when supplied. Treat this as model loading, not fine-tuning.

## Device And Precision Behavior

When `devices=None`, embedders and rerankers try accelerator backends before CPU.
For deterministic smoke checks, pass `devices="cpu"` and disable fp16/bf16.
When using multiple devices, pass one process target per device, such as
`["cuda:0", "cuda:1"]`. Multi-device inference starts multiprocessing pools;
stop or delete model objects after use in long-running processes to release
memory.
