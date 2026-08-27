---
name: vectorizers-ctfidf
description: "Tunes BERTopic topic-term extraction with c-TF-IDF,
  CountVectorizer, OnlineCountVectorizer, and update_topics refreshes."
disable-model-invocation: true
metadata:
  disco-role: operating
  package: "BERTopic"
  package-version: "0.17.4"
  parent-skill: "bertopic"
license: MIT
---

# vectorizers-ctfidf

Use this sub-skill when the task is about BERTopic topic-term extraction: c-TF-IDF scoring, vectorizer tuning, or online vocabulary updates.

## Route here for

- `ClassTfidfTransformer` setup, including `bm25_weighting`, `reduce_frequent_words`, and seed-word boosts.
- `CountVectorizer` tuning for topic words: `ngram_range`, `stop_words`, `min_df`, `max_features`, and custom tokenizers.
- `OnlineCountVectorizer` incremental vocabulary workflows, including `decay` and `delete_min_df`.
- Refreshing fitted topic words with `BERTopic.update_topics(...)` using a new vectorizer or c-TF-IDF transformer.
- Debugging sparse topic-term matrices, empty vocabularies, or online cleanup behavior.

## Route elsewhere

- Embedding model or backend selection: use the embeddings backend sub-skill.
- Representation models, LLM labels, MMR, POS, KeyBERT-inspired labels, or multi-aspect labels: use the representations/labeling sub-skill.
- Plotting, hierarchy analysis, topic distributions, or dashboards: use the analysis/visualization sub-skill.
- Saving, loading, hub upload, or serialization format choices: use the serialization sub-skill.

## Read next

1. [`references/api-reference.md`](references/api-reference.md) for verified classes, signatures, and parameter behavior.
2. [`references/workflows.md`](references/workflows.md) for fit-time tuning, post-fit refreshes, custom tokenizers, and streaming vocabulary updates.
3. [`references/troubleshooting.md`](references/troubleshooting.md) for import, parameter, and online-vocabulary failures.
4. [`scripts/smoke_vectorizers.py`](scripts/smoke_vectorizers.py) for a safe synthetic smoke that exercises custom tokenization, c-TF-IDF sweeps, `update_topics`, and online cleanup.

## Minimal decision flow

- If the clusters are acceptable but the words are noisy, refresh representations with `update_topics(docs, vectorizer_model=..., ctfidf_model=...)` rather than retraining embeddings or clustering.
- If the vocabulary is too large, prefer `min_df` or `max_features`; for streaming models add `delete_min_df` on `OnlineCountVectorizer`.
- If generic words dominate many topics, try `stop_words`, a domain stopword list, `ClassTfidfTransformer(reduce_frequent_words=True)`, and on smaller corpora `bm25_weighting=True`.
- If terms need phrases, raise `ngram_range` and remove stopwords so multiword terms survive scoring.
- If the text needs custom segmentation, pass a deterministic tokenizer to `CountVectorizer` or `OnlineCountVectorizer` and keep it consistent across fit and refresh calls.

## Verification anchors

- Tiny synthetic corpus with a custom tokenizer and CountVectorizer sweep: expected output includes stable topic-specific terms, at least one phrase when bigrams are enabled, and a bounded vocabulary when `max_features` is set.
- Incremental `OnlineCountVectorizer` stream with `decay` and `delete_min_df`: expected output is a sparse matrix whose vocabulary can drop low-frequency historical terms and later re-add them when they become frequent again.
