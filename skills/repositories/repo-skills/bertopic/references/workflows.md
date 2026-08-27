# BERTopic workflows

## Purpose

Use this page when you know the task family but want the shortest route through the generated skill tree.

## Route by intent

- Build or mutate topic models: `sub-skills/topic-modeling/`
- Choose or wrap embedding backends: `sub-skills/embeddings-backends/`
- Improve topic-word extraction and online term updates: `sub-skills/vectorizers-ctfidf/`
- Improve labels, rerank keywords, or manage multi-aspect outputs: `sub-skills/representations-labeling/`
- Inspect fitted models and render plots: `sub-skills/analysis-visualization/`
- Save, load, or publish a fitted model: `sub-skills/serialization/`

## Common end-to-end order

Most BERTopic tasks flow through the same sequence:

1. Choose embeddings or pass precomputed embeddings.
2. Build and fit the topic model.
3. Tune the topic-word representation if the labels are noisy.
4. Add one or more representation models if labels should be cleaner or multi-aspect.
5. Inspect with tables and plots.
6. Save or publish the final model.

## Offline and no-download path

If you already have embeddings or need to stay offline, keep the model construction path simple:

- use `embedding_model=None` and pass the matrix through `fit_transform(..., embeddings=...)`
- keep the reducer and clusterer synthetic or lightweight when possible
- prefer the topic-modeling, vectorizers-ctfidf, and analysis-visualization subskills for the no-download workflow
- use the embeddings-backends subskill only when you truly need a backend object instead of precomputed embeddings

## When to switch subskills mid-task

- If the clusters are acceptable but the words are noisy, move from topic-modeling to vectorizers-ctfidf.
- If the cluster and words are good but the label is not, move from vectorizers-ctfidf to representations-labeling.
- If the fitted model is ready and you need interpretation, move to analysis-visualization.
- If the fitted model must be persisted or shared, move to serialization last.

## Quick route reminders

- `topic-modeling` owns `fit`, `fit_transform`, `transform`, `partial_fit`, topic mutation, and model combination.
- `embeddings-backends` owns backend selection, backend inventory, and custom embedders.
- `vectorizers-ctfidf` owns c-TF-IDF and vectorizer refresh logic.
- `representations-labeling` owns labels, prompt-based topic text, and multi-aspect topic views.
- `analysis-visualization` owns topic tables, hierarchy, distributions, and plots.
- `serialization` owns save/load and Hub sharing.
