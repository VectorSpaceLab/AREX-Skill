# API reference

This page captures the core BERTopic lifecycle contract for this sub-skill. It intentionally excludes embedding backend choice, representation tuning, visualization, and serialization.

## Constructor knobs that matter here

| Parameter | What it controls | Notes |
| --- | --- | --- |
| `language` | Default language preset for the embedding backend | Only matters when you are not passing an embedding backend yourself. |
| `top_n_words` | Number of top terms kept per topic | Large values can make topics less coherent. |
| `n_gram_range` | CountVectorizer n-gram range | Usually keep between 1 and 3. |
| `min_topic_size` | Minimum topic size / HDBSCAN cluster size proxy | The main knob for topic count in the default pipeline. |
| `nr_topics` | Reduce to a fixed topic count or `"auto"` | Merges topics after fitting. |
| `low_memory` | Lower-memory UMAP mode | Only affects reducer objects that use it. |
| `calculate_probabilities` | Request probability outputs when supported | Slower and more memory intensive. |
| `seed_topic_list` | Guided topic seeds | Nudges topics toward seed phrases. |
| `zeroshot_topic_list` | Predefined zero-shot topics | Requires a live embedding backend. |
| `zeroshot_min_similarity` | Zero-shot assignment threshold | Raise to assign fewer docs to zero-shot topics. |
| `umap_model` | Dimensionality reduction backend | Accepts PCA, UMAP, TruncatedSVD, or custom reducers with `fit`/`transform`. |
| `hdbscan_model` | Clustering backend | Accepts HDBSCAN, KMeans, MiniBatchKMeans, classifiers, or custom clusterers. |
| `embedding_model` | Embedding backend | Needed for automatic embeddings, `find_topics`, and some zero-shot flows. |
| `vectorizer_model` | BoW / vocabulary backend | Accepted here, but vectorizer tuning is routed elsewhere. |
| `ctfidf_model` | Topic-term weighting backend | Accepted here, but detailed tuning is routed elsewhere. |
| `representation_model` | Post-hoc topic representation backend | Not owned by this sub-skill. |

## Core methods

| Method | Signature focus | Return | Notes |
| --- | --- | --- | --- |
| `fit` | `fit(documents, embeddings=None, images=None, y=None)` | `self` | Fits in place. |
| `fit_transform` | Same inputs as `fit` | `(topics, probabilities)` | Full fit plus per-document output. |
| `transform` | `transform(documents, embeddings=None, images=None)` | `(topics, probabilities)` | Requires a fitted model. |
| `partial_fit` | `partial_fit(documents, embeddings=None, y=None)` | `self` | Streaming/online update path. |
| `get_topics` | `get_topics(full=False)` | mapping | Returns all topic representations. |
| `get_topic` | `get_topic(topic, full=False)` | list or `False` | Single-topic lookup. |
| `get_topic_info` | `get_topic_info(topic=None)` | DataFrame | Topic ids, counts, names, representations, and optional extras. |
| `get_topic_freq` | `get_topic_freq(topic=None)` | DataFrame or int | Frequency lookup. |
| `get_document_info` | `get_document_info(docs, df=None, metadata=None)` | DataFrame | Document-level topic information. |
| `get_representative_docs` | `get_representative_docs(topic=None)` | list or mapping | Representative-document lookup. |
| `find_topics` | `find_topics(search_term=None, image=None, top_n=5)` | `(topic_ids, similarities)` | Requires a live embedding backend. |
| `reduce_topics` | `reduce_topics(docs, nr_topics=20, images=None, use_ctfidf=False)` | `self` | In-place topic reduction. |
| `merge_topics` | `merge_topics(docs, topics_to_merge, images=None)` | `None` | In-place merge. |
| `delete_topics` | `delete_topics(topics_to_delete)` | `None` | In-place delete; may create `-1` if needed. |
| `reduce_outliers` | `reduce_outliers(documents, topics, ...)` | new topic list | Returns reassigned topics only. |
| `merge_models` | `merge_models(models, min_similarity=0.7, embedding_model=None)` | new model | Merges fitted models into one. |
| `get_params` | `get_params(deep=False)` | mapping | Estimator parameter snapshot. |

## Model state to watch

| Attribute | Meaning | Notes |
| --- | --- | --- |
| `topics_` | Current topic assignment per document | After `partial_fit`, this is the current batch only. |
| `probabilities_` | Per-document probabilities or similarities | Depends on clustering backend. |
| `topic_sizes_` | Topic counts | Useful for smoke checks and mutation validation. |
| `topic_mapper_` | Topic history and remapping tracker | Essential after merge/delete/reduce/online updates. |
| `topic_representations_` | Top words per topic | Recomputed after fitting and many mutations. |
| `c_tf_idf_` | Topic-term matrix | Updated by fitting and mutation workflows. |
| `topic_embeddings_` | Topic centroids / topic vectors | Used by query and merge logic. |
| `representative_docs_` | Representative docs by topic | Useful for inspection and smoke checks. |
| `representative_images_` | Representative images by topic | Present in multimodal flows. |
| `topic_labels_` | Default labels | Derived from topic representations. |
| `custom_labels_` | Optional user labels | Set with post-hoc label helpers, which are outside this sub-skill. |

## Custom component contracts

### Dimensionality reduction

A reducer only needs to support:

- `fit(X[, y])`
- `transform(X)`

`partial_fit` is optional but needed for online learning. Examples that fit this contract: `UMAP`, `PCA`, `TruncatedSVD`, `IncrementalPCA`, and `BaseDimensionalityReduction`.

### Clustering

A clusterer should support:

- `fit(X[, y])`
- `labels_` after fitting
- `predict(X)` when you want `.transform()` on unseen data

`partial_fit` is required for online learning. Examples that fit this contract: `HDBSCAN`, `KMeans`, `MiniBatchKMeans`, `BaseCluster`, and custom classifier-style clusterers.

### Online vocabulary

`OnlineCountVectorizer` adds:

- `partial_fit(raw_documents)`
- `update_bow(raw_documents)`

BERTopic uses that path only in `partial_fit` mode.

### Multimodal inputs

`fit`, `fit_transform`, and `transform` accept `images`. Image-only workflows use `documents=None, images=...`, but the chosen embedding backend must know how to embed images.

## Common failure contracts

| Condition | Raised behavior |
| --- | --- |
| Documents are not an iterable of strings | TypeError from input validation. |
| Embeddings row count does not match documents | ValueError from shape validation. |
| `partial_fit` clusterer lacks `partial_fit` | ValueError. |
| `transform` or `find_topics` has no embedding backend | ValueError / Exception. |
| `reduce_outliers` is called when there are no `-1` topics | ValueError. |
| `reduce_outliers(strategy="probabilities")` has no probabilities | ValueError. |
| `zeroshot_topic_list` is active but `nr_topics` is too small | ValueError. |
| `merge_models` cannot find `torch` or `safetensors` | ImportError. |

## Mutation semantics

- `merge_topics` and `delete_topics` mutate the fitted model in place.
- `reduce_topics` mutates in place and returns the model.
- `reduce_outliers` does not mutate the model; it returns reassigned topic ids.
- After any mutation, re-read `get_topic_info()` and `topic_mapper_` instead of assuming topic ids stayed stable.
- `partial_fit` mutates in place, but only the latest batch is stored in `topics_`; if you need a cumulative stream view, append each batch yourself.
