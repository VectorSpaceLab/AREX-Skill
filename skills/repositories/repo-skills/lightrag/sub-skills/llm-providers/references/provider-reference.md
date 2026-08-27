# Provider Reference

LightRAG has two provider configuration surfaces:

- Embedded Python usage: pass async callables to `LightRAG(llm_model_func=..., embedding_func=...)` and optional `role_llm_configs`.
- API/server usage: select binding names, models, hosts, keys, provider options, role overrides, VLM processing, and rerank bindings through the server configuration layer.

Provider demo patterns often require live API keys, local services, cloud credentials, optional packages, or sample files, so bundled runtime checks in this skill stay limited to import and symbol inspection.

## Server Binding Names

| Surface | Supported binding names | Notes |
| --- | --- | --- |
| LLM | `lollms`, `ollama`, `openai`, `openai-ollama`, `azure_openai`, `bedrock`, `gemini` | `openai-ollama` normalizes to OpenAI LLM plus Ollama embeddings. |
| Embedding | `lollms`, `ollama`, `openai`, `azure_openai`, `bedrock`, `jina`, `gemini`, `voyageai` | `jina` and `gemini` force dimension sending when the wrapped function accepts `embedding_dim`; other bindings respect `EMBEDDING_SEND_DIM`. |
| Rerank | `null`, `cohere`, `jina`, `aliyun` | `null` means no rerank function is configured. |
| VLM role | `openai`, `azure_openai`, `gemini`, `bedrock`, `ollama` | `lollms` is rejected for VLM image inputs in server configuration. |

Core inspected API facts:

- `EmbeddingFunc(embedding_dim, func, max_token_size=None, send_dimensions=False, model_name=None, supports_asymmetric=False)` wraps async embedding functions, injects supported metadata, strips unsupported `context`, and validates vector count/dimension.
- `wrap_embedding_func_with_attrs(**kwargs)` returns an `EmbeddingFunc` and auto-detects `supports_asymmetric=True` when the decorated function accepts a `context` parameter unless explicitly overridden.
- `RoleLLMConfig(func=None, kwargs=None, max_async=None, timeout=None, metadata=None)` configures per-role LLM overrides.
- Role ids are `extract`, `keyword`, `query`, and `vlm`.

## Provider Modules

| Module | Completion functions | Embedding functions | Typical prerequisites |
| --- | --- | --- | --- |
| `lightrag.llm.openai` | `openai_complete_if_cache`, `openai_complete`, `gpt_4o_complete`, `gpt_4o_mini_complete`, `nvidia_openai_complete`, Azure helpers | `openai_embed`, `azure_openai_embed` | OpenAI-compatible endpoint and key, or a compatible local/proxy service. Azure requires endpoint, deployment, version, and key. |
| `lightrag.llm.azure_openai` | Re-exports Azure completion helpers | Re-exports `azure_openai_embed` | Azure OpenAI endpoint/deployment configuration. |
| `lightrag.llm.ollama` | `_ollama_model_if_cache`, `ollama_model_complete` | `ollama_embed` | Running Ollama-compatible service or Ollama Cloud model; optional bearer key. |
| `lightrag.llm.gemini` | `gemini_complete_if_cache`, `gemini_model_complete` | `gemini_embed` | Google GenAI API key or Vertex AI process-level configuration. |
| `lightrag.llm.bedrock` | `bedrock_complete_if_cache`, `bedrock_complete` | `bedrock_embed` | AWS Bedrock Runtime with SigV4 credentials or process-level Bedrock bearer token. |
| `lightrag.llm.jina` | None | `jina_embed` | Jina API key and embedding API endpoint. |
| `lightrag.llm.voyageai` | None | `voyageai_embed` | Voyage API key and `voyageai` package. |
| `lightrag.llm.lollms` | `lollms_model_if_cache`, `lollms_model_complete` | `lollms_embed` | Running LoLLMS/Ollama-compatible service. |
| `lightrag.llm.anthropic` | `anthropic_complete_if_cache`, `anthropic_complete`, Claude helpers | `anthropic_embed` deprecation shim | Anthropic package/key for embedded use; not a server binding. |
| `lightrag.llm.hf` | `hf_model_complete` | `hf_embed` | Local Hugging Face model/tokenizer runtime. |
| `lightrag.llm.llama_index_impl` | `llama_index_complete` | `llama_index_embed` | LlamaIndex objects and optional provider packages. |
| `lightrag.llm.lmdeploy` | `lmdeploy_model_if_cache` | None | LMDeploy runtime/service. |
| `lightrag.llm.nvidia_openai` | None | `nvidia_openai_embed` | NVIDIA/OpenAI-compatible endpoint and key. |
| `lightrag.llm.zhipu` | `zhipu_complete_if_cache`, `zhipu_complete` | `zhipu_embedding` | Zhipu package/key. |

