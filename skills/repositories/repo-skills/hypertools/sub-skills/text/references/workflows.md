# Text workflows

## 1) Quick text plot from your own corpus

Use this when you want a plot first and the exact text model matters less than getting a useful local result.

```python
import hypertools as hyp

fig = hyp.plot(docs, '.', corpus=docs, show=False, backend='matplotlib')
```

Notes:
- `hyp.plot` sends the raw text through `format_data(...)` first.
- Passing `corpus=docs` keeps the workflow local and avoids the hosted wiki model/corpus path.
- If the corpus is short or slang-heavy, expect topic vectors to be less separable.

## 2) sklearn topic matrix for downstream analysis

Use this when you want a matrix, not a figure.

```python
from hypertools.tools import text2mat

mat = text2mat(
    [docs],
    vectorizer='CountVectorizer',
    semantic='LatentDirichletAllocation',
    corpus=docs,
)[0]
```

Typical variant:

```python
mat = text2mat(
    [docs],
    vectorizer='TfidfVectorizer',
    semantic={'model': 'NMF', 'kwargs': {'n_components': 3}},
    corpus=docs,
)[0]
```

Use `CountVectorizer` when you want classic topic counts and `TfidfVectorizer` when you want weighted features.

## 3) gensim embeddings

Use this when you want document embeddings instead of topics.

```python
emb = text2mat(
    [docs],
    vectorizer='Word2Vec',
    semantic=None,
    corpus=docs,
)[0]
```

Variant:

```python
emb = text2mat(
    [docs],
    vectorizer='Doc2Vec',
    semantic=None,
    corpus=docs,
)[0]
```

Optional follow-up:
- send the matrix to `../pipeline/` if you need `reduce=`, `align=`, `normalize=`, or `cluster=`
- send the plot styling questions to `../visualization/`

## 4) gensim topic proportions

Use this when you want a gensim topic model instead of sklearn LDA.

```python
topics = text2mat(
    [docs],
    vectorizer='CountVectorizer',
    semantic={'model': 'LdaModel', 'kwargs': {'num_topics': 3}},
    corpus=docs,
)[0]
```

Related variants:
- `LsiModel` for signed projections
- `HdpModel` for variable topic discovery with a fixed-width truncation

## 5) Hugging Face fallback embeddings

Use this only when you intentionally want a sentence-transformers model id.

```python
emb = text2mat(
    [docs],
    vectorizer='all-MiniLM-L6-v2',
    semantic=None,
    corpus=None,
)[0]
```

Notes:
- The name is resolved after sklearn and gensim miss.
- This path needs the optional `text` extra (`pydata-wrangler[hf]`).
- Keep `semantic=None` for embeddings; the HF fallback does not turn them into topic models.
- Use `corpus=None` for pretrained HF embeddings so the default hosted wiki corpus is not loaded just to perform a no-op fit.
- If the model id is wrong, fix the spelling rather than assuming HyperTools added a new built-in.

## Practical decision tree

1. Need quick topic plots on raw text? Use `hyp.plot(docs, '.', corpus=docs, ...)`.
2. Need a matrix for later analysis? Use `text2mat(...)`.
3. Need embeddings? Use `Word2Vec`/`Doc2Vec`/`FastText` with `semantic=None`.
4. Need topic proportions from gensim? Use `LdaModel`/`LsiModel`/`HdpModel`.
5. Need a pretrained sentence-transformers embedding? Use the HF fallback and keep `semantic=None`.
6. If the question is about layout, color, animation, or export, hand it to `../visualization/`.
7. If the question is about reduction or clustering after text conversion, hand it to `../pipeline/`.
