# Core workflows

All examples are bounded, local, and CPU-safe. They disable progress output so they can be embedded in tests or batch jobs. Use the tokenizer route for splitter/stopword/stemmer choices and the persistence route for writing or reopening index files.

## 1. Index text tokens and return IDs

```python
import bm25s

texts = ["red cat likes purr", "blue dog likes play", "fish swim water"]
corpus_tokens = bm25s.tokenize(texts, stopwords=None, show_progress=False)
retriever = bm25s.BM25(method="lucene")
retriever.index(corpus_tokens, show_progress=False)

queries = bm25s.tokenize(["cat purr", "fish"], stopwords=None, show_progress=False)
results = retriever.retrieve(
    queries, k=2, return_as="tuple", sorted=True, show_progress=False
)
assert results.documents.shape == (2, 2)
assert results.scores.shape == (2, 2)
```

The module tokenizer returns a vocabulary-carrying object by default in this revision. Passing a list of token strings is also valid when the caller already owns the vocabulary convention. For a stateful corpus/query vocabulary, use `Tokenizer` and `update_vocab=False` for queries.

## 2. Return aligned metadata

Keep the text used for indexing separate from the records returned to the application. Validate alignment before indexing or retrieval because the current low-level API does not validate a supplied display corpus length.

```python
import bm25s

records = [
    {"id": "r", "title": "Red cat", "text": "red cat likes purr"},
    {"id": "b", "title": "Blue dog", "text": "blue dog likes play"},
]
texts = [record["text"] for record in records]
corpus_tokens = bm25s.tokenize(texts, stopwords=None, show_progress=False)
num_docs = len(corpus_tokens.ids) if hasattr(corpus_tokens, "ids") else len(corpus_tokens)
if len(records) != num_docs:
    raise ValueError("records must have one entry per indexed document")

retriever = bm25s.BM25(corpus=records)
retriever.index(corpus_tokens, show_progress=False)
query = bm25s.tokenize(["red purr"], stopwords=None, show_progress=False)
result = retriever.retrieve(query, k=1, show_progress=False)
assert result.documents[0, 0]["id"] == "r"
```

The same mapping can be supplied per call with `retrieve(query, corpus=records)`. A long corpus is not proof of correctness: only selected positions are looked up, so reordered metadata can silently produce plausible but false answers. The bounded [scripts/metadata_retrieval.py](../scripts/metadata_retrieval.py) fixture demonstrates this pattern and emits JSON.

## 3. Numeric corpus and explicit vocabulary

Use numeric IDs only when the query producer can use the same ID space. A `Tokenized` object or `(ids, vocab)` pair carries the mapping with the corpus:

```python
import bm25s
from bm25s.tokenization import Tokenized

ids = [[0, 1], [1, 2], [3]]
vocab = {"cat": 0, "dog": 1, "fish": 2, "bird": 3}
# Tokenized vocab values are dense IDs used in its ids lists.
corpus = Tokenized(ids=ids, vocab=vocab)
retriever = bm25s.BM25()
retriever.index(corpus, create_empty_token=True, show_progress=False)
result = retriever.retrieve([[0]], k=2, show_progress=False)
```

For a bare `list[list[int]]`, the model creates its own mapping and exposes it as `retriever.vocab_dict`. Capture that mapping for query construction instead of guessing the dense internal positions:

```python
numeric_docs = [[10, 20], [20, 30], [40]]
retriever = bm25s.BM25()
retriever.index(numeric_docs, show_progress=False)
query_id = retriever.vocab_dict[10]
result = retriever.retrieve([[query_id]], k=2, show_progress=False)
```

The second example is intentionally different: `vocab_dict` maps the caller's token ID to the model's internal column. Do not use this bare-ID form with a separately generated query vocabulary unless you persist and share the mapping yourself.

## 4. Compare scoring variants

Use the same tokenized corpus for each model and record both `method` and `idf_method`:

```python
models = {}
for method in ("robertson", "lucene", "atire", "bm25l", "bm25+"):
    model = bm25s.BM25(method=method, delta=0.5)
    model.index(corpus_tokens, show_progress=False)
    models[method] = model.retrieve(query, k=2, show_progress=False)
```

Do not compare only document IDs on tiny tied fixtures: score scales differ, Robertson may clamp common-term IDF to zero, and BM25L/BM25+ add non-occurrence contributions. Use explicit `k1`, `b`, and `delta` when reproducing a published configuration. A typo such as `"bm25plus"` is rejected at index time.

## 5. Apply a candidate mask

```python
import numpy as np

mask = np.array([1, 0], dtype=np.float32)  # one value per indexed document
result = retriever.retrieve(
    query, k=2, weight_mask=mask, sorted=True, show_progress=False
)
```

The mask changes scores; it is not a hard deletion operation. For a strict security or tenant filter, filter candidate records outside the retrieval call or verify returned IDs after retrieval. Validate `mask.ndim == 1` and `len(mask) == retriever.scores["num_docs"]` before calling.

## 6. Empty and unknown query checks

```python
empty = retriever.retrieve([[]], k=2, show_progress=False)
assert empty.scores.shape == (1, 2)
assert (empty.scores[0] == 0).all()

unknown = retriever.retrieve([["term-never-seen"]], k=2, show_progress=False)
assert unknown.scores.shape == (1, 2)
```

These are valid retrieval calls but not useful relevance rankings. With integer queries, `retrieve` filters unknown IDs. If all IDs are unknown and the index has no usable empty-token sentinel, expect a `ValueError`. Do not call `get_scores([])` as an empty-query substitute.

## 7. Bounded local helper

Run the metadata fixture from any current working directory using the installed package:

```bash
python /path/to/core-indexing-retrieval/scripts/metadata_retrieval.py
python /path/to/core-indexing-retrieval/scripts/metadata_retrieval.py --query "dog play" --k 1
```

The script uses no relative data files, network calls, repository paths, or accelerator-specific imports. Its JSON output contains only the selected metadata and numeric scores, making it suitable for a smoke test or an agent handoff.
