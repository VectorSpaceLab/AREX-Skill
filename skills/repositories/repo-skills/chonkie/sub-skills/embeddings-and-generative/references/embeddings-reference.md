# Embeddings reference

This reference covers Chonkie 1.7.0 embedding classes and provider wrappers. Treat every local model load, model cache miss, and provider call as optional unless the user explicitly authorizes downloads or external API traffic.

## Selection guide

| Need | Prefer | Why | Common gates |
| --- | --- | --- | --- |
| Fast local semantic chunking with a small default model | `Model2VecEmbeddings` or `AutoEmbeddings.get_embeddings("minishlab/potion-base-32M")` | Chonkie's semantic defaults route to Model2Vec-style models. | `chonkie[semantic]` or `chonkie[model2vec]`, model cache or download access. |
| Sentence-transformers models or late chunking | `SentenceTransformerEmbeddings` | Supports sentence embeddings plus token-level embeddings used by `LateChunker`. | `chonkie[st]`, model cache/download, optional accelerator. |
| Existing custom embedding object | Implement/extend `BaseEmbeddings` | Keeps tokenization, `dimension`, `embed_batch`, and `similarity` explicit. | No package gate beyond Chonkie and NumPy if implemented locally. |
| Provider embeddings with a unified provider catalog | `CatsuEmbeddings` | Current provider wrappers for OpenAI, Gemini, Jina, Cohere, and Voyage delegate through Catsu in this release. | `chonkie[catsu]`, provider credentials, network, provider limits. |
| OpenAI-compatible multi-provider access | `LiteLLMEmbeddings` | One interface for OpenAI, Voyage, Cohere, Bedrock, and other LiteLLM providers. | `chonkie[litellm]`, provider credentials, `dimension` for unknown models to avoid a dimension-detection call. |
| Azure-hosted OpenAI embeddings | `AzureOpenAIEmbeddings` | Uses Azure endpoint/deployment conventions and Azure auth fallback. | `chonkie[azure-openai]`, Azure endpoint, API key or Azure identity configuration. |
| Generative text/JSON splitting | A `BaseGenie` implementation plus `SlumberChunker` | Lets Chonkie ask an LLM for split indices. | Provider-specific genie extra, API key, network, JSON-mode dependency. |

If the user asks for deterministic or offline chunking and has not approved a model download, route to `../chunking-and-types/` and choose `RecursiveChunker`, `SentenceChunker`, or `TokenChunker` instead of silently invoking embeddings.

## `BaseEmbeddings` contract

Every embedding class used by Chonkie chunkers/refineries must support:

| Member | Contract |
| --- | --- |
| `embed(text: str) -> np.ndarray` | Embed one text string. |
| `embed_batch(texts: list[str]) -> list[np.ndarray]` | Embed many strings; default loops over `embed`, providers usually batch. Empty input should return an empty list where implemented. |
| `aembed` / `aembed_batch` | Async helpers. The base class runs sync methods in a thread unless a subclass overrides them. |
| `similarity(u, v)` | Defaults to cosine similarity; some models override it. |
| `dimension` | Integer vector width; provider classes may need a known model or explicit dimension. |
| `get_tokenizer()` | Tokenizer/token counter used by model-dependent chunkers. |
| `__call__(text_or_texts)` | Dispatches to `embed` for a string and `embed_batch` for a list. |

For custom local embeddings, subclass `BaseEmbeddings`, return NumPy arrays, and ensure `get_tokenizer()` provides `count_tokens` or equivalent behavior expected by Chonkie tokenizers/chunkers.

## `AutoEmbeddings` routing

Use `AutoEmbeddings.get_embeddings(model, **kwargs)` when the model string is user-facing and you want Chonkie to pick a registered implementation.

Supported routing patterns include:

| Identifier pattern | Typical implementation |
| --- | --- |
| `minishlab/...`, `potion-...` | `Model2VecEmbeddings` |
| `sentence-transformers/...`, `all-MiniLM...`, `paraphrase...`, `multi-qa...`, `msmarco...` | `SentenceTransformerEmbeddings` |
| `openai://text-embedding-3-small` or `text-embedding-*` | `OpenAIEmbeddings` wrapper through Catsu |
| `azure_openai://text-embedding-3-small` | `AzureOpenAIEmbeddings` |
| `gemini://gemini-embedding-001` | `GeminiEmbeddings` wrapper through Catsu |
| `cohere://embed-english-light-v3.0` | `CohereEmbeddings` wrapper through Catsu |
| `jina://jina-embeddings-v4` | `JinaEmbeddings` wrapper through Catsu |
| `voyageai://voyage-3` or `voyage-...` | `CatsuEmbeddings` / Voyage wrapper |
| `catsu://model-name` | `CatsuEmbeddings` with provider inferred unless supplied |
| `litellm://text-embedding-3-small` | `LiteLLMEmbeddings` |

