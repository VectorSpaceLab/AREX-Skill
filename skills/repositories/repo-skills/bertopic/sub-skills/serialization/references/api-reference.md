# Serialization API reference

This reference covers BERTopic 0.17.4 persistence APIs: `BERTopic.save`, `BERTopic.load`, `BERTopic.push_to_hf_hub`, and the format-specific files that BERTopic writes. It assumes the model already exists; fitting and backend construction are owned by sibling sub-skills.

## `BERTopic.save(...)`

```python
topic_model.save(
    path,
    serialization="pickle",        # "pickle", "safetensors", or "pytorch"
    save_embedding_model=True,
    save_ctfidf=False,
)
```

| Argument | Contract | Operational notes |
| --- | --- | --- |
| `path` | File path for `serialization="pickle"`; directory path for `serialization="safetensors"` or `"pytorch"`. | Lightweight formats create the directory if needed. Pickle opens the exact file path for writing. |
| `serialization` | Selects the format. | `pickle` stores the full object. `safetensors` and `pytorch` store a lightweight model without the original embedding, dimensionality-reduction, or clustering sub-models. |
| `save_embedding_model` | Controls how the embedding backend is handled. | For pickle, `False` temporarily removes the backend before dumping. For lightweight formats, pass a string model id such as `"sentence-transformers/all-MiniLM-L6-v2"` when the backend can later be restored by SentenceTransformers. If the backend exposes `_hf_model` and this argument is truthy, BERTopic can store that id automatically. |
| `save_ctfidf` | Adds c-TF-IDF matrix and vectorizer/c-TF-IDF config for lightweight formats. | Only applies to `safetensors` and `pytorch`. If `c_tf_idf_` is missing, BERTopic warns and skips it. |

## Format matrix

| Format | Path shape | Stores | Main advantages | Main drawbacks / risks | Key dependencies |
| --- | --- | --- | --- | --- | --- |
| `pickle` | One local file | Full BERTopic object, including original reducer/clusterer and optionally embedding backend. | Most complete local round trip; native test `test_load_save_model` verifies basic constructor fields survive. | Untrusted pickle can execute arbitrary code; large files; requires the same Python, BERTopic, and dependency versions. Not intended for Hub sharing. | `joblib` plus base BERTopic dependencies. |
| `safetensors` | Directory | Topic embeddings, topic metadata, config, optional c-TF-IDF, optional image files. Does not store original reducer/clusterer/backend object. | Recommended portable format: small, fast, relatively safe, and Hub-friendly. | Needs an embedding pointer or explicit backend for future embedding-based operations; transform uses topic-embedding similarity after reload. | `safetensors`; SentenceTransformers only if restoring a saved string embedding pointer. |
| `pytorch` | Directory | Same lightweight contents as `safetensors`, but tensor weights are `.bin` files written with `torch.save`. | Useful when `torch` is already available or `safetensors` is not. Hub-friendly. | Larger/safety profile is less attractive than `safetensors`; requires torch. | `torch`. |

## Lightweight directory layout

For `serialization="safetensors"`, expect files like:

```text
model_dir/
  config.json
  topics.json
  topic_embeddings.safetensors
  ctfidf.safetensors          # only with save_ctfidf=True and fitted c_tf_idf_
  ctfidf_config.json          # only with save_ctfidf=True and fitted c_tf_idf_
  images/                     # only when visual topic aspects exist and image support is available
```

For `serialization="pytorch"`, the weight file names change to:

```text
topic_embeddings.bin
ctfidf.bin                    # only with save_ctfidf=True and fitted c_tf_idf_
```

Important file meanings:

- `config.json` contains constructor-style parameters and an `embedding_model` string only when a string pointer was saved.
- `topics.json` contains topic representations, topic ids, topic sizes, topic mapper state, labels, custom labels, outlier metadata, and non-image topic aspects.
- `topic_embeddings.*` contains dense topic embeddings used for similarity-based transform after lightweight load.
- `ctfidf.*` plus `ctfidf_config.json` allow c-TF-IDF-backed topic-term inspection after lightweight load.

## `BERTopic.load(...)`

```python
from bertopic import BERTopic

loaded = BERTopic.load(path, embedding_model=None)
```

| Input form | Resolution behavior | Notes |
| --- | --- | --- |
| Existing local file | Loaded as a pickle model. | Only load trusted pickle files from compatible environments. |
| Existing local directory | Loaded as a lightweight local model directory. | BERTopic reads `topics.json`, `config.json`, topic embeddings, optional c-TF-IDF files, and optional images. |
| Missing/non-local string containing `/` | Treated as a Hugging Face Hub repo id. | Example: `"MaartenGr/BERTopic_Wikipedia"`. Requires `huggingface_hub`, network access, and any needed auth for private repos. |
| Missing string without `/` | Raises `ValueError` asking for a valid directory or HF model. | `BERTopic.load("my_model")` works only if `my_model` exists as a local pickle file or directory. |

`embedding_model` at load time is the recovery hook for lightweight models:

- If a saved `config.json` contains a SentenceTransformer-compatible `embedding_model` string, BERTopic tries to instantiate it through SentenceTransformers.
- If that import or model resolution fails, BERTopic falls back to `BaseEmbedder` and warns that no backend was explicitly defined.
- Passing `embedding_model=...` to `BERTopic.load(...)` replaces the loaded backend with the provided object or string-selected backend.
- Even without a backend, `transform(..., embeddings=precomputed_embeddings)` can still work because lightweight models retain topic embeddings.

## `BERTopic.push_to_hf_hub(...)`

```python
topic_model.push_to_hf_hub(
    repo_id,
    commit_message="Add BERTopic model",
    token=None,
    revision=None,
    private=False,
    create_pr=False,
    model_card=True,
    serialization="safetensors",
    save_embedding_model=True,
    save_ctfidf=False,
)
```

Behavior:

1. Requires `huggingface_hub`.
2. Creates or reuses the target Hub repository.
3. Temporarily saves the model with the requested lightweight serialization.
4. Generates a README model card when `model_card=True` and the repo lacks one.
5. Uploads the temporary folder and returns the `huggingface_hub.upload_folder(...)` result.

Hub-specific notes:

- Use `serialization="safetensors"` unless there is a concrete reason to use `"pytorch"`.
- Hub upload needs credentials: prior `huggingface-cli login`, `huggingface_hub.login()`, or a `token=` argument.
- Set `private=True` for private repositories.
- Use `create_pr=True` when the upload should be opened as a pull request instead of committed directly.
- Loading a public repo id with `BERTopic.load("namespace/repo")` does not require local model files, but it does require network access and `huggingface_hub`.

## Internal save/load helpers worth knowing

The public methods delegate to `bertopic._save_utils`:

- `save_hf(...)` writes `topic_embeddings.safetensors` or `topic_embeddings.bin`.
- `save_ctfidf(...)` writes sparse c-TF-IDF matrix pieces as tensors.
- `save_ctfidf_config(...)` writes the CountVectorizer vocabulary and c-TF-IDF flags needed to rebuild topic-term inspection state.
- `save_config(...)` writes non-model constructor parameters and a string embedding pointer when provided.
- `save_topics(...)` writes topic metadata and non-image aspects.
- `load_local_files(...)` and `load_files_from_hf(...)` collect the same file set before BERTopic reconstructs a lightweight model.

Do not call these helpers for ordinary workflows; use them to understand file expectations when diagnosing incomplete or corrupted model directories.
