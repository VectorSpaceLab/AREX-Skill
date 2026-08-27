# Troubleshooting provider configuration

Use this checklist when Langroid provider access fails before or during the first LLM/embedding call.

## Missing API keys

Symptoms:

- authentication or 401 errors;
- explicit messages such as `OPENAI_API_KEY must be set`, `AZURE_OPENAI_API_KEY not set`, `GEMINI_API_KEY env variable must be set`, or missing provider key errors;
- gateway errors saying a provider key or virtual key is missing.

Fixes:

- Plain OpenAI LLM: set `OPENAI_API_KEY` or pass `api_key` for local tests.
- OpenAI embeddings: set `OPENAI_API_KEY` unless using a LangDB embedding prefix.
- Azure LLM/embeddings: set `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_API_BASE`; also set deployment and API version.
- Gemini LLM/embeddings: set `GEMINI_API_KEY`; for Vertex-style endpoints, use a current bearer token and set `GEMINI_API_BASE` or explicit `api_base`.
- Groq/Cerebras/OpenRouter/DeepSeek/MiniMax/GLHF: set the corresponding provider key environment variable.
- LangDB: set `LANGDB_API_KEY` and usually `LANGDB_PROJECT_ID`.
- Portkey: set `PORTKEY_API_KEY`; also ensure provider keys or virtual keys exist as required by the gateway.
- LiteLLM adapter: install the optional LiteLLM dependency and set whatever provider variables LiteLLM requires.
- LiteLLM proxy: set `LITELLM_API_KEY`/`LITELLM_API_BASE` or pass `LiteLLMProxyConfig`.

Avoid printing raw keys in debug output. Report only whether a key source is present.

## Wrong `api_base` or model string

Symptoms:

- 404 for `/chat/completions` or `/v1/chat/completions`;
- server says model not found;
- local server receives no requests;
- provider-specific prefix remains in the final model sent to a server that does not understand it.

Fixes:

- Generic OpenAI-compatible servers usually need `api_base` ending in `/v1` and `chat_model` equal to the server's advertised model id.
- `local/host:port/v1` encodes the endpoint in the model string; use explicit `api_base` when the endpoint also requires a specific model id.
- `vllm/` normalizes bare host/port bases to `/v1`; still confirm the server is serving the same model id.
- `llamacpp/host:port` expects a llama.cpp server endpoint, not an embedding-only URL.
- `openrouter/`, `portkey/`, and `langdb/` expect gateway-specific provider/model names. Check provider spelling and model availability.
- Clear `OPENAI_API_BASE` and `OPENAI_CHAT_MODEL` when debugging because they can override config fields through the `OPENAI_` settings prefix.

## LiteLLM proxy versus direct LiteLLM adapter

Symptoms:

- `litellm-proxy/` config tries to reach the wrong URL;
- `litellm/` fails with missing optional dependency;
- provider variables are set for the proxy but the config uses the adapter form, or vice versa.

Fixes:

- Use `chat_model="litellm-proxy/<model>"` only when a LiteLLM proxy server is deployed. Provide `LiteLLMProxyConfig(api_base=..., api_key=...)` or `LITELLM_API_BASE` and `LITELLM_API_KEY`.
- Use `chat_model="litellm/<provider>/<model>"` only for the in-process LiteLLM adapter. Install the optional dependency and provider keys required by LiteLLM.
- For a generic OpenAI-compatible proxy that is not a LiteLLM proxy, use `chat_model=<served-model>` plus explicit `api_base` instead.

## Local server not running

Symptoms:

- connection refused;
- timeout before any provider response;
- TLS or scheme errors for local endpoints;
- llama.cpp embedding errors such as failed tokenization or embedding endpoint connection.

Fixes:

- Confirm the server is listening on the host/port in `api_base` or the `local/`, `ollama/`, `vllm/`, or `llamacpp/` model string.
- For Ollama, ensure the model is pulled and the OpenAI-compatible endpoint is available. `OLLAMA_HOST` can change the base host.
- For vLLM, ensure the served model name and `chat_model` agree.
- For llama.cpp chat, ensure the chat server is running. For llama.cpp embeddings, ensure the server was started with embeddings enabled and exposes tokenize/detokenize/embeddings endpoints.
- Use `http://` for local non-TLS servers. Use HTTP-client SSL settings only when a trusted HTTPS endpoint has certificate issues.

## Azure deployment naming

Symptoms:

