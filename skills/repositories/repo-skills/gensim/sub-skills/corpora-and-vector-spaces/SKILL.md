---
name: corpora-and-vector-spaces
description: "Guides Gensim dictionaries, bag-of-words vectors, streaming
  corpora, corpus persistence formats, and preprocessing workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: LGPL 2.1
---

# Corpora and Vector Spaces

Use this sub-skill when the task starts from raw text, token lists, corpus files,
Wikipedia dumps, or sparse vector streams and needs Gensim's corpus/vector-space
abstractions before modeling or similarity indexing.

## Read when

- A user asks to create or update a `Dictionary`, call `doc2bow`, or filter
  tokens by document frequency.
- A corpus must be streamed instead of loaded fully into memory.
- A task mentions Matrix Market, SVMlight, Blei/LDA-C, UCI, Mallet, Low, text
  directory, or Wikipedia corpus formats.
- A downstream model fails because query vectors, training vectors, or persisted
  corpora are in the wrong feature space.

## Quick workflow

1. Tokenize documents with a stable preprocessing function such as
   `gensim.utils.simple_preprocess` or `gensim.parsing.preprocess_string`.
2. Build `dictionary = corpora.Dictionary(tokenized_documents)` or stream token
   lists into the constructor.
3. Convert token lists, not raw strings, with `dictionary.doc2bow(tokens)`.
4. Filter only after deciding what must remain: `filter_extremes`,
   `filter_tokens`, `filter_n_most_frequent`, then `compactify` when needed.
5. Expose large data as an iterable yielding one BoW vector at a time.
6. Persist corpora with the format-specific `serialize()` method and reload with
   the matching corpus class.

Read [`references/workflows.md`](references/workflows.md) for end-to-end corpus
recipes and [`references/api-reference.md`](references/api-reference.md) for
verified signatures and parameter notes. Read
[`references/data-formats.md`](references/data-formats.md) when selecting an IO
format or handling compression/metadata.

## API anchors

- `corpora.Dictionary(documents=None, prune_at=2000000)` builds token-id and
  frequency mappings.
- `Dictionary.doc2bow(document, allow_update=False, return_missing=False)` takes
  an iterable of string tokens.
- `Dictionary.filter_extremes(no_below=5, no_above=0.5, keep_n=100000,
  keep_tokens=None)` removes rare/common tokens and limits vocabulary size.
- `corpora.MmCorpus.serialize(fname, corpus, id2word=None, index_fname=None,
  progress_cnt=None, labels=None, metadata=False)` writes a lazy corpus with
  optional offset metadata.
- `TextCorpus`, `TextDirectoryCorpus`, and `WikiCorpus` help turn text files or
  XML dumps into streamed vectors.

## Bundled helper

Run [`scripts/corpus_io_smoke.py`](scripts/corpus_io_smoke.py) to verify that the
target environment can build a dictionary, serialize/reload Matrix Market data,
and process a tiny local text-directory corpus without network access.

## Boundaries and routing

- After the corpus is vectorized, route TF-IDF, BM25, LSI, LDA, HDP, NMF, and
  coherence tasks to
  [`../topic-modeling-and-transformations/SKILL.md`](../topic-modeling-and-transformations/SKILL.md).
- Route Word2Vec/FastText/Doc2Vec/Phrases to
  [`../embeddings-and-phrases/SKILL.md`](../embeddings-and-phrases/SKILL.md).
- Route document retrieval/indexing to
  [`../similarity-and-search/SKILL.md`](../similarity-and-search/SKILL.md).
- Route downloader/cache/vector-conversion/Wikipedia command-line utilities to
  [`../data-and-cli-utilities/SKILL.md`](../data-and-cli-utilities/SKILL.md).

## Common decisions

- Prefer `Dictionary` when the model needs stable token ids and document
  frequencies. Use `HashDictionary` only when bounded hash ids are acceptable.
- Use `TextDirectoryCorpus` when files are already laid out in directories and
  optional filename filtering matters.
- Use custom iterators for application-specific parsing, databases, or streams;
  Gensim only requires iteration over BoW vectors for most models.
- Use `WikiCorpus` or the data/CLI utilities only after acknowledging full dump
  size, compression, and runtime constraints.
- Save both the dictionary and the model/index that depends on it; a model alone
  cannot reconstruct the original feature mapping.

## Troubleshooting

Read [`references/troubleshooting.md`](references/troubleshooting.md) for raw
string `doc2bow` errors, empty vectors, dictionary drift, malformed corpus files,
encoding/compression problems, and large Wikipedia dump constraints.
