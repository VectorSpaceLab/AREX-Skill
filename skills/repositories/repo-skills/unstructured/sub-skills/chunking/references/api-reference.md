# Chunking API Reference

## Public Entry Points

### `chunk_elements(elements, **chunking_kwargs)`

Import from `unstructured.chunking.basic`. It combines sequential partition elements into output chunks while respecting size limits. It does not add semantic boundaries beyond ordering, size windows, and table isolation.

Typical output types:

- `CompositeElement` for text-like chunks built from one or more non-table elements.
- `Table` for table chunks that fit within the chunking window or are passed through with `skip_table_chunking=True`.
- `TableChunk` for oversized tables split into multiple table continuations.

### `chunk_by_title(elements, **chunking_kwargs)`

Import from `unstructured.chunking.title`. It uses `Title` elements as section boundaries before applying the same size, table, overlap, and metadata behavior as basic chunking.

Additional options:

- `combine_text_under_n_chars`: recombines small title-derived pre-chunks when they fit; defaults to the hard maximum in this strategy. Use `0` to suppress recombination.
- `multipage_sections`: defaults to `True`. Set `False` to split sections at page-number changes.

### Partition-integrated chunking

Many partitioners are decorated with chunking dispatch. When a partition function accepts `chunking_strategy`, pass `"basic"` or `"by_title"` plus the chunking kwargs accepted by the chosen strategy. Dispatch forwards only kwargs supported by the selected chunker.

```python
elements_or_chunks = partition_html(
    filename="page.html",
    chunking_strategy="by_title",
    max_characters=1200,
    new_after_n_chars=900,
    include_orig_elements=False,
)
```

If `chunking_strategy` is omitted or `None`, partitioning returns unchunked elements. An unrecognized strategy raises `ValueError`.

## Sizing Options

### Character mode

- `max_characters`: hard maximum chunk text length. A single oversized element is split mid-text into multiple chunks.
- `new_after_n_chars`: soft preferred boundary. Once a working chunk reaches this size, the next element starts a new chunk even if it would still fit under `max_characters`.
- Default hard maximum is 500 characters when neither character nor token maximum is specified by the chunking options.
- `new_after_n_chars=0` forces each element into its own pre-chunk, except oversized elements can still be split.
- `new_after_n_chars` greater than `max_characters` is behaviorally capped at `max_characters`.

### Token mode

- `max_tokens`: hard maximum token count. Mutually exclusive with `max_characters`.
- `new_after_n_tokens`: soft preferred token boundary. Requires `max_tokens`.
- `tokenizer`: required with `max_tokens`; accepts a tiktoken model name such as `"gpt-4"` or encoding name such as `"cl100k_base"`.
- Token counting imports `tiktoken` lazily. If the extra is not installed, token mode fails when token counting is first used.

## Overlap Options

- `overlap`: amount of text carried forward when an oversized element is split. In token mode it is measured in tokens; in character mode it is measured in characters.
- `overlap_all`: defaults to `False`. When `True`, applies overlap between normal chunks formed from whole elements, not only split chunks.
- Avoid `overlap_all=True` for section-accurate RAG unless duplicate boundary text is acceptable. Table isolation prevents narrative overlap from leaking into table chunks and prevents table text overlap from leaking into neighboring text chunks.

## Table Options

- `isolate_table`: defaults to `True`. `Table` and `TableChunk` elements are staged alone rather than mixed into `CompositeElement` text chunks.
- `repeat_table_headers`: defaults to `True`. For oversized tables with parseable `text_as_html`, detected header rows are repeated on continuation `TableChunk` outputs when practical.
- `skip_table_chunking`: defaults to `False`. When `True`, a `Table` passes through unchanged even if it exceeds `max_characters` or `max_tokens`. This requires `isolate_table=True`.

Oversized tables may split into `TableChunk` outputs. Chunk metadata can include `table_id`, `chunk_index`, `is_continuation`, and `num_carried_over_header_rows` so consumers can identify and order table continuations. `unstructured.chunking.dispatch.reconstruct_table_from_chunks()` can reconstruct tables from ordered `TableChunk` outputs when needed.

## Metadata Options

- `include_orig_elements`: defaults to `True`. Chunk metadata gets `orig_elements`, preserving the original elements used to form each chunk.
- `include_orig_elements=False` reduces memory and serialized JSON size. Use it when downstream systems need chunk text and consolidated metadata only.
- When chunks are used as input to another chunking run, nested `orig_elements` are stripped from copied original elements to avoid recursive metadata structures.

When serialized through Unstructured element JSON, `metadata.orig_elements` is compacted into a base64 gzipped JSON representation. It is useful for auditability and source metadata recovery, but it can still increase payload size materially.

## Validation Rules

Common invalid combinations raise `ValueError` before chunking proceeds:

- `max_characters <= 0`.
- `max_tokens <= 0`.
- Both `max_tokens` and `max_characters` are provided.
- `max_tokens` is provided without `tokenizer`.
- `new_after_n_tokens` is provided without `max_tokens`.
- `new_after_n_chars < 0` or `new_after_n_tokens < 0`.
- `overlap >= max_characters` in character mode.
- `skip_table_chunking=True` while `isolate_table=False`.
- `chunk_by_title(..., combine_text_under_n_chars < 0)`.
- `chunk_by_title(..., combine_text_under_n_chars > hard_max)`.

## Evidence Sources

This reference is distilled from the package chunking implementation and behavior tests for base options, basic chunking, title chunking, dispatch, and table isolation.
