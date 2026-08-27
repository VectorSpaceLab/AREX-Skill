# Inference workflows

Use these patterns to score pairs, rerank passages, handle long documents, configure LLM rankers, and validate the installed API surface without downloading models.

## No-download API check

Do this before any model construction when the user asks for an environment check or wants to avoid Hugging Face downloads:

From this sub-skill directory, run:

```bash
python scripts/reranker_api_smoke.py
```

From the `references/` directory, run:

```bash
python ../scripts/reranker_api_smoke.py
```

The script imports `rag_retrieval`, inspects `Reranker` and registered ranker method signatures, constructs only `Result`/`RankedResults`, prints JSON, and exits nonzero if expected APIs are missing. It does not instantiate a transformer model.

## Choose a supported ranker

Prefer explicit `model_type` when the model architecture is known:

```python
from rag_retrieval import Reranker

ranker = Reranker(
    "BAAI/bge-reranker-base",
    model_type="cross-encoder",
    device="cuda",
    dtype="fp16",
    verbose=0,
)
```

Use cross-encoder for `BAAI/bge-reranker-base`, `BAAI/bge-reranker-large`, `BAAI/bge-reranker-v2-m3`, and BCE-style sequence-classification rerankers. Use LLM for `BAAI/bge-reranker-v2-gemma` or `BAAI/bge-reranker-v2-minicpm-layerwise`.

Do not choose `model_type="colbert"` for this package version. The mapping name exists, but the ColBERT inference ranker is not registered.

## Score query-document pairs

```python
from rag_retrieval import Reranker

ranker = Reranker("BAAI/bge-reranker-base", model_type="cross-encoder", verbose=0)

query = "what is panda?"
pairs = [
    [query, "hi"],
    [query, "The giant panda is a bear species endemic to China."],
]

scores = ranker.compute_score(
    pairs,
    batch_size=64,
    max_length=512,
    normalize=False,
    enable_tqdm=False,
)
print(scores)
```

Expected shape:

- One pair returns a single `float`.
- Multiple pairs return `list[float]`.
- Cross-encoder BGE scores are raw logits unless `normalize=True`.
- BCE model names/paths containing `bce` are always sigmoid-normalized by the implementation, even when `normalize=False`.

## Rerank passages

```python
from rag_retrieval import Reranker

ranker = Reranker("BAAI/bge-reranker-base", model_type="cross-encoder", verbose=0)

query = "what is panda?"
docs = [
    "hi",
    "The giant panda is a bear species endemic to China.",
]

ranked = ranker.rerank(
    query,
    docs,
    batch_size=64,
    max_length=512,
    normalize=False,
    long_doc_process_strategy="max_score_slice",
)

for item in ranked.top_k(2):
    print(item.rank, item.doc_id, item.score, item.text)

print("count", ranked.results_count())
print("original doc 0 score", ranked.get_score_by_docid(0))
```

`doc_id` is the original index among valid retained docs. Empty or non-string docs are filtered before ranking, so sanitize upstream if stable external ids are required.

## Handle empty-input compatibility

`rerank` returns a `RankedResults` object only when query and docs survive validation. Empty inputs return a legacy dict:

```python
ranked = ranker.rerank(query, docs)

if isinstance(ranked, dict):
    scores = ranked.get("rerank_scores", [])
else:
    scores = [result.score for result in ranked.results]
```

Use this guard in production wrappers that might receive empty queries or empty document lists.

## Long-document strategy

Use `max_score_slice` when recall matters for long passages:

```python
ranked = ranker.rerank(
    query,
    long_docs,
    max_length=512,
    long_doc_process_strategy="max_score_slice",
)
```

How it behaves:

- Tokenizes the query without truncation for cross-encoders.
- Computes available document-token budget as `max_length - len(query_tokens) - 2`.
- Splits long docs into overlapping chunks.
- Uses each document's maximum chunk score for final ranking.

Use `max_length_truncation` when speed and deterministic one-pass behavior matter more than finding matches later in a long passage:

```python
ranked = ranker.rerank(
    query,
    docs,
    max_length=512,
    long_doc_process_strategy="max_length_truncation",
)
```

If cross-encoder `max_score_slice` raises `Your query is too long!`, shorten the query or increase `max_length`; the implementation asserts that the remaining document budget must exceed 100 tokens.

## LLM ranker scoring

```python
from rag_retrieval import Reranker

ranker = Reranker(
    "BAAI/bge-reranker-v2-gemma",
    model_type="llm",
    dtype="fp16",
    verbose=0,
)

pairs = [["what is panda?", "The giant panda is a bear species endemic to China."]]
score = ranker.compute_score(
    pairs,
    batch_size=4,
    max_length=1024,
    normalize=False,
    prompt=None,
    enable_tqdm=False,
)
```

For non-layerwise LLM rankers, the score is the final-position logit for the token `Yes`. `normalize=True` applies sigmoid to these scores.

## LLM prompt override

Use a prompt override when reranking criteria differ from answer containment:

```python
prompt = (
    "Given query A and passage B, answer only Yes or No: "
    "is B directly useful for answering A?"
)

ranked = ranker.rerank(
    query,
    docs,
    prompt=prompt,
    max_length=1024,
    batch_size=8,
)
```

Keep prompts short because the implementation appends the prompt after the formatted query/passage and pads to `max_length + prompt_length`.

## MiniCPM layerwise cutoff

For `BAAI/bge-reranker-v2-minicpm-layerwise`, pass `cutoff_layers` when reproducing layerwise behavior:

```python
ranker = Reranker(
    "BAAI/bge-reranker-v2-minicpm-layerwise",
    model_type="llm",
    dtype="fp16",
    verbose=0,
)

scores = ranker.compute_score(
    pairs,
    cutoff_layers=[28],
    batch_size=4,
    max_length=1024,
    enable_tqdm=False,
)

ranked = ranker.rerank(
    query,
    docs,
    cutoff_layers=[28],
    batch_size=4,
    max_length=1024,
)
```

Only layerwise models use `cutoff_layers`; ordinary LLM rankers ignore it because the package calls the model without that argument unless `"layerwise"` appears in the model name/path.

## Local model paths and downloads

`model_name` can be a Hugging Face model id or a local model directory. If automatic download is undesirable or unavailable, download/cache the model outside the agent workflow and pass the local model directory at runtime:

```python
ranker = Reranker(local_model_dir, model_type="cross-encoder", verbose=0)
```

When writing reusable code, do not hard-code local paths. Accept the model id/path from user configuration.

## Defensive wrapper pattern

```python
def build_reranker(model_name, model_type=None, **kwargs):
    from rag_retrieval import Reranker

    ranker = Reranker(model_name, model_type=model_type, **kwargs)
    if ranker is None:
        raise RuntimeError(
            f"Unsupported or unavailable rag_retrieval ranker for model_type={model_type!r}. "
            "Use 'cross-encoder' or 'llm'; ColBERT inference is not registered."
        )
    return ranker
```

Use this wrapper because `Reranker` prints errors and returns `None` for unsupported or unregistered ranker types instead of raising a structured exception.
