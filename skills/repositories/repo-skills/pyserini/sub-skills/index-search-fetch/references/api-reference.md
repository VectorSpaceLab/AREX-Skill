# API Reference for Lucene Workflows

This reference is distilled from Pyserini `2.3.0` Lucene, analysis, collection, and query-builder source plus usage documentation. Verify signatures with `help()` or `inspect.signature()` in the user's runtime when working against a newer Pyserini release.

## `pyserini.search.lucene.LuceneSearcher`

Constructors and discovery:

```python
LuceneSearcher(index_dir: str, prebuilt_index_name=None, index_reader=None)
LuceneSearcher.from_prebuilt_index(prebuilt_index_name: str, verbose=False)
LuceneSearcher.list_prebuilt_indexes()
```

Search and ranking:

```python
searcher.search(q, k=10, query_generator=None, fields={}, strip_segment_id=False, remove_dups=False)
searcher.batch_search(queries, qids, k=10, threads=1, query_generator=None, fields={}, strip_segment_id=False, remove_dups=False)
searcher.set_bm25(k1=0.9, b=0.4)
searcher.set_qld(mu=1000)
searcher.set_rm3(fb_terms=10, fb_docs=10, original_query_weight=0.5, debug=False, filter_terms=True, use_python=False)
searcher.set_language(language)
searcher.set_analyzer(analyzer)
```

Fetching:

```python
searcher.doc(docid_or_internal_docid)
searcher.doc_by_field(field, q)
```

`docid_or_internal_docid` is overloaded: a string is an external collection docid; an integer is Lucene's internal docid. Do not persist internal docids.

## `pyserini.search.lucene.LuceneImpactSearcher`

```python
LuceneImpactSearcher(index_dir: str, query_encoder, min_idf=0, encoder_type='pytorch', prebuilt_index_name=None)
LuceneImpactSearcher.from_prebuilt_index(prebuilt_index_name: str, query_encoder, min_idf=0, encoder_type='pytorch')
searcher.search(q: str, k=10, fields={})
searcher.batch_search(queries, qids, k=10, threads=1, fields={})
searcher.doc(docid_or_internal_docid)
searcher.doc_by_field(field, q)
searcher.set_rm3(...)
```

Use this for Lucene learned sparse/impact indexes. Query encoders can trigger model downloads or optional backend requirements; route backend setup problems to `dense-encoding` or `install-and-runtime`.

## `pyserini.search.lucene.LuceneHnswDenseSearcher`

```python
LuceneHnswDenseSearcher(index_dir: str, ef_search=100, encoder=None, prebuilt_index_name=None, verbose=False)
LuceneHnswDenseSearcher.from_prebuilt_index(prebuilt_index_name: str, ef_search=100, encoder=None, verbose=False)
searcher.search(q: str, k=10)
searcher.batch_search(queries, qids, k=10, threads=4)
searcher.close()
```

Use this for Lucene HNSW dense search. Creating dense vectors, building Faiss indexes, selecting model devices, and hybrid fusion are sibling-skill responsibilities.

## `pyserini.index.lucene.LuceneIndexer`

```python
LuceneIndexer(index_dir: str = None, args: list[str] = None, append: bool = False, threads: int = 8)
indexer.add_doc_raw(doc: str)
indexer.add_doc_dict(doc: dict[str, str])
indexer.add_doc_json(node)
indexer.add_batch_raw(docs: list[str])
indexer.add_batch_dict(docs: list[dict[str, str]])
indexer.add_batch_json(nodes: list)
indexer.close()
```

`add_doc_dict()` and `add_batch_dict()` expect at least `id` and `contents`. `args` can pass low-level SimpleIndexer options such as `['-index', 'indexes/pretokenized', '-pretokenized']`; Pyserini appends the empty input, `JsonCollection`, and thread arguments internally.

## `pyserini.index.lucene.LuceneIndexReader`

```python
LuceneIndexReader(index_dir)
LuceneIndexReader.from_prebuilt_index(prebuilt_index_name: str, verbose=False)
LuceneIndexReader.list_prebuilt_indexes()
reader.stats()
reader.terms()
reader.analyze(text: str, analyzer=None)
reader.get_term_counts(term: str, analyzer=get_lucene_analyzer())
reader.get_postings_list(term: str, analyzer=get_lucene_analyzer())
reader.get_document_vector(docid: str)
reader.get_term_positions(docid: str)
reader.doc(docid: str)
reader.doc_by_field(field: str, q: str)
reader.doc_raw(docid: str)
reader.doc_contents(docid: str)
reader.compute_bm25_term_weight(docid: str, term: str, analyzer=get_lucene_analyzer(), k1=0.9, b=0.4)
reader.compute_query_document_score(docid: str, query: str, similarity=None)
reader.convert_internal_docid_to_collection_docid(docid: int)
reader.convert_collection_docid_to_internal_docid(docid: str)
```

`reader.terms()` and `reader.get_document_vector()` expose analyzed terms. `get_term_counts()` and `get_postings_list()` apply the analyzer by default; pass `analyzer=None` only when the input term is already analyzed.

## `pyserini.index.lucene.Document`

Documents returned by `searcher.doc()` and `reader.doc()` are Pyserini wrappers with methods including:

```python
doc.docid()
doc.id()
doc.contents()
doc.raw()
doc.get(field)
doc.lucene_document()
```

A hit's `lucene_document` is a Java Lucene document, not the wrapper. Wrap it if you need convenience methods:

```python
from pyserini.index.lucene import Document
wrapped = Document(hits[0].lucene_document)
print(wrapped.raw() or wrapped.contents())
```

## `pyserini.analysis`

```python
from pyserini.analysis import Analyzer, JWhiteSpaceAnalyzer, get_lucene_analyzer

get_lucene_analyzer(language='en', stemming=True, stemmer='porter', stopwords=True, huggingFaceTokenizer=None)
Analyzer(lucene_analyzer).analyze(text)
```

Common analyzer choices:

- `get_lucene_analyzer()` uses the default English analyzer with Porter stemming.
- `get_lucene_analyzer(stemmer='krovetz')` changes the stemmer.
- `get_lucene_analyzer(stemming=False)` tokenizes without stemming.
- `get_lucene_analyzer(stemming=False, stopwords=False)` preserves stopwords too.
- `JWhiteSpaceAnalyzer()` preserves pretokenized whitespace-separated tokens.

## Query Builder

```python
from pyserini.search.lucene import querybuilder

term = querybuilder.get_term_query('hubble')
boosted = querybuilder.get_boost_query(term, 2.0)
should = querybuilder.JBooleanClauseOccur['should'].value
builder = querybuilder.get_boolean_query_builder()
builder.add(boosted, should)
query = builder.build()
hits = searcher.search(query, k=10)
```

Use `querybuilder` when the query must be a Lucene `Query` object rather than a string. This is useful for explicit boosts and boolean clauses.

## Collection Wrappers

`pyserini.collection.Collection`, `FileSegment`, and `SourceDocument` wrap Anserini collection iteration. They are primarily useful when inspecting collection parsing behavior before indexing. For most user tasks, validate the JSONL shape first and then use the CLI or `LuceneIndexer`.
