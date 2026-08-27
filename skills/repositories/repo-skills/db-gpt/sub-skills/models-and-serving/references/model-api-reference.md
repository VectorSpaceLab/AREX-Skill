# Model API reference

This reference distills the DB-GPT 0.8.1 model configuration and serving
interfaces. It is an operating reference, not a copy of implementation files.

## Model roles and provider field

Every model entry has a `name` and `provider` (the provider is also the
configuration discriminator). The three model collections map to worker roles:

| TOML table | Worker type | Typical operation |
|---|---|---|
| `models.llms` | `llm` | chat/completions and token counting |
| `models.embeddings` | `text2vec` | text embeddings for RAG/knowledge |
| `models.rerankers` | `reranker` | relevance scoring |

`LLMDeployModelParameters` adds `backend`, `prompt_template`,
`context_length`, and `reasoning_model`. `backend` is the provider-facing model
name when it differs from the DB-GPT entry `name`; otherwise `name` is passed
to the provider. `verbose` and `concurrency` are common controls. Embeddings
default to concurrency 100, rerankers to 50, and LLMs to 5 in the generic base
classes; provider-specific classes may raise an LLM concurrency default.

`ModelsDeployParameters` contains `default_llm`, `default_embedding`, and
`default_reranker`. If a default is omitted, DB-GPT selects the first entry in
the corresponding list. With multiple providers, set the defaults explicitly
and use unique names.

## Provider-independent TOML shape

```toml
[models]
default_llm = "chat-model"
default_embedding = "embedding-model"

[[models.llms]]
name = "chat-model"
provider = "proxy/openai"
# provider-specific fields follow

[[models.embeddings]]
name = "embedding-model"
provider = "proxy/openai"

[[models.rerankers]]
name = "reranker-model"
provider = "hf"
path = "models/reranker-model"
```

Use repeated array-of-table syntax. A single inline map under `models.llms` is
not equivalent to `[[models.llms]]`. Keep `name` stable: registry keys are
formed as `<model-name>@<worker-type>`, and `@` is not allowed inside a worker
name.

## Provider model parameter families

### OpenAI-compatible proxy

The common `proxy/openai` family accepts:

```toml
[[models.llms]]
name = "chat-model"
provider = "proxy/openai"
api_base = "${env:OPENAI_API_BASE:-https://api.openai.com/v1}"
api_key = "${env:OPENAI_API_KEY}"
# Optional: backend, api_type, api_version, http_proxy, context_length,
# reasoning_model, prompt_template, concurrency
```

Embedding entries use the same provider family but should specify the embedding
endpoint field expected by the installed provider adapter when an explicit URL
is required:

```toml
[[models.embeddings]]
name = "embedding-model"
provider = "proxy/openai"
api_url = "${env:EMBEDDING_API_URL:-https://api.openai.com/v1/embeddings}"
api_key = "${env:OPENAI_API_KEY}"
```

An OpenAI-compatible chat endpoint does not imply that the endpoint supports
embeddings. Configure and test the embedding model independently.

### DeepSeek

```toml
[[models.llms]]
name = "deepseek-chat"
provider = "proxy/deepseek"
api_base = "${env:DEEPSEEK_API_BASE:-https://api.deepseek.com/v1}"
api_key = "${env:DEEPSEEK_API_KEY}"
# Optional provider field: thinking_enabled = false
```

`thinking_enabled` is provider-specific. It is not a generic local-backend
flag. Use a model name actually offered by the selected DeepSeek endpoint.

### Tongyi / DashScope

```toml
[[models.llms]]
name = "qwen-plus"
provider = "proxy/tongyi"
api_base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
api_key = "${env:DASHSCOPE_API_KEY}"

[[models.embeddings]]
name = "text-embedding-v3"
provider = "proxy/tongyi"
api_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"
api_key = "${env:DASHSCOPE_API_KEY}"
```

### Ollama proxy

Ollama is a local service reached through a proxy adapter; it is not the same
as loading a Hugging Face model inside a DB-GPT worker.

