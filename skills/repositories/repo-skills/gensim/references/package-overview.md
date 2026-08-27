# Gensim Package Overview

## When to read

Read this for a compact map of Gensim's public workflow families before choosing
a sub-skill. Gensim revolves around streamed text corpora, sparse vector spaces,
transformations/topic models, embeddings, and similarity indexes.

## Core concepts

- **Document**: usually a Unicode string before preprocessing.
- **Tokens**: a list of strings produced by a tokenizer or preprocessing
  function such as `gensim.utils.simple_preprocess`.
- **Dictionary**: `gensim.corpora.Dictionary` maps tokens to integer feature ids
  and stores document/collection frequency statistics.
- **Bag-of-words vector**: a sparse list of `(token_id, weight_or_count)` pairs.
  `Dictionary.doc2bow(tokens)` creates count vectors.
- **Corpus**: any iterable that yields one sparse vector at a time. Many Gensim
  models consume corpora lazily instead of requiring all vectors in memory.
- **Model/Transformation**: an object such as `TfidfModel`, `LsiModel`, or
  `LdaModel` trained on a corpus and applied with `model[vector_or_corpus]`.
- **Similarity index**: an object such as `MatrixSimilarity` or `Similarity`
  that indexes vectors in a chosen vector space and returns similarity scores.
- **Embedding model**: `Word2Vec`, `FastText`, and `Doc2Vec` learn dense vectors
  from token or tagged-document iterables; `KeyedVectors` stores vectors for
  lookup/similarity without full training state.

## Workflow dependencies

```text
raw text -> tokens -> Dictionary -> BoW corpus -> transformations/topic models -> similarity index
                       |                         |
                       |                         +-> topic coherence/evaluation
                       +-> word/doc sentence streams -> Word2Vec/FastText/Doc2Vec/Phrases
```

Use one dictionary and preprocessing pipeline consistently across corpus,
training, query, and evaluation steps. Feature ids are numeric; if the query or
new corpus was vectorized with a different dictionary, model and similarity
results become meaningless or fail with shape/feature errors.

## Public package surfaces

| Surface | Main objects | Owning sub-skill |
| --- | --- | --- |
| Corpus and vector space | `Dictionary`, `HashDictionary`, `MmCorpus`, `SvmLightCorpus`, `BleiCorpus`, `LowCorpus`, `UciCorpus`, `MalletCorpus`, `TextCorpus`, `TextDirectoryCorpus`, `WikiCorpus`, `parsing`, `simple_preprocess` | `corpora-and-vector-spaces` |
| Transformations and topic models | `TfidfModel`, `OkapiBM25Model`, `LsiModel`, `LdaModel`, `LdaMulticore`, `HdpModel`, `Nmf`, `RpModel`, `LogEntropyModel`, `NormModel`, `CoherenceModel` | `topic-modeling-and-transformations` |
| Embeddings and phrases | `Word2Vec`, `FastText`, `Doc2Vec`, `TaggedDocument`, `KeyedVectors`, `Phrases`, `FrozenPhrases`, `CallbackAny2Vec` | `embeddings-and-phrases` |
| Similarity and search | `MatrixSimilarity`, `SparseMatrixSimilarity`, `Similarity`, `SoftCosineSimilarity`, `WmdSimilarity`, `SparseTermSimilarityMatrix`, `WordEmbeddingSimilarityIndex`, `LevenshteinSimilarityIndex`, optional Annoy/NMSLIB indexers | `similarity-and-search` |
| Data and scripts | `gensim.downloader.info/load`, `python -m gensim.downloader`, `glove2word2vec`, `word2vec2tensor`, `segment_wiki`, `make_wikicorpus`, package diagnostics | `data-and-cli-utilities` |

## Optional dependencies and boundaries

- `Pyro4` enables distributed LDA/LSI worker/dispatcher flows; most users should
  use single-machine CPU or `LdaMulticore` first.
- `annoy` and `nmslib` enable optional approximate-neighbor helpers; exact
  Matrix/Sparse/Similarity indexes work without them.
- POT (`import ot`) enables Word Mover's Distance implementations.
- NLTK and scikit-learn appear in documentation examples, not the base runtime.
- Visdom is only for selected training callbacks/visualizations.
- Gensim's main workflows are CPU/scientific-Python workflows. A visible GPU is
  not evidence that a Gensim task should install GPU stacks.

## Persistence conventions

- Gensim models usually support `.save(path)` and `Class.load(path)`.
- `KeyedVectors` supports Gensim-native persistence plus word2vec text/binary
  format through `load_word2vec_format` and `save_word2vec_format`.
- Corpus classes provide class-specific `serialize()` helpers and lazy loaders.
- Use temporary directories for examples and avoid writing large model/corpus
  artifacts unless the task explicitly requires it.

## Safe bundled checks

- Root [`../scripts/check_gensim_environment.py`](../scripts/check_gensim_environment.py) checks imports and optional dependency presence without exposing local install paths.
- Root [`../scripts/core_workflow_smoke.py`](../scripts/core_workflow_smoke.py) runs a small document-to-similarity workflow.
- Each sub-skill has a focused smoke script for its main workflow family.
