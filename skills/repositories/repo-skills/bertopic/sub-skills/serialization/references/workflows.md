# Serialization workflows

Use these workflows after a BERTopic model has already been fitted or otherwise created. They focus on persistence, reload, and sharing decisions rather than training or backend selection.

## 1) Exact local round trip with pickle

Use this when the saved file is trusted and will be loaded in the same Python/BERTopic/dependency environment.

```python
from bertopic import BERTopic

# topic_model is already fitted.
topic_model.save("model.pkl", serialization="pickle")
loaded_model = BERTopic.load("model.pkl")
```

Choose pickle when:

- you need the original dimensionality-reduction and clustering objects preserved;
- you need a local checkpoint for the same project environment;
- the file will not be shared with untrusted users.

Avoid pickle when:

- the model will be downloaded from an untrusted source;
- the target environment may have different BERTopic, Python, NumPy, scikit-learn, UMAP, HDBSCAN, or embedding-backend versions;
- the model should be small or Hub-friendly.

If the embedding backend is large or non-serializable but the rest of the pickle round trip is useful:

```python
topic_model.save("model_without_backend.pkl", serialization="pickle", save_embedding_model=False)
loaded_model = BERTopic.load("model_without_backend.pkl", embedding_model=my_embedding_backend)
```

Create `my_embedding_backend` using the embeddings-backends sub-skill; this workflow only owns the injection point.

## 2) Portable local directory with `safetensors`

Use this for small local artifacts, production-style reloads, or artifacts that may later be pushed to the Hub.

```python
embedding_model_id = "sentence-transformers/all-MiniLM-L6-v2"

topic_model.save(
    "my_model_dir",
    serialization="safetensors",
    save_ctfidf=True,
    save_embedding_model=embedding_model_id,
)

loaded_model = BERTopic.load("my_model_dir")
```

Expected effects:

- The directory contains topic metadata, config, topic embeddings, and c-TF-IDF files when `save_ctfidf=True`.
- The original reducer and clusterer are not saved; after reload, BERTopic uses topic-embedding similarity for `transform(...)`.
- The embedding backend object is not saved. The string pointer lets BERTopic try to recreate a SentenceTransformer model on load.
- If no backend can be restored, pass `embeddings=` to `transform(...)` or load with an explicit `embedding_model=`.

Use this format by default unless a concrete local-only pickle requirement exists.

## 3) Portable local directory with `pytorch`

Use this only when `torch` is already part of the accepted runtime or `safetensors` is unavailable.

```python
topic_model.save(
    "my_model_dir_bin",
    serialization="pytorch",
    save_ctfidf=True,
    save_embedding_model="sentence-transformers/all-MiniLM-L6-v2",
)
loaded_model = BERTopic.load("my_model_dir_bin")
```

The behavior mirrors `safetensors`, but tensor weights are written as `topic_embeddings.bin` and, when requested, `ctfidf.bin`.

## 4) Restore a backend at load time

Use this when the lightweight model did not save a usable SentenceTransformer pointer or the backend requires custom credentials/configuration.

```python
# Build or load the backend elsewhere.
embedding_backend = my_existing_backend

loaded_model = BERTopic.load(
    "my_model_dir",
    embedding_model=embedding_backend,
)
```

For external API backends, reconstruct the client securely before load-time injection. For example, define an OpenAI/Cohere/LangChain backend through the embeddings-backends sub-skill, then pass it here. Do not store API keys in model directories.

When you already have new-document embeddings, you can avoid backend restoration entirely:

```python
loaded_model = BERTopic.load("my_model_dir")
topics, probabilities = loaded_model.transform(new_docs, embeddings=new_embeddings)
```

This works because lightweight models retain topic embeddings.

## 5) Decide whether to save c-TF-IDF

Set `save_ctfidf=True` when future users need topic-word inspection or c-TF-IDF-backed analysis after a lightweight reload.

```python
topic_model.save("model_with_terms", serialization="safetensors", save_ctfidf=True)
loaded_model = BERTopic.load("model_with_terms")
loaded_model.get_topic_info()
loaded_model.get_topic(0)
```

Do not rely on `save_ctfidf=True` when the fitted model does not have `c_tf_idf_`; BERTopic will warn and skip c-TF-IDF persistence. This can happen for lightweight merged models or unusual construction paths.

## 6) Publish to the Hugging Face Hub

Use this when the model should be shared or consumed by a Hub repo id.

Authentication options:

```bash
huggingface-cli login
# or
huggingface-cli login --token "$HUGGINGFACE_TOKEN"
```

Notebook/script login:

```python
from huggingface_hub import login
login()
```

Push:

```python
topic_model.push_to_hf_hub(
    repo_id="namespace/my-bertopic-model",
    serialization="safetensors",
    save_ctfidf=True,
    save_embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    private=False,
)
```

Load from Hub:

```python
from bertopic import BERTopic

loaded_model = BERTopic.load("namespace/my-bertopic-model")
```

Hub guidance:

- `push_to_hf_hub(...)` creates/reuses the repo, saves a temporary lightweight model, optionally generates a README, and uploads the folder.
- Uploading needs credentials, network access, and `huggingface_hub`.
- Loading a public repo id needs network access and `huggingface_hub`; private repos also need valid authentication.
- Prefer `safetensors` for Hub publishing.
- Keep `save_embedding_model` as a public model id when possible so downstream users can reload without extra backend instructions.

## 7) Local path versus Hub repo id checklist

| Goal | Call | Requires credentials? | Requires network? |
| --- | --- | --- | --- |
| Save local pickle | `topic_model.save("model.pkl", serialization="pickle")` | No | No |
| Load local pickle | `BERTopic.load("model.pkl")` | No | No |
| Save local lightweight dir | `topic_model.save("model_dir", serialization="safetensors")` | No | No |
| Load local lightweight dir | `BERTopic.load("model_dir")` | No | No |
| Push to Hub | `topic_model.push_to_hf_hub("namespace/repo")` | Yes, unless already authenticated | Yes |
| Load public Hub repo | `BERTopic.load("namespace/repo")` | Usually no | Yes |
| Load private Hub repo | `BERTopic.load("namespace/repo")` | Yes | Yes |

Before treating a string as a local path, confirm the file or directory exists. A missing string with `/` is routed to Hugging Face Hub loading.

## 8) Tiny smoke-check workflow

Run the bundled local-only smoke script from this sub-skill directory:

```bash
python scripts/smoke_serialization.py
```

The script:

- fits a tiny deterministic model using synthetic documents and precomputed embeddings;
- saves/reloads a pickle file;
- saves/reloads a lightweight local directory with `safetensors` when available, otherwise `pytorch` when available;
- asserts topic counts and lightweight file layout;
- does not call the Hugging Face Hub and does not require credentials.

Use `--light-format pytorch`, `--light-format safetensors`, or `--light-format none` to force a specific local branch.

## 9) Reproducibility record to keep beside saved models

For any persisted BERTopic artifact, record:

- BERTopic version;
- Python version;
- NumPy, pandas, scikit-learn, UMAP, HDBSCAN, torch, safetensors, sentence-transformers, and transformers versions when relevant;
- serialization format and save options;
- whether an embedding-model pointer was saved, omitted, or injected at load time;
- whether `save_ctfidf=True` was used;
- whether the artifact is local-only, Hub-published, private, or public.

This is mandatory for pickle and still useful for lightweight formats because transform semantics and embedding backends can drift across environments.
