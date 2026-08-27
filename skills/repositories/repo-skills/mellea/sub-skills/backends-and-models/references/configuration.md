# Provider configuration and option workflow

Read this before changing a backend or moving a program between local and
hosted inference. Keep three questions separate:

1. **Package extra:** can the Python backend module import?
2. **Credential/service:** can the process authenticate to the endpoint or
   local service?
3. **Model/checkpoint:** does the provider expose the selected model, or does
   the local machine have the weights and enough memory?

An import success answers only the first question.

## Install by capability

The base `mellea` install includes the OpenAI SDK, Ollama client, Pillow, and
core formatters. Use only the extra needed by the selected route:

| Capability | Extra | What it adds |
|---|---|---|
| Local HF inference, constrained decoding, PEFT adapters | `mellea[hf]` | Transformers, Torch-adjacent HF tooling, `llguidance`, PEFT, datasets, and related packages. |
| LiteLLM and its Bedrock path | `mellea[litellm]` | `litellm` and `boto3`. Provider SDKs may still be separately required, such as Vertex AI's Google package. At this snapshot, the `mellea.backends.bedrock` helper module also imports `LiteLLMBackend`, so install this extra before importing either Bedrock helper even though the dedicated Mantle guide describes the OpenAI client path as base-only. |
| Native WatsonX backend | `mellea[watsonx]` | IBM WatsonX AI SDK. This backend is deprecated for new work. |
| Tools/MCP integrations | `mellea[tools]` | Tool ecosystem packages; not required merely to select a backend. |
| OpenTelemetry metrics/traces | `mellea[telemetry]` | OpenTelemetry API/SDK/exporters and hooks. |
| HTTP server | `mellea[server]` | Uvicorn, FastAPI, and CLI support. |
| `m` CLI | `mellea[cli]` | Typer. |

The `backends` convenience extra groups `watsonx`, `hf`, and `litellm`; it is
not required if the narrower extra is enough. `all` also enables unrelated
features and is not a minimum installation.

## Selection recipes

### Ollama: local default

Run the Ollama service separately, then select a model tag or a
`ModelIdentifier` with `ollama_name`:

```python
from mellea import start_session
from mellea.backends import ModelOption, model_ids

session = start_session(
    backend_name="ollama",
    model_id=model_ids.IBM_GRANITE_4_1_3B,
    model_options={ModelOption.MAX_NEW_TOKENS: 256},
)
```

`OLLAMA_HOST` or `base_url` selects a non-default service. `base_url` wins over
the environment value. Construction checks the server and may pull a missing
model, so do not use it in a no-network unit test without mocking.

### OpenAI-compatible endpoint

Use `OpenAIBackend` for OpenAI, LM Studio, vLLM, Ollama's `/v1` endpoint, or
another server implementing compatible chat completions. Set
`OPENAI_API_KEY`, or pass `api_key`; local servers commonly accept a placeholder
non-empty key. Set `OPENAI_BASE_URL`, or pass `base_url`:

```python
from mellea import MelleaSession
from mellea.backends.openai import OpenAIBackend

session = MelleaSession(
    OpenAIBackend(
        model_id="served-model-name",
        base_url="http://127.0.0.1:8000/v1",
        api_key="local",
    )
)
```

Use `default_extra_body={...}` for persistent provider-specific request fields.
Per-call `model_options={"extra_body": {...}}` overrides them. Nested
`chat_template_kwargs` are deep-merged, which matters when adapter activation
and thinking controls both add fields. Do not invent server flags: pass only
fields documented by that endpoint and remove an option after an unsupported-
parameter error.

### LiteLLM, Bedrock, and Vertex AI

Use a `<provider>/<model>` string in `LiteLLMBackend`. For cloud providers,
leave `base_url` unset so LiteLLM infers the provider; set it for a local server
or LiteLLM proxy. Typical prefixes are `anthropic/`, `azure/`, `watsonx/`,
`bedrock/converse/`, `vertex_ai/`, and `litellm_proxy/`.

For Bedrock:

- At this package snapshot, import `mellea.backends.bedrock` only after
  installing `mellea[litellm]`: the helper module imports `LiteLLMBackend` even
  for the Mantle/OpenAI helper. This is an implementation prerequisite, not a
  provider flag.
- `create_bedrock_openai_backend(model_id, region=...)` uses the Bedrock Mantle
  OpenAI-compatible endpoint and requires `AWS_BEARER_TOKEN_BEDROCK`; it
  checks regional model availability and makes a network request.
- `create_bedrock_litellm_backend(model_id, region=..., num_retries=3)` uses
  LiteLLM and can use standard AWS credential resolution. A region must be
  explicit or resolvable from the AWS region environment variables.
- The LiteLLM model spelling is `bedrock/converse/<bedrock-model-id>`.

For Vertex AI, install the LiteLLM extra plus the provider's Google package,
configure `VERTEXAI_PROJECT` and `VERTEXAI_LOCATION`, and use a `vertex_ai/` or
`vertex_ai_beta/` model string. Authentication comes from application default
credentials or a service-account mechanism; never commit a key file.

### Native WatsonX (legacy)

The native backend uses `WATSONX_URL`, `WATSONX_API_KEY`, and
`WATSONX_PROJECT_ID`, or explicit constructor arguments. It requires the
WatsonX extra and is deprecated. The recommended migration is LiteLLM with a
`watsonx/` prefix, whose API-key variable is `WATSONX_APIKEY` (different from
the native backend's `WATSONX_API_KEY`), or an OpenAI-compatible endpoint.

### Hugging Face local

Install `mellea[hf]`, provide a valid local/HF model ID or a custom tokenizer,
model, and device tuple via `custom_config`, and expect checkpoint access or
pre-existing local weights. Device auto-selection is CUDA, MPS, then CPU. This
backend is designed for small-scale local inference and experimental HF-only
features; it is not evidence of scalable CUDA serving.

Use `use_caches=False` while isolating KV-cache issues, or provide a
`SimpleLRUCache` with explicit capacity. A cache setting does not reduce the
base model's memory requirement.

## Option layering and validation

Use this repeatable sequence:

1. Start with a provider-independent `ModelOption` dictionary.
2. Add provider-native keys only when the endpoint documents them.
3. Put stable defaults on the backend; put experiment-specific overrides on
   the call; make `MAX_NEW_TOKENS` explicit.
4. Inspect the resulting request through a mocked client or backend unit test.
5. Verify metadata and output shape before enabling live credentials.

For a model with reasoning enabled, a blank final `.value` can be legitimate
when the response contains only reasoning. Inspect `.thinking` and usage before
calling it a provider failure. Use a stable `default_extra_body` setting when
the server requires a persistent thinking switch; changing chat-template
settings mid-conversation can invalidate server-side prefix/KV caches.
