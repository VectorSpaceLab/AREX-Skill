# Embedding Provider Reference

The embedding API lives under the `unstructured.embed` import namespace. It is provider-specific and separate from broad ingest connectors. The package-level provider map exposes provider keys for encoder classes, but most workflows should import the explicit config and encoder classes.

## Common API Contract

| Concept | Behavior |
| --- | --- |
| Config base | `EmbeddingConfig`, a Pydantic base class extended by each provider. |
| Encoder base | `BaseEmbeddingEncoder`, a dataclass-style interface with `config`. |
| Document embedding | `embed_documents(elements)` embeds `[str(element) for element in elements]`, assigns each vector to `element.embeddings`, and returns elements. |
| Query embedding | `embed_query(query)` embeds one query string and returns one vector. |
| Dimension helpers | `num_of_dimensions` and `is_unit_vector` generally call a sample embedding request, so do not use them in no-network validation. |
| Metadata behavior | Provider tests assert embedding does not break `element.to_dict()["text"]`; callers should additionally check metadata fields important to their workflow. |

## Provider Table

| Provider | Import | Config fields and defaults | SDK/dependency route | Credential notes | Behavioral notes |
| --- | --- | --- | --- | --- | --- |
| OpenAI via LangChain | `OpenAIEmbeddingConfig`, `OpenAIEmbeddingEncoder` from `unstructured.embed.openai` | `api_key`, `model_name="text-embedding-ada-002"` | Requires `langchain_openai`; dependency guard names extra `openai`. | Pass from `OPENAI_API_KEY` or a secret manager; config expects an API key value. | Uses LangChain `OpenAIEmbeddings.embed_documents()` and `.embed_query()`. |
| OctoAI | `OctoAiEmbeddingConfig`, `OctoAIEmbeddingEncoder` from `unstructured.embed.octoai` | `api_key`, `model_name="thenlper/gte-large"`, `base_url="https://text.octoai.run/v1"` | Requires `openai` and `tiktoken`; dependency guard names extra `embed-octoai`. | Pass from provider env/secret storage; the OpenAI SDK is pointed at OctoAI `base_url`. | `embed_documents()` loops through elements and calls `embed_query()` per element, so large batches may be slow or rate-limit prone. |
| Mixedbread AI | `MixedbreadAIEmbeddingConfig`, `MixedbreadAIEmbeddingEncoder` from `unstructured.embed.mixedbreadai` | `api_key` defaults from `MXBAI_API_KEY`, `model_name="mixedbread-ai/mxbai-embed-large-v1"` | Requires `mixedbread_ai`; dependency guard names extra `embed-mixedbreadai`. | Prefer `MXBAI_API_KEY`; `initialize()` raises if no key is present. | Uses batches of 128, `normalized=True`, float encoding, end truncation, 60-second timeout, and 3 retries. Call `initialize()` before embedding if request options are needed. |
| VoyageAI | `VoyageAIEmbeddingConfig`, `VoyageAIEmbeddingEncoder` from `unstructured.embed.voyageai` | `api_key`, required `model_name`, optional `show_progress_bar`, `batch_size`, `truncation`, `output_dimension` | Requires `voyageai`; dependency guard names extra `embed-voyageai`; `show_progress_bar=True` also needs `tqdm`. | Pass from `VOYAGE_API_KEY` or secret storage; config itself requires a key value. | Tokenizes inputs for batching, caps batches at 1000 documents, supports context models via `contextualized_embed()`, and can pass `output_dimension`. |
| Vertex AI | `VertexAIEmbeddingConfig`, `VertexAIEmbeddingEncoder` from `unstructured.embed.vertexai` | `api_key`, `model_name="textembedding-gecko@001"` | Requires `langchain` and `langchain_google_vertexai`; dependency guard names extra `embed-vertexai`. | The config expects service-account JSON text and writes it to a temporary Google credentials file when creating the client. Treat it as highly sensitive. | `get_client()` sets `GOOGLE_APPLICATION_CREDENTIALS`; do not call it in dry-run checks. |
| Amazon Bedrock | `BedrockEmbeddingConfig`, `BedrockEmbeddingEncoder` from `unstructured.embed.bedrock` | `aws_access_key_id`, `aws_secret_access_key`, `region_name="us-west-2"` | Requires `boto3`, `numpy`, and `langchain_community`; dependency guard names extra `bedrock`. | Prefer standard AWS credential providers in application code when possible; this config requires explicit key fields. | `__post_init__()` calls `initialize()`, but `initialize()` is only abstractly declared in the base; verify behavior in your installed version before relying on automatic setup. |
| HuggingFace local/LangChain | `HuggingFaceEmbeddingConfig`, `HuggingFaceEmbeddingEncoder` from `unstructured.embed.huggingface` | `model_name="sentence-transformers/all-MiniLM-L6-v2"`, `model_kwargs={"device":"cpu"}`, `encode_kwargs={"normalize_embeddings": False}`, `cache_folder=None` | Requires `langchain_huggingface`; package optional `huggingface` group includes heavy ML dependencies such as `torch`, `transformers`, and `sentencepiece`. | Usually no API key for local sentence-transformer models, but model downloads may require network or authenticated model access. | Best for local/no-provider-key workflows, but can be slow, memory-heavy, and platform-sensitive. |

