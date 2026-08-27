# Workflows

This page collects the recommended topic-modeling flows for this sub-skill. Prefer the safe synthetic path first, then move to larger corpora only if needed.

## 1) Safe synthetic fit and query path

Use this path when you need a no-download smoke check or a quick model sanity test.

1. Build a tiny synthetic corpus with 2-4 obvious themes.
2. Supply precomputed embeddings so the fit does not fetch models.
3. Use a custom reducer and clusterer, such as PCA + KMeans, to keep the run deterministic.
4. Call `fit_transform`, then verify `get_topic_info`, `get_topic`, `transform`, and `find_topics`.
5. Clone the fitted model before mutation if you want to test multiple mutation types.

Success signals:

- topic counts sum to the number of documents
- `transform` returns one prediction per input document
- `find_topics` returns the requested number of ids and scores
- `get_topic(topic)` returns a non-empty word list

## 2) Custom reducer + custom cluster

Use this when the default UMAP/HDBSCAN pipeline is not the right fit.

| Reducer | Clusterer | When it helps |
| --- | --- | --- |
| `UMAP` | `HDBSCAN` | Default modular pipeline, good for irregular clusters. |
| `PCA` | `KMeans` | Fast, deterministic, and good for smoke tests or coarse topics. |
| `TruncatedSVD` | `KMeans` / classifier-style model | Useful for sparse or tabular-style inputs. |
| `BaseDimensionalityReduction` | `BaseCluster` | Manual / label-driven workflows that skip learning steps. |
| `IncrementalPCA` | `MiniBatchKMeans` | Online / streaming topic modeling. |

Workflow notes:

- The reducer only needs `fit` + `transform`; `partial_fit` is optional unless you are streaming.
- The clusterer should expose `labels_` after fit and `predict` if you want `.transform()` later.
- `AgglomerativeClustering` can fit a topic model, but it is not a good choice if you need unseen-document inference.

## 3) Guided, supervised, semi-supervised, manual, and zero-shot

### Guided

- Provide `seed_topic_list` at construction time.
- The model nudges both the embedding space and the topic-word weighting toward those seed topics.
- Use this when you know a few anchor topics should appear, but you still want the model to discover more.

### Semi-supervised / supervised

- Pass `y` into `fit` or `fit_transform`.
- Use `-1` for documents whose class is unknown.
- Use all labels for a fully supervised workflow.
- Pair with `BaseDimensionalityReduction` + `BaseCluster` if you want to skip the unsupervised clustering path entirely.

### Manual

- Treat the labels you pass as the source of truth.
- Keep manual assignment as the last step before any reduction or mutation.
- If you later merge or delete topics, do not expect the original label ids to remain stable.

### Zero-shot

- Provide `zeroshot_topic_list` and `zeroshot_min_similarity`.
- Documents above the threshold are assigned to predefined topics first.
- The remaining documents go through the normal clustering pipeline.
- If the threshold is too strict, lower it; if the model matches too many zero-shot topics, increase `nr_topics`.

## 4) Multimodal fit-time workflows

- `fit`, `fit_transform`, and `transform` accept `images`.
- For image-only runs, use `documents=None, images=...`.
- Only use this path when the chosen embedding backend knows how to embed images.
- This sub-skill does not own backend selection; it only owns the topic-model lifecycle that consumes the resulting embeddings.

## 5) Online / partial_fit streaming

Recommended stack:

- `IncrementalPCA` or another reducer with `partial_fit`
- `MiniBatchKMeans` or another clusterer with `partial_fit`
- `OnlineCountVectorizer` for streaming vocabulary updates

Workflow:

1. Split the corpus into short batches.
2. Call `partial_fit` once per batch.
3. After each call, inspect the current batch through `topics_`.
4. If you need a cumulative history, append `topics_` to your own list after every batch.
5. Watch `topic_sizes_` for cumulative counts and `topic_mapper_` for label tracking.

Success signals:

- `len(topics_)` equals the current batch size
- the running topic count grows as batches are processed
- `sum(topic_sizes_.values())` matches the total number of documents seen so far

Important contract:

- Do not mix `fit` and `partial_fit` on the same model.
- `partial_fit` is intended for incremental learning from the start.

## 6) Topic mutation and reduction

### `reduce_outliers`

- Call this only when the fitted model actually contains `-1` topics.
- Choose `probabilities`, `distributions`, `c-tf-idf`, or `embeddings` based on what you already have.
- The function returns a new topic list; it does not mutate the model by itself.

### `reduce_topics`

- Use this to shrink the topic inventory after fitting.
- It mutates the model in place and updates the topic mapping state.
- Prefer reducing after you have already controlled topic count through the clusterer.

### `merge_topics`

- Use for manual merges, or when the model has found multiple near-duplicate topics.
- `topic_mapper_` is updated automatically.
- Re-read `get_topic_info()` after the merge instead of assuming ids stayed the same.

### `delete_topics`

- Use when you want to discard noisy or unwanted topics.
- If the model had no outlier topic before, deleting a topic creates `-1` and updates the model state accordingly.
- Re-check `topic_mapper_` and `get_topic_info()` after deletion.

### `merge_models`

- Train multiple fitted models separately, then merge them into one.
- This is useful when new data arrives in shards but you do not want to switch to online learning.
- If the merge fails with an import error, install `torch` or `safetensors`.

## 7) Recommended smoke order

When validating this sub-skill, run the bundled helper in this order:

1. fit with precomputed synthetic embeddings and a PCA + KMeans pipeline
2. verify `transform`, `get_topic`, and `find_topics`
3. clone and test `reduce_topics`, `merge_topics`, and `delete_topics`
4. run a short `partial_fit` stream and confirm topic tracking

That order covers the core lifecycle without requiring any network downloads.
