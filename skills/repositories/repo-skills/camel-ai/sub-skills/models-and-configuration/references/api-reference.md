# CAMEL Model API Reference

## Core Construction Flow

Most CAMEL chat model work follows this shape:

```python
from camel.configs import ChatGPTConfig
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType

model = ModelFactory.create(
    model_platform=ModelPlatformType.OPENAI,
    model_type=ModelType.GPT_4O_MINI,
    model_config_dict=ChatGPTConfig(temperature=0.2).as_dict(),
    timeout=60,
    max_retries=3,
)
```

`ModelFactory.create()` accepts:

- `model_platform`: `ModelPlatformType` or the enum value string, such as `"openai"`, `"ollama"`, or `"openai-compatible-model"`.
- `model_type`: `ModelType`, a `UnifiedModelType`, or any string. Unknown strings are wrapped as `UnifiedModelType`, which is how local model names such as `"llama3.2"` or hosted catalog names are supported.
- `model_config_dict`: provider request parameters, usually from `ConfigClass(...).as_dict()`.
- `api_key` and `url`: direct overrides for provider credentials and base URL; when omitted many backends look for provider-specific environment variables.
- `token_counter`: optional custom token counter; otherwise CAMEL chooses a provider/default counter where possible.
- `timeout` and `max_retries`: transport controls passed to the backend/client.
- `client` and `async_client`: supported by OpenAI-compatible backends for custom client objects.
- provider-specific `**kwargs`, such as Azure OpenAI deployment/API-version fields or OpenAI-compatible client initialization options.

`BaseModelBackend(model_type, model_config_dict=None, api_key=None, url=None, token_counter=None, timeout=None, max_retries=3)` is the common superclass. Backends expose `run(messages, response_format=None, tools=None)` and `arun(...)`; the public wrappers preprocess `<think>` tags, log request metadata when tracing integrations are enabled, and return chat completion objects or streams depending on config.

## ModelPlatformType and ModelType

`camel.types.ModelPlatformType` is the provider selector. Current factory-backed platforms include OpenAI, Azure OpenAI, Anthropic, Gemini, Mistral, Groq, DeepSeek, Qwen, ZhipuAI, Moonshot, Cohere, Reka, Cerebras, NVIDIA, Together, OpenRouter, OrcaRouter, CometAPI, PPIO, SiliconFlow, ModelScope, WatsonX, Qianfan, Crynux, AIHubMix, AtlasCloud, Avian, AIML, AMD, Volcano, NetMind, MiniMax, SambaNova, AWS Bedrock, AWS Bedrock Converse, LiteLLM, Ollama, vLLM, SGLang, LMStudio, Function Gemma, XAI, OpenAI-compatible, and Stub.

Important enum behavior:

- `ModelPlatformType.DEFAULT` reads `DEFAULT_MODEL_PLATFORM_TYPE`, defaulting to `"openai"`.
- `ModelType.DEFAULT` reads `DEFAULT_MODEL_TYPE`, defaulting to an OpenAI model string.
- `ModelPlatformType.from_name(value)` resolves enum values like `"openai"`; `ModelFactory.create()` also accepts strings and converts them through `ModelPlatformType(value)`.
- `ModelType.STUB` forces the factory to use `StubModel`, which is useful in tests and offline examples.
- `ModelType` includes token-limit and capability metadata for many built-in models, but provider catalog strings are allowed when the enum is behind the service.

Use the bundled `scripts/inspect_model_registry.py` to inspect the exact installed enum and factory map rather than hard-coding a stale provider list.

## ModelFactory Helpers

`ModelFactory.create_from_json(path)` and `ModelFactory.create_from_yaml(path)` load a config file and pass it to `ModelFactory.create()`. The config must include `model_platform`; the loader accepts values such as `"ModelPlatformType.OPENAI"` or `"OPENAI"` and normalizes them to the enum.

A minimal JSON/YAML equivalent is:

```yaml
model_platform: OPENAI
model_type: gpt-4o-mini
model_config_dict:
  temperature: 0.2
  max_tokens: 1000
```

Keep credentials out of config files that may be committed. Prefer environment variables or a runtime secret store.

## ModelManager and ChatAgent Scheduling

`ModelManager(models, scheduling_strategy="round_robin")` wraps one or more `BaseModelBackend` objects and chooses a backend per call. Strategies observed in source/tests are:

- `round_robin`: cycles through models.
- `always_first`: always chooses index 0; on an exception it switches to `round_robin` before re-raising.
- `random_model`: chooses one model randomly.
- custom strategies: use `add_strategy(name, strategy_fn)` on `ModelManager`, or `ChatAgent.add_model_scheduling_strategy(...)` when the manager is inside a `ChatAgent`.

Passing a list of model objects into `ChatAgent(model=[...], scheduling_strategy="random_model")` creates this scheduling behavior at the agent layer. Keep society/agent choreography in `../agents-and-societies/SKILL.md`; use this sub-skill only for selecting/configuring model objects and scheduling policies.

## Structured Output and Schema Conversion

CAMEL supports structured outputs through two related mechanisms:

1. Pass a Pydantic `BaseModel` subclass as `response_format` to `ChatAgent.step(...)`, `BaseModelBackend.run(...)`, or store it in `model_config_dict` where the backend supports it.
2. Use `camel.schemas.OpenAISchemaConverter` to convert free text into a Pydantic model from a `BaseModel`, a function signature, or a JSON-like string template.

Example pattern:

```python
from pydantic import BaseModel

class Student(BaseModel):
    name: str
    age: int

class StudentList(BaseModel):
    students: list[Student]

response = agent.step("Return two students as structured data", response_format=StudentList)
parsed = response.msgs[0].parsed
```

Backend behavior differs:

- OpenAI/OpenAI-compatible backends can use beta parse APIs for Pydantic response formats; some OpenAI-compatible providers fall back to JSON-mode prompting.
- Ollama examples pass `response_format` in `model_config_dict`; structured output requires a sufficiently recent Ollama server/model support.
- Gemini source rejects mixing function tools with `response_format` in the same request.
- DeepSeek thinking mode, Function Gemma, and some provider wrappers impose response-format restrictions.
- `OpenAISchemaConverter` requires OpenAI credentials and calls the OpenAI backend; it is not a local/offline validator.

If parsed output is missing or mismatched, first determine whether the backend returned native parsed data, JSON text, or a provider error. See `references/troubleshooting.md` for debug steps.

## Audio and Multimodal Notes

`camel.models` exports `BaseAudioModel`, `OpenAIAudioModels`, and `FishAudioModel`. OpenAI audio helpers cover text-to-speech, speech-to-text, and audio question answering; they require audio-related provider credentials and optional media packages depending on file/chunking operations.

Multimodal image support is provider-specific. Examples show image inputs for providers such as Mistral and Bedrock Converse; do not assume every `ModelType` accepts `image_list`, data URLs, or audio bytes just because the `ChatAgent` task includes media. Check the backend implementation and provider documentation before sending media.

## Stub and Offline Patterns

For tests, examples, and skills that must avoid provider calls:

- Use `ModelType.STUB` or `camel.models.StubModel` when you need a deterministic no-provider backend.
- Use `scripts/inspect_model_registry.py` for registry/config introspection without backend instantiation.
- Do not call `ModelFactory.create()` for real cloud/local endpoints unless the user supplied credentials or confirmed that the local service is running.
