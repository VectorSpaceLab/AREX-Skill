# Word2Vec, FastText, and Doc2Vec

## Word2Vec

Word2Vec learns word embeddings from sentence-like iterables.

Common tiny-smoke settings:

- `vector_size=10` or `20`
- `min_count=1`
- `workers=1`
- `epochs=3` to `5`
- a very small sentence iterator

Useful tasks:

- `model.wv.most_similar(word)` for nearest-neighbor lookup.
- `model.wv.similarity(w1, w2)` for pairwise similarity.
- `model.build_vocab(...)` and `model.train(...)` for continuation flows.

Be careful with `corpus_file`: it expects line-sentence style data and is not
interchangeable with a sentence iterator unless the model API supports both.

## FastText

FastText extends Word2Vec with subword character n-grams. It is the right choice
when:

- out-of-vocabulary words should still produce vectors,
- morphology is important, or
- the corpus is small and word-level sparsity is a problem.

Key parameters beyond Word2Vec-style controls:

- `min_n` and `max_n` for character n-gram lengths.
- `bucket` for hashed subword buckets.
- `word_ngrams` for using word n-grams as features.

FastText can return vectors for OOV words when the word shares subword n-grams
with the trained vocabulary. If a word has no known subwords, it can still fail.

## Doc2Vec

Doc2Vec learns document vectors from tagged documents.

Important points:

- Training documents must be tagged, typically with `TaggedDocument(tokens, [tag])`.
- `tokens_only=True` should be used only for the inference/test side.
- `model.infer_vector(tokens)` creates vectors for unseen documents.
- `model.dv` contains learned document vectors; `model.wv` contains learned word
  vectors.

Tiny smoke checks should verify:

- a short tagged corpus trains without error,
- `infer_vector` returns the expected vector size,
- model save/load round-trips preserve similarity/inference behavior.

## Tiny training pattern

```python
from gensim.models import Word2Vec, FastText, Doc2Vec
from gensim.models.doc2vec import TaggedDocument

sentences = [["human", "computer"], ["graph", "trees"]]
w2v = Word2Vec(sentences, vector_size=10, min_count=1, workers=1, epochs=5)
ft = FastText(sentences, vector_size=10, min_count=1, workers=1, epochs=5)
documents = [TaggedDocument(s, [i]) for i, s in enumerate(sentences)]
d2v = Doc2Vec(documents, vector_size=10, min_count=1, workers=1, epochs=5)
```

## Save/load strategy

- Use full model save/load when future training or vocabulary updates matter.
- Use `KeyedVectors` when only lookup/similarity/export is needed.
- Keep the training corpus, seed, and hyperparameters recorded for reproducibility.
