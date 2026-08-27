# Troubleshooting

This page focuses on failures that matter for the topic-modeling lifecycle. It does not cover representation, visualization, or serialization internals beyond the few cases that affect model construction and merging.

## Install and import issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError` for `hdbscan`, `umap`, `scikit-learn`, `numpy`, `pandas`, or `scipy` | The core BERTopic stack is incomplete | Install the missing dependency or use a prepared environment with the core package set. |
| `ImportError` during `BERTopic.merge_models(...)` | Neither `torch` nor `safetensors` is available | Install one of them before merging models. |
| A zero-shot or fit-time workflow tries to load a model unexpectedly | No local embedding backend was supplied | Pass precomputed embeddings for smoke tests, or use a local embedding backend chosen elsewhere. |
| Image-only fitting fails | The selected embedding backend cannot embed images | Use an image-capable backend and keep backend selection out of this sub-skill. |

## Input and API misuse

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Make sure that the documents variable is an iterable containing strings only.` | Documents were passed as a dataframe, scalar, or mixed iterable | Pass a list of strings. |
| `Make sure to supply a list of strings, not a dataframe.` | A dataframe was passed directly into fit-time methods | Extract the document column first. |
| `Make sure that the embeddings are a numpy array...` | Embeddings are not a NumPy array or CSR matrix | Convert to `np.ndarray` or `scipy.sparse.csr_matrix`. |
| `shape (len(docs), vector_dim)` mismatch | Embeddings and documents have different row counts | Make the first dimension equal to the number of documents. |
| `No embedding model was found to embed the documents.` | `transform` or `find_topics` was called without a backend and without embeddings | Provide embeddings or a local embedder. |
| `This BERTopic instance is not fitted yet.` | Query or mutation was called before fitting | Fit first. |

## Online and mutation gotchas

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `In order to use .partial_fit, the cluster model should have a .partial_fit function.` | The clusterer is not streaming-capable | Use `MiniBatchKMeans` or another `partial_fit`-capable clusterer. |
| `partial_fit` works once but later topic history looks inconsistent | The caller expected cumulative history from `topics_` | Append each batch yourself; `topics_` only stores the current batch. |
| `partial_fit` after a normal `fit` gives confusing results | The two training modes have different update contracts | Start a fresh model for online training. |
| `No outliers to reduce.` | The fitted model has no `-1` topic | Only call `reduce_outliers` when outliers exist. |
| `The set nr_topics (...) must exceed ... zero-shot topics` | Zero-shot threshold matched too many predefined topics | Raise `nr_topics` or loosen `zeroshot_min_similarity`. |
| Topic ids shift after merges or deletes | Mutating methods update the internal topic mapper | Re-read `get_topic_info()` and `topic_mapper_` after every mutation. |

## Backend-specific gotchas

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `.transform()` fails with a custom clusterer | The clusterer has no `predict` path | Use a predictor-friendly clusterer such as KMeans or HDBSCAN with prediction support. |
| `.transform()` with HDBSCAN-like models gives incomplete probabilities on unseen data | The backend does not support the same unseen-data probability path | Use standard HDBSCAN with prediction data, or accept the reduced inference contract. |
| cuML training works but unseen-data probabilities are unavailable | Known backend limitation in the docs | Use standard HDBSCAN if unseen-document probabilities are required. |
| Image-only inputs fail even though BERTopic itself imports fine | The chosen backend is not multimodal | Switch to an image-capable backend before retrying the same topic workflow. |

## Practical smoke advice

- Prefer synthetic documents plus precomputed embeddings when checking this sub-skill.
- Use a deterministic PCA + KMeans pipeline for the first pass.
- Clone the fitted model before trying several mutations.
- Treat `reduce_outliers` as a topic-list transform, not a model update.
- Treat `partial_fit` as a streaming contract, not a drop-in replacement for `fit`.

## Boundary note

If you are trying to refresh topic descriptions after `reduce_outliers`, that is an `update_topics` / vectorizer-reshaping task and belongs in the vectorizer or representation sub-skill, not here.
