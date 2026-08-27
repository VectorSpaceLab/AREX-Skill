# Model API Reference

All smolagents model wrappers are callable: `model(messages, stop_sequences=..., tools_to_call_from=..., response_format=...)` delegates to `generate`. Agent classes receive an already constructed model through their `model=` argument.

## Base `Model`

Signature:

```python
Model(flatten_messages_as_text=False, tool_name_key="name", tool_arguments_key="arguments", model_id=None, **kwargs)
```

Behavior:

- Subclasses implement `generate(...) -> ChatMessage`.
- `**kwargs` become model-level defaults and override call-time kwargs during `_prepare_completion_kwargs`.
- `REMOVE_PARAMETER` as a model kwarg removes that parameter from completion kwargs.
- `stop_sequences` is passed as `stop` only when `supports_stop_parameter` is true; unsupported model families are post-trimmed when wrappers implement that fallback.
- `to_dict()` exports non-secret config but intentionally omits `token` and `api_key`.

Custom subclass minimum shape:

```python
from smolagents import ChatMessage, Model

class MyModel(Model):
    def generate(self, messages, stop_sequences=None, response_format=None, tools_to_call_from=None, **kwargs):
        return ChatMessage(role="assistant", content="result")
```

If an API returns tool calls embedded as text, set `tool_name_key` and `tool_arguments_key` so `parse_tool_calls` can extract arguments.

## API Base Class

`ApiModel(model_id, custom_role_conversions=None, client=None, requests_per_minute=None, retry=True, **kwargs)` underpins hosted wrappers.

- `requests_per_minute` throttles before requests.
- `retry=True` retries rate-limit-like failures with exponential backoff.
- `client` can inject a prebuilt client for tests or advanced SDK configuration.
- `custom_role_conversions` is applied while normalizing smolagents `ChatMessage` objects.

## `InferenceClientModel`

Signature:

```python
InferenceClientModel(
    model_id="Qwen/Qwen3-Next-80B-A3B-Thinking",
    provider=None,
    token=None,
    timeout=120,
    client_kwargs=None,
    custom_role_conversions=None,
    api_key=None,
    bill_to=None,
    base_url=None,
    **kwargs,
)
```

Use for Hugging Face Inference Providers and HF InferenceClient-compatible endpoints.

- Pass either `token` or `api_key`, not both; `api_key` is an alias for `token`.
- If no token is passed, the wrapper reads `HF_TOKEN` and then Hugging Face CLI credentials.
- `provider=None` allows automatic provider choice; set `provider` for deterministic provider routing.
- `base_url` targets a specific endpoint and bypasses provider selection.
- Structured outputs are limited to providers declared by smolagents as structured-generation capable (`cerebras`, `fireworks-ai`).

## `LiteLLMModel`

Signature:

```python
LiteLLMModel(
    model_id=None,
    api_base=None,
    api_key=None,
    custom_role_conversions=None,
    flatten_messages_as_text=None,
    **kwargs,
)
```

Use for LiteLLM-supported providers and local endpoints like Ollama.

- Install `smolagents[litellm]`.
- `model_id` follows LiteLLM naming, such as `anthropic/claude-...`, `groq/...`, or `ollama_chat/...`.
- `model_id` currently has a fallback default but is expected to become required; always pass it explicitly.
- `flatten_messages_as_text` defaults to `True` for IDs beginning with `ollama`, `groq`, or `cerebras`.
- `api_base`, `api_key`, and arbitrary provider kwargs are forwarded to `litellm.completion`.

## `LiteLLMRouterModel`

Signature:

```python
LiteLLMRouterModel(
    model_id,
    model_list,
    client_kwargs=None,
    custom_role_conversions=None,
    flatten_messages_as_text=None,
    **kwargs,
)
```

Use for LiteLLM Router load balancing and fallback strategies.

- `model_id` is the logical model group used at completion time.
- `model_list` entries must include `model_name` and `litellm_params` recognized by LiteLLM Router.
- `client_kwargs` are passed to `litellm.router.Router`, e.g. routing strategy settings.

## `OpenAIModel`

