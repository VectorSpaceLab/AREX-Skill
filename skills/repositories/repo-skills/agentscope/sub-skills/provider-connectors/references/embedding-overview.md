# Embedding Overview

## Purpose

Read this for the verified embedding-model constructors and the dimension rules that matter for RAG or memory workflows.

## Verified embedding model families

| Class | Credential | Verified defaults / notes |
| --- | --- | --- |
| `DashScopeEmbeddingModel` | `CredentialBase` | `context_size=8192`, `max_retries=3`, `retry_delay=1.0`; supports `dimensions` and `embedding_cache` |
| `OpenAIEmbeddingModel` | `CredentialBase` | `context_size=8191`, `pass_dimensions=True`, `max_retries=3`, `retry_delay=1.0` |
| `GeminiEmbeddingModel` | `CredentialBase` | `context_size=8192`, `max_retries=3`, `retry_delay=1.0` |
| `OllamaEmbeddingModel` | `CredentialBase` | `context_size=8192`, `max_retries=3`, `retry_delay=1.0` |

## Verified constructor shape

All four families share the same basic shape:

`ModelClass(credential, model, dimensions, parameters=None, embedding_cache=None, context_size=..., max_retries=3, retry_delay=...)`

## Dimension facts

- `KnowledgeBase` and the vector store expect the embedding dimension to match the store collection.
- `DashScopeEmbeddingModel.list_models()` is a useful discovery helper.
- The unit tests verify these DashScope embedding cards in particular:
  - `text-embedding-v4`
  - `qwen3-vl-embedding`
  - `multimodal-embedding-v1`
- The DashScope tests also confirm that `multimodal-embedding-v1` uses a fixed dimension of `1024`, while `qwen3-vl-embedding` exposes supported dimension choices.

## Practical notes

- A CPU import succeeding does not prove the embedding model will match a RAG or memory backend.
- When a RAG or memory workflow fails, check both the provider model and the vector-store dimension before changing the code.
- If the issue is only the embedding provider class, the right place to debug it is still `provider-connectors`, not the RAG sub-skill.
