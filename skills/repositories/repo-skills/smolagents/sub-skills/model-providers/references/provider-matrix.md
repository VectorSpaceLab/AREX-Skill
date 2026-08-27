# Provider Matrix

## Hosted and API Providers

| Use case | Wrapper | Install extra | Key fields | Credential source | Notes |
| --- | --- | --- | --- | --- | --- |
| Hugging Face Inference Providers | `InferenceClientModel` | base package uses `huggingface_hub` | `model_id`, `provider`, `token`/`api_key`, `timeout`, `bill_to` | `HF_TOKEN`, Hugging Face CLI token, or explicit `token`/`api_key` | `provider=None` lets Hugging Face choose; specify providers like `together`, `nebius`, `novita`, `hyperbolic`, `fireworks-ai`, `cerebras` when predictable routing matters. |
| Dedicated HF endpoint or local HF-compatible URL | `InferenceClientModel` | base package | `base_url`, optional `token`, `timeout` | Endpoint-specific token or none for trusted local endpoints | When `base_url` is set, provider selection is not used. Avoid passing conflicting endpoint/model assumptions. |
| Many commercial providers via LiteLLM | `LiteLLMModel` | `smolagents[litellm]` | `model_id`, `api_base`, `api_key`, provider kwargs | Provider env vars recognized by LiteLLM or explicit `api_key` | Prefix model IDs as LiteLLM expects, e.g. `anthropic/...`, `groq/...`, `cerebras/...`, `ollama_chat/...`. |
| LiteLLM routing/load balancing | `LiteLLMRouterModel` | `smolagents[litellm]` | `model_id`, `model_list`, `client_kwargs` | Per-route `litellm_params` | `model_id` is the model group name; `model_list[].model_name` must match it for selected deployments. |
| OpenAI API | `OpenAIModel` | `smolagents[openai]` | `model_id`, `api_base`, `api_key`, `organization`, `project` | `OPENAI_API_KEY` via explicit `os.getenv` or OpenAI client defaults | Uses `openai.OpenAI(...).chat.completions.create`. `api_base` defaults to the OpenAI client default if omitted. |
| OpenAI-compatible servers | `OpenAIModel` | `smolagents[openai]` | `model_id`, `api_base`, `api_key`, `client_kwargs` | Server-specific token env var | Works for OpenRouter, Gemini OpenAI-compatible API, vLLM server, LM Studio, and similar servers if the endpoint implements chat completions. Use the server's `/v1`-style base URL. |
| Azure OpenAI | `AzureOpenAIModel` | `smolagents[openai]` | `model_id`, `azure_endpoint`, `api_key`, `api_version` | `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `OPENAI_API_VERSION` | `model_id` is the Azure deployment name, not necessarily the public model family name. |
| Amazon Bedrock | `AmazonBedrockModel` | `smolagents[bedrock]` | `model_id`, `client`, `client_kwargs`, Bedrock inference kwargs | AWS credential chain or `AWS_BEARER_TOKEN_BEDROCK` for supported boto3 versions | Defaults role conversion toward `user` because many Bedrock models reject `system`/tool roles. |

## Local Model Providers

| Use case | Wrapper | Install extra | Key fields | Hardware notes | Caveats |
| --- | --- | --- | --- | --- | --- |
| Local Transformers text or vision-language model | `TransformersModel` | `smolagents[transformers]` | `model_id`, `device_map`, `torch_dtype`, `trust_remote_code`, `model_kwargs`, `max_new_tokens`/`max_tokens` | Defaults to CUDA when available, otherwise CPU | Loads model and tokenizer/processors eagerly; memory failures happen at construction. Structured outputs are not supported. |
| Apple Silicon MLX local model | `MLXModel` | `smolagents[mlx-lm]` | `model_id`, `trust_remote_code`, `load_kwargs`, `apply_chat_template_kwargs`, generation kwargs | Intended for macOS Apple Silicon | Flattens messages as text and does not support vision or structured outputs. |
| Local vLLM in-process engine | `VLLMModel` | `smolagents[vllm]` | `model_id`, `model_kwargs`, `apply_chat_template_kwargs`, sampling kwargs | GPU memory and vLLM engine constraints apply | Supports structured outputs by translating schema to vLLM structured output params. No vision support in this wrapper. |
| OpenAI-compatible vLLM server | `OpenAIModel` | `smolagents[openai]` | `model_id`, `api_base`, optional `api_key` | Server owns model loading | Prefer this over in-process `VLLMModel` when the model is already served externally. |
| Ollama chat endpoint through LiteLLM | `LiteLLMModel` | `smolagents[litellm]` | `model_id="ollama_chat/..."`, `api_base`, `api_key`, `num_ctx` | Local Ollama manages model memory | Increase context (`num_ctx`) for agent tasks; LiteLLM defaults may be too small. |

## Formatting and Compatibility Knobs

- `custom_role_conversions` maps smolagents roles to provider-supported roles, e.g. convert `system` to `user` for APIs that reject system messages.
- `flatten_messages_as_text` collapses list-style message content into text. `LiteLLMModel` defaults it to `True` for model IDs starting with `ollama`, `groq`, or `cerebras`; `OpenAIModel` defaults `False`; `MLXModel` forces text flattening.
- `convert_images_to_image_urls` is handled internally by API models that support image URL payloads; local wrappers choose formatting based on tokenizer/processor support.
- `REMOVE_PARAMETER` removes a kwarg during completion preparation, useful when a provider rejects `stop`, `tool_choice`, or other default parameters.
- `requests_per_minute` and `retry` are inherited by API-based models through `ApiModel`; use them for rate-limit safety without adding custom retry loops.
