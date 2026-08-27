# Provider Routing

LiteLLM chooses provider behavior from the model string, explicit provider fields, and endpoint family. Most normalized calls accept OpenAI-format inputs and pass provider-specific values through keyword arguments or proxy JSON/config fields.

## Model Prefix Rules

Use provider prefixes when the raw model name is ambiguous or when routing through the proxy:

| Provider family | Typical model string pattern | Common credentials/options |
| --- | --- | --- |
| OpenAI | `openai/gpt-...` or raw OpenAI model where unambiguous | `OPENAI_API_KEY`, `api_key`, optional `base_url`/`api_base` for compatible endpoints. |
| Azure OpenAI | `azure/<deployment-name>` | `AZURE_API_KEY`, `AZURE_API_BASE`, `AZURE_API_VERSION`, or explicit `api_key`, `api_base`, `api_version`; deployment name is not always the model name. |
| Anthropic | `anthropic/claude-...` | `ANTHROPIC_API_KEY`; messages and files/batches/pass-through capabilities vary by endpoint. |
| Bedrock | `bedrock/<model-id>` plus optional region/provider hints | AWS credential chain, `aws_region_name`, optional `api_base` or Bedrock runtime endpoint override. |
| Vertex AI | `vertex_ai/<model>` or partner model path | Google credentials, `vertex_project`, `vertex_location`, optional `api_base`; endpoint construction varies by publisher/model. |
| Gemini | `gemini/<model>` | Gemini API key or Google auth depending on selected Gemini/Vertex path. |
| OpenAI-compatible providers | provider prefix such as `openrouter/`, `deepinfra/`, `together_ai/`, `groq/`, `hosted_vllm/`, `openai_like/`, `lm_studio/`, `ollama/`, or custom compatible base | Provider API key and compatible `api_base`/`base_url`; confirm endpoint suffix handling. |
| Specialty endpoints | `cohere/`, `jina_ai/`, `voyage/`, `mistral/`, `reducto/`, search/vector/OCR providers | Use the endpoint-specific helper and provider docs in this skill; chat model support does not imply rerank/OCR/search/vector support. |

When two providers can share a raw model name, add the prefix. When the proxy exposes aliases in `model_list`, clients send the alias as `model`, and `litellm_params.model` carries the provider-prefixed backing model.

## OpenAI-Format Parameter Translation

- Chat, embeddings, completions, responses, images, audio, files, and batches generally accept OpenAI-compatible request shapes at LiteLLM boundaries.
- Provider configs map supported parameters to provider wire format. Common cross-provider parameters include `temperature`, `top_p`, `max_tokens`, `stream`, `tools`, `tool_choice`, `response_format`, `stop`, `user`, and metadata-like fields, but support differs by provider and endpoint.
- Provider-specific extras can be supplied as SDK keyword arguments or proxy JSON fields. Examples include Azure `api_version`, Bedrock `aws_region_name`, Vertex `vertex_project`/`vertex_location`, provider beta headers, safety settings, or search/rerank filters.
- Unsupported parameters can fail validation or be dropped when `drop_params=True` is set globally or per request. Use dropping only when losing that option is acceptable.

## `api_base` Versus `base_url`

LiteLLM code and proxy configs often use `api_base`; OpenAI-compatible clients often use `base_url`. Treat them as the same concept only at the boundary where the client or config maps one to the other.

- In SDK calls, `api_base` is the common LiteLLM argument for custom provider endpoints.
- In OpenAI SDK clients pointed at the LiteLLM proxy, use the OpenAI client’s `base_url` to point at the proxy, while the proxy config uses `api_base` inside `litellm_params` for upstream provider targets.
- Some provider transformers append endpoint suffixes such as `/chat/completions`, `/embeddings`, `/audio/transcriptions`, `:predict`, or `:rawPredict`; others expect the complete endpoint URL. If a request doubles a path segment, remove the suffix from `api_base` or use the provider’s expected base form.

## Azure Checklist

Azure failures are usually routing failures, not message-format failures:

1. Use deployment name in the model string or proxy alias mapping.
2. Provide `api_base` for the Azure resource, not an OpenAI base URL.
3. Provide `api_version` explicitly or through environment/config.
4. Confirm the Azure deployment supports the endpoint family; chat, embeddings, responses, images, audio, files, batches, vector stores, and containers are separate capabilities.
5. If using OpenAI SDK through the proxy, the client `base_url` points to LiteLLM, while Azure upstream settings remain in proxy config or request metadata.

## Bedrock And Vertex Provider Detection

Bedrock has nested provider concepts. A model may route through Bedrock while the underlying invoke provider is Anthropic, Amazon, Meta/Llama, Cohere, Mistral, AI21, DeepSeek, OpenAI, Qwen, Stability, Moonshot, TwelveLabs, or Nova depending on endpoint family. If Bedrock cannot infer the invoke/embedding provider, use a clearer model path or provider-specific route.

Vertex AI also has multiple surfaces: native Vertex models, partner publisher models, Gemini paths, RAG/vector stores, OCR, rerank, text-to-speech, images, videos, and fine tuning. Check `vertex_project`, `vertex_location`, and API version, and verify whether the target endpoint uses `v1`, `v1beta1`, `rawPredict`, `streamRawPredict`, `predict`, or OpenAPI-compatible endpoints.

## Proxy `model_list` Patterns

Use aliases to hide provider details from clients:

```yaml
model_list:
  - model_name: chat-prod
    litellm_params:
      model: anthropic/claude-sonnet-4-5-20250929
      api_key: os.environ/ANTHROPIC_API_KEY
  - model_name: embeddings-prod
    litellm_params:
      model: openai/text-embedding-3-large
      api_key: os.environ/OPENAI_API_KEY
  - model_name: azure-chat
    litellm_params:
      model: azure/my-deployment
      api_base: os.environ/AZURE_API_BASE
      api_key: os.environ/AZURE_API_KEY
      api_version: os.environ/AZURE_API_VERSION
```

Use wildcard aliases such as `anthropic/*` or `openai/*` only when you deliberately allow clients to select arbitrary provider models under that prefix.

## Validation Snippets

Python SDK shape check:

```python
import litellm

response = litellm.completion(
    model="openai/gpt-4o-mini",
    messages=[{"role": "user", "content": "Return one word."}],
    temperature=0,
)
print(response.choices[0].message.content)
```

OpenAI-compatible proxy client shape check:

```python
from openai import OpenAI

client = OpenAI(api_key="proxy-key", base_url="http://localhost:4000/v1")
response = client.chat.completions.create(
    model="chat-prod",
    messages=[{"role": "user", "content": "Return one word."}],
)
print(response.choices[0].message.content)
```

Use real provider credentials only in the runtime environment. Do not commit keys or local machine paths in configs.
