---
name: index-search-fetch
description: "Build, search, fetch, and inspect Pyserini Lucene indexes using
  CLI and Python APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Index, Search, and Fetch with Pyserini Lucene

Use this sub-skill when the user wants to build a BM25/Lucene index, index JSON or JSONL documents, search a custom or prebuilt Lucene index, fetch raw documents, inspect terms or term vectors, configure analyzers, or construct Lucene queries by hand.

Do not use this sub-skill for Faiss indexing/search, encoder model selection, GPU embedding pipelines, evaluation metrics, run fusion, REST servers, or MCP servers. Route those to the sibling `dense-encoding`, `evaluation-and-fusion`, or `serving-and-agent-tools` sub-skills. If the failure is an import, Java, JVM, Anserini fatjar, or optional dependency problem, route first to `install-and-runtime`.

## Quick Routing

- **Custom sparse indexing:** Validate `JsonCollection` input, build a Lucene index with `python -m pyserini.index.lucene`, then search with `LuceneSearcher` or `python -m pyserini.search.lucene`.
- **Search and fetch:** Use `LuceneSearcher(index_path)` or `LuceneSearcher.from_prebuilt_index(name)`, then `searcher.search(query, k)` and `searcher.doc(docid)`.
- **Index introspection:** Use `LuceneIndexReader` for `stats()`, `terms()`, `get_term_counts()`, `get_postings_list()`, `get_document_vector()`, `get_term_positions()`, and BM25 term weights.
- **Analysis and query construction:** Use `Analyzer(get_lucene_analyzer(...))`, `JWhiteSpaceAnalyzer` for pretokenized text, and `pyserini.search.lucene.querybuilder` for explicit Lucene query objects.
- **Lucene dense or impact search:** Keep Lucene HNSW/impact search here, but route dense vector creation, Faiss, encoder downloads, OpenAI, and GPU model issues to `dense-encoding`.

## Default Tiny Pipeline

1. Put documents in `JsonCollection` form, one object per line when using JSONL:

   ```json
   {"id": "doc1", "contents": "city buses run on time"}
   {"id": "doc2", "contents": "information retrieval with lucene"}
   ```

2. Validate before indexing:

   ```bash
   python scripts/validate_jsonl_collection.py corpus.jsonl --format jsonl --require-unique-ids
   ```

3. Build an indexing command without running Java-backed indexing yet:

   ```bash
   python scripts/lucene_cli_builder.py index --input corpus_dir --index indexes/demo --store-raw --store-positions --store-docvectors
   ```

4. Run the printed command in an environment where Pyserini and Java are working.

5. Search and fetch:

   ```python
   from pyserini.search.lucene import LuceneSearcher

   searcher = LuceneSearcher('indexes/demo')
   searcher.set_bm25(k1=0.9, b=0.4)
   hits = searcher.search('information retrieval', k=10)
   doc = searcher.doc(hits[0].docid)
   print(doc.raw() or doc.contents())
   ```

## What to Read Next

- `references/data-formats.md` for `JsonCollection`, topics, run output, stored field, and docid conventions.
- `references/lucene-workflows.md` for complete indexing, BM25, RM3, QLD, impact, HNSW, fetch, and language workflows.
- `references/api-reference.md` for source-grounded Python API signatures and common method combinations.
- `references/troubleshooting.md` for invalid JSONL, wrong generators, missing stored raw text, analyzed-term bugs, and Java/fatjar routing.
- `scripts/validate_jsonl_collection.py --help` to validate collections safely without starting Java.
- `scripts/lucene_cli_builder.py --help` to generate reproducible index/search/fetch commands without executing them.

## Acceptance Checklist

- Validate custom input before indexing; each document needs a string `id` and string `contents`.
- Add `--storeRaw` when future document fetch needs `raw()`, `--storeDocvectors` when RM3 or document vectors are needed, and `--storePositions` when positions are needed.
- Keep external collection `docid` values as strings; do not treat Lucene internal integer docids as stable identifiers.
- Decide whether terms are analyzed or unanalyzed before calling index-reader methods; pass `analyzer=None` for already analyzed terms.
- For non-English or pretokenized collections, use matching indexing and search analyzers (`--language`, `set_language`, or `JWhiteSpaceAnalyzer`).