- Azure reports deployment not found;
- model name works in OpenAI but not Azure;
- embeddings fail while chat works, or the reverse.

Fixes:

- `deployment_name` is the custom Azure deployment name, not necessarily the model id.
- Use `AzureConfig`/`AzureGPT` for Azure LLMs and `AzureOpenAIEmbeddingsConfig` for embeddings.
- Set the right `api_version`; structured-output support depends on Azure API version.
- For older code using `model_name`, migrate to `chat_model` and keep `deployment_name` explicit.
- For Entra ID auth, provide Azure SDK clients through the Azure client-provider fields rather than `api_key_provider`.

## Gemini and Vertex-style OpenAI-compatible usage

Symptoms:

- `OPENAI_API_BASE` appears ignored for Gemini;
- Vertex endpoint receives no traffic;
- auth works for Google tools but Langroid LLM calls return 401.

Fixes:

- Use `chat_model="gemini/<model>"` for direct Gemini via the OpenAI client.
- Set `GEMINI_API_KEY` for Google AI Studio or a current Vertex bearer token.
- Set `GEMINI_API_BASE` or explicit `api_base` for Vertex-style endpoints.
- Do not rely on `OPENAI_API_BASE`; Langroid intentionally ignores it for `gemini/` models to prevent accidental leakage from other OpenAI-compatible configs.
- Gemini embeddings use `GeminiEmbeddingsConfig` and require the Gemini embedding optional dependency when instantiated.

## Client caching and key rotation

Symptoms:

- too many open files or connection exhaustion;
- stale short-lived bearer tokens;
- unexpected client sharing during multiprocessing;
- cache grows when token values rotate.

Fixes:

- Keep `use_cached_client=True` unless isolation is required.
- Set `use_cached_client=False` for multiprocessing, debugging client identity, or strict per-instance isolation.
- Use `api_key_provider` for short-lived tokens on the OpenAI-client path. The cache keys on the provider callable identity instead of token value.
- Share the same provider callable when multiple LLM objects should share a cached rotating-key client.
- Do not use `api_key_provider` with `groq/`, `cerebras/`, or `litellm/`; those paths reject it.
- If custom auth must run at the HTTP layer, return both sync and async clients from `http_client_factory` when both call styles are needed. Factory clients are not cacheable.

## HTTP client, proxy, and SSL issues

Symptoms:

- certificate verification errors;
- proxy connection failures;
- sync calls work but async calls fail through the proxy;
- cached and non-cached runs behave differently.

Fixes:

- Prefer `http_client_config` for stable proxy/CA settings because it remains cacheable.
- Use `http_verify_ssl=False` only in trusted development or local test environments.
- Use `http_client_factory` only for dynamic auth, event hooks, or custom transports; return `(Client, AsyncClient)` if async calls need the same behavior.
- Confirm proxy URL shape and authentication requirements.
- Remember priority order: factory, then config dict, then SSL flag.

## Optional embedding dependencies and downloads

Symptoms:

- import errors for sentence-transformers, transformers, fastembed, google-genai, or grpc pieces;
- first embedding call stalls while downloading a model;
- vector store rejects vectors due to wrong dimension;
- low-quality retrieval from local embeddings.

Fixes:

- Install only the optional backend needed by the selected embedding config.
- For offline/deterministic runs, pre-populate local model caches and avoid choosing a model that must download at first use.
- Set `dims` to the provider's actual vector length.
- For SentenceTransformer, choose `device`, `data_parallel`, and `devices` intentionally.
- For FastEmbed, set `cache_dir`, `threads`, and `parallel` to match local CPU constraints.
- For llama.cpp embeddings, prefer a dedicated embedding GGUF model, start the server with embedding support, and match `context_length`, `batch_size`, and `dims` to that model.

## Reasoning content and streaming confusion

Symptoms:

- `response.reasoning` is empty for a reasoning-capable model;
- reasoning tokens appear mixed into the answer text;
- provider rejects `reasoning_effort` or `extra_body`.

Fixes:

- Use `OpenAICallParams(reasoning_effort=...)` only for models that accept that parameter.
- Use `extra_body={"include_reasoning": True}` for providers that require an extra flag to return reasoning.
- Some models perform reasoning internally but do not expose the trace through the API.
- Streaming can deliver reasoning through separate reasoning fields, inline thought delimiters, or not at all, depending on provider. Consume `LLMResponse.reasoning` and `StreamEventType.REASONING` when present rather than assuming every token belongs to the final answer.
