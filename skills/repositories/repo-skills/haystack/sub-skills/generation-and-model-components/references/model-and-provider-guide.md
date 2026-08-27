# Model and Provider Guide

Use this guide to choose a Haystack model-backed component, configure provider credentials, and avoid common local/API model pitfalls.

## Selection Matrix

| Need | Recommended component | Why |
| --- | --- | --- |
| New LLM chat or RAG answer generation | `OpenAIChatGenerator`, `AzureOpenAIChatGenerator`, `HuggingFaceAPIChatGenerator`, or `HuggingFaceLocalChatGenerator` | Preserves roles, metadata, tool calls, multimodal parts, streaming chunks, and structured responses as `ChatMessage`. |
| Existing string prompt slot | `OpenAIGenerator`, `AzureOpenAIGenerator`, `HuggingFaceAPIGenerator`, or `HuggingFaceLocalGenerator` | Accepts `prompt: str` and returns `list[str]`; simpler but less expressive. |
| Query embedding | `OpenAITextEmbedder`, `AzureOpenAITextEmbedder`, `HuggingFaceAPITextEmbedder`, or `SentenceTransformersTextEmbedder` | Takes one string and returns one vector. |
| Document indexing embeddings | `OpenAIDocumentEmbedder`, `AzureOpenAIDocumentEmbedder`, `HuggingFaceAPIDocumentEmbedder`, or `SentenceTransformersDocumentEmbedder` | Takes `list[Document]` and writes embeddings back to documents. |
| Local/private model inference | Hugging Face local generators or Sentence Transformers embedders | Avoids provider APIs but requires optional packages, model files, and suitable CPU/GPU/MPS/XPU memory. |
| Provider-hosted model inference | OpenAI, Azure OpenAI, Hugging Face API components | Avoids local model memory but requires credentials, endpoint/model/deployment names, network access, and provider-specific quotas. |
| Deterministic JSON output | Chat generator `generation_kwargs={"response_format": ...}` plus `JsonSchemaValidator` | Provider-side structured output reduces errors; validator creates explicit repair messages. |
| Resilient provider fallback | `FallbackChatGenerator` | Tries several chat generators and returns the first successful result. |

## Credentials and Secrets

Always use `haystack.utils.Secret` for credentials in serializable components:

```python
from haystack.utils import Secret

openai_key = Secret.from_env_var("OPENAI_API_KEY")
hf_token = Secret.from_env_var(["HF_API_TOKEN", "HF_TOKEN"], strict=False)
azure_key = Secret.from_env_var("AZURE_OPENAI_API_KEY", strict=False)
```

Guidelines:

- Use `Secret.from_env_var(...)` in examples and pipelines so serialized pipeline YAML does not contain tokens.
- Use `Secret.from_token(...)` only for short-lived, non-serialized scripts and never commit literal secrets.
- Azure OpenAI components require an endpoint plus either an API key, Azure AD token, or token provider. Validate `AZURE_OPENAI_ENDPOINT`, deployment name, and API version separately.
- Hugging Face local components may still need an HF token for private model downloads even when inference is local.
- If a component initializes its client in `__init__`, missing strict env vars can fail during construction rather than during `run()`.

## Provider Configuration Patterns

### OpenAI Chat

```python
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.utils import Secret

llm = OpenAIChatGenerator(
    api_key=Secret.from_env_var("OPENAI_API_KEY"),
    model="gpt-5-mini",
    generation_kwargs={"max_completion_tokens": 200, "temperature": 0},
    timeout=30,
    max_retries=3,
)
```

Use runtime overrides for per-call tuning:

```python
result = llm.run(messages=messages, generation_kwargs={"temperature": 0.2})
```

`generation_kwargs` is forwarded to the provider API. Keep model-specific parameters provider-compatible; unsupported keys usually surface as provider API errors.

### Azure OpenAI Chat

```python
from haystack.components.generators.chat import AzureOpenAIChatGenerator
from haystack.utils import Secret

llm = AzureOpenAIChatGenerator(
    azure_endpoint="https://example-resource.openai.azure.com/",
    azure_deployment="gpt-4.1-mini",
    api_version="2024-12-01-preview",
    api_key=Secret.from_env_var("AZURE_OPENAI_API_KEY", strict=False),
)
```

Common Azure mistakes are mixing model names with deployment names, omitting the endpoint, using an unsupported API version for a feature, or providing neither API key nor AD token.

### Hugging Face API Chat

Use API chat components for provider/serverless chat-completion style models. Use `api_params` for model, provider, URL, or timeout settings depending on the selected API mode. Prefer `HuggingFaceAPIChatGenerator` for current generative Hugging Face serverless/provider integrations; older text-generation endpoint support is provider dependent.

### Local Hugging Face Models

