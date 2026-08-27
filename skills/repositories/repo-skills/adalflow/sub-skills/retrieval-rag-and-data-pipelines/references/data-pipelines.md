# Data Pipelines

This reference covers the document and transform layer used before retrieval. Keep it simple: normalize to `Document`, chunk when needed, optionally embed, and persist the corpus if the same data will be reused.

## Core contracts

| Type | Purpose | Important notes |
| --- | --- | --- |
| `Document` | Text container for retrieval, chunking, and context assembly. | Holds `text`, optional `meta_data`, `vector`, `id`, `order`, `score`, `parent_doc_id`, and `estimated_num_tokens`. `estimated_num_tokens` is auto-filled when omitted. `Document.from_dict(...)` expects `text` and `meta_data`. |
| `RetrieverOutput` | Standard retriever return type. | Contains `doc_indices`, optional `doc_scores`, optional `query`, and optional `documents`. A retriever may fill only indices and scores first, then attach `documents` later. |

## Verified runtime surface

- `TextSplitter(split_by="word"|"sentence"|"page"|"passage"|"token", chunk_size=800, chunk_overlap=200, batch_size=1000, separators=...)`
- `ToEmbeddings(embedder, batch_size=50)`
- `RetrieverOutputToContextStr(deduplicate=False)`
- `LocalDB(name="LocalDB", items=[], transformed_items={}, transformer_setups={}, mapper_setups={}, index_path="index.faiss")`

## Text splitting

`TextSplitter` turns a list of `Document` objects into a new list of chunked `Document` objects.

### Behavior to remember

- `split_by` must be one of the supported separators.
- `chunk_size` must be greater than zero.
- `chunk_overlap` must be non-negative and strictly smaller than `chunk_size`.
- `TextSplitter.call(...)` expects a list of `Document` objects.
- The output chunks preserve `meta_data`, set `parent_doc_id`, and assign `order`.
- `split_by="token"` uses the built-in tokenizer path rather than `str.split(...)`.

### Minimal recipe

```python
from adalflow.components.data_process import TextSplitter
from adalflow.core.types import Document

splitter = TextSplitter(split_by="word", chunk_size=400, chunk_overlap=200)
documents = [Document(text="A long passage.", meta_data={"title": "demo"})]
chunks = splitter.call(documents)
```

### Practical guidance

- Use `word` or `sentence` when semantic boundaries matter more than exact token budgets.
- Use `token` when the downstream model budget must be tracked tightly.
- For non-text sources, extract plain text first and then feed `Document` objects to the splitter.
- When a corpus is very small, avoid oversized overlap because repeated content can dominate retrieval.

## Embedding transform

`ToEmbeddings` is the retrieval-side bridge from chunked documents to vectors.

### Behavior to remember

- It deep-copies the input documents.
- It embeds `chunk.text` values in batches through a `BatchEmbedder`.
- It writes the resulting vector into each `Document.vector` field.
- It does not mutate the original input list.

### Minimal recipe

```python
from adalflow.components.data_process import ToEmbeddings

# embedder is constructed elsewhere
transform = ToEmbeddings(embedder=embedder, batch_size=50)
vectorized_docs = transform(chunks)
```

### Practical guidance

- Keep the embedder and vector store dimension contract stable once an index is built.
- Rebuild vectors whenever the embedder model changes.
- For larger corpora, batch in a way that matches your downstream service limits.

## Context assembly

`RetrieverOutputToContextStr` converts one or many `RetrieverOutput` objects into a single context string.

### Behavior to remember

- `deduplicate=True` removes repeated chunk ids before concatenation.
- It accepts a single `RetrieverOutput` or a list of outputs.
- It concatenates chunk text in retrieval order.

### Minimal recipe

```python
from adalflow.components.data_process import RetrieverOutputToContextStr

context_builder = RetrieverOutputToContextStr(deduplicate=True)
context_str = context_builder(retriever_outputs)
```

### Practical guidance

- Use deduplication when query expansion or multi-pass retrieval can return the same chunk more than once.
- Normalize whitespace if your prompt template is sensitive to leading spaces or exact string comparisons.

## LocalDB

`LocalDB` stores raw items and transformed items together so the retrieval pipeline can be rebuilt without recomputing everything from scratch.

### What it is good for

- Keeping the raw documents alongside processed chunks.
- Replaying the same transformer pipeline later.
- Saving and restoring a local experiment state.
- Filtering or staging different transform outputs under different keys.

### Key operations

- `load(items)` replaces the in-memory corpus.
- `extend(items, apply_transformer=True)` appends new items.
- `register_transformer(transformer, key=..., map_fn=...)` records a transform for reuse.
- `transform(key=...)` or `transform(transformer=..., key=...)` applies the transform.
- `save_state(filepath)` writes the full state to disk.
- `load_state(filepath)` restores the saved state.

### Minimal recipe

```python
from adalflow.core.db import LocalDB

local_db = LocalDB(name="rag-cache")
local_db.load(documents)
local_db.register_transformer(transformer=splitter, key="chunks")
local_db.transform(key="chunks")
local_db.save_state("rag-cache.pkl")
```

### Practical guidance

- Use an explicit save path for portability and repeatability.
- Treat transforms that expand one document into many chunks as rebuild-friendly, not index-in-place friendly.
- If the corpus changes materially, rebuild the stored state instead of trying to merge stale chunks.
- `load_state(...)` may return `None` when the file does not exist.

## A clean pipeline shape

```python
raw_documents -> Document -> TextSplitter -> ToEmbeddings -> LocalDB
```

A good rule is to keep the raw `Document` records and the processed chunk records available together, so the retriever can be rebuilt or filtered without re-ingesting the source data.
