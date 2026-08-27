# Model Provider Troubleshooting

## Missing Optional Extras

Symptoms:

- `ModuleNotFoundError` mentioning `litellm`, `openai`, `boto3`, `transformers`, `torch`, `mlx_lm`, or `vllm`.
- Error text says to install an extra such as `smolagents[openai]`.

Fix:

- `LiteLLMModel` and `LiteLLMRouterModel`: install `smolagents[litellm]`.
- `OpenAIModel` and `AzureOpenAIModel`: install `smolagents[openai]`.
- `AmazonBedrockModel`: install `smolagents[bedrock]`.
- `TransformersModel`: install `smolagents[transformers]`.
- `MLXModel`: install `smolagents[mlx-lm]`.
- `VLLMModel`: install `smolagents[vllm]`.

## Absent or Misrouted Credentials

Symptoms:

- Authentication errors, unauthorized errors, or provider messages about missing keys.
- Hugging Face gated model failures despite a token being present.
- Bedrock region or credential-chain errors.

Fix:

- Keep credentials in environment variables or SDK credential stores; pass `os.getenv(...)` values into constructors when explicit wiring is clearer.
- `InferenceClientModel` accepts `token` or `api_key`, but not both. If neither is passed, it tries `HF_TOKEN` and then Hugging Face CLI credentials.
- Hugging Face gated models require token permissions for both inference calls and gated repository read access.
- Azure uses `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, and `OPENAI_API_VERSION` when constructor values are omitted.
- Bedrock uses the AWS credential chain unless using supported Bedrock bearer-token authentication.

## Wrong Provider or Model ID

Symptoms:

- Provider says model is unknown.
- LiteLLM routes to an unexpected vendor.
- Azure returns deployment-not-found.

Fix:

- For `InferenceClientModel`, `model_id` is a Hugging Face model ID or endpoint model; `provider` is a Hugging Face Inference Provider name. Set both intentionally.
- For `LiteLLMModel`, `model_id` must follow LiteLLM provider prefixes.
- For `LiteLLMRouterModel`, `model_id` must match the `model_name` group in `model_list`.
- For `AzureOpenAIModel`, `model_id` is the Azure deployment name, not necessarily the base model name.
- For Bedrock, use the exact Bedrock model ID for the selected region.

## OpenAI-Compatible Base URL Mistakes

Symptoms:

- 404 on `/chat/completions`.
- Client points to the wrong host or double-appends `/v1`.
- Local server works with curl but not through smolagents.

Fix:

- Use `OpenAIModel(api_base=...)`, not `InferenceClientModel`, for OpenAI-compatible servers.
- Confirm whether the provider wants a base ending in `/v1`, `/openai`, or another compatibility path.
- Keep `model_id` equal to the server's advertised model/deployment name.
- For local servers that require a key syntactically, pass a harmless non-secret placeholder only if the server docs require it.

## Role and Message Formatting Failures

Symptoms:

- Provider rejects `system`, `tool`, or multi-part content messages.
- Tool calls are returned as JSON text rather than structured tool-call objects.
- Vision inputs fail with text-only local wrappers.

Fix:

- Use `custom_role_conversions` to map unsupported roles to `user` or `assistant`.
- Use `flatten_messages_as_text=True` for providers/templates that cannot accept multi-part content.
- For custom models returning text-encoded tool calls, set `tool_name_key` and `tool_arguments_key` and return content parseable by `parse_tool_calls`.
- Do not expect `MLXModel` or `VLLMModel` wrapper vision support; use a compatible API or Transformers vision-language path when needed.

## Local Memory and Device Failures

Symptoms:

- CUDA out-of-memory or process killed during construction.
- `TransformersModel` chooses CPU and generation is too slow.
- vLLM engine initialization fails before the agent starts.

Fix:

- Choose a smaller or quantized model.
- Set `device_map="auto"`, an explicit `torch_dtype`, or model-specific `model_kwargs`.
- Reduce context length (`max_model_len`, `num_ctx`) or generation length (`max_tokens`, `max_new_tokens`).
- Prefer an external OpenAI-compatible server with `OpenAIModel` when model loading should be isolated from the agent process.
- On long-running vLLM processes, call `cleanup()` when disposing the in-process engine.

## Token Limits and Stop Parameters

Symptoms:

- Agent truncates code, final answers, or JSON.
- Provider rejects `stop` or ignores stop sequences.
- Reasoning models fail with unsupported parameter errors.

Fix:

- Set generation length explicitly: `max_tokens` for API providers, `max_new_tokens` for Transformers, or provider-specific context settings.
- Import and pass `REMOVE_PARAMETER` for rejected kwargs, for example `stop=REMOVE_PARAMETER`.
- Some model families do not support stop parameters; smolagents avoids or post-trims stop sequences where possible.
- Increase context for local/Ollama/vLLM deployments before changing agent prompts.

## Streaming Incompatibility

Symptoms:

- Non-streaming works but `stream_outputs=True` fails.
- Tool-call deltas are incomplete.
- Token usage is missing or arrives as a separate empty-content event.

Fix:

- Reproduce with direct `model.generate_stream(...)` before debugging the agent.
- Disable streaming for providers that cannot stream tool-call deltas reliably.
- Check whether the provider supports `stream_options={"include_usage": True}`; missing usage is not always fatal.
- For custom subclasses, implement `generate` first and add streaming only when required by the task.

## Custom Model Return Formatting

Symptoms:

- Agent crashes because response has no `.content`.
- ToolCallingAgent cannot find tool calls.
- Final output is a raw provider object rather than a smolagents message.

Fix:

- Return `smolagents.ChatMessage(role="assistant", content=...)` from `generate`.
- Include `tool_calls` in the returned `ChatMessage` when your backend supports structured tool calls.
- If the backend returns text JSON for tool calls, make content match the configured `tool_name_key` and `tool_arguments_key`.
- Preserve token usage only when available; absence of usage should not block a custom wrapper.
