---
name: topic-modeling
description: "Build, fit, query, and mutate BERTopic topic models."
metadata:
  disco-role: operating
  package: BERTopic
  package-version: "0.17.4"
  parent-skill: bertopic
disable-model-invocation: true
license: MIT
---

# Topic Modeling

Use this sub-skill for BERTopic lifecycle work when the task is about building or changing a topic model rather than choosing embeddings, tuning c-TF-IDF/vectorizers, labeling topics, plotting, or saving models.

## Covered workflows

- Construct BERTopic with default or custom reducer/cluster components.
- Fit, `fit_transform`, `transform`, and `partial_fit` on documents, precomputed embeddings, or image-aligned inputs.
- Run guided, supervised, semi-supervised, manual, zero-shot, online, and multimodal fitting variants.
- Query topics, frequencies, documents, representative docs, and topic search results.
- Reduce, merge, delete, and outlier-correct topics.
- Merge multiple fitted models.
- Inspect parameter state with `get_params`.

## Not covered here

- Embedding backend selection or download troubleshooting.
- c-TF-IDF/vectorizer tuning, seed-word weighting, or online vocabulary tuning details.
- Topic representation and labeling models.
- Visualizations, comparison plots, or downstream analysis.
- Save/load, hub publishing, or other serialization paths.

## Working notes

- `fit` / `fit_transform` accept `documents`, optional `embeddings`, optional `images`, and optional `y`.
- `partial_fit` is the streaming path; use a reducer and clusterer that support `partial_fit`.
- `transform` only works on fitted models with an inference-capable cluster path.
- `find_topics` needs a live `embedding_model`; if you only have precomputed embeddings, provide a local offline embedder or route the request elsewhere.
- `reduce_outliers` returns a new topic list; if you need refreshed representations afterward, hand that job to the vectorizer/representation sub-skill.
- `merge_topics`, `delete_topics`, and `reduce_topics` mutate the fitted model in place and update `topic_mapper_`.
- `partial_fit` tracks the current batch in `topics_`; keep your own history if you need a cumulative stream view.
- `images` are supported for fit-time and transform-time multimodal workflows; `partial_fit` does not take images.

## References

- `references/api-reference.md`
- `references/workflows.md`
- `references/troubleshooting.md`
- `scripts/smoke_topic_model.py`
