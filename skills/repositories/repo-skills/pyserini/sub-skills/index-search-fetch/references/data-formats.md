# Data Formats for Lucene Workflows

## `JsonCollection` Documents

The simplest custom collection format is one JSON document with at least two fields:

```json
{"id": "doc1", "contents": "this is the text to index"}
```

- `id` is the external collection docid. Treat it as a string even if it looks numeric.
- `contents` is the text indexed by the default document generator.
- Extra fields may exist, but the default `DefaultLuceneDocumentGenerator` indexes `contents` and stores configured fields according to indexing flags.
- Use UTF-8. Blank lines in JSONL are ignored by the bundled validator, but avoid writing them in production collections.

Pyserini's `JsonCollection` accepts three layouts:

- A directory containing one JSON object per file.
- A directory containing files whose top-level JSON value is an array of document objects.
- A directory containing JSONL files, one document object per line.

The Pyserini index CLI expects `--input` to be a directory, not a single file. For a lone JSONL file, place it in a directory and pass the directory.

## Stored Fields and Future Fetching

Indexing flags decide which document data can be recovered later:

- `--storeRaw` stores the original raw document representation. Use this when `searcher.doc(docid).raw()` or `reader.doc_raw(docid)` must work.
- `--storeDocvectors` stores document vectors. Use this for RM3 feedback, `LuceneIndexReader.get_document_vector()`, and BM25 vector work.
- `--storePositions` stores positions. Use this for phrase/position-sensitive workflows and `get_term_positions()`.

If none of these flags are set, Pyserini builds a smaller term-frequency index that can support simple bag-of-words search but cannot support all fetch or inspection operations.

## Topics Files

For `python -m pyserini.search.lucene`, a small custom topics file can be tab-separated:

```text
q1	information retrieval
q2	city buses
```

Use `--topics path/to/topics.tsv`. A `.tsv` extension lets Pyserini infer the default TSV topics format. For other topic formats, set `--topics-format` explicitly.

## Run Output

The default Lucene CLI output is TREC run format:

```text
q1 Q0 doc2 1 0.256200 Anserini
```

Columns are query id, literal `Q0`, docid, rank, score, and run tag. Evaluation and fusion are owned by the `evaluation-and-fusion` sub-skill, but search workflows should still write run files in this format unless a downstream tool requires another `--output-format`.

## Document and Hit Objects

`LuceneSearcher.search()` returns scored hits with:

- `hit.docid`: external collection docid as a string.
- `hit.lucene_docid`: Lucene's internal integer docid.
- `hit.score`: retrieval score.
- `hit.lucene_document`: the underlying Java Lucene document.

`searcher.doc(docid)` returns a Pyserini `Document` wrapper. Its convenience methods include:

- `doc.docid()` for the external collection id.
- `doc.raw()` for stored raw JSON/text when available.
- `doc.contents()` for stored indexed contents when available.
- `doc.lucene_document()` for direct Java Lucene document access.

Lucene internal docids are not stable across separately built indexes because they depend on ingestion order and segment merges. Use external collection docids in saved artifacts and tests.

## Impact and Dense Lucene Notes

Learned sparse impact indexes and Lucene HNSW dense indexes may not store original passages. Fetch the text from a compatible sparse index that stores raw documents, or build your local index with `--storeRaw` if future fetch is required. Faiss-specific workflows and vector encoding are handled by `dense-encoding`.
