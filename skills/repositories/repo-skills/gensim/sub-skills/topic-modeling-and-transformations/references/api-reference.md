# Topic Modeling and Transformation API Reference

## Transformations

### TF-IDF

`models.TfidfModel` transforms integer BoW counts into weighted vectors. The
verified constructor is:

```python
TfidfModel(corpus=None, id2word=None, dictionary=None,
           wlocal=identity, wglobal=df2idf, normalize=True,
           smartirs=None, pivot=None, slope=0.25)
```

Apply it lazily with `tfidf[bow]` or `tfidf[corpus]`. The training corpus and
future vectors must use the same feature ids.

### BM25

`models.OkapiBM25Model(corpus=None, dictionary=None, k1=1.5, b=0.75,
epsilon=0.25)` produces Okapi BM25-style weights. It is a weighting transform,
not a full document index; route retrieval/index construction to the similarity
sub-skill.

### LSI

`models.LsiModel` performs latent semantic indexing/SVD-style projection. Useful
parameters include `num_topics`, `chunksize`, `decay`, `onepass`, `power_iters`,
`extra_samples`, and `random_seed`. It supports incremental updates through
`add_documents` and folds new vectors into the learned space with `model[vector]`.

## Topic models

### LDA

`models.LdaModel` trains online latent Dirichlet allocation. Key parameters:

- `num_topics`: number of topics to learn.
- `chunksize`: documents processed per update.
- `passes`: passes over the corpus.
- `iterations`: per-document inference iterations.
- `alpha` and `eta`: document/topic and topic/word priors; may be scalar,
  vector, or supported strings such as `'symmetric'`/`'auto'`.
- `eval_every`: perplexity evaluation interval; set to `None` to avoid extra
  evaluation on large runs.
- `random_state`: reproducible initialization for controlled experiments.
- `minimum_probability`, `per_word_topics`, and `callbacks`: output and
  monitoring controls.

`LdaMulticore` follows the LDA API while using multiple CPU workers. Keep
`workers` conservative and use `random_state` plus small fixtures for smoke
checks.

### Other models

- `HdpModel` learns a nonparametric topic structure; it requires an explicit
  corpus and `id2word` and has different convergence/runtime behavior.
- `Nmf` performs online non-negative matrix factorization.
- `RpModel` provides random projection dimensionality reduction.
- `LogEntropyModel` and `NormModel` provide additional vector transforms.

## Topic coherence

`models.CoherenceModel(model=None, topics=None, texts=None, corpus=None,
dictionary=None, window_size=None, keyed_vectors=None, coherence='c_v', topn=20,
processes=-1)` can score topics from a model or explicit topic lists. Choose
inputs that match the coherence measure:

- `u_mass` commonly uses a BoW corpus and dictionary.
- `c_v`, `c_uci`, and `c_npmi` generally use tokenized texts and a dictionary.
- `c_w2v` needs keyed vectors and compatible topic terms.

Do not compare coherence scores from incompatible preprocessing or different
`topn`/window settings without recording those choices.

## Persistence and application

Models normally support `model.save(path)` and `Class.load(path)`. A model
persisted without the dictionary may not be enough to display readable terms;
save the dictionary and record the preprocessing pipeline alongside it.

Most transforms are lazy wrappers over a corpus. Iterating the result performs
conversion; calling the wrapper itself does not materialize every document.
