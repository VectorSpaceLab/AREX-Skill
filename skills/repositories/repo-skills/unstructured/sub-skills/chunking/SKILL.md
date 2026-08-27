---
name: chunking
description: "Configure and validate Unstructured post-partition chunking for
  RAG, embedding, and downstream processing. Use when an agent needs
  chunk_elements(), chunk_by_title(), partition-integrated chunking kwargs,
  character/token limits, overlap, table chunking behavior, or orig_elements
  metadata decisions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Chunking

Use this sub-skill after a document has been partitioned into Unstructured elements, or when a partition call should return chunks directly via `chunking_strategy`.

## Start Here

1. Choose the entry point:
   - Use `unstructured.chunking.basic.chunk_elements(elements, ...)` when you already have elements and want sequential size-based chunks.
   - Use `unstructured.chunking.title.chunk_by_title(elements, ...)` when `Title` elements should start sections and optional page boundaries should split sections.
   - Use `partition(..., chunking_strategy="basic" | "by_title", ...)` when the partitioner supports integrated chunking and you want one call.
2. Pick one sizing mode:
   - Character mode: `max_characters` is the hard maximum, `new_after_n_chars` is the soft preferred boundary.
   - Token mode: `max_tokens` is the hard maximum, `new_after_n_tokens` is the soft preferred boundary, and `tokenizer` is required.
3. Decide table handling before overlap:
   - Default `isolate_table=True` keeps `Table` and `TableChunk` separate from surrounding text.
   - Default `repeat_table_headers=True` repeats detected headers on continuation table chunks.
   - Use `skip_table_chunking=True` only when oversized tables must pass through unchanged.
4. Decide metadata weight:
   - Default `include_orig_elements=True` preserves original elements in `metadata.orig_elements`.
   - Set `include_orig_elements=False` for lighter JSON payloads when original metadata is not needed.

## Key References

- `references/api-reference.md`: public functions, parameters, defaults, output element types, and validation rules.
- `references/workflows.md`: RAG, table-heavy, integrated partitioning, token-based, and validation workflows.
- `references/troubleshooting.md`: common `ValueError`s, token extra issues, overlap pollution, table edge cases, and metadata size trade-offs.
- `scripts/chunk_elements_preview.py`: preview chunking behavior from element JSON and summarize chunk types, lengths, table metadata, and `orig_elements` counts.

## Routing Boundaries

- Route element creation, file parsing, strategies like OCR/table extraction, and partition signatures to the `partitioning` sub-skill.
- Route JSON schema interpretation, `elements_to_json()`, `elements_from_json()`, and serialized metadata payload design to the `elements-and-metadata` sub-skill.
- Keep this sub-skill focused on chunking already-created elements or partition-integrated chunking arguments.

## Quick Patterns

```python
from unstructured.chunking.title import chunk_by_title

chunks = chunk_by_title(
    elements,
    max_characters=1200,
    new_after_n_chars=900,
    overlap=80,
    overlap_all=False,
    include_orig_elements=False,
)
```

```python
from unstructured.partition.auto import partition

chunks = partition(
    filename="report.pdf",
    chunking_strategy="by_title",
    max_characters=1500,
    new_after_n_chars=1000,
    combine_text_under_n_chars=200,
    multipage_sections=False,
)
```

## Review Checklist

- Confirm the request uses one sizing mode, not both character and token limits.
- Explain hard maximum versus soft maximum when recommending values.
- State whether tables remain isolated, split into `TableChunk`, or pass through unchanged.
- State whether `metadata.orig_elements` is retained and how that affects serialized size.
- Warn before using `overlap_all=True`, because it can duplicate text across semantic chunk boundaries.
