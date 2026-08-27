# Data Preparation

FlashRAG retrieval indexes start from an indexable corpus. The safest default is JSONL with one document per line and a `contents` string.

## Corpus JSONL Contract

Minimum shape:

```jsonl
{"id": "0", "contents": "Title\nBody text for retrieval."}
{"id": "1", "contents": "Another title\nAnother body."}
```

Practical rules:

- `id` should be unique and stable; integer and string ids are both common, but avoid mixing types casually.
- `contents` must be non-empty text. FlashRAG chunking and examples expect `"title\ntext"` formatting.
- Optional `title` and `text` fields can help downstream readability, but index building uses `contents`.
- Rebuild indexes whenever document order, document count, `contents`, or corpus file path semantics change.
- Keep very long documents chunked before indexing so dense encoders do not truncate most of the document body.

Use the bundled validator before chunking or indexing:

```bash
python skills/flashrag/sub-skills/retrieval-and-indexing/scripts/validate_corpus_jsonl.py corpus.jsonl --sample 50 --require-title-newline
```

## Chunking Document Corpora

FlashRAG’s document chunking semantics take a JSONL corpus whose `contents` is `title\ntext`, split `text`, and write chunks like:

```jsonl
{"id": 0, "doc_id": "original-id", "title": "Title", "contents": "Title\nchunk text"}
```

The original document id is preserved as `doc_id`; the new `id` is the chunk id. Supported chunking styles are `token`, `word`, `sentence`, and `recursive`; `chunk_size` controls the target unit count. Token/sentence/recursive chunking may require tokenizer and chunking dependencies.

Recommended workflow:

1. Validate the raw corpus and check that most sampled `contents` values contain a title/body newline.
2. Pick `chunk_by` based on retrieval model behavior: `sentence` for readable chunks, `token` for consistent token windows, `recursive` for robust long text splitting, or `word` for simple CPU-only experiments.
3. Re-validate the chunked corpus before building BM25 or dense indexes.
4. Record the chunk size with the index so retrieval quality can be reproduced.

Do not run large chunking jobs inside a skill or assistant verification step by default. Treat chunking as a user-confirmed preprocessing job because it can read/write large corpora.

## Wikipedia Preprocessing

FlashRAG’s wiki preprocessing flow expects an external Wikipedia XML dump, parses articles, and writes JSONL with chunking options such as `chunk_by`, `chunk_size`, `seg_size`, `stride`, `num_workers`, and tokenizer selection.

Use this as a reference workflow only unless the user explicitly provides dumps and output locations. Wikipedia dumps are large, processing is slow, and outputs can be large enough to surprise users. After preprocessing, validate the resulting JSONL and build indexes from the cleaned corpus.

## Multimodal Corpus Notes

CLIP indexing can encode both text and image fields. When using `--index_modal all`, FlashRAG creates separate text and image Faiss indexes. Ensure the corpus format used by the caller contains the fields expected by the indexing path, and configure retrieval with:

```yaml
multimodal_index_path_dict:
  text: indexes/mmqa/openai-clip-vit-large-patch14-336_Flat_text.index
  image: indexes/mmqa/openai-clip-vit-large-patch14-336_Flat_image.index
```

For image retrieval, check that image paths/URLs are resolvable at query time. URL images require network access and `requests`; local images require readable files and image decoding support.

## Corpus Quality Checklist

- Sample documents have meaningful titles and bodies, not only IDs or metadata.
- No blank `contents`, malformed JSON, duplicate IDs, or binary/control-heavy text.
- Chunked corpora keep enough title context for BM25 and rerankers.
- Dense index `max_length` is compatible with chunk length; otherwise dense retrieval may truncate heavily.
- `corpus_path` used for retrieval points to the same corpus used for index building.
