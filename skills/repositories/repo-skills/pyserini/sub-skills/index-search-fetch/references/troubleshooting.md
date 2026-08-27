# Troubleshooting Lucene Index, Search, and Fetch Workflows

## Invalid JSONL or Missing Fields

Symptoms:

- Indexing fails while reading a collection.
- Search runs complete but expected documents are absent.
- A Python indexing call raises a key error for `id` or `contents`.

Checks:

```bash
python scripts/validate_jsonl_collection.py corpus.jsonl --format jsonl --require-unique-ids
```

Fixes:

- Ensure every document is a JSON object with string `id` and string `contents`.
- Keep the Pyserini CLI `--input` as a directory; place JSONL files inside that directory.
- Remove duplicate ids unless the workflow intentionally appends/replaces documents.
- Avoid nested text in non-`contents` fields unless the selected generator explicitly indexes those fields.

## Wrong Collection, Generator, or Input Flags

Symptoms:

- CLI errors mention collection classes, document generators, or `-input`.
- An index is built but contains zero or unexpected documents.

Fixes:

- For standard JSON/JSONL documents, use `--collection JsonCollection` and `--generator DefaultLuceneDocumentGenerator`.
- Pass a directory to `--input`, not a single file.
- For non-English text, set `--language` during indexing and search.
- For pretokenized text, build with `-pretokenized` via low-level args and search with `JWhiteSpaceAnalyzer()`.
- Generate commands with `scripts/lucene_cli_builder.py` to avoid common spelling and flag-shape mistakes.

## Fetch Returns `None` or Missing Raw Text

Symptoms:

- `searcher.doc(docid)` returns `None`.
- `doc.raw()` or `reader.doc_raw(docid)` returns `None`.
- Hits exist, but fetched content is unavailable.

Fixes:

- Confirm the id is the external collection docid string, not the rank or Lucene internal integer docid.
- Build local indexes with `--storeRaw` when raw document fetch is required.
- Use `doc.contents()` or `reader.doc_contents()` only when indexed contents were stored.
- Some prebuilt impact and dense Lucene indexes do not store original passages; fetch from a compatible sparse/raw index.

## RM3 or Index Reader Vector Failures

Symptoms:

- RM3 search fails or gives empty expansion evidence.
- `get_document_vector(docid)` returns `None` unexpectedly.
- Term-position inspection returns no positions.

Fixes:

- Build with `--storeDocvectors` before using RM3 or document vectors.
- Build with `--storePositions` before position-sensitive inspection.
- Confirm the document id exists with `reader.doc(docid)`.
- For prebuilt indexes, choose a variant that includes document vectors when RM3 is required.

## Analyzed vs Unanalyzed Term Bugs

Symptoms:

- `get_term_counts()` returns zero for a term known to exist.
- BM25 term weights differ from expected values.
- A term from `get_document_vector()` does not work when reused in another reader call.

Cause:

Pyserini methods often apply the default analyzer unless told not to. Terms from `reader.terms()` and keys from `reader.get_document_vector()` are already analyzed. Passing them through analysis again can silently produce wrong results.

Fix pattern:

```python
vector = reader.get_document_vector('doc1')
for analyzed_term in vector:
    df, cf = reader.get_term_counts(analyzed_term, analyzer=None)
    weight = reader.compute_bm25_term_weight('doc1', analyzed_term, analyzer=None)
```

Use the default analyzer only for raw user text such as `retrieval`; use `analyzer=None` for analyzed terms such as `retriev`.

## Stopword, Stemming, and Pretokenized Surprises

Symptoms:

- Searching for a stopword returns no hits.
- Tokens appear stemmed (`cities` becomes `citi`).
- Pretokenized input loses intended tokens.

Fixes:

- Inspect analysis with `Analyzer(get_lucene_analyzer(...)).analyze(text)`.
- Use `get_lucene_analyzer(stemming=False, stopwords=False)` for diagnostic term lookup.
- For pretokenized indexes, set `searcher.set_analyzer(JWhiteSpaceAnalyzer())`.
- Keep analyzer choices consistent across indexing, searching, and reader diagnostics.

## Java, JVM, or Fatjar Errors

Symptoms:

- Imports fail around `jnius`, JVM startup, or Java classes.
- CLI errors mention Anserini classes or missing jars.
- `python -m pyserini.index.lucene` or `python -m pyserini.search.lucene --help` cannot start.

Routing:

- Route Java/JVM, Python version, Pyserini installation, optional dependencies, and missing Anserini fatjar issues to `install-and-runtime`.
- Do not solve Java resource problems by embedding local machine paths in runtime instructions.
- Once runtime checks pass, return to this sub-skill for indexing/search semantics.

## Impact, Lucene HNSW, Encoder, and Backend Confusion

Symptoms:

- `LuceneImpactSearcher` fails while loading a query encoder.
- `LuceneHnswDenseSearcher` needs an ONNX encoder name.
- The user asks for Faiss, GPU, OpenAI, or embedding generation.

Routing:

- Keep Lucene impact and HNSW search command/API shape here.
- Route encoder model selection, vector generation, Faiss indexing/search, GPU/CPU torch choices, OpenAI credentials, and hybrid dense-sparse search to `dense-encoding`.
- Fetch text for impact/HNSW hits from a compatible sparse/raw index if the dense or impact index does not store raw documents.

## Batch Search Output Looks Wrong

Symptoms:

- Run file has unexpected query ids or no rows.
- Evaluation tools reject the run.

Fixes:

- Use a `.tsv` topics file with `qid<TAB>query text` for small custom runs.
- Set `--topics-format` if using a non-TSV topic format.
- Keep default TREC output unless the downstream tool explicitly requires another `--output-format`.
- Route metric computation, qrels validation, and fusion to `evaluation-and-fusion`.
