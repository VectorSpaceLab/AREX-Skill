---
name: embeddings-backends
description: "Select, adapt, and troubleshoot BERTopic embedding backends,
  precomputed embeddings, and multimodal image/text inputs."
disable-model-invocation: true
metadata:
  disco-role: operating
  package: BERTopic
  package-version: "0.17.4"
  parent-skill: bertopic
license: MIT
---

# embeddings-backends

Use this sub-skill when the task is about BERTopic embedding selection or backend adaptation rather than topic representations or c-TF-IDF.

## Route here for

- `embedding_model=` choices, `select_backend(...)`, and language-driven defaults.
- Sentence Transformers, Hugging Face feature-extraction pipelines, Model2Vec, Flair, spaCy, USE, Gensim, scikit-learn pipelines, OpenAI, Cohere, FastEmbed, LangChain, and MultiModal wrappers.
- `BaseEmbedder` subclasses, custom embedding classes, document/word backend composition, and deterministic offline embedders.
- Precomputed embeddings passed to `fit_transform(...)`, `transform(...)`, or tiny synthetic smoke checks.
- Multimodal text + image embeddings, `embed_images(...)`, and image/document alignment.
- Optional dependency detection, `NotInstalled` placeholders, and safe backend inventory checks.

## Route elsewhere

- Topic labels, KeyBERT-inspired/MMR/POS/LLM aspects, or `topic_aspects_`: use the representations-labeling sub-skill.
- c-TF-IDF, CountVectorizer tuning, online vocabulary updates, or `update_topics(...)` term refreshes: use the vectorizers-ctfidf sub-skill.
- Plotting, hierarchy analysis, topic distributions, or dashboards: use the analysis-visualization sub-skill.
- Save/load, format selection, or hub upload: use the serialization sub-skill.

## Operating references

1. Start with [`references/api-reference.md`](references/api-reference.md) for backend classes, selection rules, shape expectations, and optional-placeholder behavior.
2. Use [`references/workflows.md`](references/workflows.md) for explicit backend-selection paths, offline precomputed embeddings, custom backend construction, multimodal setup, and inventory checks.
3. Use [`references/troubleshooting.md`](references/troubleshooting.md) for install/import failures, placeholder errors, invalid shapes, wrong wrapper types, and download-related gotchas.
4. Run [`scripts/inventory_backends.py`](scripts/inventory_backends.py) to inventory available backends without downloads and to smoke-test a tiny deterministic local encoder.

## Minimal decision flow

- If you already have embeddings or need a no-download path, keep `embedding_model=None` and pass the matrix through `fit_transform(..., embeddings=...)` or `transform(..., embeddings=...)`.
- If you want BERTopic to choose a default backend, set `language=` only when no explicit embedding model is being passed; otherwise provide the backend directly.
- If you need one backend for documents and another for topic words, use `WordDocEmbedder` or a custom `BaseEmbedder`.
- If the task includes images, use `MultiModalBackend` or a custom backend that defines `embed_images(...)`; keep image/document rows aligned.
- If the backend selection must stay offline, avoid string model IDs because they can still trigger downloads.
- If you only need to know what is installed, use the bundled inventory script instead of probing by downloading models.

## Verification anchors for future checks

- Deterministic local custom backend: a tiny function-backed encoder that always returns the same `(n, d)` matrix for the same input.
- Precomputed embedding smoke: a small document list with a hand-built dense embedding matrix and explicit topic labels, fitted with `embedding_model=None` and no downloads.
- Optional-backend inventory: a report that distinguishes present modules, missing extras, and `NotInstalled` placeholders without instantiating remote models.
