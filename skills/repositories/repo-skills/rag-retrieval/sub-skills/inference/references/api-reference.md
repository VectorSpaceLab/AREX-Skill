# Inference API reference

This reference describes the installed `rag_retrieval` inference surface for reranking. It is intended to be usable without reopening the source repository.

## Public import

```python
from rag_retrieval import Reranker
```

The package public export is `Reranker`.

```python
Reranker(
    model_name: str,
    model_type: Optional[str] = None,
    verbose: int = 1,
    **kwargs,
)
```

`Reranker(...)` is a factory. It infers a ranker class from `model_type` or `model_name`, then returns an instance from the registered ranker map. Constructing it loads a Hugging Face model and tokenizer, so do not call it in no-download checks.

Common `**kwargs` accepted by registered rankers:

- `device`: explicit inference device such as `"cpu"`, `"cuda"`, `"cuda:0"`, `"mps"`, or `"npu"`; if omitted, the code prefers CUDA, then MPS, then NPU, then CPU.
- `dtype`: `"fp32"`, `"fp16"`, `"float16"`, `"bf16"`, or `"bfloat16"`; CPU forces float32.
- `verbose`: controls informational prints from the selected ranker.

## Model type mapping

Explicit `model_type` values map as follows:

| `model_type` | Internal class name | Registered in current package? | Notes |
| --- | --- | --- | --- |
| `"cross-encoder"` | `CorssEncoderRanker` | Yes | Typo is part of the package API: `CorssEncoderRanker`, not `CrossEncoderRanker`. |
| `"llm"` | `LLMRanker` | Yes | Uses causal LM logits for relevance scoring. |
| `"colbert"` | `ColBERTRanker` | No | Mapping exists, but the ranker import/registration is commented out. `Reranker(..., model_type="colbert")` returns `None` after printing a dependency-style message. |

Automatic `model_name` inference checks lowercase substrings in order:

| Model-name substring | Selected class |
| --- | --- |
| `bge-reranker-base` | `CorssEncoderRanker` |
| `bge-reranker-large` | `CorssEncoderRanker` |
| `bge-reranker-v2-m3` | `CorssEncoderRanker` |
| `bce` | `CorssEncoderRanker` |
| `bge-m3` | `ColBERTRanker` |
| `bge-reranker-v2-gemma` | `LLMRanker` |
| `bge-reranker-v2-minicpm-layerwise` | `LLMRanker` |

If auto-detection finds no mapping, `Reranker` warns and defaults to `CorssEncoderRanker`. If an explicit unsupported `model_type` is provided, it prints a supported-type message and returns `None`.

Important edge case: `BAAI/bge-m3` contains `bge-m3`, so auto-detection selects unregistered `ColBERTRanker`. Use a supported cross-encoder model such as `BAAI/bge-reranker-v2-m3`, or pass a supported `model_type` only when the model architecture matches that ranker.

## Registered rankers

The current `AVAILABLE_RANKERS` surface contains only:

- `CorssEncoderRanker`
- `LLMRanker`

`ColBERTRanker` is not registered, even though constants and docs mention `colbert`.

## Cross-encoder ranker

`CorssEncoderRanker` loads `AutoModelForSequenceClassification` and `AutoTokenizer`.

```python
ranker.compute_score(
    sentence_pairs,
    batch_size: int = 256,
    max_length: int = 512,
    normalize: bool = False,
    enable_tqdm: bool = True,
)
```

- `sentence_pairs` should be a list of two-item query/document pairs, for example `[[query, doc], ...]`.
- Returns a `float` for one scored pair and a list of floats for multiple pairs.
- Scores are logits unless `normalize=True` or the model path/name contains `"bce"`; BCE scores are always passed through sigmoid.
- `max_length` is the tokenizer truncation length for direct pair scoring.

```python
ranker.rerank(
    query: str,
    docs,
    batch_size: int = 256,
    max_length: int = 512,
    normalize: bool = False,
    long_doc_process_strategy: str = "max_score_slice",
)
```

- `docs` should be a list of strings. Invalid or empty docs are removed; each kept doc is truncated to at most 128000 characters before tokenization.
- Returns `RankedResults` for valid non-empty inputs.
- Returns the legacy dict `{"rerank_docs": [], "rerank_scores": []}` when `query` is empty/`None` or all docs are empty/invalid.
- `long_doc_process_strategy="max_length_truncation"` scores one truncated query-document pair per doc.
- `long_doc_process_strategy="max_score_slice"` chunks long docs and uses each document's maximum chunk score.

## LLM ranker

`LLMRanker` loads `AutoModelForCausalLM` and `AutoTokenizer` with `trust_remote_code=True`.

```python
ranker.compute_score(
    sentence_pairs,
    batch_size: int = 16,
    max_length: int = 1024,
    normalize: bool = False,
    prompt: str = None,
    cutoff_layers: list = None,
    enable_tqdm: bool = True,
)
```

- Default prompt: `Given a query A and a passage B, determine whether the passage contains an answer to the query by providing a prediction of either 'Yes' or 'No'.`
- Non-layerwise LLM rankers score the final-token logit for `Yes`.
- Models whose name/path contains `layerwise` use `cutoff_layers` in the model call and read scores from the returned layerwise logits.
- `normalize=True` applies sigmoid after score collection.

```python
ranker.rerank(
    query: str,
    docs,
    batch_size: int = 256,
    normalize: bool = False,
    prompt: str = None,
    cutoff_layers: list = None,
    max_length: int = 1024,
    long_doc_process_strategy: str = "max_score_slice",
)
```

The same empty-input legacy dict behavior and long-document strategies apply. LLM long-document preprocessing formats inputs as `A: {query}`, `B: {doc}`, then appends the prompt.

## Result objects

Reranking normally returns a Pydantic `RankedResults` object:

```python
Result(
    doc_id: Union[int, str],
    text: str,
    score: Optional[float] = None,
    rank: Optional[int] = None,
)

RankedResults(
    results: List[Result],
    query: str,
    has_scores: bool = False,
)
```

Helpers:

```python
ranked.results_count() -> int
ranked.top_k(k: int) -> List[Result]
ranked.get_score_by_docid(doc_id: Union[int, str]) -> Optional[float]
```

When `has_scores=True`, `top_k` sorts by descending score. Otherwise it sorts by ascending rank. `get_score_by_docid` returns `None` if the doc id is absent.

`Result` validation requires at least one of `score` or `rank`.

## Limitations to preserve

- ColBERT inference is not available in the current package surface.
- Constructor calls can download/load model artifacts; use signature/registration inspection for no-download checks.
- LLM rankers use `trust_remote_code=True`, so only load trusted local/model sources.
- The cross-encoder class is spelled `CorssEncoderRanker` in the package; preserve the typo when inspecting internals.
- Empty rerank inputs return a legacy dict rather than `RankedResults`; robust code should handle both.
