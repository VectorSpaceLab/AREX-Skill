# API Reference: Index-Free Reranking

This reference covers the index-free methods on `ragatouille.RAGPretrainedModel` in RAGatouille `0.0.9post2`. These methods still require a loaded pretrained model instance, but they do not create or read a persisted ColBERT index.

## Compatibility Baseline

- Import module: `ragatouille`.
- Distribution version verified during skill generation: `RAGatouille 0.0.9.post2`.
- RAGatouille imports were verified with a legacy-compatible LangChain set. Newer LangChain `1.x` can miss `langchain.retrievers.document_compressors.base`, which affects top-level imports and integration helpers.
- `fast-pytorch-kmeans` may require `psutil` to import cleanly.
- Model loading, checkpoint download, GPU use, and real reranking/search execution are not safe lightweight verification steps.

## Load a Model Before Calling These Methods

Typical entry point:

```python
from ragatouille import RAGPretrainedModel

rag = RAGPretrainedModel.from_pretrained("colbert-ir/colbertv2.0")
```

`from_pretrained()` can download model files and initialize ColBERT runtime state. Use it only when network/model-cache/hardware side effects are acceptable.

## `rerank()`

Signature verified from installed package facts:

```python
RAGPretrainedModel.rerank(
    self,
    query: str | list[str],
    documents: list[str],
    k: int = 10,
    zero_index_ranks: bool = False,
    bsize: "auto" | int = "auto",
)
```

Behavior:

- Encodes the supplied `documents` and `query` in memory, scores with ColBERT MaxSim, and returns the top `k` candidates.
- Does not persist an index and does not attach document IDs or metadata.
- Source docstring says ranks start at `1` unless `zero_index_ranks=True`, but the underlying index-free search enumerates ranks from `0`; with `zero_index_ranks=True`, ranks become `-1, 0, ...`. Treat observed rank values as implementation-specific and prefer result order when possible.
- Returns `None` after printing a warning if `k > len(documents)`.
- Prints a warning for duplicate document strings.
- Prints a warning for more than 1000 documents and recommends a persisted index.

Single-query result shape:

```json
[
  {"content": "candidate text", "score": 12.34, "rank": 0, "result_index": 2}
]
```

Multi-query result shape:

```json
[
  [
    {"content": "candidate text for query 1", "score": 12.34, "rank": 0, "result_index": 2}
  ],
  [
    {"content": "candidate text for query 2", "score": 9.87, "rank": 0, "result_index": 0}
  ]
]
```

Required keys observed in the underlying index-free implementation are `content`, `score`, `rank`, and `result_index`. `result_index` is the zero-based position of the chosen string in the input `documents` list.

## `encode()`

Signature verified from installed package facts:

```python
RAGPretrainedModel.encode(
    self,
    documents: list[str],
    bsize: "auto" | int = "auto",
    document_metadatas: list[dict] | None = None,
    verbose: bool = True,
    max_document_length: "auto" | int = "auto",
)
```

Behavior:

- Encodes `documents` into transient in-memory attributes on the model object.
- Does not split documents. Pre-chunk long source text before calling `encode()`.
- Uses version-specific max-token behavior. The notebook describes dynamic max-token selection for `max_document_length="auto"`; in the inspected `0.0.9post2` source, `auto` sets the inference document length to the base model maximum. Passing an explicit oversized `max_document_length` triggers a 90th-percentile estimate, caps to the model maximum, and can print a long-document slowdown warning.
- Further `encode()` calls append to the same in-memory collection rather than replacing it.
- `document_metadatas`, when provided, should have one dict per document. The implementation stores and extends this list for later result metadata, but it does not perform the robust length validation used by persisted indexing.
- In RAGatouille `0.0.9post2`, appending a batch without `document_metadatas` after metadata already exists can hit a source typo (`in_memory_metadatas` instead of `in_memory_metadata`). Keep metadata usage consistent across appended batches.
- `bsize="auto"` starts at `32` and can be reduced internally for long document token lengths.

Return value: no explicit return value. With `verbose=True`, the wrapper prints encoding progress and the model prints tensor shapes.

## `search_encoded_docs()`

Signature verified from installed package facts:

```python
RAGPretrainedModel.search_encoded_docs(
    self,
    query: str | list[str],
    k: int = 10,
    bsize: int = 32,
) -> list[dict[str, object]]
```

Behavior:

- Searches only documents previously added with `encode()` on the same model instance.
- Returns the same index-free result keys as `rerank()`: `content`, `score`, `rank`, and `result_index`.
- Adds `document_metadata` when in-memory metadata exists for the matching `result_index`.
- Raises an attribute error if called before any `encode()` call created the in-memory collection.
- Can fail if `k` exceeds the number of encoded documents because encoded search calls `torch.topk()` directly instead of using the `rerank()` pre-check.

Single-query result with metadata:

```json
[
  {
    "content": "encoded document text",
    "score": 10.5,
    "rank": 0,
    "result_index": 1,
    "document_metadata": {"source": "draft", "section": "faq"}
  }
]
```

Multi-query result shape should be treated as a list of lists from the shared index-free search implementation. In RAGatouille `0.0.9post2`, metadata injection iterates the top-level result object as if it were a flat list, so metadata handling for multi-query encoded search is fragile. Prefer one query at a time when metadata is required.

## `clear_encoded_docs()`

Signature verified from installed package facts:

```python
RAGPretrainedModel.clear_encoded_docs(self, force: bool = False)
```

Behavior:

- Deletes in-memory collection, metadata, encodings, document masks, and the dynamic inference-length flag.
- With `force=False`, prints a warning and sleeps for 10 seconds before deletion.
- With `force=True`, clears immediately.
- After clearing, call `encode()` again before `search_encoded_docs()`.

## Result Shape Validation

Use `scripts/check_result_shapes.py` to validate JSON examples or saved samples offline. The script accepts either a single result list or a multi-query list of result lists and can require encoded-search metadata when relevant.
