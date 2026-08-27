# Provider and backend matrix

Use this matrix to choose a model path before writing TOML. “CPU verified”
means only configuration/import and deterministic package checks in the
prepared environment; it does not mean local inference is fast or that a
provider endpoint is reachable.

## Provider choices

| Provider value | Execution boundary | LLM fields | Embedding/reranker pairing | Credentials/service |
|---|---|---|---|---|
| `proxy/openai` | remote OpenAI-compatible chat or embedding API | `api_base`, `api_key`, optional `backend` and HTTP settings | configure a separate embedding entry and endpoint | API key and network required |
| `proxy/deepseek` | remote DeepSeek-compatible chat API | `api_base`, `api_key`, optional `thinking_enabled` | use a provider that explicitly serves embeddings; do not assume chat endpoint does | API key and network required |
| `proxy/tongyi` | DashScope-compatible API | `api_base`, `api_key` | configure compatible embedding name and API URL separately | `DASHSCOPE_API_KEY` and network required |
| `proxy/ollama` | local Ollama HTTP service | `api_base`; key commonly empty | Ollama must have a separately pulled embedding model | Ollama process and model inventory required |
| `proxy/siliconflow` | remote SiliconFlow model API | `api_key`, optional endpoint fields | can use SiliconFlow or another compatible embedding provider | API key and network required |
| `proxy/litellm` | embedded LiteLLM Python gateway | provider-prefixed `name`, optional endpoint overrides | pair with local or remote embedding provider | matching provider environment variables required |
| other `proxy/*` | provider-specific adapter | inspect its registered parameter class | verify embedding support independently | provider package/credentials/network vary |
| `hf` | in-process Hugging Face model | `path`, device and loading fields | local embedding/reranker adapters may use the same provider family | model files and compatible ML stack required |
| `vllm` | in-process vLLM worker | `path`, dtype, GPU and batching fields | embedding support depends on the selected model/backend | vLLM, torch, model files, and GPU normally required |
| `llama.cpp` | in-process GGUF runtime | `path`, context/thread/GPU-layer fields | embedding/reranking flags and model support must be checked | llama.cpp Python/backend and model file required |
| `llama.cpp.server` | child llama.cpp server process | `path`, server binary and server parameters | server must expose the requested role | executable, model file, ports, and optional GPU required |
| `mlx` | Apple MLX local runtime | local model path and MLX options | host/backend-specific | Apple Silicon and MLX stack required |

Provider names are case-sensitive in configuration. `proxy/foo` is a provider
family, not proof that the `foo` extra is installed. A model name is not a
provider credential and should not be used to infer endpoint support.

## Secret and endpoint precedence

Prefer this pattern:

```toml
api_key = "${env:PROVIDER_API_KEY}"
api_base = "${env:PROVIDER_API_BASE:-https://provider.example/v1}"
```

DB-GPT's configuration manager resolves `${env:NAME}` and
`${env:NAME:-fallback}` while converting configuration values. A missing
required environment value must remain an actionable configuration error; do
not replace it with a fake key. Some provider clients also resolve their own
provider-specific environment variables. When debugging, establish which
layer owns the value and redact the effective value from output.

Environment variables used in the documented provider patterns include:

| Provider | Key variable examples |
|---|---|
| OpenAI-compatible | `OPENAI_API_KEY`, `OPENAI_API_BASE` |
| DeepSeek | `DEEPSEEK_API_KEY`, `DEEPSEEK_API_BASE` |
| Tongyi | `DASHSCOPE_API_KEY`, optionally `DASHSCOPE_API_BASE` |
| Ollama | `OLLAMA_API_BASE` (usually no secret) |
| SiliconFlow | `SILICONFLOW_API_KEY` |
| LiteLLM | upstream provider variables such as `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` |

Do not put an upstream provider key in `service.model.api.api_keys`: that field
protects the optional DB-GPT model API server, while model-entry `api_key`
fields authenticate to an upstream provider.

## Model-role pairing rules

1. A chat/LLM entry answers prompts; it is not an embedding model.
2. A configured embedding model is required for knowledge ingestion and vector
   retrieval unless the consuming workflow deliberately uses a non-embedding
   path such as BM25. “OpenAI-compatible” describes a protocol, not all model
   capabilities.
3. A reranker is optional and must be enabled/configured as a separate
   `models.rerankers` entry.
4. If a provider only exposes chat completions, fail early with a missing
   embedding correction instead of starting a nominally complete RAG service.
5. Set `default_*` names when more than one entry of a role is present. Defaults
   must match an entry's `name`, not its provider-facing `backend` value unless
   those names are intentionally identical.

## Backend boundary table

| Backend | Model artifact | Typical hardware | Safe claim in CPU-only inspection |
|---|---|---|---|
| Proxy | none in DB-GPT process | network/provider service | config shape/import only; no live call |
| HF | local directory or permitted model id | CPU possible, GPU often needed | parameter parsing only; no model download/inference |
| vLLM | local/HF model and vLLM runtime | CUDA GPU normally expected | do not claim backend startup |
| llama.cpp | GGUF file or server binary | CPU possible; GPU layers optional | config shape only unless runtime is separately tested |
| llama.cpp.server | GGUF plus executable child server | CPU or CUDA depending binary | no child process proof |
| MLX | MLX-compatible model | Apple Silicon | not verified on Linux CPU |
| bitsandbytes quantization | HF model plus bitsandbytes/torch | CUDA required by DB-GPT validation for 4/8-bit path | never equate with CPU |

The current verified route covers CPU imports, parser/config behavior, registry
logic, and safe CLI help. CUDA, torch local inference, vLLM, bitsandbytes,
llama.cpp acceleration, MLX, provider credentials, and external services remain
optional or unverified unless a later run explicitly prepares and exercises them.
A visible GPU or driver is hardware evidence only; it does not install the
Python stack or prove a selected backend.
