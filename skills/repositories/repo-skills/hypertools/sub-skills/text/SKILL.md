---
name: text
description: "Convert text into matrices and plots with HyperTools text models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Text

Use this route for HyperTools text-to-matrix work and text-aware plotting.

## Use this sub-skill when you need to
- Turn raw documents, corpora, or mixed text collections into matrices.
- Choose or debug `vectorizer=`, `semantic=`, or `corpus=` for `hypertools.tools.text2mat` and `hypertools.tools.format_data`.
- Plot text directly with `hyp.plot(...)`, including the default wiki-topic workflow and custom corpora.
- Use sklearn text models (`CountVectorizer`, `TfidfVectorizer`, `LatentDirichletAllocation`, `NMF`).
- Use gensim text models (`Word2Vec`, `Doc2Vec`, `FastText`, `LdaModel`, `LsiModel`, `HdpModel`).
- Understand Hugging Face sentence-transformers fallback behavior when an unresolved model name is treated as an embedding id.

## Route elsewhere when the task is really about
- Plot styling, layout, colors, legends, backends, animation, or export: use `../visualization/`.
- Reduction, alignment, normalization, clustering, or pipeline stage ordering: use `../pipeline/`.

## Read first
- `references/text-reference.md`
- `references/workflows.md`
- `references/troubleshooting.md`
- `scripts/smoke_text.py`

## Fast rules
1. `hyp.plot(...)` forwards text through `format_data(...)` before the ordinary analysis pipeline.
2. `text2mat(...)` and `format_data(...)` both accept text as `str`, list of `str`, or list of lists of `str`.
3. String model names resolve in this order: sklearn → gensim → Hugging Face fallback.
4. `semantic=None` means “skip the topic-model stage and return the embedding/vectorized matrix directly.”
5. `CountVectorizer` and `TfidfVectorizer` pair naturally with sklearn `LatentDirichletAllocation` and `NMF`.
6. `Word2Vec`, `Doc2Vec`, and `FastText` are embedding vectorizers; use `semantic=None` for direct embeddings unless you intentionally want a later semantic model.
7. `LdaModel`, `LsiModel`, and `HdpModel` are gensim semantic models; feed them a document-term matrix, usually from `CountVectorizer`.
8. `corpus='wiki'`, `'nips'`, or `'sotus'` selects a hosted corpus or pretrained topic model when the default text path applies; a custom `corpus=` list trains on your own documents.
9. If the question becomes “how should I reduce, align, normalize, or cluster the text matrix?”, hand it to `../pipeline/`.
10. If the question becomes “how should I style the resulting plot?”, hand it to `../visualization/`.