## Provider Selection Guidance

- Use OpenAI, VoyageAI, Mixedbread, OctoAI, Vertex AI, or Bedrock when the application already has approved provider credentials, network access, rate-limit handling, and vector-dimension expectations for that provider.
- Use HuggingFace when local execution is required and the environment can tolerate model downloads, `torch` installation, and CPU/GPU memory use.
- Use VoyageAI when model-specific token batching or `output_dimension` is required; use `count_tokens()` for planning but remember it calls the provider tokenizer.
- Avoid provider mixing in one index unless the vector store explicitly separates model/dimension spaces.
- The provider map keys are `langchain-openai`, `langchain-huggingface`, `langchain-aws-bedrock`, `langchain-vertexai`, `voyageai`, `mixedbread-ai`, and `octoai`.

## Minimal Import Patterns

```python
from unstructured.embed.voyageai import VoyageAIEmbeddingConfig, VoyageAIEmbeddingEncoder

encoder = VoyageAIEmbeddingEncoder(
    config=VoyageAIEmbeddingConfig(
        api_key=os.environ["VOYAGE_API_KEY"],
        model_name="voyage-3.5",
        output_dimension=1024,
    )
)
embedded = encoder.embed_documents(chunks)
query_vector = encoder.embed_query("find risk factors")
```

```python
from unstructured.embed.huggingface import HuggingFaceEmbeddingConfig, HuggingFaceEmbeddingEncoder

encoder = HuggingFaceEmbeddingEncoder(
    config=HuggingFaceEmbeddingConfig(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": False},
    )
)
embedded = encoder.embed_documents(chunks)
```

## Dimension and Vector Checks

- Check dimensions with a known vector result from `embed_query()` or a mocked client in tests; avoid calling `num_of_dimensions` during offline configuration checks because it may make a live provider call.
- For VoyageAI tests, observed model expectations include `voyage-3.5` returning 1024 dimensions and `voyage-3.5-lite` returning 512 dimensions in mocked coverage; verify current provider documentation before hard-coding.
- `is_unit_vector` computes a norm check on a sample embedding; this is useful after provider access is confirmed, not before.
- When a provider supports `output_dimension`, ensure both indexed documents and queries use the same value.

## Metadata Preservation Pattern

```python
before = [(element.id, element.category, element.metadata.to_dict()) for element in chunks]
embedded = encoder.embed_documents(chunks)
after = [(element.id, element.category, element.metadata.to_dict()) for element in embedded]
assert before == after
assert all(getattr(element, "embeddings", None) for element in embedded if str(element).strip())
```

Keep this assertion in application tests or synthetic usability cases when embedding table chunks, titled chunks, or elements that carry data-source metadata.
