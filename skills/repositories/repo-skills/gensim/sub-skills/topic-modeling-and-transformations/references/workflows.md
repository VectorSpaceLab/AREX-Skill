# Transformation and Topic Workflows

## TF-IDF then LSI

```python
from gensim import corpora, models

texts = [["human", "computer"], ["graph", "trees"], ["human", "system"]]
dictionary = corpora.Dictionary(texts)
corpus = [dictionary.doc2bow(text) for text in texts]
tfidf = models.TfidfModel(corpus)
corpus_tfidf = tfidf[corpus]
lsi = models.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=2, random_seed=0)
new_vector = lsi[tfidf[dictionary.doc2bow(["human", "computer"])] ]
```

Keep the dictionary and preprocessing stable. `model[corpus]` usually creates a
lazy transformed corpus; iterate it when results are needed.

## Small LDA

For a deterministic smoke or debugging case:

```python
lda = models.LdaModel(
    corpus=corpus,
    id2word=dictionary,
    num_topics=2,
    passes=3,
    iterations=30,
    eval_every=None,
    random_state=0,
)
print(lda.print_topics())
```

Tiny corpora are not statistically meaningful; use them to validate API wiring,
shapes, persistence, and error recovery only. For production tuning, record
corpus size, vocabulary filtering, topic count, passes, iterations, priors,
and random seed.

## Online updates

Use `LsiModel.add_documents` or `LdaModel.update` when new documents arrive and
the model supports incremental updates. Do not silently rebuild the dictionary
with incompatible ids; if new terms are allowed, persist the updated dictionary
and explain how old vectors remain compatible.

## Save/load boundary

```python
model.save("model.gensim")
reloaded = models.LsiModel.load("model.gensim")
```

Use a temporary or explicit artifact directory and keep the dictionary near the
model. Compressed persistence can reduce space but may change load/mmap options.

## Distributed note

Gensim has optional distributed LSI/LDA dispatcher and worker modules using
`Pyro4`. A distributed cluster requires service/process/network setup and is not
a drop-in replacement for a local model. Prefer BLAS tuning or `LdaMulticore`
first; route cluster setup to an explicitly requested workflow.
