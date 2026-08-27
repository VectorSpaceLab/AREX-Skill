# Chunking Troubleshooting

## `ValueError: 'max_tokens' and 'max_characters' are mutually exclusive`

Use one sizing system per chunking call. Character mode is simpler and has no optional tokenizer dependency. Token mode is better when an LLM or embedding model imposes token limits.

Fix:

```python
chunk_elements(elements, max_tokens=300, tokenizer="cl100k_base")
```

or:

```python
chunk_elements(elements, max_characters=1500)
```

Do not pass both in the same call.

## `ValueError: 'tokenizer' is required when using 'max_tokens'`

Token-based chunking needs a tokenizer name. Use a tiktoken encoding or model name.

```python
chunk_by_title(elements, max_tokens=350, tokenizer="cl100k_base")
```

If the tokenizer import fails, install the package extra or dependency that provides `tiktoken` in the runtime environment. Character chunking does not need `tiktoken`.

## `new_after_n_tokens` Errors

`new_after_n_tokens` is only valid with token sizing. It requires `max_tokens` and `tokenizer`.

Valid:

```python
chunk_elements(
    elements,
    max_tokens=300,
    new_after_n_tokens=240,
    tokenizer="cl100k_base",
)
```

Invalid:

```python
chunk_elements(elements, new_after_n_tokens=240)
```

## Invalid Character Relationships

- `max_characters` must be greater than zero.
- `new_after_n_chars` must be zero or greater.
- `overlap` must be less than `max_characters` in character mode.
- `new_after_n_chars=0` is valid and forces each element into its own pre-chunk, with oversized elements still split.
- `new_after_n_chars > max_characters` is accepted and behaves as if capped to `max_characters`.

For `chunk_by_title`, `combine_text_under_n_chars` must be zero or greater and must not exceed the hard maximum.

## Overlap Pollution

`overlap` alone applies to chunks produced by splitting oversized text. `overlap_all=True` also overlaps normal chunk boundaries. That can improve recall but can duplicate text across section boundaries, titles, or neighboring paragraphs.

Prefer:

```python
chunk_by_title(elements, max_characters=1200, overlap=80, overlap_all=False)
```

Use `overlap_all=True` only when downstream retrieval benefits from duplicated boundary context and consumers tolerate repeated text.

## Tables Are Too Large or Too Fragmented

Symptoms:

- Large tables split into many `TableChunk` objects.
- Header rows dominate continuation chunks.
- A vector database rejects oversized pass-through tables.

Actions:

1. Keep `isolate_table=True` so table chunks do not mix with narrative text.
2. Increase `max_characters` or `max_tokens` enough to fit useful row groups.
3. Keep `repeat_table_headers=True` when column context matters.
4. Set `repeat_table_headers=False` if repeated headers consume too much of a small chunk window.
5. Avoid `skip_table_chunking=True` unless downstream systems can accept tables larger than the hard maximum.

If `skip_table_chunking=True` is requested together with `isolate_table=False`, chunking raises an error because skipping table chunking requires standalone table isolation.

## Tables Mix With Text Unexpectedly

Default behavior keeps tables isolated. If a `CompositeElement` contains table text, check whether the caller set `isolate_table=False`. Restore the default unless mixed-content chunks are intentional.

```python
chunk_elements(elements, isolate_table=True)
```

## Missing or Huge `orig_elements`

By default, chunks include `metadata.orig_elements`. This helps recover original metadata and audit chunk composition. It can increase memory and serialized JSON size, especially for table-heavy or metadata-rich documents.

Use:

```python
chunk_by_title(elements, include_orig_elements=False)
```

when downstream systems only need chunk text and consolidated metadata. If keeping `orig_elements`, be aware that serialized element JSON stores them in compressed base64 form; compact does not mean free.

## Chunking Integrated With Partitioning Gives Unexpected Output

Check whether `chunking_strategy` was passed:

- `None` or omitted returns unchunked partition elements.
- `"basic"` uses sequential chunking.
- `"by_title"` uses title section boundaries.
- Unknown names raise `ValueError`.

If a chunking kwarg appears ignored, verify it is accepted by the selected chunker. For example, `combine_text_under_n_chars` and `multipage_sections` are specific to `by_title`.

## `by_title` Creates Too Many Tiny Chunks

Causes:

- The partitioner classified many short items as `Title`.
- `combine_text_under_n_chars=0` disables recombination.
- `multipage_sections=False` adds page boundaries.

Actions:

```python
chunk_by_title(
    elements,
    max_characters=1200,
    new_after_n_chars=900,
    combine_text_under_n_chars=250,
)
```

Increase `combine_text_under_n_chars` cautiously to recombine tiny title-derived chunks while preserving real section boundaries.

## Need To Verify Before Indexing

Use `scripts/chunk_elements_preview.py` on representative serialized elements. Confirm category counts, longest chunk size, table continuation metadata, and `orig_elements` counts before sending chunks to embeddings, search, or LLM prompts.