```python
from haystack.components.generators.chat import HuggingFaceLocalChatGenerator
from haystack.utils import ComponentDevice

llm = HuggingFaceLocalChatGenerator(
    model="Qwen/Qwen3-0.6B",
    device=ComponentDevice.from_str("cpu"),
    generation_kwargs={"max_new_tokens": 128, "temperature": 0.7},
)
llm.warm_up()
```

Local model guidance:

- Use `ComponentDevice.from_str("cpu")`, `ComponentDevice.from_str("cuda:0")`, `ComponentDevice.from_str("mps")`, or `ComponentDevice.from_multiple(...)` when explicit placement matters.
- `huggingface_pipeline_kwargs` can override `model`, `task`, `device`, and `token`. Check for duplicate/conflicting settings before debugging the wrong parameter.
- For stop behavior, use the component `stop_words` parameter or provider generation stop settings, but avoid conflicting `stopping_criteria` when the component forbids both.
- Call `warm_up()` before benchmarking latency or before starting a production pipeline worker; first load can download models and allocate memory.

## Prompting Guidance

Use `PromptBuilder` for plain text and `ChatPromptBuilder` for chat messages:

- Set `required_variables` for variables that must be present. By default, missing variables render as empty strings, which can hide upstream routing mistakes.
- Use `template_variables` for values that should override both pipeline kwargs and defaults at runtime.
- When embedding Jinja inside Python f-strings, escape braces: `{{{{ variable }}}}`.
- Treat user-editable Jinja templates as untrusted. Haystack uses a sandboxed Jinja environment by default, but unsafe template rendering in related components should be avoided unless the template source is trusted.
- `ChatPromptBuilder` string templates are useful for mixed content and chat-message blocks; list templates are simpler and safer for ordinary role-based prompts.

## Streaming

Most OpenAI, Azure, and Hugging Face generator components accept `streaming_callback` at initialization and at runtime. The runtime callback overrides the init callback.

```python
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.dataclasses import StreamingChunk

chunks = []

def collect(chunk: StreamingChunk) -> None:
    chunks.append(chunk.content)

llm = OpenAIChatGenerator(streaming_callback=collect)
result = llm.run(messages=messages)
```

Streaming cautions:

- Many components require a single generated response while streaming. For OpenAI text generation, streaming with `n > 1` raises `ValueError`.
- For structured outputs with OpenAI/Azure chat generators, streaming requires JSON schema response format rather than a Pydantic model.
- Some provider/tool combinations disallow streaming with tools or require a different generator class. If tools are involved, check the chat-generator-specific constraints and reroute tool orchestration to `../agents-tools-and-hitl/SKILL.md`.
- Async callbacks are only valid for async generator methods that explicitly support them.

## Structured Output and Validation

Best practice for JSON-producing LLM tasks:

1. Prompt for raw JSON only and specify the schema in natural language.
2. Use provider structured output when supported, for example OpenAI/Azure `generation_kwargs={"response_format": {"type": "json_object"}}` or strict JSON schema.
3. Pass replies into `JsonSchemaValidator` with the same schema.
4. If `validation_error` is returned, route that message back to the chat generator in a pipeline loop or correction step.
5. Stop after a bounded number of retries at the pipeline layer.

`JsonSchemaValidator` validates only the last `ChatMessage`. If your pipeline stores a conversation history, append the candidate assistant reply last before validation.

## Embedding Configuration

OpenAI/Azure embedders:

- Use text embedders for queries and document embedders for indexing.
- Use `dimensions` only with OpenAI embedding models that support dimensionality reduction.
- Use `prefix` and `suffix` for model-specific instructions such as query/document prompts.
- Async `run_async` exists on API-backed text/document embedders where implemented; match this with `AsyncPipeline` or your async code.

Sentence Transformers embedders:

- Use `normalize_embeddings=True` when the downstream vector store or retriever expects cosine-normalized vectors.
- Use `batch_size`, `precision`, `backend`, and `truncate_dim` deliberately; changes can alter retrieval quality.
- Set `local_files_only=True` for offline deployments where model files are preloaded.
- Keep `trust_remote_code=False` unless the model repository is trusted and custom code is required.

## Classifier and Sampler Configuration

For `TransformersZeroShotDocumentClassifier`:

```python
from haystack.components.classifiers import TransformersZeroShotDocumentClassifier

classifier = TransformersZeroShotDocumentClassifier(
    model="cross-encoder/nli-deberta-v3-xsmall",
    labels=["billing", "technical", "legal"],
    multi_label=False,
    classification_field="subject",
)
```

If `classification_field` is set, every input `Document.meta` must contain that field. Classification output is stored under the document metadata key `classification`.

For `TopPSampler`, provide scored documents. If scores are in metadata instead of `Document.score`, set `score_field`. Use `min_top_k` to guarantee a minimum number of documents when top-p is aggressive.

## Safe Smoke Checks

The bundled `../scripts/model_component_smoke_check.py` checks public imports, prompt rendering, answer extraction, JSON validation, and top-p sampling without network calls or provider credentials. Use it before adding a provider key to isolate local API/import mistakes from provider errors.
