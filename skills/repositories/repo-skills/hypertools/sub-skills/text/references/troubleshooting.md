# Text troubleshooting

## Missing optional extras

### Symptom
`ImportError` mentioning `gensim` or `hypertools.tools.gensim_models requires gensim`.

### Fix
Install the optional gensim extra:
```bash
pip install "hypertools[gensim]"
```

### Symptom
An unresolved string falls through to the Hugging Face fallback and fails with a `datawrangler` / `sentence_transformers` import or download error.

### Fix
Install the optional text extra:
```bash
pip install "hypertools[text]"
```
If you did not mean to use a Hugging Face embedding model, switch to a built-in sklearn or gensim model name.

## Default wiki corpus and cache behavior

### Symptom
The first text plot is slow, touches the network, or seems to download `wiki` / `wiki_model`.

### Cause
The default text path can use hosted corpora or pretrained topic models.
Non-default vectorizers such as `Word2Vec` also train on the default `corpus='wiki'` unless you override it.
Those files are cached after the first successful load.

### Fix
- Use `corpus=docs` for a local training corpus.
- Use `corpus=None` for pretrained embedding model ids that do not need a training corpus.
- Wait for the first cache fill if you actually want the hosted corpus.
- If the environment has no network, avoid the hosted default and pass your own documents.

## `semantic=None` for embeddings

### Symptom
You used `Word2Vec`, `Doc2Vec`, `FastText`, or another embedding-style model and still saw a topic-model error or warning.

### Fix
Pass `semantic=None` explicitly.
That tells HyperTools to return the embedding matrix directly instead of trying to run a topic model on top of it.

## Negative values with LDA / NMF

### Symptom
`LatentDirichletAllocation` or `NMF` complains about negative values in the input.

### Cause
Embedding vectors can contain negative entries, but topic models expect nonnegative document-term style input.

### Fix
- Use `semantic=None` with embedding vectorizers.
- Or keep the semantic stage but feed it a document-term matrix from `CountVectorizer` or `TfidfVectorizer`.

## Typos that resolve as Hugging Face ids

### Symptom
A misspelled `vectorizer=` or `semantic=` string does not fail immediately and instead produces a network-style error.

### Cause
Unknown strings are treated as Hugging Face sentence-transformers ids after sklearn and gensim resolution miss.

### Fix
- Check the spelling of the built-in name first.
- If you meant a built-in, use one of the documented sklearn or gensim names.
- If you really meant a Hugging Face model id, install the `text` extra and use the full model id intentionally.

## Short or slang-heavy text

### Symptom
Very short snippets, slang, or niche jargon cluster almost on top of each other under the default wiki-topic path.

### Cause
The pretrained wiki topic model is tuned for sentence- or paragraph-length documents with common dictionary words.

### Fix
- Use a longer document window or a custom corpus.
- Try embeddings with `semantic=None`.
- Or pick a different text model that better matches your corpus.

## Corpus string mistakes

### Symptom
`corpus='something'` is accepted but the result looks wrong.

### Cause
A plain string corpus is treated as one literal training document unless it is one of the hosted corpus names.

### Fix
- Pass a list of documents for a real custom corpus.
- Or use exactly `wiki`, `nips`, or `sotus` when you want a hosted corpus.
