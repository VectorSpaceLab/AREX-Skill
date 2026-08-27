# Lucene Workflows

## Build a BM25 Index from JSONL

Prepare a directory containing JSONL files with `id` and `contents` fields, validate them, then build the index:

```bash
python scripts/validate_jsonl_collection.py corpus_dir/docs.jsonl --format jsonl --require-unique-ids
python -m pyserini.index.lucene \
  --collection JsonCollection \
  --input corpus_dir \
  --index indexes/demo \
  --generator DefaultLuceneDocumentGenerator \
  --threads 1 \
  --storePositions --storeDocvectors --storeRaw
```

Use a directory for `--input`. Use `--storeRaw` if later fetch is required, `--storeDocvectors` for RM3 or document vectors, and `--storePositions` for positional inspection. Increase `--threads` after the tiny workflow works.

For non-English text, use an ISO language code consistently at index and search time:

```bash
python -m pyserini.index.lucene --collection JsonCollection --input corpus_zh --language zh --index indexes/demo_zh --generator DefaultLuceneDocumentGenerator --threads 1 --storeRaw
python -m pyserini.search.lucene --index indexes/demo_zh --topics queries_zh.tsv --language zh --bm25 --output run.zh.txt
```

## Build an Index from Python Objects

Use `LuceneIndexer` when documents are already in memory:

```python
from pyserini.index.lucene import LuceneIndexer

indexer = LuceneIndexer('indexes/demo', threads=4)
indexer.add_doc_dict({'id': 'doc1', 'contents': 'information retrieval with lucene'})
indexer.add_batch_dict([
    {'id': 'doc2', 'contents': 'city buses run on time'},
    {'id': 'doc3', 'contents': 'lucene stores inverted indexes'},
])
indexer.close()
```

`close()` is required because it commits in-memory data. Creating `LuceneIndexer(index_dir)` overwrites the target index by default; use `append=True` to add documents to an existing index.

For pretokenized input, pass Anserini arguments and search with whitespace analysis:

```python
from pyserini.analysis import JWhiteSpaceAnalyzer
from pyserini.index.lucene import LuceneIndexer
from pyserini.search.lucene import LuceneSearcher

indexer = LuceneIndexer(args=['-index', 'indexes/pretokenized', '-pretokenized'])
indexer.add_doc_dict({'id': 'doc1', 'contents': 'in format tokens stay unchanged'})
indexer.close()

searcher = LuceneSearcher('indexes/pretokenized')
searcher.set_analyzer(JWhiteSpaceAnalyzer())
hits = searcher.search('in', k=10)
```

## Search a Local or Prebuilt Sparse Index

```python
from pyserini.search.lucene import LuceneSearcher

searcher = LuceneSearcher('indexes/demo')
# Or: searcher = LuceneSearcher.from_prebuilt_index('msmarco-v1-passage')
searcher.set_bm25(k1=0.9, b=0.4)
hits = searcher.search('information retrieval', k=10)
for rank, hit in enumerate(hits, start=1):
    print(rank, hit.docid, hit.score)
```

The equivalent batch CLI writes a run file:

```bash
python -m pyserini.search.lucene \
  --index indexes/demo \
  --topics queries.tsv \
  --output run.demo.txt \
  --bm25 \
  --hits 100
```

`--k1` and `--b` must be supplied together. Pyserini automatically sets known BM25 parameters for some prebuilt indexes, but custom indexes should specify deliberate values when reproducibility matters.

## RM3 and QLD

RM3 needs document vectors, so build or choose an index with docvectors:

```python
searcher = LuceneSearcher('indexes/demo')
searcher.set_bm25(k1=0.9, b=0.4)
searcher.set_rm3(fb_terms=10, fb_docs=10, original_query_weight=0.5)
hits = searcher.search('query expansion', k=10)
```

CLI examples:

```bash
python -m pyserini.search.lucene --index indexes/demo --topics queries.tsv --output run.rm3.txt --bm25 --rm3
python -m pyserini.search.lucene --index indexes/demo --topics queries.tsv --output run.qld.txt --qld
```

