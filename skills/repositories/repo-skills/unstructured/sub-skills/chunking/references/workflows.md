# Chunking Workflows

## Workflow: Choose Parameters for RAG

1. Partition first unless the request already provides elements.
2. Prefer `chunk_by_title()` or `chunking_strategy="by_title"` for documents with headings, sections, and page metadata.
3. Set a hard maximum based on the embedding model or vector database constraint.
4. Set a soft maximum below the hard maximum so chunks close before they become too large.
5. Keep `include_orig_elements=True` during debugging or audit-heavy pipelines; turn it off for production ingestion when serialized payload size matters.
6. Use `overlap` for long paragraphs that may split mid-text; avoid `overlap_all=True` unless duplicate boundary text improves retrieval more than it pollutes chunks.

Example character-mode RAG profile:

```python
chunks = chunk_by_title(
    elements,
    max_characters=1500,
    new_after_n_chars=1000,
    combine_text_under_n_chars=250,
    overlap=100,
    overlap_all=False,
    include_orig_elements=False,
)
```

Explain that `max_characters` is a hard cap for chunk text except tables passed through with `skip_table_chunking=True`, while `new_after_n_chars` is a preferred target that closes a chunk before adding another element.

## Workflow: Preserve Table Usability

Use this when the document includes important financial, scientific, or compliance tables.

1. Keep `isolate_table=True` unless a downstream consumer explicitly expects table text merged with surrounding prose.
2. Keep `repeat_table_headers=True` so continuation chunks retain column context when the table splits.
3. Choose a hard maximum large enough to fit header rows plus at least some body rows; very small windows can produce many tiny `TableChunk` objects.
4. Avoid `skip_table_chunking=True` unless the downstream system accepts oversized table chunks.
5. Inspect output categories and table metadata before indexing.

```python
chunks = chunk_elements(
    elements,
    max_characters=1200,
    new_after_n_chars=900,
    isolate_table=True,
    repeat_table_headers=True,
    include_orig_elements=False,
)
```

For reconstruction or table-specific post-processing, collect `TableChunk` objects by `metadata.table_id` and order by `metadata.chunk_index`, or use `reconstruct_table_from_chunks()`.

## Workflow: Use Token Limits

Use token mode when a downstream LLM or embedding model has token-based limits and character length is an unreliable proxy.

1. Ensure `tiktoken` is installed in the runtime environment.
2. Choose either `max_tokens` or `max_characters`; do not provide both.
3. Provide `tokenizer`, using an encoding name such as `"cl100k_base"` or a model name such as `"gpt-4"`.
4. Use `new_after_n_tokens` only with `max_tokens`.
5. Remember `overlap` is token-counted in token mode.

```python
chunks = chunk_by_title(
    elements,
    max_tokens=350,
    new_after_n_tokens=275,
    tokenizer="cl100k_base",
    overlap=30,
)
```

If token mode fails before output is produced, first check missing `tiktoken`, missing `tokenizer`, or accidentally passing both token and character limits.

## Workflow: Chunk During Partitioning

Use integrated chunking when there is no need to inspect or clean unchunked elements first.

```python
from unstructured.partition.auto import partition

chunks = partition(
    filename="document.pdf",
    strategy="auto",
    chunking_strategy="by_title",
    max_characters=1500,
    new_after_n_chars=1000,
    combine_text_under_n_chars=250,
    include_orig_elements=False,
)
```

Use two-step partitioning when you need to clean, filter, inspect, enrich, or serialize elements before chunking:

```python
elements = partition(filename="document.pdf", strategy="auto")
chunks = chunk_by_title(elements, max_characters=1500, new_after_n_chars=1000)
```

Partition-integrated chunking forwards only kwargs supported by the chosen chunker. If a partition-specific kwarg is ignored by chunking, check whether it belongs to partitioning rather than chunking.

## Workflow: Validate a Chunking Configuration

Run a small representative element set through the helper script before indexing a large corpus.

```bash
python sub-skills/chunking/scripts/chunk_elements_preview.py elements.json \
  --strategy by_title \
  --max-characters 1200 \
  --new-after-n-chars 900 \
  --include-orig-elements false
```

Review:

- Total chunks and category counts.
- Maximum observed text length.
- Whether tables stayed isolated or became `TableChunk` continuations.
- Whether `orig_elements_count` is present and acceptable.
- Whether overlap settings duplicate undesirable boundary text.

## Workflow: Diagnose Mutually Exclusive Options

When a user reports a chunking `ValueError`, reduce the options to a minimal valid set:

1. Remove either token or character sizing.
2. If using token sizing, keep `tokenizer` and `max_tokens` together.
3. If using character sizing, check `overlap < max_characters`.
4. If preserving oversized tables, keep `skip_table_chunking=True` with default `isolate_table=True`.
5. For `chunk_by_title`, check `0 <= combine_text_under_n_chars <= max_characters` or omit it.

Minimal valid character profile:

```python
chunks = chunk_elements(elements, max_characters=1000, new_after_n_chars=800)
```

Minimal valid token profile:

```python
chunks = chunk_elements(elements, max_tokens=300, new_after_n_tokens=240, tokenizer="cl100k_base")
```
