# analysis-visualization troubleshooting

Use this page when topic inspection, hierarchy extraction, distribution approximation, or visualization fails after a BERTopic model has already been fitted.

## Install/import and optional dependency failures

### `ModuleNotFoundError: No module named 'bertopic'`

- Verify that the current Python environment is the one with BERTopic 0.17.4 installed.
- A minimal check should be `python -c "import bertopic; from bertopic import BERTopic; print(bertopic.__version__)"`.

### Plotly import failures

Most visualization methods here return Plotly figures. If `plotly` is missing or broken, the following methods will fail:

- `visualize_topics`
- `visualize_documents`
- `visualize_hierarchical_documents`
- `visualize_term_rank`
- `visualize_topics_over_time`
- `visualize_topics_per_class`
- `visualize_distribution`
- `visualize_hierarchy`
- `visualize_heatmap`
- `visualize_barchart`

Fix: install or repair `plotly` and the core scientific stack that BERTopic uses.

### UMAP-related failures

`visualize_topics()` and `visualize_hierarchy()` always use UMAP internally.

`visualize_documents()` and `visualize_hierarchical_documents()` only need UMAP when you do **not** provide `reduced_embeddings`.

Typical symptoms:

- `ModuleNotFoundError: No module named 'umap'`
- a `ModuleNotFoundError` raised from inside a plot helper that tries to reduce topic embeddings

Fix options:

- install `umap-learn`, or
- precompute `reduced_embeddings` for the document views, or
- fall back to the non-UMAP plots (`visualize_barchart`, `visualize_heatmap`, `visualize_term_rank`, `visualize_distribution`).

### DataMapPlot failures

`visualize_document_datamap()` requires `datamapplot`.

- If the dependency is missing, the module may warn at import time and the plot call may later fail with a `NameError` because the backend is unavailable.
- If you only need a document view, use `visualize_documents()` with `reduced_embeddings` instead.

### Jinja2 / styled-table behavior

`visualize_approximate_distribution()` does **not** fail when Jinja2 is missing.

- With Jinja2 installed, it returns a styled DataFrame.
- Without Jinja2, it returns a plain DataFrame.
- This is expected behavior, not an error.

### Pandas 3.0 styled-table regression

Some BERTopic builds still call `Styler.applymap(...)` inside the approximate-distribution styling helper. In pandas 3.0 this can raise:

- `AttributeError: 'Styler' object has no attribute 'applymap'`

Recovery:

- treat `visualize_approximate_distribution()` as optional in pandas 3.0 environments;
- inspect the raw `approximate_distribution(...)` output first;
- if the styled table is important, use a pandas version that still supports the helper or patch the styling path in the package before relying on that plot.

### Hierarchical document plots on tiny corpora

`visualize_hierarchical_documents()` can fail with an `IndexError` when the fitted model has too few hierarchical levels for the requested slider layout.

Recovery:

- use a slightly larger corpus;
- reduce the visual complexity by lowering `nr_levels`;
- fall back to `visualize_hierarchy()` and `get_topic_tree()` if the hierarchy view is all you need.

## CLI/API misuse and invalid inputs

### Passing the wrong object to `visualize_distribution`

`visualize_distribution()` expects one 1D probability or distribution row.

Common mistakes:

- passing the full `n x m` matrix
- passing a list of topic ids instead of probabilities
- passing a nested array whose first dimension is not one document

Fix: select a single row, such as `topic_distr[0]` or `probabilities[0]`.

### Empty bars in `visualize_distribution`

If `min_probability` is too high, everything can be filtered out and the plot raises a `ValueError`.

Fix: lower `min_probability` or use the approximate distribution row with a denser threshold.

### Shape mismatch in document views

For document plots, the lengths must align:

- `len(docs)` must match the fitted topic assignment length
- `embeddings` must have one row per document when supplied
- `reduced_embeddings` must have one 2D point per document when supplied

This also applies to `topics_over_time()` and `topics_per_class()` inputs.

### `topics_over_time()` / `topics_per_class()` misalignment

These methods assume the documents and their auxiliary labels are aligned to the fitted model’s document order.

Common mistakes:

- filtering `docs` but not filtering `timestamps`, `classes`, or `topics`
- passing labels from a different corpus
- mixing the fit-time corpus with a reordered analysis corpus

Fix: filter or reorder all aligned inputs together before calling the method.

### `hierarchical_topics()` used on the wrong corpus

`hierarchical_topics(docs)` expects the original documents used with the fitted model.

If the document set no longer matches the fitted model, the hierarchy may be misleading even if it does not crash.

### `visualize_heatmap(..., n_clusters=...)` fails

`n_clusters` must be smaller than the number of selected topics.

Fix: reduce `n_clusters`, or choose a larger topic subset.

### `visualize_approximate_distribution()` gives a token error

This method uses the fitted model’s tokenizer.

- If the document has no tokens under that tokenizer, it raises `ValueError`.
- The second argument must come from `approximate_distribution(..., calculate_tokens=True)`.
- Older examples may mention `calculate_token_level`; the current API uses `calculate_tokens`.

## Backend and dependency-specific gotchas

### `visualize_topics()` and `visualize_hierarchy()` are not fully reproducible from run to run

They rely on internal UMAP reduction of topic representations.

- Topic plots use fixed random state internally.
- Document plots can still vary when internal UMAP is used.

Fix: precompute and pass `reduced_embeddings` for document views if you want stable layouts.

### `visualize_documents()` or `visualize_hierarchical_documents()` hide a topic unexpectedly

Common causes:

- `sample` is too small
- `topics=` filters the topic out
- the model produced outlier topic `-1`

Fix: use `sample=None` or `1.0` for smoke checks and inspect `topic_model.get_topic_info()` first.

### `visualize_term_rank()` seems to skip a topic

The current implementation may omit topics whose c-TF-IDF values are outside the expected range.

Fix: inspect `get_topic_info()` and `get_topic()` for the missing topic before assuming the plot is wrong.

### `visualize_topics_over_time()` or `visualize_topics_per_class()` look too busy

- Use `top_n_topics` or `topics=` to narrow the selection.
- Use `normalize_frequency=True` when you want shape comparisons rather than raw counts.
- Keep the number of unique timestamps/classes small; bins or group labels before plotting when the axis is too wide.

### `visualize_hierarchy()` annotations do not match the hierarchy DataFrame

This usually means the hierarchy was generated with one distance/linkage choice and plotted with another.

Fix: reuse the same `distance_function` and `linkage_function` for both `hierarchical_topics()` and `visualize_hierarchy()`.

### `custom_labels` string lookup fails

If you pass `custom_labels="AspectName"`, that aspect must exist in `topic_model.topic_aspects_`.

Fix: use `custom_labels=True` for the default custom labels, or inspect the available aspect names first.
