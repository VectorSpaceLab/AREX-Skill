---
name: analysis-visualization
description: "Inspect and visualize trained BERTopic models with topic,
  document, distribution, time, class, and hierarchy views."
disable-model-invocation: true
metadata:
  disco-role: operating
  package: BERTopic
  package-version: "0.17.4"
  parent-skill: bertopic
license: MIT
---

# analysis-visualization

Use this sub-skill when the model is already fitted and the task is to inspect, compare, or visualize topics, documents, topic distributions, hierarchy, temporal change, or class-specific topic views.

## Route here for

- `get_topic_info`, `get_topic`, `get_topics`, `get_topic_freq`, `get_representative_docs`
- `hierarchical_topics`, `get_topic_tree`
- `approximate_distribution`, `topics_over_time`, `topics_per_class`
- all `visualize_*` methods, including topic maps, document views, hierarchy views, heatmaps, bar charts, term-rank plots, topic-over-time plots, topics-per-class plots, probability/distribution plots, and approximate-distribution tables

## Route elsewhere

- Fitting, transforming, partial updates, topic mutation, outlier reassignment, or model building: use the topic-modeling sub-skill.
- Embedding backend selection or downloads: use the embeddings-backends sub-skill.
- Vectorizer / c-TF-IDF tuning and topic-word refreshes: use the vectorizers-ctfidf sub-skill.
- Representation models, labeling, or multi-aspect label generation: use the representations-labeling sub-skill.
- Save/load, hub publishing, or serialization formats: use the serialization sub-skill.

## Operating references

1. [`references/api-reference.md`](references/api-reference.md)
2. [`references/workflows.md`](references/workflows.md)
3. [`references/troubleshooting.md`](references/troubleshooting.md)
4. [`scripts/smoke_visualization.py`](scripts/smoke_visualization.py)

## Minimal decision flow

- Need a quick readout of what the model learned? Start with `get_topic_info()`, `get_topic_freq()`, `get_topic()`, and `get_representative_docs()`.
- Need a global topic landscape? Use `visualize_topics()`, `visualize_barchart()`, `visualize_heatmap()`, and `visualize_term_rank()`.
- Need document-level inspection? Use `visualize_documents()` or `visualize_hierarchical_documents()` with precomputed `reduced_embeddings` when possible.
- Need a single-document distribution? Use `approximate_distribution()` and then `visualize_distribution()` or `visualize_approximate_distribution()`.
- Need time or class comparison? Use `topics_over_time()` / `visualize_topics_over_time()` or `topics_per_class()` / `visualize_topics_per_class()`.
- Need hierarchy? Use `hierarchical_topics()`, inspect `get_topic_tree()`, then render `visualize_hierarchy()`.

## Notes

- Most plot functions exclude topic `-1` by default.
- `custom_labels` in plotting calls can be a boolean or an aspect-name string when the model has matching topic aspects.
- `visualize_topics()` and `visualize_hierarchy()` need UMAP for internal 2D topic layout; document views can avoid UMAP by accepting `reduced_embeddings`.
- `visualize_document_datamap()` needs `datamapplot`; `visualize_approximate_distribution()` returns a styled table only when Jinja2 is available.

## Verification anchors

- Tiny synthetic no-download model: exercise `visualize_topics`, `visualize_barchart`, `visualize_heatmap`, `visualize_documents`, and `visualize_distribution` from precomputed embeddings without downloading external models.
- Small-corpus analysis loop: compute `approximate_distribution`, `hierarchical_topics`, and `get_topic_tree`, then connect them to the distribution and hierarchy plots.

## Handoff constraint

Keep this sub-skill focused on inspection and visualization. Do not pull fit, backend, vectorizer, representation, or serialization setup into this skill.