```toml
[[models.llms]]
name = "qwen2.5:latest"
provider = "proxy/ollama"
api_base = "${env:OLLAMA_API_BASE:-http://localhost:11434}"
api_key = ""

[[models.embeddings]]
name = "bge-m3:latest"
provider = "proxy/ollama"
api_url = "${env:OLLAMA_API_BASE:-http://localhost:11434}"
api_key = ""
```

The Ollama service must be running and the named models must already be
available to it. A parsed URL is not a model availability check.

### Local providers

Local entries generally use `path` and a provider-specific parameter class:

```toml
[[models.llms]]
name = "local-chat"
provider = "hf"
path = "models/local-chat"

[[models.llms]]
name = "local-vllm-chat"
provider = "vllm"
path = "models/local-vllm-chat"

[[models.llms]]
name = "local-gguf-chat"
provider = "llama.cpp"
path = "models/local-chat.Q4_K_M.gguf"

[[models.llms]]
name = "local-server-chat"
provider = "llama.cpp.server"
path = "models/local-chat.Q4_K_M.gguf"
```

`hf` uses `HFLLMDeployModelParameters`; relevant fields include `device`,
`trust_remote_code`, `quantization`, `num_gpus`, `max_gpu_memory`,
`torch_dtype`, and `attn_implementation`. `vllm` uses
`VLLMDeployModelParameters`; important fields include `dtype`,
`kv_cache_dtype`, `max_model_len`, `tensor_parallel_size`,
`pipeline_parallel_size`, `gpu_memory_utilization`, `cpu_offload_gb`,
`quantization`, and `extras`. `llama.cpp.server` uses
`LlamaServerParameters`; relevant fields include `server_bin_path`,
`server_host`, `server_port`, `n_gpu_layers`, `ctx_size`, `n_predict`,
`threads`, `startup_timeout`, and `api_key`. Consult
[backends.md](backends.md) before selecting these fields.

## Service parameter shape

The service model config has three sections:

```toml
[service.model.controller]
host = "0.0.0.0"
port = 8000
heartbeat_interval_secs = 20
heartbeat_timeout_secs = 60

[service.model.worker]
host = "0.0.0.0"
port = 8001
worker_type = "llm"
controller_addr = "http://127.0.0.1:8000"
register = true
send_heartbeat = true
heartbeat_interval = 20
standalone = false

[service.model.api]
host = "0.0.0.0"
port = 8100
controller_addr = "http://127.0.0.1:8000"
api_keys = "${env:DBGPT_MODEL_API_KEYS:-}"
embedding_batch_size = 16
cors_allowed_origins = "http://localhost:5670"
```

Defaults in the public parameter classes are controller `8000`, worker `8001`,
model API server `8100`, controller heartbeat interval 20 seconds and timeout
60 seconds. The worker defaults to registration and heartbeats enabled. The
API server defaults to controller `http://127.0.0.1:8000` and unrestricted CORS
unless explicitly narrowed. Change these for a networked deployment; do not
bind an externally exposed service to a broad interface without an access
policy.

## Model controller registry

A registered instance includes model key, host, port, optional weight, health
checking, enabled state, prompt template, and heartbeat time. A model key is
`name@llm`, `name@text2vec`, or `name@reranker`. The controller considers an
instance healthy only while heartbeats remain within the configured timeout.
`dbgpt model list` displays registry state, including health and heartbeat; it
does not exercise the worker's generate/embedding endpoint.

## Model API server endpoints

The optional model API server exposes OpenAI-style routes under `/v1` and
uses `controller_addr` to discover workers:

| Route | Purpose |
|---|---|
| `GET /v1/models` | list available models |
| `POST /v1/chat/completions` | chat completion |
| `POST /v1/completions` | text completion |
| `POST /v1/embeddings` | embeddings |
| `POST /v1/beta/relevance` | reranking/relevance |

When `api_keys` is configured, send a permitted key using the API's supported
Authorization header. Keep the API server's key list separate from upstream
provider keys. A successful `/v1/models` response verifies API-server routing,
not necessarily a successful provider generation; issue a minimal operation
for the selected model role as a second check.
