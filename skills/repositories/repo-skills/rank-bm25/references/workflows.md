# Retrieval Workflows

Read this for an end-to-end recipe that future agents can adapt without the
original repository. The package expects you to own preprocessing and to keep
raw documents aligned with their tokenized representation.

## Basic index and top-n retrieval

```python
from rank_bm25 import BM25Okapi

# Keep this list for output; its order is the index order.
documents = [
    "Hello there good man!",
    "It is quite windy in London",
    "How is the weather today?",
]

tokenized_documents = [document.split() for document in documents]
index = BM25Okapi(tokenized_documents)

query = "windy London"
tokenized_query = query.split()

scores = index.get_scores(tokenized_query)       # NumPy array, len == 3
best_documents = index.get_top_n(tokenized_query, documents, n=1)
# best_documents == ["It is quite windy in London"]
```

Do not pass `documents` to `get_top_n` if it has been filtered or reordered
since indexing. If you use lowercasing, punctuation normalization, stemming,
or stopword removal, apply the exact same transform to `documents` and
`query` before calling the package.

## Compare the implemented variants

```python
from rank_bm25 import BM25Okapi, BM25L, BM25Plus

classes = (BM25Okapi, BM25L, BM25Plus)
indexes = [cls(tokenized_documents) for cls in classes]
for cls, index in zip(classes, indexes):
    scores = index.get_scores(tokenized_query)
    print(cls.__name__, scores, index.get_top_n(tokenized_query, documents, n=2))
```

Use the same corpus, preprocessing, query set, and evaluation metric when
comparing algorithms. Score values are variant-specific; a threshold learned
for one class should not be reused for another without validation.

## Batch scoring for a candidate subset

```python
candidate_ids = [1, 2]  # positions in tokenized_documents
candidate_scores = index.get_batch_scores(tokenized_query, candidate_ids)
paired = list(zip(candidate_ids, candidate_scores))
# paired preserves [1, 2] order; it is not automatically sorted.
ranked_subset = sorted(paired, key=lambda item: item[1], reverse=True)
```

Validate every id before calling the method with
`0 <= id < index.corpus_size`. The returned list is aligned to the requested
ids, not to the complete corpus and not necessarily to descending score order.

## Raw-string corpus with a tokenizer

A callable tokenizer can be supplied as the second constructor argument:

```python
from rank_bm25 import BM25Okapi

def tokenize(text):
    return text.lower().split()

index = BM25Okapi(documents, tokenizer=tokenize)
scores = index.get_scores(tokenize("WINDY London"))
```

Because the package maps this callable through multiprocessing, define it at
module scope and keep it picklable. For notebooks, lambdas, closures, or
platforms where process spawning makes serialization awkward, pre-tokenize the
corpus yourself instead:

```python
index = BM25Okapi([tokenize(document) for document in documents])
```

## Deterministic smoke check

After installation, run the bundled helper:

```bash
python scripts/smoke_rank_bm25.py
python scripts/smoke_rank_bm25.py --variant bm25plus --top-n 2
```

It uses only a tiny in-memory fixture, performs no network or file writes, and
checks construction, full scores, top-n alignment, and batch-score alignment.
