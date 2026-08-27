---
name: embeddings-and-phrases
description: "Guides Gensim Word2Vec, FastText, Doc2Vec, KeyedVectors, and
  phrase-detection workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: LGPL 2.1
---

# Embeddings and Phrases

Use this sub-skill when the task needs dense vectors for words, documents, or
phrases rather than sparse bag-of-words topic models.

## Read when

- A user asks to train or fine-tune `Word2Vec`, `FastText`, or `Doc2Vec`.
- The task needs `KeyedVectors` for similarity lookup or vector export/import.
- A workflow needs phrase/bigram detection via `Phrases` or `FrozenPhrases`.
- The problem mentions out-of-vocabulary tokens, vector persistence, word2vec
  format files, tagged documents, or embedding continuation.

## Quick workflow

1. Build sentence iterators or `TaggedDocument` iterables that emit token lists.
2. Train an embedding model with conservative `vector_size`, `min_count`,
   `workers`, and `epochs` for smoke tests.
3. Use `model.wv` for word vectors and `model.dv`/inference for document vectors.
4. Save only the artifact you need: full model if continued training matters,
   `KeyedVectors` if you only need lookup/similarity.
5. Use `Phrases` when adjacent token combinations should be discovered before
   embedding or downstream retrieval.

Read [`references/word2vec-fasttext-doc2vec.md`](references/word2vec-fasttext-doc2vec.md)
for model-specific recipes, [`references/keyedvectors-and-formats.md`](references/keyedvectors-and-formats.md)
for vector-file handling, and [`references/phrases.md`](references/phrases.md) for phrase detection.

## API anchors

- `Word2Vec(sentences=None, corpus_file=None, vector_size=100, alpha=0.025,
  window=5, min_count=5, max_vocab_size=None, sample=0.001, seed=1,
  workers=3, min_alpha=0.0001, sg=0, hs=0, negative=5, ns_exponent=0.75,
  cbow_mean=1, hashfxn=hash, epochs=5, null_word=0, trim_rule=None,
  sorted_vocab=1, batch_words=10000, compute_loss=False, callbacks=(),
  comment=None, max_final_vocab=None, shrink_windows=True)`.
- `FastText(...)` shares the Word2Vec-style API and adds `min_n`, `max_n`, and
  `bucket` for subword vectors and OOV handling.
- `Doc2Vec(documents=None, corpus_file=None, vector_size=100, dm_mean=None,
  dm=1, dbow_words=0, dm_concat=0, dm_tag_count=1, dv=None, dv_mapfile=None,
  comment=None, trim_rule=None, callbacks=(), window=5, epochs=10,
  shrink_windows=True, **kwargs)`.
- `KeyedVectors(vector_size, count=0, dtype=numpy.float32, mapfile_path=None)`.
- `KeyedVectors.load_word2vec_format(fname, fvocab=None, binary=False,
  encoding='utf8', unicode_errors='strict', limit=None, datatype=numpy.float32,
  no_header=False)`.
- `Phrases(sentences=None, min_count=5, threshold=10.0, max_vocab_size=40000000,
  delimiter='_', progress_per=10000, scoring='default', connector_words=frozenset())`.
- `FrozenPhrases(phrases_model)`.

## Bundled helper

Run [`scripts/embedding_smoke.py`](scripts/embedding_smoke.py) to verify that the
current environment can train tiny Word2Vec, FastText, and Doc2Vec models,
build phrases, and save/load `KeyedVectors` without network access.

## Boundaries and routing

- For sparse BoW dictionaries, route to
  [`../corpora-and-vector-spaces/SKILL.md`](../corpora-and-vector-spaces/SKILL.md).
- For TF-IDF/LSI/LDA/HDP/NMF/coherence, route to
  [`../topic-modeling-and-transformations/SKILL.md`](../topic-modeling-and-transformations/SKILL.md).
- For document retrieval/indexing, route to
  [`../similarity-and-search/SKILL.md`](../similarity-and-search/SKILL.md).
- For vector conversion and downloader/Wikipedia CLIs, route to
  [`../data-and-cli-utilities/SKILL.md`](../data-and-cli-utilities/SKILL.md).

## Common decisions

- Use `Word2Vec` when the task needs learned token embeddings and OOV support is
  not essential.
- Use `FastText` when subword information or OOV vectors matter.
- Use `Doc2Vec` when the task needs a vector per document or paragraph.
- Use `KeyedVectors` when you only need to store and query vectors, not continue
  training.
- Use `Phrases`/`FrozenPhrases` to add bigrams/trigrams before training or when
  phrase tokens should be preserved in later corpora.

## Troubleshooting

Read [`references/troubleshooting.md`](references/troubleshooting.md) for
min_count/vocabulary issues, OOV behavior, sentence iterator shape, `model.wv`
vs full model confusion, persistence format mismatches, and reproducibility
notes.
