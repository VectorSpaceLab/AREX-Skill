# analysis-visualization workflows

These workflows are safe operating patterns for inspecting and visualizing a fitted BERTopic 0.17.4 model. They assume model fitting, embedding selection, vectorizer tuning, and labeling are handled elsewhere when those concerns are primary.

## 1. Fast inspection after fit

Start with the non-plot methods when you need to understand what the model learned without building figures.

```python
info = topic_model.get_topic_info()
freq = topic_model.get_topic_freq()
representatives = topic_model.get_representative_docs()

# Pick a topic id from the table and inspect it directly.
first_topic = int(info.loc[info.Topic != -1, "Topic"].iloc[0])
words = topic_model.get_topic(first_topic)
count = topic_model.get_topic_freq(first_topic)
```

What to check:

- `get_topic_info()` gives the fastest global summary.
- `get_topic_freq()` is useful when you want a count-only view.
- `get_topic()` and `get_representative_docs()` are the fastest way to sanity-check a single topic before plotting.
- If the topic ids look unfamiliar, inspect `info` immediately after fit or after any later mutation step performed elsewhere.

## 2. Topic landscape without downloads

Use the topic-map style plots when you want a compact overview of the model.

```python
fig_topics = topic_model.visualize_topics()
fig_bar = topic_model.visualize_barchart(top_n_topics=8)
fig_heat = topic_model.visualize_heatmap(top_n_topics=8)
fig_rank = topic_model.visualize_term_rank()
```

Guidance:

- `visualize_topics()` and `visualize_hierarchy()` need UMAP inside the plotting path.
- `visualize_barchart()`, `visualize_heatmap()`, and `visualize_term_rank()` do not need UMAP.
- If the environment does not have UMAP, you can still inspect the model with the non-UMAP plots and the raw topic tables.
- If the topic labels are too generic, use the plot-level `custom_labels` argument only after sibling labeling workflows have populated matching labels or aspects.

## 3. Document and hierarchy views

Document plots are easiest to use when you precompute a stable 2D layout yourself.

```python
from sklearn.decomposition import PCA

reduced_embeddings = PCA(n_components=2).fit_transform(embeddings)

fig_docs = topic_model.visualize_documents(
    docs,
    reduced_embeddings=reduced_embeddings,
    hide_document_hover=True,
)

hierarchical_topics = topic_model.hierarchical_topics(docs)
fig_hdocs = topic_model.visualize_hierarchical_documents(
    docs,
    hierarchical_topics,
    reduced_embeddings=reduced_embeddings,
    hide_document_hover=True,
)
```

Guidance:

- Precomputing `reduced_embeddings` avoids internal UMAP randomness and avoids extra downloads.
- `hide_document_hover=True` keeps large figures lighter.
- `sample` is useful for huge corpora, but for tiny smoke checks keep the full set.
- `visualize_hierarchical_documents()` works best when you reuse the same `hierarchical_topics` DataFrame you will also inspect with `get_topic_tree()` or `visualize_hierarchy()`.

## 4. Distribution and token contribution

This is the main workflow when you want to explain why a single document is assigned to a topic.

```python
topic_distr, token_distr = topic_model.approximate_distribution(
    docs,
    calculate_tokens=True,
    min_similarity=0.0,
)

fig_dist = topic_model.visualize_distribution(topic_distr[0], min_probability=0.0)
fig_tokens = topic_model.visualize_approximate_distribution(docs[0], token_distr[0], normalize=True)
```

Guidance:

- Use `min_similarity=0.0` for tiny smoke checks when you want to guarantee a non-empty distribution.
- `visualize_distribution()` expects one row vector, not the whole matrix.
- `visualize_approximate_distribution()` only works with the token-level output from `calculate_tokens=True`.
- If the table is styled, Jinja2 is installed; if it is plain, the workflow still worked.

## 5. Time and class comparison

When the question is “how do these topics vary across time or subgroups?”, use the summary tables first and only then plot them.

```python
tot = topic_model.topics_over_time(docs, timestamps, nr_bins=10)
fig_tot = topic_model.visualize_topics_over_time(tot, top_n_topics=10)

classes = [...]  # one class per document
per_class = topic_model.topics_per_class(docs, classes)
fig_class = topic_model.visualize_topics_per_class(per_class, top_n_topics=10)
```

Guidance:

- Keep the `docs`, `timestamps`, `classes`, and topic assignments aligned.
- Use `nr_bins` if the timestamp axis would otherwise have many unique values.
- Set `global_tuning=False` when you want the local time/class representation to stay as raw as possible.
- If the plot has too many lines or bars, narrow the selected topics with `topics=` or `top_n_topics=` before trying to restyle the figure.

## 6. Hierarchy tree and dendrogram

Use the hierarchy methods when you want to understand what merges would look like.

```python
hierarchical_topics = topic_model.hierarchical_topics(docs)
tree = topic_model.get_topic_tree(hierarchical_topics)
fig_hierarchy = topic_model.visualize_hierarchy(hierarchical_topics=hierarchical_topics)
```

Guidance:

- Keep the `distance_function` and `linkage_function` choices consistent between hierarchy generation and hierarchy plotting.
- Use `use_ctfidf=True` when you want the merge logic to reflect topic-term structure rather than semantic embeddings.
- The tree is often the easiest artifact to paste into a review note when you need a text-only hierarchy summary.

## 7. Suggested no-download smoke order

If you are building a helper script, a compact and reliable order is:

1. Fit a tiny synthetic model from precomputed embeddings.
2. Run `get_topic_info()`, `get_topic_freq()`, and `get_representative_docs()`.
3. Run `visualize_barchart()`, `visualize_heatmap()`, `visualize_term_rank()`, and `visualize_topics()`.
4. Build `topics_over_time()` and `topics_per_class()` and visualize them.
5. Build `approximate_distribution()` and inspect one document with `visualize_distribution()` and `visualize_approximate_distribution()`.
6. Build `hierarchical_topics()`, print `get_topic_tree()`, and render `visualize_hierarchy()`.
7. If available, add `visualize_documents()`, `visualize_hierarchical_documents()`, and `visualize_document_datamap()` using precomputed `reduced_embeddings`.

This order keeps the workflow robust: the cheap inspection methods run first, and the more dependency-sensitive plots run later.
