---
name: serialization
description: "Save, load, and share BERTopic models locally or on the Hugging
  Face Hub with safe format and dependency choices."
disable-model-invocation: true
metadata:
  disco-role: operating
  package: BERTopic
  package-version: "0.17.4"
  parent-skill: bertopic
license: MIT
---

# serialization

Use this sub-skill when the task is about persisting an already fitted BERTopic model, reloading it locally, or publishing/loading it through the Hugging Face Hub.

## Route here for

- `BERTopic.save(...)` and `BERTopic.load(...)` workflows.
- Choosing among `serialization="safetensors"`, `serialization="pytorch"`, and `serialization="pickle"`.
- Deciding whether to include `save_ctfidf=True` for topic-term inspection after reload.
- Deciding how to use `save_embedding_model`: a lightweight model pointer, omitting the backend, or reinjecting a backend at load time.
- Local save/load from a pickle file or from a lightweight model directory.
- Hub upload with `BERTopic.push_to_hf_hub(...)` and Hub loading with `BERTopic.load("namespace/repo")`.
- Serialization-side failures from `BERTopic.merge_models(...)`, such as missing `torch` or `safetensors`; route the model-combination decision itself to topic-modeling.

## Route elsewhere

- Training, fitting, transforming, partial fitting, topic reduction, topic merging, or outlier workflows: use the topic-modeling sub-skill.
- Embedding backend selection, custom backend implementation, API-client setup, or precomputed embedding construction: use the embeddings-backends sub-skill.
- c-TF-IDF or vectorizer tuning before saving: use the vectorizers-ctfidf sub-skill.
- Representation models, custom labels, or multi-aspect labels: use the representations-labeling sub-skill.
- Plotting, visualization, hierarchy dashboards, or figure export: use the analysis-visualization sub-skill.

## Operating references

1. Start with [`references/api-reference.md`](references/api-reference.md) for save/load/push signatures, format behavior, local file layout, and load-path resolution.
2. Use [`references/workflows.md`](references/workflows.md) for local exact round trips, portable lightweight saves, embedding-model restoration, Hub upload/load, and local-vs-Hub decisions.
3. Use [`references/troubleshooting.md`](references/troubleshooting.md) for import failures, optional dependency errors, invalid paths, credential issues, embedding-backend gaps, and version/security warnings.
4. Run [`scripts/smoke_serialization.py`](scripts/smoke_serialization.py) for a tiny local-only smoke check of pickle plus a lightweight format when the BERTopic runtime dependencies are available.

## Minimal decision flow

- If the file will only be loaded in the same trusted Python and dependency environment, `pickle` is the most complete format because it stores the full BERTopic object, including dimensionality-reduction and clustering sub-models.
- If the model should be small, safer to share, production-oriented, or Hub-friendly, prefer `safetensors` with `save_ctfidf=True` when topic-term inspection after reload matters.
- If `safetensors` is unavailable but `torch` is already an accepted dependency, use `pytorch`; it creates the same lightweight directory style with `.bin` weights.
- If future `transform(...)` calls should work without passing `embeddings=`, save a SentenceTransformer-compatible model id with `save_embedding_model="sentence-transformers/..."` or pass a freshly constructed backend to `BERTopic.load(..., embedding_model=...)`.
- If the backend is custom or uses external API credentials, do not expect lightweight serialization to store it; reconstruct that backend separately and inject it at load time.
- If uploading to the Hub, use `push_to_hf_hub(...)` only after confirming `huggingface_hub` is installed and the process is authenticated or has a token.
- If loading locally, pass an existing file or directory. If a missing path contains `/`, BERTopic treats it as a Hub repo id.

## Verification anchors

- Local no-network save/reload: fit or reuse a tiny synthetic model with precomputed embeddings, save as pickle and at least one lightweight format, reload from local file/directory, and assert topic counts plus representative topic metadata survive.
- Local-vs-Hub guidance: confirm local round trips do not require Hugging Face credentials, while `push_to_hf_hub(...)` and `BERTopic.load("namespace/repo")` require Hub-oriented dependencies and network/auth conditions.
- Embedding restoration edge case: load a lightweight model once without an embedding backend and once with an explicit backend or precomputed embeddings, then document the difference in future `transform(...)` behavior.
