# Corpora and Vector Spaces Workflows

## Build a tiny corpus

```python
from gensim import corpora
from gensim.utils import simple_preprocess

documents = ["Human computer interaction", "Graph minors and trees"]
texts = [simple_preprocess(doc) for doc in documents]
dictionary = corpora.Dictionary(texts)
corpus = [dictionary.doc2bow(text) for text in texts]
```

Save the dictionary together with any model or index trained from `corpus`.

## Memory-friendly corpus iterator

```python
class StreamingCorpus:
    def __init__(self, lines, dictionary):
        self.lines = lines
        self.dictionary = dictionary

    def __iter__(self):
        for line in self.lines:
            yield self.dictionary.doc2bow(line.lower().split())
```

A corpus is a stream, not necessarily a list. Use `list(corpus)` only for tiny
fixtures or debugging.

## Persist Matrix Market corpus

```python
from gensim import corpora

corpora.MmCorpus.serialize("corpus.mm", corpus, id2word=dictionary)
loaded = corpora.MmCorpus("corpus.mm")
for bow in loaded:
    pass
```

If you need random access, keep the generated index file with the Matrix Market
file. For compressed files, use the extension supported by the corpus class and
confirm whether an index can be built.

## Text directory corpus

Use `TextDirectoryCorpus` when a directory tree already contains one document per
file or one document per line.

```python
from gensim.corpora import TextDirectoryCorpus

corpus = TextDirectoryCorpus(
    "text-root",
    dictionary=dictionary,
    lines_are_documents=True,
    min_depth=0,
    pattern=".*\\.txt",
)
```

`pattern` and `exclude_pattern` are useful when the directory contains sidecar
metadata or generated files.

## Wikipedia corpus planning

`WikiCorpus` streams compressed MediaWiki XML dumps, but full Wikipedia dumps are
large. Before running full conversion:

1. Confirm the dump path, compression, disk space, and expected article count.
2. Choose token length, namespace, and article-length filters.
3. Run a tiny XML fixture or a short sample first.
4. Decide whether output should be raw tokens, BoW vectors, Matrix Market, or
   downstream model input.
5. Route command-line dump segmentation/conversion details to
   `data-and-cli-utilities`.

## Recover from feature-space mismatch

If a model or index gives nonsensical results:

1. Check that training vectors and query vectors were produced by the same
   `Dictionary` object or a saved/loaded copy.
2. Verify the preprocessing function did not change.
3. Check `len(dictionary)` against the `num_features` used by similarity indexes.
4. Re-vectorize the query with the saved dictionary.

## Bundled smoke

`../scripts/corpus_io_smoke.py` uses embedded text, a temporary directory, and
Matrix Market serialization. It is a safe starting point for adapting a corpus
workflow to a new environment.
