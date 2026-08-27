# Provider and Model Reference

## Core concepts

Upsonic uses `provider/model` identifiers and lazy provider inference to keep the agent runtime agnostic to the backing API client.

| Surface | Verified behavior |
| --- | --- |
| `infer_provider(provider)` | Returns a provider instance for names such as `openai`, `anthropic`, `google-gla`, `google-vertex`, `bedrock`, `groq`, `openrouter`, `vercel`, `ollama`, `lmstudio`, `together`, `xai`, `deepseek`, and others in the provider registry. `gateway/...` prefixes are normalized to gateway-backed providers. |
| `infer_model(model)` | Accepts either a `Model` instance or a string. It normalizes shorthand model ids, infers the provider, and can be overridden by environment variables such as `LLM_MODEL_KEY` or `LLM_CUSTOM_PROVIDER`. |
| `ModelProfile` | Captures model capability hints such as tool support, JSON schema output support, image output support, and the default structured-output mode. |
| `ModelProfile.from_dict()` | Rehydrates profiles from plain dictionaries, including known json-schema transformer names. |

## Typical selection flow

```python
from upsonic import Agent

agent = Agent(model="anthropic/claude-sonnet-4-6")
```

```python
from upsonic.models import infer_model

model = infer_model("openai/gpt-4o")
```

## Selection notes

- Prefer `provider/model` strings in public guidance; bare model names are deprecated and only kept for compatibility.
- Use `gateway/...` when the request explicitly wants the gateway/provider routing layer.
- Use `ModelProfile` knowledge when the model supports different structured-output modes or tool behavior.
- Provider credentials belong in the environment, not in the skill tree.
