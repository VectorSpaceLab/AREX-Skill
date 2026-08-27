# analysis-visualization API reference

This reference covers BERTopic 0.17.4 APIs owned by the analysis-visualization sub-skill: topic inspection, hierarchy extraction, temporal and class summaries, approximate distributions, and plotting. It intentionally does not explain model fitting, embedding backend selection, vectorizer tuning, representation models, or persistence.

## Dependency map

| Method family | Return type | Main dependencies | Notes |
| --- | --- | --- | --- |
| `get_topic*`, `get_topic_info`, `get_representative_docs` | pandas / Python objects | fitted `BERTopic` instance | Fastest way to inspect a trained model. |
| `hierarchical_topics`, `get_topic_tree` | DataFrame / string | fitted model, SciPy, vectorizer state | Produces hierarchy data and a printable tree. |
| `topics_over_time`, `topics_per_class`, `approximate_distribution` | DataFrame / ndarray | fitted model | These are the analysis tables that feed the comparison plots. |
| `visualize_topics`, `visualize_hierarchy` | `plotly.graph_objects.Figure` | Plotly, SciPy, UMAP | UMAP is used internally for 2D topic layout. |
| `visualize_documents`, `visualize_hierarchical_documents` | Plotly figure | Plotly, optional UMAP | UMAP is only needed when `reduced_embeddings` is not supplied. |
| `visualize_document_datamap` | Matplotlib / DataMapPlot figure | `datamapplot`, optional UMAP | Requires `datamapplot`; interactive mode is optional. |
| `visualize_heatmap`, `visualize_barchart`, `visualize_term_rank`, `visualize_topics_over_time`, `visualize_topics_per_class`, `visualize_distribution` | Plotly figure | Plotly | No UMAP required. |
| `visualize_approximate_distribution` | pandas Styler or DataFrame | pandas, optional Jinja2 | Jinja2 only affects styling; the plain DataFrame is still returned. |

## Topic inspection

### `get_topics(full=False)`

Return the fitted topic representations as a mapping from topic id to `[(word, score), ...]`.

- `full=False` returns the main topic representation only.
- `full=True` returns a dictionary with `"Main"` plus any fitted aspects.
- Use this when you need a programmatic view of every topic without plotting.

### `get_topic(topic, full=False)`

Return the representation for one topic id.

- Returns `False` when the topic id does not exist.
- `full=True` returns `"Main"` plus any fitted aspects for that topic.
- Use `get_topic_info()` first if you are not sure which ids are present.

### `get_topic_info(topic=None)`

Return a DataFrame with topic metadata.

Typical columns include:

- `Topic`
- `Count`
- `Name`
- `Representation`
- optional aspect columns
- optional `Representative_Docs` / `Representative_Images`
- optional `CustomName`

Notes:

- The full table is sorted by topic id.
- Passing `topic=<id>` filters to a single topic row.

### `get_topic_freq(topic=None)`

Return topic frequency information.

- Without `topic`, returns a DataFrame sorted by `Count` descending.
- With `topic=<id>`, returns a single integer count.
- This is a good first check before choosing a subset for plots.

### `get_representative_docs(topic=None)`

Return the representative documents stored for the fitted topics.

- With `topic=<id>`, returns the list for that topic or `None` if the topic is missing.
- Without `topic`, returns the full topic-to-documents mapping.
- BERTopic does not store every training document; this is a curated subset.

## Topic analysis tables

### `hierarchical_topics(docs, use_ctfidf=True, linkage_function=None, distance_function=None)`

Build a hierarchy of topics from a fitted model and the original documents.

- Returns a DataFrame with parent/child ids, names, topic membership, and `Distance`.
- The `docs` list must correspond to the documents used to fit the model.
- `use_ctfidf=True` bases the hierarchy on topic-term representations; `False` uses topic embeddings.
- If you pass custom linkage or distance functions, reuse the same choices when plotting the hierarchy.

