# Text reference

## Verified API snapshot

Inspection ran against HyperTools 1.0.0 with `gensim` available in the private inspection environment.
Tiny local smoke checks passed for:
- sklearn text topic modeling with `CountVectorizer` + `LatentDirichletAllocation`
- gensim embeddings with `Word2Vec` and gensim semantic topics with `LdaModel`
- `hyp.plot(..., corpus=docs, show=False)` on a tiny local corpus

## Core entry points

### `hypertools.tools.text2mat.text2mat`
```python
text2mat(
    data,
    vectorizer='CountVectorizer',
    semantic='LatentDirichletAllocation',
    corpus='wiki',
)
```

Returns a `list` of `numpy.ndarray` matrices.

### `hypertools.tools.format_data.format_data`
```python
format_data(
    x,
    vectorizer='CountVectorizer',
    semantic='LatentDirichletAllocation',
    corpus='wiki',
    ppca=True,
    text_align='hyper',
    impute=None,
)
```

This is the shared input-preparation path used by `hyp.plot(...)` and `hyp.analyze(...)`.
It converts text to numeric matrices, fills missing numeric values, and aligns mixed text/numeric inputs when possible.

### `hyp.plot(...)`
`hyp.plot` forwards `vectorizer=`, `semantic=`, and `corpus=` into `format_data(...)` before the normal analysis pipeline runs.
That means text handling happens first; `reduce`, `align`, `normalize`, `cluster`, and style choices belong in sibling sub-skills.

## String resolution order

When `vectorizer=` or `semantic=` is a string, HyperTools resolves it in this order:

| Tier | Matches | Result |
| --- | --- | --- |
| 1 | sklearn built-ins | `CountVectorizer`, `TfidfVectorizer`, `LatentDirichletAllocation`, `NMF` |
| 2 | gensim wrappers | `Word2Vec`, `Doc2Vec`, `FastText`, `LdaModel`, `LsiModel`, `HdpModel` |
| 3 | Hugging Face fallback | treated as a sentence-transformers model id |

If a string is not a built-in name, the HF fallback is attempted.
When the call is routed through `format_data(...)` or `hyp.plot(...)`, HF/import failures are rewrapped as a clear `ValueError` naming the kwarg and the built-in alternatives.
Direct `text2mat(...)` calls can surface the lower-level HF/import error directly.

## Model/spec details

### sklearn vectorizers
- `CountVectorizer`: document-term counts.
- `TfidfVectorizer`: TF-IDF weights.
- Both accept the normal sklearn constructor kwargs through the dict spec, e.g. `{'model': 'CountVectorizer', 'kwargs': {'max_features': 5000}}`.

### sklearn semantic models
- `LatentDirichletAllocation`: topic proportions; rows sum to ~1.
- `NMF`: nonnegative components; useful with counts or TF-IDF features.
- Dict specs accept `kwargs` or legacy `params`.

### gensim vectorizers
- `Word2Vec`: mean token embeddings per document; default width `100`.
- `Doc2Vec`: inferred document embeddings; default width `100`.
- `FastText`: subword-safe mean embeddings; default width `100`.
- These produce embedding vectors, not topic proportions.
- Use `semantic=None` when you want the embeddings directly.

### gensim semantic models
- `LdaModel`: topic proportions from a document-term matrix.
- `LsiModel`: signed projections, not probabilities.
- `HdpModel`: variable topic discovery, truncated to the first `max_topics` columns.
- The usual input is `CountVectorizer` output, although dense TF-IDF matrices also pass through the same dispatcher.

## Corpus handling

- `corpus='wiki'`, `corpus='nips'`, and `corpus='sotus'` are hosted corpora.
- With the default `CountVectorizer` + `LatentDirichletAllocation` path, hosted corpora can use a pretrained topic model instead of refitting.
- A custom corpus is a `list` of text samples or a list of lists of text samples.
- A bare string corpus is treated as one literal training document, not as a corpus name.
- For mixed text + numeric inputs, `text_align='hyper'` is the default alignment choice when sample counts match.
- When text and numeric sample counts differ, HyperTools warns and keeps the datasets in separate spaces.

## Output expectations

- `CountVectorizer`/`TfidfVectorizer` + sklearn semantic models: dense topic matrices.
- `Word2Vec`/`Doc2Vec`/`FastText`: dense numpy embedding arrays after `text2mat(...)`, with one row per document. The underlying wrapper transformers use sparse matrices internally.
- `LdaModel`: dense topic proportions, row sums approximately 1.
- `LsiModel`: dense signed topic projections.
- `HdpModel`: dense truncated topic proportions.

## Verified smoke facts

- `CountVectorizer` + `LatentDirichletAllocation` on a 6-document local corpus returned `(6, 20)` with row sums of 1.
- `Word2Vec` on the same local corpus returned `(6, 100)`.
- `LdaModel` on the same local corpus returned `(6, 20)` with row sums of 1.
- `hyp.plot(docs, '.', corpus=docs, show=False, backend='matplotlib')` returned a figure.