Some provider modules rely on optional dependencies or dynamic dependency helpers. In reproducible or offline environments, preinstall the relevant provider extras instead of relying on runtime installation.

## Embedded Python Pattern

Use installed package imports and async callables. This pattern shows structure only; it contacts a service if executed with real provider functions:

```python
from functools import partial
from lightrag import LightRAG
from lightrag.llm.ollama import ollama_model_complete, ollama_embed
from lightrag.utils import EmbeddingFunc

rag = LightRAG(
    llm_model_func=ollama_model_complete,
    llm_model_name="qwen2.5-coder:7b",
    llm_model_kwargs={"host": "http://localhost:11434", "options": {"num_ctx": 8192}},
    embedding_func=EmbeddingFunc(
        embedding_dim=1024,
        max_token_size=8192,
        model_name="bge-m3:latest",
        func=partial(ollama_embed.func, embed_model="bge-m3:latest", host="http://localhost:11434"),
    ),
)
```

Use `provider_embed.func` when the imported embedding function is already decorated with `@wrap_embedding_func_with_attrs` and a new `EmbeddingFunc` must change dimension, model, host, or prefix behavior.

## API/Server Base Settings

Use placeholder values in examples and keep real secrets outside reusable docs:

```env
LLM_BINDING=openai
LLM_MODEL=<chat-model>
LLM_BINDING_HOST=<openai-compatible-base-url>
LLM_BINDING_API_KEY=<secret>
LLM_TIMEOUT=240
MAX_ASYNC_LLM=4

EMBEDDING_BINDING=openai
EMBEDDING_MODEL=<embedding-model>
EMBEDDING_DIM=1536
EMBEDDING_BINDING_HOST=<openai-compatible-base-url>
EMBEDDING_BINDING_API_KEY=<secret>
EMBEDDING_FUNC_MAX_ASYNC=8
EMBEDDING_BATCH_NUM=10
EMBEDDING_TIMEOUT=30
```

Keep `EMBEDDING_DIM`, `EMBEDDING_MODEL`, `EMBEDDING_SEND_DIM`, and `model_name` aligned with the actual embedding model and vector storage data.

## Provider Option Prefixes

Binding option dataclasses create provider-specific CLI and env names. Common prefixes are:

| Provider | Base option env prefix | Role option env prefix example | Examples |
| --- | --- | --- | --- |
| OpenAI/Azure OpenAI | `OPENAI_LLM_*` | `QUERY_OPENAI_LLM_*` | `OPENAI_LLM_TEMPERATURE`, `QUERY_OPENAI_LLM_REASONING_EFFORT`, `OPENAI_LLM_EXTRA_BODY`. |
| Ollama/LoLLMS | `OLLAMA_LLM_*`, `OLLAMA_EMBEDDING_*` | `EXTRACT_OLLAMA_LLM_*` | `OLLAMA_LLM_NUM_CTX`, `OLLAMA_LLM_NUM_PREDICT`, `OLLAMA_EMBEDDING_NUM_CTX`. |
| Gemini | `GEMINI_LLM_*`, `GEMINI_EMBEDDING_*` | `VLM_GEMINI_LLM_*` | `GEMINI_LLM_THINKING_CONFIG`, `GEMINI_LLM_MAX_OUTPUT_TOKENS`, `GEMINI_EMBEDDING_TASK_TYPE`. |
| Bedrock | `BEDROCK_LLM_*` | `EXTRACT_BEDROCK_LLM_*` | `BEDROCK_LLM_TEMPERATURE`, `BEDROCK_LLM_MAX_TOKENS`, `BEDROCK_LLM_EXTRA_FIELDS`. |