### `get_topic_tree(hier_topics, max_distance=None, tight_layout=False)`

Turn the hierarchical topic DataFrame into a printable tree string.

- `hier_topics` should be the DataFrame returned by `hierarchical_topics()`.
- The blocks (`■`) mark leaf topics that can be accessed directly with `get_topic()`.
- Use `tight_layout=True` when you need a narrower tree for many topics.

### `topics_over_time(docs, timestamps, topics=None, nr_bins=None, datetime_format=None, evolution_tuning=True, global_tuning=True)`

Create a topic-over-time DataFrame.

- Returns columns: `Topic`, `Words`, `Frequency`, `Timestamp`.
- `timestamps` can be integers or strings; string timestamps may use `datetime_format`.
- `nr_bins` bins timestamps into a smaller set of intervals.
- `evolution_tuning` and `global_tuning` smooth the time-specific topic words.
- Keep the number of unique timestamps small; many unique timestamps make this expensive.

### `topics_per_class(docs, classes, global_tuning=True)`

Create a topic-by-class DataFrame.

- Returns columns: `Topic`, `Words`, `Frequency`, `Class`.
- `classes` can be strings or integers and must align with `docs`.
- `global_tuning=False` exposes the local class-specific topic words more directly.
- Keep the number of unique classes modest; many classes make this slower.

### `approximate_distribution(documents, window=4, stride=1, min_similarity=0.1, batch_size=1000, padding=False, use_embedding_model=False, calculate_tokens=False, separator=" ")`

Approximate document-topic distributions post hoc.

- Accepts one string or a list of strings.
- Returns `(topic_distributions, topic_token_distributions)`.
- `topic_distributions` is an `n x m` array.
- `topic_token_distributions` is `None` unless `calculate_tokens=True`.
- `use_embedding_model=False` uses c-TF-IDF similarity; `True` uses the embedding backend.
- `padding=True` keeps edge windows when token sets would otherwise be shorter than `window`.
- `min_similarity` is a useful knob when the output is too sparse.

## Plotting methods

### `visualize_topics(topics=None, top_n_topics=None, use_ctfidf=False, custom_labels=False, title="<b>Intertopic Distance Map</b>", width=650, height=650)`

Plot a 2D topic map.

- Uses internal UMAP on topic representations.
- `top_n_topics` is the easiest way to keep the figure readable.
- `use_ctfidf=True` swaps to c-TF-IDF topic representations before the 2D layout.
- `custom_labels` can be `True` or an aspect name string when the model has matching topic aspects.

### `visualize_documents(docs, topics=None, embeddings=None, reduced_embeddings=None, sample=None, hide_annotations=False, hide_document_hover=False, custom_labels=False, title="<b>Documents and Topics</b>", width=1200, height=750)`

Plot documents in 2D with their topic assignments.

- Pass `reduced_embeddings` to avoid internal UMAP and to get stable layouts.
- If `embeddings` and `reduced_embeddings` are both omitted, BERTopic will try to extract embeddings.
- `sample` downsamples per topic; use `hide_document_hover=True` for large corpora.
- Good for checking whether documents cluster as expected.

### `visualize_document_datamap(docs=None, topics=None, embeddings=None, reduced_embeddings=None, custom_labels=False, title="Documents and Topics", sub_title=None, width=1200, height=750, interactive=False, enable_search=False, topic_prefix=False, datamap_kwds={}, int_datamap_kwds={})`

Plot a publication-style document map with DataMapPlot.

- Requires `datamapplot`.
- `interactive=True` switches to the interactive DataMapPlot path; `enable_search` only applies there.
- `topic_prefix=True` prepends the topic id to the label.
- Use `reduced_embeddings` when you already have a 2D layout.

### `visualize_hierarchical_documents(docs, hierarchical_topics, topics=None, embeddings=None, reduced_embeddings=None, sample=None, hide_annotations=False, hide_document_hover=True, nr_levels=10, level_scale="linear", custom_labels=False, title="<b>Hierarchical Documents and Topics</b>", width=1200, height=750)`