If RM3 fails because vectors are unavailable, rebuild with `--storeDocvectors` or use a prebuilt index variant that includes document vectors.

## Fetch Documents

```python
from pyserini.search.lucene import LuceneSearcher

searcher = LuceneSearcher('indexes/demo')
doc = searcher.doc('doc1')
if doc is None:
    raise KeyError('doc1 not found')
print(doc.raw() or doc.contents())

hits = searcher.search('lucene', k=1)
wrapped = searcher.doc(hits[0].docid)
print(wrapped.raw() or wrapped.contents())
```

`raw()` requires stored raw text; `contents()` requires stored indexed contents. Some prebuilt impact or dense indexes do not store passages, so fetch text from a compatible sparse index that stores raw documents.

## Inspect an Index

```python
from pyserini.index.lucene import LuceneIndexReader

reader = LuceneIndexReader('indexes/demo')
print(reader.stats())
print(reader.get_term_counts('retrieval'))       # unanalyzed term: analyzer applied
print(reader.get_term_counts('retriev', analyzer=None))
print(reader.get_postings_list('retrieval'))
print(reader.get_document_vector('doc1'))
print(reader.get_term_positions('doc1'))
print(reader.compute_bm25_term_weight('doc1', 'retrieval'))
```

Terms from `terms()` and keys from `get_document_vector()` are already analyzed. Pass `analyzer=None` when looking up those analyzed terms to avoid double analysis.

## Analyze Text

```python
from pyserini.analysis import Analyzer, get_lucene_analyzer

Analyzer(get_lucene_analyzer()).analyze('City buses are running on time.')
Analyzer(get_lucene_analyzer(stemmer='krovetz')).analyze('City buses are running on time.')
Analyzer(get_lucene_analyzer(stemming=False)).analyze('City buses are running on time.')
```

Default English analysis stems with Porter and removes stopwords. Use `stemming=False`, `stopwords=False`, language-specific analyzers, or `JWhiteSpaceAnalyzer` when exact tokens must be preserved.

## Build Lucene Query Objects

```python
from pyserini.search.lucene import LuceneSearcher, querybuilder

term1 = querybuilder.get_term_query('hubble')
term2 = querybuilder.get_boost_query(querybuilder.get_term_query('space'), 2.0)
should = querybuilder.JBooleanClauseOccur['should'].value
builder = querybuilder.get_boolean_query_builder()
builder.add(term1, should)
builder.add(term2, should)
query = builder.build()

searcher = LuceneSearcher.from_prebuilt_index('robust04')
hits = searcher.search(query, k=10)
```

Use query builders when term boosts, boolean structure, or fielded query objects need to be explicit. For ordinary bag-of-words retrieval, passing a string to `search()` is simpler.

## Impact and Lucene HNSW Search

Learned sparse impact search uses `LuceneImpactSearcher` and usually needs a query encoder:

```python
from pyserini.search.lucene import LuceneImpactSearcher

searcher = LuceneImpactSearcher.from_prebuilt_index(
    'msmarco-v1-passage.splade-pp-ed',
    'naver/splade-cocondenser-ensembledistil')
hits = searcher.search('what is a lobster roll?', k=10)
```

Lucene dense HNSW search uses `LuceneHnswDenseSearcher` and can use ONNX encoders for some prebuilt indexes:

```python
from pyserini.search.lucene import LuceneHnswDenseSearcher

searcher = LuceneHnswDenseSearcher.from_prebuilt_index(
    'msmarco-v1-passage.bge-base-en-v1.5.hnsw',
    ef_search=1000,
    encoder='BgeBaseEn15')
hits = searcher.search('what is a lobster roll?', k=10)
```

If the task involves generating embeddings, selecting encoder backends, Faiss indexes, GPU settings, or hybrid dense-sparse fusion, route to `dense-encoding` instead of expanding this workflow.
