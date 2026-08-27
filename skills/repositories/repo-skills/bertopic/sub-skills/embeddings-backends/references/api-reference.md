# API reference

## Core embedding contract

- `BaseEmbedder.embed(documents: list[str], verbose: bool = False) -> np.ndarray`
- `BaseEmbedder.embed_words(words: list[str], verbose: bool = False) -> np.ndarray` defaults to `embed(words, verbose)`.
- `BaseEmbedder.embed_documents(documents: list[str], verbose: bool = False) -> np.ndarray` defaults to `embed(documents, verbose)`.
- A valid backend returns a 2D matrix with shape `(n_docs, embedding_dim)`.
- For precomputed embeddings passed into BERTopic, the first dimension must match `len(documents)`.
- Dense `np.ndarray` embeddings are the simplest path; sparse `csr_matrix` embeddings are also accepted by BERTopic when the input is sparse.
- When you want to stay on the precomputed path, construct `BERTopic(embedding_model=None, ...)` and pass `embeddings=...` explicitly.

## Backend selection

`select_backend(embedding_model, language=None, verbose=False)` applies a small set of heuristics:

- A `BaseEmbedder` instance is returned unchanged.
- A scikit-learn `Pipeline` is wrapped in `SklearnEmbedder`.
- Objects whose type string contains `flair`, `spacy`, `gensim`, `saved_model`, `pipeline`, `model2vec`, or `fastembed` are routed to the matching backend wrapper.
- A string is treated as a SentenceTransformer model id or path.
- `language="english"` maps to `sentence-transformers/all-MiniLM-L6-v2`.
- Other supported languages, or `language="multilingual"`, map to `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.
- If `sentence_transformers` is missing and a language was supplied, BERTopic may fall back to a lightweight `SklearnEmbedder` built from `TfidfVectorizer()` + `TruncatedSVD(100)`.

The supported language tokens are exported as `bertopic.backend.languages`.

## Backend matrix

| Backend | Constructor / import | Contract | Install / gotcha |
| --- | --- | --- | --- |
| `SentenceTransformerBackend` | Use `BERTopic(embedding_model="all-MiniLM-L6-v2")`, or import the backend module directly when you need the class. | Dense document embeddings from `SentenceTransformer.encode(...)`. Also supports a `model2vec=True` bridge when the source is a string. | `sentence-transformers`; string ids can download. |
| `HFTransformerBackend` | Wrap a `transformers.pipelines.Pipeline` feature-extraction pipeline. | Mean-pools token embeddings using the attention mask. | `transformers` and torch; the input must be a feature-extraction pipeline. |
| `SklearnEmbedder` | Wrap a scikit-learn `Pipeline`. | Calls `fit_transform` on the first batch and `transform` afterwards. | `scikit-learn`; a base `Pipeline` does not support `.partial_fit()`. |
| `FlairBackend` | Wrap `TokenEmbeddings` or `DocumentEmbeddings`. | Token embedders are pooled into document embeddings; document embedders are used directly. | `flair`; `fine_tune` is disabled when present to reduce OOM risk. |
| `SpacyBackend` | Pass a loaded spaCy `nlp` object. | Uses `.vector` when available and transformer tensors otherwise. | `spacy`; pass an `nlp` object, not a model name string. |
| `GensimBackend` | Pass `Word2VecKeyedVectors`, often from `gensim.downloader`. | Pools word vectors per document and returns zeros for all-OOV documents. | `gensim`; the model must be keyed vectors, not a generic Gensim object. |
| `USEBackend` | Pass a callable TensorFlow Hub model. | Embeds one document at a time and converts the result back to NumPy. | `tensorflow_hub`; the object must be callable on a list of texts. |
| `OpenAIBackend` | `OpenAIBackend(client, embedding_model=..., batch_size=..., delay_in_seconds=...)`. | Uses `client.embeddings.create(...)`; empty strings are normalized to a single space. | `openai`; placeholder when the extra is missing. |
| `CohereBackend` | `CohereBackend(client, embedding_model=..., embed_kwargs=...)`. | Uses `client.embed(texts=...)`; batching and per-batch delays are supported. | `cohere`; `embed_kwargs["model"]` can override the constructor model. |
| `FastEmbedBackend` | `FastEmbedBackend("BAAI/bge-small-en-v1.5")`. | Uses supported `TextEmbedding` model names only. | `fastembed`; unsupported names fail before any download. |
| `Model2VecBackend` | `Model2VecBackend(model, distill=False)` or `distill=True`. | Loads a `StaticModel` or distills once on the first `embed(...)` call. | `model2vec`; `distill=True` needs `model2vec[distill]` and a string source model. |
| `LangChainBackend` | `LangChainBackend(Embeddings())`. | Calls `.embed_documents(...)` and returns a dense matrix. | `langchain`; it expects a LangChain embeddings instance. |
| `MultiModalBackend` | `MultiModalBackend("clip-ViT-B-32", image_model=..., batch_size=...)`. | Can embed documents, images, or both; when both are present it averages the matrices. | `bertopic[vision]` plus image-capable sentence-transformers and image-loading support. |
| `WordDocEmbedder` | `WordDocEmbedder(doc_backend, word_backend)`. | Wraps separate document and word embedders. | Use it when document and topic-word embeddings need different backends. |

## Optional placeholders

- `bertopic.backend.__init__` exposes `NotInstalled` placeholders for missing optional extras: `OpenAIBackend`, `CohereBackend`, `MultiModalBackend`, `Model2VecBackend`, `FastEmbedBackend`, and `LangChainBackend`.
- Accessing or calling a placeholder raises `ModuleNotFoundError` with the relevant install hint.
- A placeholder means the backend is unavailable in the current environment; do not try to recover by loading a remote model id blindly.

## Multimodal contract

- `MultiModalBackend.embed(documents, images=None, verbose=False)` accepts text, images, or both.
- `embed_documents(...)` truncates text to 77 tokens when a tokenizer is available.
- `embed_images(...)` accepts image paths or image objects, batches them, and can use a separate `image_model`.
- When both modalities are provided, the backend averages the two embedding matrices.

## Precomputed embeddings

- Use `embedding_model=None` when you want BERTopic to stay on the precomputed path.
- `fit_transform`, `transform`, and `partial_fit` accept precomputed embeddings as long as the number of rows matches the input documents.
- Sparse `csr_matrix` embeddings are allowed; keep them aligned with the document list.
- A custom backend can still be useful for offline smoke checks even when the main model uses precomputed embeddings.
