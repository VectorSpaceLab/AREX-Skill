# Model Configuration

## Provider Config Classes

`camel.configs` exposes Pydantic config classes and API parameter sets for provider request dictionaries. The normal pattern is:

```python
from camel.configs import ChatGPTConfig

model_config_dict = ChatGPTConfig(
    temperature=0.2,
    max_tokens=1000,
    stream=False,
).as_dict()
```

`BaseConfig.as_dict()` removes `None` fields and converts any `FunctionTool` objects in `tools` into OpenAI-style tool schemas. Because `BaseConfig` uses Pydantic with `extra="forbid"`, misspelled provider parameters fail early instead of being silently forwarded.

Common exported config classes include:

| Provider | Config class | Parameter set constant |
| --- | --- | --- |
| OpenAI / compatible defaults | `ChatGPTConfig` | `OPENAI_API_PARAMS` |
| Anthropic | `AnthropicConfig` | `ANTHROPIC_API_PARAMS` |
| Gemini | `GeminiConfig` | `Gemini_API_PARAMS` |
| Mistral | `MistralConfig` | `MISTRAL_API_PARAMS` |
| Groq | `GroqConfig` | `GROQ_API_PARAMS` |
| DeepSeek | `DeepSeekConfig` | `DEEPSEEK_API_PARAMS` |
| Qwen | `QwenConfig` | `QWEN_API_PARAMS` |
| Ollama | `OllamaConfig` | `OLLAMA_API_PARAMS` |
| vLLM | `VLLMConfig` | `VLLM_API_PARAMS` |
| LMStudio | `LMStudioConfig` | `LMSTUDIO_API_PARAMS` |
| SGLang | `SGLangConfig` | `SGLANG_API_PARAMS` |
| LiteLLM | `LiteLLMConfig` | `LITELLM_API_PARAMS` |
| OpenRouter / OrcaRouter | `OpenRouterConfig`, `OrcaRouterConfig` | router-specific constants |
| Bedrock | `BedrockConfig` | `BEDROCK_API_PARAMS` |
| SambaNova | `SambaCloudAPIConfig`, `SambaVerseAPIConfig` | `SAMBA_CLOUD_API_PARAMS`, `SAMBA_VERSE_API_PARAMS` |

Run `python scripts/inspect_model_registry.py --format json` to get the installed list of config classes and parameter constants.

## Common Config Fields

Frequently used fields across OpenAI-like config classes:

- `temperature`, `top_p`: sampling behavior.
- `max_tokens`: output token budget.
- `stream`: stream partial deltas; check structured-output limitations before combining with `response_format`.
- `stop`: string or list of stop sequences.
- `response_format`: either a provider JSON mode dict or a Pydantic `BaseModel` class for backends that support native parsing.
- `tools`, `tool_choice`, `parallel_tool_calls`: tool-calling controls; see sibling `../tools-runtimes-and-services/SKILL.md` for tool authoring.
- `reasoning_effort`: OpenAI reasoning-model option when the selected model supports it.
- `extra_headers` or provider-specific `extra_body`: service-specific extensions.

Keep `api_key`, `url`, `timeout`, `max_retries`, `client`, and `async_client` at `ModelFactory.create()` level unless the backend documentation specifically says otherwise.

## JSON/YAML Factory Configs

`ModelFactory.create_from_json(path)` and `ModelFactory.create_from_yaml(path)` are useful for experiments and reproducible examples. Keep these files free of credentials.

Example YAML:

```yaml
model_platform: OPENAI_COMPATIBLE_MODEL
model_type: local-qwen
model_config_dict:
  temperature: 0.0
  max_tokens: 512
timeout: 120
max_retries: 1
```

The loader normalizes `model_platform`; `model_type` can remain a string. If a config file uses `ModelPlatformType.OPENAI`, the parser strips the enum prefix.

## Optional Extras and Installation

The base `camel-ai` install imports core model abstractions, but some provider backends require optional packages. The project defines at least these relevant extras:

- `camel-ai[model_platforms]`: provider SDKs such as LiteLLM, Mistral, Reka, Anthropic, Cohere, Fish Audio, IBM WatsonX, Boto3, and XAI SDK.
- `camel-ai[huggingface]`: Transformers, Diffusers, Datasets, SoundFile, SafeTensors, SentencePiece, and Hugging Face Hub.
- `camel-ai[media_tools]`: useful for some audio/video file handling paths.
- `camel-ai[all]`: broad install; avoid unless the user intentionally wants every optional surface.

The package metadata allows Python `>=3.10,<3.15`, but several optional dependencies in extras are guarded away on Python 3.13 or newer in project metadata. If a media/document/storage optional import is missing on Python 3.13, check the extra's environment markers before treating it as a CAMEL bug.

## Timeouts, Retries, and Rate Limits

`BaseModelBackend` accepts `timeout` and `max_retries`; OpenAI-compatible models also read `MODEL_TIMEOUT` if `timeout` is omitted. Practical defaults:

- Cloud chat: keep `max_retries=3` unless the provider has strict rate limits.
- Local slow models: increase `timeout`, reduce `max_retries` to avoid repeated long waits.
- Tests/smoke checks: set `max_retries=0` or `1` and use `ModelType.STUB` where possible.
- Rate limit debugging: distinguish HTTP 429 from schema/config errors; do not blindly increase retries if the provider rejects parameters.

## Structured Output Configuration

Two safe patterns:

```python
response = agent.step("Return JSON", response_format=MyPydanticModel)
```

or:

```python
model_config_dict = ChatGPTConfig(
    temperature=0,
    response_format=MyPydanticModel,
).as_dict()
```

Provider differences matter. OpenAI and OpenAI-compatible backends may use parse APIs for Pydantic models. Some providers accept only `{"type": "json_object"}`. Some local servers accept JSON schema, while others only follow prompt instructions. When a provider returns plain JSON text but `response.msgs[0].parsed` is empty, validate manually with `MyPydanticModel.model_validate_json(...)` or switch provider/schema strategy.

## Environment Defaults

Useful environment variables seen in the model stack include:

- `DEFAULT_MODEL_PLATFORM_TYPE` and `DEFAULT_MODEL_TYPE` for enum defaults.
- `OPENAI_COMPATIBILITY_API_KEY` and `OPENAI_COMPATIBILITY_API_BASE_URL` for `OpenAICompatibleModel`.
- `MODEL_TIMEOUT` for OpenAI-compatible default timeout.
- Provider-specific key variables used by individual backends and schema converters, such as `OPENAI_API_KEY` for OpenAI and `OpenAISchemaConverter`.
- `LANGFUSE_ENABLED` and `TRACEROOT_ENABLED` for optional tracing wrappers.

Do not write real key values into skill files, examples, JSON/YAML configs, or logs.
