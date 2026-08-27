# Corpora and Vector Spaces API Reference

## Dictionary

`corpora.Dictionary(documents=None, prune_at=2000000)` builds a mapping from
string tokens to integer ids and stores statistics such as document frequencies
(`dfs`), collection frequencies (`cfs`), and document count (`num_docs`).

Important methods:

| Method | Use |
| --- | --- |
| `doc2bow(document, allow_update=False, return_missing=False)` | Convert an iterable of tokens to sparse `(token_id, count)` pairs. `allow_update=True` adds new tokens; `return_missing=True` also reports tokens not found. |
| `add_documents(documents, prune_at=2000000)` | Extend a dictionary from an iterable of tokenized documents. |
| `filter_extremes(no_below=5, no_above=0.5, keep_n=100000, keep_tokens=None)` | Drop rare/common terms and keep the top-N by frequency, optionally preserving named tokens. |
| `filter_tokens(bad_ids=None, good_ids=None)` | Filter by explicit ids. Call `compactify()` if contiguous ids are needed afterward. |
| `save(path)` / `Dictionary.load(path)` | Gensim-native dictionary persistence. |
| `save_as_text(path)` / `load_from_text(path)` | Human-readable token-id-frequency mapping. |

Do not pass a raw string to `doc2bow`; Python will iterate over characters and
Gensim raises `TypeError` for string input. Tokenize first.

## Corpus classes and persistence

Gensim corpus objects are iterable streams of sparse vectors. Many classes can
load lazily from disk and support indexing if an index file exists.

| Class | Purpose |
| --- | --- |
| `MmCorpus` | Matrix Market coordinate format, often used as a durable Gensim corpus representation. |
| `SvmLightCorpus` | SVMlight format for sparse labeled data interoperability. |
| `BleiCorpus` | Blei LDA-C style corpora with a vocabulary file. |
| `LowCorpus` | GibbsLDA++/Low-style corpus format. |
| `UciCorpus` | UCI bag-of-words format. |
| `MalletCorpus` | Mallet-compatible corpus format. |
| `TextCorpus` | Base helper for turning plain text into BoW vectors with configurable filters/tokenizers. |
| `TextDirectoryCorpus` | Recursively read files or lines from a directory with depth and filename filtering. |
| `WikiCorpus` | Stream a compressed MediaWiki XML dump as tokenized articles. |

The verified signature for `MmCorpus.serialize` is:

```python
MmCorpus.serialize(fname, corpus, id2word=None, index_fname=None,
                   progress_cnt=None, labels=None, metadata=False)
```

Use the matching loader for the format you serialized. Do not use `MmCorpus` to
read SVMlight, Blei, UCI, or Mallet files.

## Text preprocessing

Useful helpers:

- `gensim.utils.simple_preprocess(doc, deacc=False, min_len=2, max_len=15)`:
  lowercases, tokenizes, and filters token lengths.
- `gensim.parsing.preprocess_string(s, filters=...)`: applies a configurable
  sequence of filters such as tag stripping, punctuation stripping, whitespace
  cleanup, numeric stripping, stopword removal, short-token removal, and stemming.
- `gensim.parsing.remove_stopwords`, `strip_punctuation`, `strip_numeric`,
  `strip_short`, and related functions can be composed for custom pipelines.

Use the same preprocessing pipeline for training documents, new documents, and
queries. Changing tokenization after a dictionary/model/index is built changes
feature ids and invalidates comparisons.

## Streaming iterator contract

Most models accept any object whose `__iter__` yields one BoW vector at a time:

```python
class MyCorpus:
    def __iter__(self):
        for tokenized_doc in source():
            yield dictionary.doc2bow(tokenized_doc)
```

Keep the dictionary stable while iterating for model training. If the iterator
adds vocabulary during iteration, save the final dictionary and be explicit that
feature ids changed.
