---
name: model-providers
description: "Select and configure smolagents Model wrappers for Hugging Face
  Inference Providers, LiteLLM, OpenAI-compatible APIs, Azure OpenAI, Amazon
  Bedrock, local Transformers/MLX/vLLM, and custom Model subclasses without
  hardcoding credentials."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Model Providers

Use this sub-skill when a task needs to choose, configure, debug, or serialize a `smolagents` model object. Agent loop design belongs in `../agent-workflows/SKILL.md`; tool schemas and integrations belong in `../tools-and-integrations/SKILL.md`; CLI model flags belong in `../cli-and-ui/SKILL.md`; sandbox and executor choices belong in `../execution-and-safety/SKILL.md`.

## Fast Routing

1. Identify the runtime: hosted API, OpenAI-compatible endpoint, Azure, Bedrock, local GPU/Apple/vLLM, or a custom adapter.
2. Pick the wrapper from `references/provider-matrix.md` and install only the optional extra it needs.
3. Read constructor details in `references/api-reference.md`, especially credential parameters and role/message formatting knobs.
4. Follow setup patterns in `references/workflows.md` for environment variables, token limits, streaming, and agent attachment.
5. If the config fails before generation, use `references/troubleshooting.md` and `scripts/check_model_config.py` before making live provider calls.

## Common Patterns

```python
import os
from smolagents import CodeAgent, InferenceClientModel

model = InferenceClientModel(
    model_id="Qwen/Qwen3-Next-80B-A3B-Thinking",
    provider="together",
    token=os.getenv("HF_TOKEN"),
    max_tokens=2048,
)
agent = CodeAgent(tools=[], model=model)
```

```python
import os
from smolagents import OpenAIModel

model = OpenAIModel(
    model_id="gpt-4o-mini",
    api_base="https://api.openai.com/v1",
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0.2,
)
```

For provider-specific unsupported parameters, pass the sentinel from `smolagents.models`:

```python
from smolagents import LiteLLMModel, REMOVE_PARAMETER

model = LiteLLMModel(model_id="xai/grok-4", api_key="...", stop=REMOVE_PARAMETER)
```

## Local Validation Helper

Run the bundled helper against a JSON or YAML model config before wiring it into an agent:

```bash
python sub-skills/model-providers/scripts/check_model_config.py model-config.json
```

The helper validates shape, class-specific fields, credential source references, and optional-extra hints. It does not import provider SDKs, instantiate smolagents classes, read secret values, or call network APIs.

## References

- `references/provider-matrix.md` maps providers and deployment styles to wrappers, extras, credentials, and caveats.
- `references/api-reference.md` records constructor signatures and behavior notes.
- `references/workflows.md` shows selection, environment, streaming, and custom model workflows.
- `references/troubleshooting.md` covers optional imports, credentials, endpoint URLs, local memory/device failures, token limits, streaming, and custom return formatting.