Role-level provider options inherit base provider options only when the role uses the same provider as the base binding. Cross-provider roles start with empty provider options and apply only role-specific options.

## Credential and Service Patterns

| Provider | Credential/service fields |
| --- | --- |
| OpenAI-compatible | Use `LLM_BINDING_API_KEY`/`EMBEDDING_BINDING_API_KEY` or provider SDK envs. Set `*_BINDING_HOST` for proxies such as vLLM, SGLang, OpenRouter, or DeepSeek-compatible services. |
| Azure OpenAI | Use Azure endpoint and deployment names. Azure API version comes from process/global configuration or embedding-specific version fields. |
| Ollama | Use `LLM_BINDING_HOST`/`EMBEDDING_BINDING_HOST` for the service URL. `OLLAMA_API_KEY` or binding API key becomes a bearer header when present. Cloud-suffixed models may default to the Ollama Cloud host if no host is set. |
| Gemini | AI Studio mode uses `LLM_BINDING_API_KEY` or `GEMINI_API_KEY`. Vertex AI mode is controlled by process-level Google env vars. `DEFAULT_GEMINI_ENDPOINT` lets the SDK choose the endpoint. |
| Bedrock | Generic LightRAG API-key fields are ignored. Use global or role-specific AWS SigV4 fields, or process-level `AWS_BEARER_TOKEN_BEDROCK`. `DEFAULT_BEDROCK_ENDPOINT` lets the AWS SDK choose the endpoint. |
| Jina embeddings/rerank | Uses `JINA_API_KEY` or the corresponding binding/rerank API-key field. |
| VoyageAI embeddings | Uses `VOYAGE_API_KEY` first, then `VOYAGEAI_API_KEY` for compatibility. |
| Cohere rerank | Uses `COHERE_API_KEY` or `RERANK_BINDING_API_KEY`. |
| Aliyun rerank | Uses `DASHSCOPE_API_KEY` or `RERANK_BINDING_API_KEY`. |

## Embedding Wrapper Rules

`EmbeddingFunc` is part of the vector data contract:

- `embedding_dim` must match the provider output and stored vector data.
- `model_name` can be used by storage backends for model/workspace-specific isolation; keep it stable and descriptive.
- `max_token_size` is injected only when the underlying function accepts it; provider behavior varies between client-side truncation and provider-side truncation.
- `send_dimensions=True` injects `embedding_dim` into the underlying function. Server configuration forces dimension sending for `jina` and `gemini` when supported.
- `supports_asymmetric=True` allows LightRAG to pass `context="query"` or `context="document"`; otherwise `context` is stripped for legacy functions.
- The wrapper validates total element count against `embedding_dim` and validates returned vector count against input text count.

Provider default metadata observed in the inspected package:

| Function | Default dimension | Default max token size | Asymmetric support | Default model metadata |
| --- | ---: | ---: | --- | --- |
| `openai_embed` | 1536 | 8192 | Yes | `text-embedding-3-small` |
| `azure_openai_embed` | 1536 | 8192 | Yes | Azure deployment placeholder metadata. |
| `ollama_embed` | 1024 | 8192 | Yes | `bge-m3:latest` |
| `gemini_embed` | 1536 | 2048 | Yes | `gemini-embedding-001` |
| `jina_embed` | 2048 | 8192 | Yes | `jina-embeddings-v4` |
| `voyageai_embed` | 1024 | 32000 | Yes | No explicit wrapper `model_name` metadata. |
| `bedrock_embed` | 1024 | 8192 | No | `amazon.titan-embed-text-v2:0` |
| `lollms_embed` | 1024 | 8192 | No | `lollms_embedding_model` |
| `hf_embed` | 1024 | 8192 | Yes | `hf_embedding_model` |
| `zhipu_embedding` | 1024 | 8192 | No | `embedding-3` |
| `nvidia_openai_embed` | 2048 | 8192 | No | `nvidia_embedding_model` |

