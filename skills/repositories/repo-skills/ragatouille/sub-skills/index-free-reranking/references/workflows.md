# Workflows: Rerank and Index-Free Encoded Search

These recipes assume a `RAGPretrainedModel` instance is already loaded. Loading a pretrained checkpoint can download files and initialize model runtime state, so do it only when those side effects are acceptable.

## Rerank External Retriever Results

Use this when an existing retriever, vector DB, BM25 search, API, or application pipeline already returned candidate text strings.

```python
from ragatouille import RAGPretrainedModel

rag = RAGPretrainedModel.from_pretrained("colbert-ir/colbertv2.0")

query = "Which policy explains the release edits?"
candidates = external_retriever.search(query, k=50)  # convert to list[str]
texts = [item["content"] for item in candidates]

reranked = rag.rerank(query=query, documents=texts, k=5, bsize="auto")
```

Checklist:

1. Convert candidate objects to plain strings before passing `documents`.
2. Keep the candidate set small. The RAGatouille notebook recommends reranking handfuls of documents on CPU or a few hundred on GPU; larger recurring workloads should use a persisted index.
3. Ensure `k <= len(documents)` or `rerank()` returns `None` after printing a warning.
4. Preserve original candidate metadata outside RAGatouille by joining on `result_index` if needed.

Example metadata rejoin:

```python
for result in reranked:
    original = candidates[result["result_index"]]
    result["source"] = original.get("source")
```

## Rerank Multiple Queries

```python
queries = ["What is the editing policy?", "Who founded the studio?"]
results_by_query = rag.rerank(query=queries, documents=texts, k=3)

for query, results in zip(queries, results_by_query):
    print(query, results[0]["content"])
```

The multi-query return shape is nested: `list[list[dict]]`. Do not process it as a flat result list.

## Encode a Small Transient Collection

Use this when the whole working set is temporary and small enough that disk index creation is unnecessary.

```python
from ragatouille import RAGPretrainedModel

rag = RAGPretrainedModel.from_pretrained("colbert-ir/colbertv2.0")

documents = [
    "Short chunk about export controls.",
    "Short chunk about licensing policy.",
]
metadatas = [
    {"doc_id": "a", "section": "export"},
    {"doc_id": "b", "section": "licensing"},
]

rag.encode(
    documents=documents,
    document_metadatas=metadatas,
    bsize="auto",
    max_document_length="auto",
)

results = rag.search_encoded_docs(query="What is the licensing rule?", k=1)
```

Important details:

- `encode()` does not split documents. Split long source documents before encoding.
- `max_document_length="auto"` follows version-specific behavior; in inspected `0.0.9post2` source it uses the base model maximum, while explicit oversized lengths trigger a capped 90th-percentile estimate and slowdown warning.
- `search_encoded_docs()` searches only the in-memory state of that `rag` object.
- Metadata appears under `document_metadata` for single-query encoded search when metadata was encoded.

## Append More Encoded Documents

Subsequent `encode()` calls append to existing in-memory state.

```python
rag.encode(
    documents=["New temporary chunk about refunds."],
    document_metadatas=[{"doc_id": "c", "section": "refunds"}],
    verbose=False,
)

results = rag.search_encoded_docs("refund policy", k=2)
```

Use this for genuinely incremental, short-lived collections. If the state is stale or the collection grows large, clear it and consider a persisted index.

## Clear Stale Encoded State

```python
rag.clear_encoded_docs(force=True)
rag.encode(["Fresh replacement chunk."], verbose=False)
results = rag.search_encoded_docs("replacement", k=1)
```

Use `force=True` in automation so the call does not sleep for 10 seconds. Use the default `force=False` only when an interactive safety delay is desired.

## Choose Between Rerank, Encoded Search, and Persisted Index

| Need | Best API |
| --- | --- |
| Rescore top candidates from another retriever | `rerank()` |
| Search a small temporary collection repeatedly inside one process | `encode()` + `search_encoded_docs()` |
| Keep documents searchable across restarts | Persisted index via `../../pretrained-indexing-search/SKILL.md` |
| Search thousands of documents efficiently | Persisted index via `../../pretrained-indexing-search/SKILL.md` |
| Integrate with LangChain retrievers or compressors | `../../integrations-export/SKILL.md` |

## Validate Sample Result Shapes Offline

The bundled helper validates representative JSON without loading RAGatouille:

From the `index-free-reranking` sub-skill directory:

```bash
python scripts/check_result_shapes.py sample-results.json --mode rerank
python scripts/check_result_shapes.py sample-results.json --mode encoded-search --require-metadata
```

Use this for docs, tests, fixtures, or application contracts where model execution would be too expensive or unsafe.
