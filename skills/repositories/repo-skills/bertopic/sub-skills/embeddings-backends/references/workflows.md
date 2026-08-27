# Workflows

## 1. Let BERTopic choose a default backend

Use this when the caller only gives a language and does not need a specific embedding model.

1. Omit `embedding_model`.
2. Set `language="english"` for the default MiniLM backend, or use another supported language / `"multilingual"`.
3. Confirm that the chosen backend matches the environment before relying on it for offline work.
4. If `sentence-transformers` is missing and a language was supplied, BERTopic may fall back to `SklearnEmbedder`.

Success check: the model resolves a backend without surprising downloads or type errors.

## 2. Use an explicit local embedding backend

Use this when the caller already has a loaded model object.

1. Load the native model in its own library first.
2. Pass the object to BERTopic or wrap it with the matching backend class.
3. Prefer explicit objects over string ids when reproducibility matters.
4. Keep the backend object around if you will later call `transform(...)` on new documents.

Common choices:

- `SentenceTransformer` objects or string ids for sentence-transformers.
- `transformers.pipelines.pipeline("feature-extraction", ...)` for HF transformers.
- `DocumentEmbeddings` / `TokenEmbeddings` for Flair.
- a loaded spaCy `nlp` object.
- `Word2VecKeyedVectors` from Gensim.
- a callable TensorFlow Hub module for USE.
- a LangChain `Embeddings` instance.
- `model2vec.StaticModel` or a model name for Model2Vec.
- a supported FastEmbed model name.

## 3. Stay offline with precomputed embeddings

Use this when the embedding matrix is already available or the task must not download anything.

1. Construct `BERTopic(embedding_model=None, ...)`.
2. Prepare a 2D embedding matrix whose row count exactly matches the document list.
3. Pass the matrix into `fit_transform(..., embeddings=...)` or `transform(..., embeddings=...)`.
4. Keep the matrix dense unless the upstream source is sparse; sparse `csr_matrix` inputs are also supported.
5. If you also need image support, keep the document and image row ordering identical.

Success check: the fit path uses the matrix directly and does not try to instantiate a remote embedding model.

## 4. Build a custom backend

Use this when none of the built-in wrappers matches the local model.

1. Subclass `BaseEmbedder`.
2. Implement `embed(...)`; optionally implement `embed_documents(...)`, `embed_words(...)`, and `embed_images(...)`.
3. Return a stable 2D matrix with a fixed second dimension.
4. Make the encoder deterministic for tests and offline smoke checks.
5. If document and word spaces must differ, combine two backends with `WordDocEmbedder`.

Recommended practice: use a tiny local function or encoder for smoke tests rather than a stochastic model.

## 5. Wire up multimodal text + image embeddings

Use this when the same topic model should consume captions, alt text, or image paths.

1. Choose a CLIP-like `SentenceTransformer` model or `MultiModalBackend`.
2. Pass aligned `documents` and `images` lists.
3. Prefer image paths when the source is large; the backend opens them only when needed.
4. Use `image_model=` when text and image encoders should be different.
5. For images-only runs, pass `documents=None` and provide `images`.

Success check: the resulting embeddings have one row per text/image pair, and paired inputs are averaged when both are present.

## 6. Check optional backends safely

Use this when you need a quick inventory without triggering model downloads.

1. Run `scripts/inventory_backends.py`.
2. Inspect the package availability section for missing extras.
3. Inspect the backend export section for `NotInstalled` placeholders.
4. Use the local smoke output to confirm the deterministic backend contract.
5. Only use the precomputed BERTopic smoke when the base import stack is healthy.

## Installation notes

- `sentence-transformers` is the default backend family.
- `model2vec[distill]` is required only for Model2Vec distillation.
- `fastembed`, `openai`, `cohere`, `langchain`, `flair`, `spacy`, `gensim`, and `tensorflow_hub` are all optional and should be installed only when that backend is needed.
- `bertopic[vision]` is required for multimodal image support.
- A missing base dependency is a package issue, not a backend issue; repair the environment before debugging wrappers.