Important behavior: if registry matching or instantiation fails, `AutoEmbeddings` tries a SentenceTransformer fallback with the supplied model string. That fallback can require the `st` extra and may download a model. For no-network operation, pass an already-created `BaseEmbeddings` object instead of relying on fallback behavior.

## Local embedding classes

### `Model2VecEmbeddings`

Constructor signature: `Model2VecEmbeddings(model="minishlab/potion-base-32M")`.

- Accepts a model name/path string or an existing `model2vec.StaticModel` instance.
- Loads with `StaticModel.from_pretrained` for strings and exposes `model.dim` as `dimension`.
- Uses `model.encode(..., convert_to_numpy=True)` for single and batch embeddings.
- `get_tokenizer()` returns the model tokenizer.
- Install gate: `chonkie[model2vec]`; `chonkie[semantic]` also includes the Model2Vec dependency family used by semantic chunking.
- Cache/download gate: string model identifiers may require model download. If downloads are not allowed, use a model already present in the user's cache or a local model object/path validated by the user.

### `SentenceTransformerEmbeddings`

Constructor signature: `SentenceTransformerEmbeddings(model="all-MiniLM-L6-v2", **kwargs)`.

- Accepts a model name/path string or an existing `sentence_transformers.SentenceTransformer` instance.
- Passes extra keyword arguments to the SentenceTransformer constructor; use this for device and cache/offline options supported by SentenceTransformer.
- Provides `embed_as_tokens`, `embed_as_tokens_batch`, `count_tokens`, and `count_tokens_batch`. `LateChunker` depends on token-level embeddings.
- `max_seq_length` uses the model's max length when available and falls back to 512.
- Install gate: `chonkie[st]`.
- Cache/download gate: model strings may access the model hub unless the user uses a local path/cache and compatible offline settings.

## Provider embeddings

### Catsu-backed wrappers

`OpenAIEmbeddings`, `GeminiEmbeddings`, `JinaEmbeddings`, `CohereEmbeddings`, and `VoyageAIEmbeddings` are backward-compatible wrappers that delegate to `CatsuEmbeddings` in this release. If these wrappers fail with a missing `catsu` import, install the Catsu extra or the aggregate embeddings extra rather than assuming the older provider-specific extra is sufficient.

Common Catsu constructor:

```python
from chonkie.embeddings import CatsuEmbeddings

emb = CatsuEmbeddings(
    model="voyage-3",
    provider="voyageai",          # optional if Catsu can infer it
    api_keys={"voyageai": "..."}, # optional; Catsu can read provider env vars
    max_retries=3,
    timeout=30,
    batch_size=128,
    dimensions=None,
)
```

Catsu notes:

- `model` is required; `provider` is optional.
- `api_keys` is a mapping keyed by provider name such as `openai`, `gemini`, `jinaai`, `cohere`, or `voyageai`.
- `dimensions` must be a positive integer when supplied.
- Do not pass `input` in extra kwargs; it is reserved by the embedding call.
- `embed_batch` chunks inputs by `batch_size` and falls back to single calls if a multi-item batch fails.
- Async methods `aembed` and `aembed_batch` are available.

Wrapper defaults and environment variables:

| Class | Default model | Credential source | Batch/default caveat |
| --- | --- | --- | --- |
| `OpenAIEmbeddings` | `text-embedding-3-small` | `api_key` or `OPENAI_API_KEY` | `tokenizer`, `dimension`, `max_tokens`, `base_url`, and `organization` are accepted for backward compatibility but ignored by the wrapper. |
| `GeminiEmbeddings` | `gemini-embedding-001` | `api_key` or `GEMINI_API_KEY` | Optional `dimensions`; `task_type` and `show_warnings` are backward-compatible and ignored. |
| `JinaEmbeddings` | `jina-embeddings-v4` | `api_key` or `JINA_API_KEY` | `task` is backward-compatible and ignored unless default; wrapper provider name is `jinaai`. |
| `CohereEmbeddings` | `embed-english-light-v3.0` | `api_key` or `COHERE_API_KEY` | Batch size is capped at 96. Uses input type `document`. |
| `VoyageAIEmbeddings` | `voyage-3` | `api_key`, `VOYAGE_API_KEY`, or `VOYAGEAI_API_KEY` | Batch size is capped at 128; `output_dimension` and `truncation` are backward-compatible and ignored. |