Plot documents across multiple hierarchy levels.

- Requires the `hierarchical_topics` DataFrame from `hierarchical_topics()`.
- Use `reduced_embeddings` to avoid an internal UMAP reduction.
- `nr_levels` controls how many hierarchy levels are shown in the slider.
- `level_scale` can be `"linear"` or `"log"`/`"logarithmic"`.

### `visualize_term_rank(topics=None, log_scale=False, custom_labels=False, title="<b>Term score decline per Topic</b>", width=800, height=500)`

Plot c-TF-IDF score decline by term rank.

- Useful for deciding how many words a topic representation should show.
- `log_scale=True` makes low-scoring terms easier to compare.
- If a topic appears to be missing, check whether its scores are unusually large or whether the model has many outlier topics.

### `visualize_distribution(probabilities, min_probability=0.015, custom_labels=False, title="<b>Topic Probability Distribution</b>", width=800, height=600)`

Plot one probability or distribution vector as a bar chart.

- Pass a single 1D row, not the full matrix.
- Use `topic_distributions[i]` or `probabilities[i]` for one document.
- Raises `ValueError` if the input is not 1D or if `min_probability` filters everything out.

### `visualize_approximate_distribution(document, topic_token_distribution, normalize=False)`

Plot the token-level distribution table for a single document.

- The second argument must come from `approximate_distribution(..., calculate_tokens=True)`.
- Returns a styled DataFrame when Jinja2 is available; otherwise returns a plain DataFrame.
- The tokenizer comes from the fitted model’s `vectorizer_model`.

### `visualize_hierarchy(orientation="left", topics=None, top_n_topics=None, use_ctfidf=True, custom_labels=False, title="<b>Hierarchical Clustering</b>", width=1000, height=600, hierarchical_topics=None, linkage_function=None, distance_function=None, color_threshold=1)`

Plot the topic dendrogram.

- Uses internal UMAP to place topic representations in 2D.
- `hierarchical_topics` lets the plot annotate a precomputed hierarchy.
- Keep `linkage_function` and `distance_function` consistent with `hierarchical_topics()` if you want matching labels.
- `orientation` can be `"left"` or `"bottom"`.

### `visualize_heatmap(topics=None, top_n_topics=None, n_clusters=None, use_ctfidf=False, custom_labels=False, title="<b>Similarity Matrix</b>", width=800, height=800)`

Plot a topic similarity matrix.

- `n_clusters` reorders the matrix into blocks of similar topics.
- `n_clusters` must be smaller than the number of unique selected topics.
- `use_ctfidf=True` compares topics in c-TF-IDF space; `False` uses topic embeddings.

### `visualize_barchart(topics=None, top_n_topics=8, n_words=5, custom_labels=False, title="Topic Word Scores", width=250, height=250, autoscale=False)`

Plot the top words for a set of topics.

- Excludes topic `-1` from the default selection.
- `top_n_topics` controls how many topic subplots are shown.
- `autoscale=True` helps when topic labels are long.
- This is a quick way to compare the topic words before building heavier plots.

## Cross-method notes

- `custom_labels` can be a boolean or an aspect-name string in plotting calls when the corresponding aspect exists in `topic_aspects_`.
- Most default selections exclude the outlier topic `-1`.
- `visualize_documents()` and `visualize_hierarchical_documents()` are easiest to use when you precompute `reduced_embeddings` yourself.
- `visualize_topics_over_time()` and `visualize_topics_per_class()` consume the DataFrames returned by `topics_over_time()` and `topics_per_class()`.
- `visualize_distribution()` expects a single row vector; use the approximate distribution or probability row for one document.
- `visualize_approximate_distribution()` needs token-level output, so call `approximate_distribution(..., calculate_tokens=True)`.
