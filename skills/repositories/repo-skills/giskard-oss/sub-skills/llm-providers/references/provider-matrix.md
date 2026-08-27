# Provider matrix

Use this matrix when choosing a provider prefix, SDK extra, credential source,
or supported operation.

## Installation extras

- Base package: `giskard-llm`
- OpenAI family: `giskard-llm[openai]`
- Google Gemini: `giskard-llm[google]`
- Anthropic: `giskard-llm[anthropic]`
- All core providers: `giskard-llm[all]`
- Azure OpenAI and Azure AI Foundry both use the OpenAI SDK, so the OpenAI
  extra covers them.

## Prefix and capability table

| Prefix | Provider class | SDK package | Default / auth env vars | Completion | Embedding | Responses / interactions | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `openai/` | OpenAI provider | `openai` | `OPENAI_API_KEY` | yes | yes | yes | Bare model names route here by default. |
| `google/` | Google provider | `google-genai` | `GOOGLE_API_KEY` or `GEMINI_API_KEY` | yes | yes | yes | `gemini/` is an alias for this provider. |
| `gemini/` | Google provider | `google-genai` | `GOOGLE_API_KEY` or `GEMINI_API_KEY` | yes | yes | yes | Alias only; identical behavior to `google/`. |
| `anthropic/` | Anthropic provider | `anthropic` | `ANTHROPIC_API_KEY` | yes | no | no | Supports optional `merge_system=True`. |
| `azure/` | Azure OpenAI provider | `openai` | `AZURE_API_KEY`, `AZURE_API_BASE`, `AZURE_API_VERSION` | yes | yes | yes | Classic Azure OpenAI path. |
| `azure_ai/` | Azure AI Foundry provider | `openai` | `AZURE_AI_API_KEY`, `AZURE_AI_ENDPOINT`, `AZURE_AI_API_VERSION` | yes | model-dependent | model-dependent | Foundry compatibility path with endpoint normalization. |

## Provider selection rules

- Bare model names default to OpenAI.
- Alias names in `LLMClient.configure(...)` are independent of provider prefix
  strings. An alias such as `foundry-v1` can point at the OpenAI provider or at
  any other provider type.
- `provider=` in `configure(...)` selects the provider implementation. The alias
  name becomes the prefix used in later model strings.
- `gemini` is a routing alias only; it does not require a separate SDK.

## Environment variable precedence

### OpenAI

- `OPENAI_API_KEY` is the standard env var.
- `api_key` kwarg overrides the environment.
- `base_url`, `timeout`, `http_client`, and `default_headers` are accepted.

### Google Gemini

- `api_key` kwarg overrides env vars.
- Otherwise the provider checks `GEMINI_API_KEY` first, then `GOOGLE_API_KEY`.
- `http_client`, `default_headers`, `http_options`, and `safety_settings` are
  supported.
- `http_options` wins over convenience kwargs when both are provided; missing
  fields can be filled from convenience kwargs.

### Anthropic

- `api_key` kwarg overrides `ANTHROPIC_API_KEY`.
- `merge_system=True` is the opt-in behavior switch for multiple system or
  developer instruction messages.
- `base_url`, `timeout`, `http_client`, and `default_headers` are supported.

### Classic Azure OpenAI

- `api_key` kwarg overrides `AZURE_API_KEY`.
- `base_url` kwarg overrides `AZURE_API_BASE`.
- `api_version` kwarg overrides `AZURE_API_VERSION`; default is `2024-10-21`.
- `http_client` and `default_headers` are passed through to the OpenAI SDK.

### Azure AI Foundry

- `api_key` kwarg overrides `AZURE_AI_API_KEY`.
- `base_url` kwarg overrides `AZURE_AI_ENDPOINT`.
- `AZURE_AI_API_VERSION` is optional; default is `2024-10-21`.
- Foundry resource roots are normalized for the OpenAI SDK, and a legacy
  `/models` suffix is stripped when the host is a Foundry endpoint.

## Azure Foundry v1 versus classic Azure

Use this decision rule:

1. If the endpoint is an OpenAI-compatible Azure Foundry v1 endpoint ending in
   `/openai/v1/`, use `provider="openai"` and keep the deployment name as the
   model segment.
2. If the endpoint is a classic Azure OpenAI deployment endpoint that relies on
   an Azure API version, use `provider="azure"`.
3. If the endpoint is an Azure AI Foundry resource URL on `*.services.ai.azure.com`,
   use `provider="azure_ai"` unless you are intentionally preserving legacy
   behavior.

## Operation support

### Completions

All providers except unsupported SDK combinations can route chat completions.
Anthropic accepts completions only.

### Embeddings

- OpenAI, Google, and classic Azure OpenAI support embeddings.
- Anthropic does not implement embeddings.
- Azure AI Foundry embedding support depends on the deployed model and endpoint.

### Responses / Interactions

- OpenAI provider supports the OpenAI Responses API.
- Google provider supports the Gemini Interactions API.
- Anthropic does not implement a stateful response API in this package.
- Azure OpenAI uses the OpenAI SDK Responses API path.
- Azure AI Foundry behavior is model-dependent and should be checked with the
  provider capability and deployment you actually plan to use.

## Message and tool format notes

- Public inputs accept nested `ToolDefParam` definitions.
- OpenAI Responses and Gemini Interactions use flattened tool definitions on the
  wire; the provider translators handle that conversion.
- Function-call outputs use the OpenAI-style `FunctionCallOutputParam` shape,
  and the Google translator adds the function name when it serializes results.
- Google and Anthropic fold system/developer instructions differently:
  - Google extracts them into `system_instruction`.
  - Anthropic extracts them into top-level `system` text blocks and may merge
    them only when `merge_system=True`.

## Error hierarchy summary

- `ProviderNotAvailableError`: SDK import missing at provider construction.
- `AuthenticationError`: missing or invalid credentials.
- `BadRequestError`: invalid input shape, unsupported message order, or other
  client-side request issues.
- `RateLimitError`: provider throttling.
- `ServerError`: upstream server failure.
- `LLMTimeoutError`: request timeout.
- `UnsupportedOperationError`: provider does not implement the requested call.
- `LLMError`: provider-specific failure that does not fit a narrower class.
