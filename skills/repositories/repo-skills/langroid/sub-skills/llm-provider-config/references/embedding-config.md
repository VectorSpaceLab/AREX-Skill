# Embedding configuration

This reference covers Langroid embedding provider configs only. It does not cover vector-store collection creation, indexing, document parsing, chunking, or retrieval-agent wiring; route those tasks to the retrieval/document-chat sub-skill.

## Core pattern

Embedding providers are configured with classes from `langroid.embedding_models.models` and materialized by `EmbeddingModel.create(config)` only when embeddings are actually needed:

```python
from langroid.embedding_models.base import EmbeddingModel
from langroid.embedding_models.models import OpenAIEmbeddingsConfig

embed_cfg = OpenAIEmbeddingsConfig(
    model_name="text-embedding-3-small",
    dims=1536,
)
# This creates the client/model object; do it only when ready to embed.
embed_model = EmbeddingModel.create(embed_cfg)
embedding_fn = embed_model.embedding_fn()
```

For no-network config validation, construct config objects only. Instantiating an embedding model can require API keys, optional dependencies, model downloads, or a running local server.

## Config classes at a glance

| Config class | Default/typical model | Key fields | Runtime requirements |
|---|---|---|---|
| `OpenAIEmbeddingsConfig` | `text-embedding-3-small` | `api_key`, `api_base`, `organization`, `dims=1536`, `context_length=8192`, `langdb_params` | OpenAI API-compatible embedding endpoint and key. |
| `AzureOpenAIEmbeddingsConfig` | `text-embedding-3-small` or deployment model | `api_base`, `api_key`, `deployment_name`, `api_version`, `dims=1536` | Azure OpenAI embedding deployment and key or Azure auth fields. |
| `GeminiEmbeddingsConfig` | `models/text-embedding-004` | `api_key` from environment, `dims=768`, `batch_size=512` | `google-genai` optional dependency and Gemini key. |
| `SentenceTransformerEmbeddingsConfig` | `BAAI/bge-large-en-v1.5` | `device`, `data_parallel`, `devices`, `context_length` | `sentence-transformers`/HF optional dependencies and local model cache/download. |
| `FastEmbedEmbeddingsConfig` | `BAAI/bge-small-en-v1.5` | `cache_dir`, `threads`, `parallel`, `batch_size=256`, `additional_kwargs` | `fastembed` optional dependency and model cache/download. |
| `LlamaCppServerEmbeddingsConfig` | server-selected GGUF embedding model | `api_base`, `dims`, `context_length=2048`, `batch_size=2048` | Running llama.cpp server with embeddings endpoints. |
| `RemoteEmbeddingsConfig` | sentence-transformer served over local/insecure gRPC | `api_base`, `port`, polling fields | gRPC server/client pieces and sentence-transformer backend. |

## OpenAI embeddings

```python
from langroid.embedding_models.models import OpenAIEmbeddingsConfig

embed_cfg = OpenAIEmbeddingsConfig(
    model_type="openai",
    model_name="text-embedding-3-small",
    dims=1536,
)
```

`OpenAIEmbeddingsConfig` uses `OPENAI_` environment variables. If `api_key` is not set in the config, Langroid reads `OPENAI_API_KEY` when the embedding model is instantiated. Set `api_base` for an OpenAI-compatible embedding server.

The implementation truncates inputs to `context_length` using the model tokenizer. For OpenAI embedding models, it can send token lists rather than strings. Keep `dims` consistent with the actual model because vector stores depend on it.

## LangDB embeddings through OpenAI config

LangDB embeddings use `OpenAIEmbeddingsConfig` with a `langdb/` model prefix:

```python
from langroid.embedding_models.models import OpenAIEmbeddingsConfig

embed_cfg = OpenAIEmbeddingsConfig(
    model_name="langdb/openai/text-embedding-3-small",
    dims=1536,
)
```

`LangDBParams` can be passed through the config or populated via `LANGDB_` environment variables. When instantiated, the model strips the `langdb/` prefix, uses LangDB base/project settings, and requires `LANGDB_API_KEY` rather than `OPENAI_API_KEY`.

