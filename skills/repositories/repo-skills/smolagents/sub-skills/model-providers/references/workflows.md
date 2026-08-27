# Model Provider Workflows

## Choose a Wrapper

1. If the user names a specific hosted provider, prefer that provider's first-class wrapper when available: Hugging Face providers use `InferenceClientModel`, Azure uses `AzureOpenAIModel`, Bedrock uses `AmazonBedrockModel`.
2. If the endpoint claims OpenAI chat-completions compatibility, use `OpenAIModel` unless LiteLLM-specific routing, provider translation, or Ollama integration is required.
3. If the user asks for many providers, fallback, or load balancing, use `LiteLLMModel` or `LiteLLMRouterModel`.
4. If the model must run inside the Python process, choose `TransformersModel`, `MLXModel`, or `VLLMModel` based on hardware and required features.
5. If none of the wrappers match, subclass `Model` and return `ChatMessage` objects.

## Credential Setup

Use environment variables or SDK default credential chains. Do not hardcode tokens in reusable code.

```python
import os
from smolagents import InferenceClientModel, OpenAIModel

hf_model = InferenceClientModel(
    model_id="Qwen/Qwen3-Next-80B-A3B-Thinking",
    provider="nebius",
    token=os.getenv("HF_TOKEN"),
)

openai_model = OpenAIModel(
    model_id="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY"),
)
```

For Azure, prefer the OpenAI Azure client's conventional names:

```python
import os
from smolagents import AzureOpenAIModel

model = AzureOpenAIModel(
    model_id=os.getenv("AZURE_OPENAI_MODEL"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("OPENAI_API_VERSION"),
)
```

For Bedrock, prefer AWS SDK configuration outside code:

```python
from smolagents import AmazonBedrockModel

model = AmazonBedrockModel(
    model_id="us.amazon.nova-pro-v1:0",
    client_kwargs={"region_name": "us-west-2"},
)
```

## OpenAI-Compatible Endpoints

Use `OpenAIModel` when a server implements OpenAI chat completions. Check all three pieces before debugging the agent:

- `api_base`: exact server base URL, often ending with `/v1`.
- `model_id`: server-side model or deployment name, not always a public model slug.
- `api_key`: provider key, placeholder key for local servers that require a non-empty value, or omitted only if the client/server permits it.

Examples:

```python
from smolagents import OpenAIModel

openrouter = OpenAIModel(
    model_id="openai/gpt-4o",
    api_base="https://openrouter.ai/api/v1",
    api_key="...",
)

gemini = OpenAIModel(
    model_id="gemini-2.0-flash",
    api_base="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key="...",
)
```

## LiteLLM and Router

Use plain LiteLLM for provider fan-out through a single model string:

```python
from smolagents import LiteLLMModel

model = LiteLLMModel(
    model_id="anthropic/claude-3-5-sonnet-latest",
    api_key="...",
    temperature=0.2,
    max_tokens=1024,
)
```

Use `LiteLLMRouterModel` when requests should route across deployments:

```python
import os
from smolagents import LiteLLMRouterModel

model = LiteLLMRouterModel(
    model_id="agent-primary",
    model_list=[
        {
            "model_name": "agent-primary",
            "litellm_params": {
                "model": "gpt-4o-mini",
                "api_key": os.getenv("OPENAI_API_KEY"),
            },
        },
        {
            "model_name": "agent-primary",
            "litellm_params": {
                "model": "bedrock/anthropic.claude-3-sonnet-20240229-v1:0",
                "aws_region_name": os.getenv("AWS_REGION"),
            },
        },
    ],
    client_kwargs={"routing_strategy": "simple-shuffle"},
)
```

## Local Model Setup

Transformers:

```python
from smolagents import TransformersModel

model = TransformersModel(
    model_id="HuggingFaceTB/SmolLM2-1.7B-Instruct",
    device_map="auto",
    torch_dtype="auto",
    max_new_tokens=1024,
)
```

MLX on Apple Silicon:

```python
from smolagents import MLXModel

model = MLXModel(
    model_id="mlx-community/Qwen2.5-Coder-32B-Instruct-4bit",
    max_tokens=4096,
)
```

vLLM in-process:

```python
from smolagents import VLLMModel

model = VLLMModel(
    model_id="HuggingFaceTB/SmolLM-135M-Instruct",
    model_kwargs={"max_model_len": 8192},
    max_tokens=2048,
)
```

For a vLLM server, use `OpenAIModel` instead of loading vLLM in the agent process.

## Attach to Agents

Model selection is independent of agent type:

```python
from smolagents import CodeAgent, ToolCallingAgent

code_agent = CodeAgent(tools=[...], model=model, stream_outputs=True)
tool_agent = ToolCallingAgent(tools=[...], model=model, max_tool_threads=4)
```

Route planning intervals, managed agents, structured internal outputs, final answer checks, and executor choices to the agent-workflows and execution-and-safety sub-skills.

## Streaming and Usage

- API wrappers implement streaming methods that yield deltas and token-usage events when the upstream SDK supplies usage.
- `CodeAgent(stream_outputs=True)` streams model output through the agent loop; this can expose provider incompatibilities earlier than non-streaming runs.
- Some providers stream content but not tool-call deltas or usage; test streaming separately from non-streaming when changing providers.
- Local Transformers streaming uses a background generation thread and token-by-token deltas.

## Token and Parameter Hygiene

- Set `max_tokens` or `max_new_tokens` explicitly for agent tasks; provider defaults are often too small.
- Use `REMOVE_PARAMETER` for providers that reject `stop` or other defaults.
- Keep `temperature` low for deterministic tool use and code generation.
- Increase local context settings such as Ollama `num_ctx` or vLLM `max_model_len` before blaming prompt logic.