## Asymmetric Embeddings

LightRAG keeps embeddings symmetric by default. Asymmetric behavior only activates when `EMBEDDING_ASYMMETRIC=true`.

| Style | Bindings | Behavior |
| --- | --- | --- |
| Provider task parameters | `jina`, `gemini`, `voyageai` | LightRAG passes query/document context to provider parameters such as Jina `task`, Gemini `task_type`, or VoyageAI `input_type`. Prefix env vars are ignored with a warning. |
| Text task prefixes | `openai`, `azure_openai`, `ollama` | LightRAG prepends configured query/document prefixes before calling the embedding API. Both prefix variables must be explicitly configured. |

Prefix-mode variables:

```env
EMBEDDING_ASYMMETRIC=true
EMBEDDING_QUERY_PREFIX=search_query: 
EMBEDDING_DOCUMENT_PREFIX=search_document: 
```

Use `NO_PREFIX` when one side intentionally has no prefix. Do not use an empty value. At least one side must have a non-empty prefix. Unsupported bindings raise a configuration error when asymmetric mode is enabled.

Changing `EMBEDDING_ASYMMETRIC`, prefixes, provider task behavior, model, or dimension changes vector semantics. Route rebuild/clear/re-index decisions to `../../storage-backends/SKILL.md`.

## VLM Image Inputs

`image_inputs` is the unified provider-facing VLM input keyword. The shared normalizer accepts:

- Raw base64 strings.
- Data URLs such as `data:image/png;base64,...`.
- Dicts with required `base64` and optional `mime_type`, `source_id`, `source_file`, `modality`, and `doc_id`.

The normalizer computes MIME type, SHA-256 digest, byte count, and raster dimensions for PNG, JPEG, GIF, and WebP when possible. Cache metadata deliberately excludes source identifiers so the same image bytes at different file paths can share a cache entry; audit metadata can include source pointers but never raw base64.

VLM-compatible API/server bindings are `openai`, `azure_openai`, `gemini`, `bedrock`, and `ollama`. `lollms` is rejected for VLM processing. Bedrock forces non-streaming Converse calls when image inputs are present because of SDK limitations.

VLM processing has a separate master switch. Provider compatibility does not mean image analysis runs unless pipeline-level VLM processing is enabled.

## Response Format Compatibility

| Provider | Structured output behavior |
| --- | --- |
| OpenAI/Azure/OpenAI-compatible | OpenAI-style `response_format` is native for compatible services. Typed response formats are rejected by cache helpers. |
| Ollama | Maps `response_format={"type": "json_object"}` to `format="json"`; JSON schema dicts map to native `format`. |
| Gemini | Maps JSON object/schema dicts into Gemini generation config; typed/Pydantic response formats are rejected. Structured output disables COT in the Gemini adapter. |
| Bedrock | Bedrock Converse has no OpenAI JSON mode; `response_format` is dropped and prompt/downstream parsing must carry the structure. |
| Anthropic | Direct adapter strips OpenAI-style `response_format`; use prompt/downstream parsing. |
| Zhipu | Accepts OpenAI-style `response_format` and forwards it to the compatible API. |
| LoLLMS | Handles or drops compatibility fields according to its adapter; verify installed behavior before promising JSON mode. |

## Cache Identity

LLM query caches are partitioned by non-secret identity fields:

```text
role + binding + model + host
```

API keys and provider options are deliberately excluded from cache identity so persisted cache keys do not contain secrets. Changing model, binding, or host should produce cache misses for the affected role. Changing only provider options can reuse prior cached answers; decide whether existing cache entries remain semantically acceptable.