### `AzureOpenAIEmbeddings`

Constructor signature: `AzureOpenAIEmbeddings(model="text-embedding-3-small", azure_endpoint=None, tokenizer=None, dimension=None, azure_api_key=None, api_version="2024-10-21", deployment=None, max_retries=3, timeout=60.0, batch_size=128, **kwargs)`.

- `azure_endpoint` is required unless `AZURE_OPENAI_ENDPOINT` is set.
- `azure_api_key` defaults to `AZURE_OPENAI_API_KEY`; without a key, the class uses Azure identity credentials.
- `deployment` defaults to `model` and is the value sent to Azure embedding calls.
- Known dimensions: `text-embedding-3-small` 1536, `text-embedding-3-large` 3072, `text-embedding-ada-002` 1536. Unknown models require explicit `dimension` and `tokenizer`.
- Batch failures fall back to single calls for the failed batch.

### `LiteLLMEmbeddings`

Constructor signature: `LiteLLMEmbeddings(model="text-embedding-3-small", api_key=None, api_base=None, timeout=60.0, max_retries=3, batch_size=128, dimension=None, **kwargs)`.

- Use LiteLLM model names such as `text-embedding-3-small`, `voyage/voyage-3-large`, `cohere/embed-english-v3.0`, or provider-specific names supported by LiteLLM.
- Known dimensions are cached for common OpenAI, Voyage, and Cohere models.
- If `dimension` is omitted for an unknown model, the class auto-detects dimension by embedding a test string. That can make a live provider call during initialization. Provide `dimension=` when no unexpected network call is acceptable.
- Tokenization uses `tiktoken` for OpenAI, tries a Voyage tokenizer for Voyage models, and otherwise falls back to `cl100k_base`.

## Provider Genies

`Genie` classes implement `BaseGenie.generate(prompt) -> str` and, when supported, `generate_json(prompt, schema) -> dict`. They are used directly by `SlumberChunker`; they are not the same as embedding providers.

| Class | Default model | Required inputs | Install gate | JSON support |
| --- | --- | --- | --- | --- |
| `OpenAIGenie` | `gpt-4.1` | `api_key` or `OPENAI_API_KEY`; optional `base_url` | `chonkie[openai]` | Uses OpenAI structured parse with Pydantic schema. |
| `AzureOpenAIGenie` | logical `gpt-4o` | `azure_endpoint`; optional `deployment`, `azure_api_key`, `api_version` | `chonkie[azure-openai]` | Uses Azure OpenAI structured parse with Pydantic schema. |
| `GeminiGenie` | `gemini-3-pro-preview` | `api_key` or `GEMINI_API_KEY` | `chonkie[gemini]` or aggregate `chonkie[genie]` dependency family | Requests JSON mime/schema and parses JSON text. |
| `GroqGenie` | `llama-3.3-70b-versatile` | `api_key` or `GROQ_API_KEY` | `chonkie[groq]` | Uses Groq JSON schema response format. |
| `CerebrasGenie` | `llama-3.3-70b` | `api_key` or `CEREBRAS_API_KEY` | `chonkie[cerebras]` | Adds schema to prompt and requests JSON object mode. |

OpenAI Genie retries rate limits, API errors, and timeouts with exponential backoff up to five attempts. Other genie classes rely on provider/client behavior unless the caller adds external retry logic.

## Installation extras map

Install only the extras the task actually needs. Examples:

```bash
pip install "chonkie[semantic]"      # Model2Vec family for SemanticChunker defaults
pip install "chonkie[model2vec]"     # Model2VecEmbeddings directly
pip install "chonkie[st]"            # SentenceTransformerEmbeddings and LateChunker
pip install "chonkie[neural]"        # NeuralChunker transformers/torch path
pip install "chonkie[catsu]"         # Unified provider embedding adapter
pip install "chonkie[litellm]"       # LiteLLM provider embeddings
pip install "chonkie[azure-openai]"  # Azure OpenAI embeddings/genie dependencies
pip install "chonkie[openai]"        # OpenAI Genie dependencies and legacy OpenAI package family
pip install "chonkie[gemini]"        # Gemini embeddings/genie package family
pip install "chonkie[groq]"          # Groq Genie
pip install "chonkie[cerebras]"      # Cerebras Genie
pip install "chonkie[embeddings]"    # Aggregate embedding extras, including Catsu
pip install "chonkie[genies]"        # Aggregate genie extras
```

The Chonkie skill was produced with live provider/model verification intentionally out of scope. Before claiming a provider works, verify the specific extra, credential, endpoint, model name, quota, timeout, and a small request in the user's current environment.
