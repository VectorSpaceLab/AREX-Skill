# Serialization troubleshooting

Use this page for failures that occur while saving, loading, or sharing an existing BERTopic model. If the failure happens while fitting, selecting an embedding backend, tuning topic words, labeling, or plotting, route to the owning sub-skill.

## 1) BERTopic import fails before any serialization call

Typical signals:

- `ModuleNotFoundError: No module named 'joblib'`
- `ModuleNotFoundError: No module named 'sklearn'`
- import errors for NumPy, pandas, SciPy, PyYAML, or tqdm

Action:

1. Fix the base BERTopic runtime first; serialization cannot proceed until `from bertopic import BERTopic` succeeds.
2. Install/repair the base package dependencies in the environment that will run the save/load code.
3. Then rerun a tiny local smoke before attempting Hub upload or a large model reload.

Do not debug Hub credentials or serialization flags until the base import works.

## 2) `safetensors` save/load fails

Typical signals:

- `ValueError: `pip install safetensors` to save as .safetensors`
- `ValueError: `pip install safetensors` to load .safetensors`
- missing `topic_embeddings.safetensors` in a supposedly safe directory

Action:

1. Install `safetensors` in the runtime that saves and loads the model.
2. If installing it is not allowed, switch to `serialization="pytorch"` when `torch` is available.
3. If neither lightweight tensor dependency is available and the artifact is trusted/local-only, use `pickle` as a last resort.
4. Verify the lightweight directory includes `config.json`, `topics.json`, and `topic_embeddings.safetensors` before handing it off.

## 3) `pytorch` / `.bin` save/load fails

Typical signals:

- assertion text similar to ``pip install pytorch` to save as bin`
- missing `topic_embeddings.bin`
- `torch.load(...)` errors while loading `.bin` files

Action:

1. Install the `torch` package or switch to `serialization="safetensors"`.
2. Treat `.bin` files as less preferred than `safetensors` for sharing.
3. Confirm `ctfidf.bin` exists only when `save_ctfidf=True` and the source model actually had `c_tf_idf_`.

## 4) `push_to_hf_hub(...)` cannot run

Typical signals:

- `ValueError: Make sure you have the huggingface hub installed via pip install --upgrade huggingface_hub`
- authentication or permission errors from Hugging Face Hub
- network, DNS, timeout, or repository-not-found errors

Action:

1. Install `huggingface_hub`.
2. Authenticate with `huggingface-cli login`, `huggingface_hub.login()`, or `token=...`.
3. Check the `repo_id` namespace and write permissions.
4. Use `private=True` when the repository should not be public.
5. Use `create_pr=True` only when uploads should open a pull request.
6. Confirm the local save path works before retrying Hub upload; Hub upload internally performs a temporary local save.

Local `save(...)` and local `load(...)` do not require Hugging Face credentials.

## 5) `BERTopic.load(...)` uses the wrong source

Typical signals:

- A local path such as `runs/model` unexpectedly triggers Hub download behavior.
- `ValueError: Make sure to either pass a valid directory or HF model.`
- Hub errors appear even though you intended to load locally.

Resolution behavior to remember:

1. Existing local file: pickle load.
2. Existing local directory: lightweight local load.
3. Non-existing string containing `/`: Hub repo id.
4. Non-existing string without `/`: invalid input error.

Action:

- Create or point to the local file/directory before calling `BERTopic.load(...)`.
- Use an absolute or correctly relative path that exists.
- For Hub, use a repo id shaped like `namespace/repo` and ensure `huggingface_hub` can access it.

## 6) Reloaded lightweight model cannot transform new documents

Typical signals:

- `ValueError: No embedding model was found to embed the documents. Make sure when loading in the model using BERTopic.load() to also specify the embedding model.`
- A warning that the model was loaded without explicitly defining an embedding model.
- SentenceTransformer download/import errors after loading a model that saved an embedding pointer.

Why it happens:

- `safetensors` and `pytorch` do not serialize the original embedding backend object.
- `save_embedding_model` stores only a string pointer when possible.
- Custom/API backends such as OpenAI, Cohere, or LangChain cannot be faithfully restored from the lightweight directory alone.

Action:

1. If you have precomputed embeddings for new documents, call `transform(new_docs, embeddings=new_embeddings)`.
2. If the backend is a SentenceTransformer model, save a stable model id with `save_embedding_model="sentence-transformers/..."` and ensure `sentence-transformers` is installed at load time.
3. If the backend is custom or credentialed, reconstruct it securely and pass it to `BERTopic.load(path, embedding_model=backend)`.
4. Route backend construction details to embeddings-backends.

## 7) c-TF-IDF/topic-word state is missing after lightweight load

Typical signals:

- `c_tf_idf_` is `None` after loading.
- `ctfidf.safetensors`, `ctfidf.bin`, or `ctfidf_config.json` is absent.
- BERTopic warns that the c-TF-IDF matrix could not be saved.

Action:

1. Save with `save_ctfidf=True` when topic-word inspection is required after reload.
2. Verify the source model has `c_tf_idf_` before saving.
3. If the source is a merged/lightweight-only model without c-TF-IDF, recreate or update topic-term state in the vectorizers-ctfidf workflow before relying on c-TF-IDF persistence.
4. Do not assume `save_ctfidf=True` can create missing c-TF-IDF data; it only persists existing state.

## 8) Pickle security or version mismatch

Typical signals:

- Loading a pickle from another environment raises import, attribute, or estimator state errors.
- Loaded models behave differently after dependency upgrades.
- Security review rejects a `.pkl`/pickle artifact.

Action:

1. Load pickle only from trusted sources.
2. Keep Python, BERTopic, NumPy, pandas, scikit-learn, UMAP, HDBSCAN, sentence-transformers, and other backend versions aligned with the save environment.
3. Prefer `safetensors` for shared or long-lived artifacts.
4. Record dependency versions next to every saved model.

## 9) Results differ after lightweight reload

Expected behavior:

- Lightweight formats do not store the original reducer and clusterer.
- After load, transform assigns topics by cosine similarity between new document embeddings and stored topic embeddings.
- This can be faster and smaller but may differ from the original full pipeline.

Action:

- Use pickle in a trusted same-environment setting if exact sub-model behavior must be preserved.
- Use lightweight formats when size, safety, Hub sharing, and production inference are more important.
- Always validate representative inputs after changing serialization format.

## 10) Image or visual-aspect artifacts are incomplete

If a model contains image-based topic aspects, BERTopic can save/load an `images/` folder only when image support is available.

Action:

- Install image support, typically through the relevant Pillow/vision dependencies, before expecting image aspects to round-trip.
- Treat plotting and visual interpretation as analysis-visualization; this note only concerns persisted image files.

## 11) Hub model card or README is not as expected

`push_to_hf_hub(..., model_card=True)` writes a README only when the target repo does not already have one.

Action:

- If an existing README should be replaced or edited, manage that explicitly in the Hub repo workflow.
- Check that topic labels and topic frequencies are acceptable before upload; the generated model card summarizes them.
- Use private repos for sensitive topic labels or training metadata.