Signature:

```python
OpenAIModel(
    model_id,
    api_base=None,
    api_key=None,
    organization=None,
    project=None,
    client_kwargs=None,
    custom_role_conversions=None,
    flatten_messages_as_text=False,
    **kwargs,
)
```

Use for OpenAI and OpenAI-compatible chat-completions servers.

- Install `smolagents[openai]`.
- `api_base` is forwarded to the OpenAI client as `base_url`; use the provider's exact OpenAI-compatible base, commonly ending in `/v1`.
- `organization`, `project`, and `client_kwargs` are OpenAI client configuration, not completion kwargs.
- Completion kwargs like `temperature`, `max_tokens`, `top_p`, and `stop=REMOVE_PARAMETER` go in `**kwargs`.
- `OpenAIServerModel` is an alias of `OpenAIModel`.

## `AzureOpenAIModel`

Signature:

```python
AzureOpenAIModel(
    model_id,
    azure_endpoint=None,
    api_key=None,
    api_version=None,
    client_kwargs=None,
    custom_role_conversions=None,
    **kwargs,
)
```

Use for Azure OpenAI deployments.

- Install `smolagents[openai]`.
- `model_id` is the Azure deployment name.
- If omitted, the underlying OpenAI Azure client can use `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, and `OPENAI_API_VERSION`.
- `AzureOpenAIServerModel` is an alias of `AzureOpenAIModel`.

## `AmazonBedrockModel`

Signature:

```python
AmazonBedrockModel(model_id, client=None, client_kwargs=None, custom_role_conversions=None, **kwargs)
```

Use for AWS Bedrock Runtime `converse` calls.

- Install `smolagents[bedrock]`.
- Uses `boto3.client("bedrock-runtime", **client_kwargs)` unless a client is provided.
- Authentication comes from the AWS credential chain or supported Bedrock bearer-token environment configuration.
- Default role conversions map `system`, `assistant`, `tool-call`, and `tool-response` to `user` for broader Bedrock compatibility.
- Bedrock-specific inference and guardrail config can be passed through `**kwargs`.
- `response_format` is not supported.

## `TransformersModel`

Signature:

```python
TransformersModel(
    model_id=None,
    device_map=None,
    torch_dtype=None,
    trust_remote_code=False,
    model_kwargs=None,
    max_new_tokens=4096,
    max_tokens=None,
    apply_chat_template_kwargs=None,
    **kwargs,
)
```

Use for local Hugging Face Transformers execution.

- Install `smolagents[transformers]`.
- `max_tokens` aliases and takes precedence over `max_new_tokens`.
- `device_map` defaults to CUDA when available, else CPU.
- The wrapper first tries image-text loading, then causal LM loading when the config is not vision-language.
- `model_kwargs` are passed to `from_pretrained`; generation kwargs are stored in `**kwargs`.
- Structured outputs are not supported; use `VLLMModel` when local structured generation is required.

## `MLXModel`

Signature shape:

```python
MLXModel(model_id, trust_remote_code=False, load_kwargs=None, apply_chat_template_kwargs=None, **kwargs)
```

Use for Apple Silicon MLX local inference.

- Install `smolagents[mlx-lm]`.
- `load_kwargs` are passed to `mlx_lm.load`; tokenizer config receives `trust_remote_code`.
- Messages are flattened to text; vision and structured outputs are not supported.
- Generation kwargs such as `max_tokens` are forwarded to `mlx_lm.stream_generate`.

## `VLLMModel`

Signature shape:

```python
VLLMModel(model_id, model_kwargs=None, apply_chat_template_kwargs=None, **kwargs)
```

Use for in-process vLLM execution.

- Install `smolagents[vllm]`.
- `model_kwargs` configure `vllm.LLM(model=model_id, ...)`.
- Generation kwargs configure `SamplingParams`; default temperature is `0.0`, default `max_tokens` is `2048` unless overridden.
- Structured outputs are mapped from smolagents/OpenAI-style response format into vLLM structured output params.
- Call `cleanup()` in long-running processes when disposing an in-process vLLM engine.
