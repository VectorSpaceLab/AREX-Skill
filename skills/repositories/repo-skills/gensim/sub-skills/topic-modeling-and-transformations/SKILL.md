---
name: topic-modeling-and-transformations
description: "Guides Gensim TF-IDF, BM25, LSI, LDA, HDP, NMF, coherence, and
  transformation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: LGPL 2.1
---

# Topic Modeling and Transformations

Use this sub-skill when the task takes a bag-of-words corpus and needs a
transformation or topic model such as TF-IDF, BM25, LSI/LSA, LDA, HDP, NMF, or
coherence scoring.

## Read when

- A task asks to train or apply `TfidfModel`, `LsiModel`, `LdaModel`, or
  `LdaMulticore`.
- A task needs `CoherenceModel`, topic comparison, or model persistence across
  topic transforms.
- A user wants to understand parameters such as `num_topics`, `passes`,
  `iterations`, `chunksize`, `alpha`, `eta`, `random_state`, or `num_workers`.
- A workflow is failing because the model was trained on a different dictionary
  or vector space than the query corpus.

## Quick workflow

1. Vectorize text through `corpora.Dictionary` and `doc2bow` first.
2. Apply a transform such as `TfidfModel` to weight the bag-of-words corpus.
3. Train an `LsiModel`, `LdaModel`, `LdaMulticore`, `HdpModel`, or `Nmf` on the
   transformed corpus using the same `id2word` mapping.
4. Save the model after training, and if needed save the transformed corpus too.
5. Use `CoherenceModel` only after you know which texts, corpus, dictionary, or
   keyed vectors correspond to the topics you want to score.

Read [`references/workflows.md`](references/workflows.md) for guided recipes,
[`references/api-reference.md`](references/api-reference.md) for verified
signatures, [`references/lda-workflows.md`](references/lda-workflows.md) for LDA
parameter strategy, and [`references/evaluation-and-coherence.md`](references/evaluation-and-coherence.md)
for coherence evaluation.

## API anchors

- `TfidfModel(corpus=None, id2word=None, dictionary=None, wlocal=..., wglobal=..., normalize=True, smartirs=None, pivot=None, slope=0.25)`.
- `OkapiBM25Model(corpus=None, dictionary=None, k1=1.5, b=0.75, epsilon=0.25)`.
- `LsiModel(corpus=None, num_topics=200, id2word=None, chunksize=20000, decay=1.0, distributed=False, onepass=True, power_iters=2, extra_samples=100, dtype=numpy.float64, random_seed=None)`.
- `LdaModel(corpus=None, num_topics=100, id2word=None, distributed=False, chunksize=2000, passes=1, update_every=1, alpha='symmetric', eta=None, decay=0.5, offset=1.0, eval_every=10, iterations=50, gamma_threshold=0.001, minimum_probability=0.01, random_state=None, ns_conf=None, minimum_phi_value=0.01, per_word_topics=False, callbacks=None, dtype=numpy.float32)`.
- `LdaMulticore(...)` mirrors `LdaModel` but uses multiple CPU workers.
- `HdpModel`, `Nmf`, `RpModel`, `LogEntropyModel`, `NormModel`, and
  `CoherenceModel` are useful when the task needs alternative topic extraction or
  evaluation.

## Bundled helper

Run [`scripts/topic_transform_smoke.py`](scripts/topic_transform_smoke.py) for a
safe tiny-corpus transform and topic-model smoke. It proves the environment can
train simple transformations without downloading external data.

## Boundaries and routing

- If the task is about raw text preprocessing, dictionaries, or corpus format
  handling, route to
  [`../corpora-and-vector-spaces/SKILL.md`](../corpora-and-vector-spaces/SKILL.md).
- If the task is about embeddings or phrase detection, route to
  [`../embeddings-and-phrases/SKILL.md`](../embeddings-and-phrases/SKILL.md).
- If the task is about querying or indexing transformed vectors, route to
  [`../similarity-and-search/SKILL.md`](../similarity-and-search/SKILL.md).
- If the task is about downloading data or conversion CLIs, route to
  [`../data-and-cli-utilities/SKILL.md`](../data-and-cli-utilities/SKILL.md).

## Common decisions

- Use `TfidfModel` when you need a lightweight inverse-document-frequency weight
  before another transformation.
- Use `LsiModel` when an SVD-like latent space is helpful and the corpus is sparse
  or streaming.
- Use `LdaModel` or `LdaMulticore` when a probabilistic topic mixture is needed;
  `LdaMulticore` is the CPU multicore variant.
- Use `HdpModel` when the topic count should be inferred automatically rather
  than fixed.
- Use `Nmf` when non-negative factorization is the requested family.
- Use `CoherenceModel` to compare or tune topic quality, not as a substitute for
  model training.

## Troubleshooting

Read [`references/troubleshooting.md`](references/troubleshooting.md) for feature
space mismatch, missing `id2word`, slow or stochastic LDA, coherence input
mismatch, and optional distributed Pyro4 issues.