## Azure OpenAI embeddings

```python
from langroid.embedding_models.models import AzureOpenAIEmbeddingsConfig

embed_cfg = AzureOpenAIEmbeddingsConfig(
    model_type="azure-openai",
    model_name="text-embedding-3-small",
    deployment_name="my-embedding-deployment",
    api_version="2024-06-01",
    dims=1536,
)
```

`AzureOpenAIEmbeddingsConfig` uses the `AZURE_OPENAI_` prefix. On instantiation it requires `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_API_BASE` unless credentials are supplied in the config. `deployment_name` is the Azure deployment name; keep it distinct from `model_name` when Azure names differ.

## Gemini embeddings

```python
from langroid.embedding_models.models import GeminiEmbeddingsConfig

embed_cfg = GeminiEmbeddingsConfig(
    model_type="gemini",
    model_name="models/text-embedding-004",
    dims=768,
)
```

Gemini embeddings require `GEMINI_API_KEY` and the `google-genai` optional dependency when the embedding model is instantiated. Keep `dims=768` for `models/text-embedding-004` unless using a different embedding model with different dimensionality.

## SentenceTransformer / Hugging Face embeddings

```python
from langroid.embedding_models.models import SentenceTransformerEmbeddingsConfig

embed_cfg = SentenceTransformerEmbeddingsConfig(
    model_name="BAAI/bge-large-en-v1.5",
    device="cuda",        # or "cpu"; omit to let the backend choose
    data_parallel=False,
)
```

This backend imports sentence-transformer and tokenizer packages only at instantiation. It may download model weights if they are not already cached. Use:

- `device` for single-device placement;
- `data_parallel=True` plus `devices=[...]` for multi-process encoding;
- `batch_size` inherited from the base embedding config.

The implementation updates `context_length` from the tokenizer once instantiated. For deterministic/offline runs, pre-populate the model cache and pin `model_name`.

## FastEmbed embeddings

```python
from langroid.embedding_models.models import FastEmbedEmbeddingsConfig

embed_cfg = FastEmbedEmbeddingsConfig(
    model_name="BAAI/bge-small-en-v1.5",
    batch_size=256,
    cache_dir=".cache/fastembed",
    threads=4,
    parallel=1,
)
```

This backend requires the `fastembed` optional dependency when instantiated. `cache_dir` controls model cache location; `threads` and `parallel` tune local CPU execution. The embedding dimensionality is discovered by embedding a sample text, so the first materialization can perform model loading and computation.

## llama.cpp server embeddings

```python
from langroid.embedding_models.models import LlamaCppServerEmbeddingsConfig

embed_cfg = LlamaCppServerEmbeddingsConfig(
    api_base="http://localhost:8080",
    dims=768,
    context_length=2048,
    batch_size=2048,
)
```

The llama.cpp server must be running with embedding support. Langroid uses these endpoints relative to `api_base`:

- `/tokenize`
- `/detokenize`
- `/embeddings`

It accepts several response shapes, including native embedding output, OpenAI-style `data[0].embedding`, arrays of embedding objects, and one-level nested embedding lists. Set `dims` to match the GGUF embedding model, not the LLM context length.

Common local failures are connection errors, missing embedding flag on the server, unsupported response format, and a dimension mismatch between `dims` and the actual vectors.

## Remote embeddings

`RemoteEmbeddingsConfig` extends sentence-transformer config and communicates over insecure gRPC. Use only in controlled environments. In local mode it can try to start an embedding server process if the configured port is not reachable; this is not a no-network/no-side-effect smoke path.

## Batch size, context length, and dimensions

- `batch_size` controls how many input texts or token batches each backend sends to the provider/model.
- `context_length` controls truncation before embedding.
- `dims` must match the vector length returned by the provider. Wrong dimensions are often first noticed when a vector store rejects inserts or queries.
- Provider configs do not build vector stores. Pass these configs to vector-store settings only after selecting the correct retrieval pipeline.
