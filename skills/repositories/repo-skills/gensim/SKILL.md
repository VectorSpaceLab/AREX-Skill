---
name: gensim
description: "Guides Gensim topic modelling, document indexing, embeddings,
  similarity retrieval, downloader, and script workflows for Python NLP and IR
  tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: LGPL 2.1
---

# Gensim Repo Skill

Use this skill when a task needs Gensim for streaming corpora, vector-space models,
topic modelling, word/document embeddings, document similarity, gensim-data
resources, or package-provided conversion/Wikipedia utilities.

Gensim is a CPU-oriented Python package for topic modelling, document indexing,
and similarity retrieval. It is optimized around streaming corpora and NumPy/SciPy
linear algebra rather than GPU backends.

## First checks

1. Confirm the package is importable in the target environment:

   ```bash
   python - <<'PY'
   import gensim
   from gensim import corpora, models, similarities
   print(gensim.__version__)
   print(corpora.Dictionary, models.TfidfModel, similarities.MatrixSimilarity)
   PY
   ```

2. For a privacy-safe diagnostic, run or adapt [`scripts/check_gensim_environment.py`](scripts/check_gensim_environment.py).
3. For an end-to-end sanity check across core concepts, run [`scripts/core_workflow_smoke.py`](scripts/core_workflow_smoke.py).
4. Read [`references/repo-provenance.md`](references/repo-provenance.md) before deciding whether this skill is current for a checkout.

## Installation notes

- Public install: `python -m pip install --upgrade gensim`.
- Local checkout inspection/development: `python -m pip install -e .` from the checkout root.
- Gensim 4.4.0 metadata requires Python `>=3.9` and runtime dependencies `numpy`, `scipy`, and `smart_open`.
- Optional surfaces are not part of the minimum install: `Pyro4` for distributed LDA/LSI, `annoy` or `nmslib` for approximate-neighbor helpers, POT/import name `ot` for WMD, NLTK/scikit/pandas/statsmodels for some documentation examples, and Visdom for selected callbacks.
- Performance depends heavily on the BLAS/LAPACK libraries used by NumPy/SciPy. GPU hardware is not required for the workflows covered here.

## Route map

| If the task is about... | Read |
| --- | --- |
| Documents, tokens, dictionaries, bag-of-words vectors, streaming corpora, Matrix Market/SVMlight/Blei/UCI/Mallet formats, `TextCorpus`, `WikiCorpus` | [`sub-skills/corpora-and-vector-spaces/SKILL.md`](sub-skills/corpora-and-vector-spaces/SKILL.md) |
| TF-IDF, BM25, LSI/LSA, LDA/LdaMulticore, HDP, NMF, topic coherence, model transforms and persistence | [`sub-skills/topic-modeling-and-transformations/SKILL.md`](sub-skills/topic-modeling-and-transformations/SKILL.md) |
| Word2Vec, FastText, Doc2Vec, KeyedVectors, phrase detection, embedding persistence and vector formats | [`sub-skills/embeddings-and-phrases/SKILL.md`](sub-skills/embeddings-and-phrases/SKILL.md) |
| MatrixSimilarity, SparseMatrixSimilarity, sharded Similarity, Soft Cosine, WMD, term-similarity matrices, Annoy/NMSLIB optional indexes | [`sub-skills/similarity-and-search/SKILL.md`](sub-skills/similarity-and-search/SKILL.md) |
| `gensim.downloader`, `GENSIM_DATA_DIR`, GloVe/word2vec/TensorBoard conversions, package diagnostics, Wikipedia dump helper CLIs | [`sub-skills/data-and-cli-utilities/SKILL.md`](sub-skills/data-and-cli-utilities/SKILL.md) |

For a compact package map and cross-workflow dependencies, read
[`references/package-overview.md`](references/package-overview.md). For install,
import, optional dependency, cache, and data-size failures, read
[`references/troubleshooting.md`](references/troubleshooting.md).

## Common workflow order

1. Start with raw text documents or an existing vector corpus.
2. Use `corpora.Dictionary` and `doc2bow` (or a streaming corpus class) to build a consistent feature space.
3. Train a transformation/model such as `TfidfModel`, `LsiModel`, or `LdaModel` on that same feature space.
4. Save models/corpora with `.save()`, `.load()`, or corpus-specific `serialize()` helpers.
5. Build an index with `MatrixSimilarity`, `SparseMatrixSimilarity`, or `Similarity` only after choosing the transformed vector space and `num_features`.
6. Use embeddings (`Word2Vec`, `FastText`, `Doc2Vec`, `KeyedVectors`) when the task needs token/document embeddings instead of bag-of-words topic models.

## Decision shortcuts

- Use `Dictionary.doc2bow(tokens)` only with token lists, never a raw string.
- Use streaming iterators when a corpus may not fit in memory.
- Use `TfidfModel` as a lightweight weighting transform before LSI or similarity.
- Use `LdaMulticore` for CPU multicore LDA on one machine; optional distributed LDA/LSI requires `Pyro4` and separate worker/dispatcher setup.
- Use `FastText` rather than `Word2Vec` when out-of-vocabulary word vectors are required.
- Use `KeyedVectors` when you only need stored vectors and similarity operations, not continued training.
- Use `Similarity` rather than `MatrixSimilarity` when the indexed vectors do not fit in memory.
- Check optional dependencies before selecting Annoy, NMSLIB, WMD/POT, Pyro4 distributed, or Visdom callback flows.

## Runtime boundaries

The guidance and bundled scripts in this skill are self-contained. Do not require
future agents to open the original repository docs, examples, tests, scripts, or
notebooks to complete normal Gensim tasks. Treat original repo files only as
provenance evidence unless this skill has bundled an adapted helper or reference.
