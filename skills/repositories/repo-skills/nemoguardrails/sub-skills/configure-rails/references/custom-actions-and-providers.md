# Custom Actions and Providers

Use this reference when you need to add Python actions, inject shared resources, register a custom LLM provider or framework, or register a custom embedding provider/search backend.

## Custom actions

Put actions in `actions.py` or an `actions/` package under the config folder.

```python
from typing import Optional

from nemoguardrails.actions import action

@action()
async def check_input_length(text: str) -> bool:
    return len(text) > 0

@action(is_system_action=True)
async def read_state(context: Optional[dict] = None):
    return context
```

### Decorator options

| Option | Meaning |
| --- | --- |
| `name` | Override the action name used from Colang. |
| `is_system_action` | Force the action to run locally even when an actions server is configured. |
| `execute_async` | Let the action continue in the background in Colang 2.x. |
| `output_mapping` | Convert the action result into an allow/block decision. |

### Action parameters

Actions can declare special parameters and receive them automatically when they run locally.

Common injected parameters:

- `context`
- `events`
- `llm`
- `config`
- `llm_task_manager`
- `state` (Colang 2.x)

Important points:

- Local actions receive injected parameters automatically.
- Remote actions sent through `actions_server_url` do not receive those local-only values unless they are system actions.
- Keep action signatures explicit and typed when possible.

### Actions server note

If you set `actions_server_url`, the runtime can send actions to a remote process. That is useful for scaling or service separation, but it changes which parameters are available locally.

## `config.py` initialization

`config.py` runs during `LLMRails` initialization.

```python
from nemoguardrails import LLMRails

def init(app: LLMRails):
    app.register_action_param("cache", object())
```

Rules:

- `init` must be synchronous.
- Top-level code in `config.py` runs at import time.
- Use `init` for shared resources, shared clients, action parameters, and provider setup that needs the `LLMRails` instance.

Typical use cases:

- open a database or cache client once
- register action parameters used by multiple actions
- choose a framework and provider stack
- register custom embedding search providers

## LLM provider and framework registration

Use the smallest hook that matches the backend shape.

| Backend shape | Best hook |
| --- | --- |
| OpenAI-compatible HTTP endpoint | Use a built-in engine like `openai`, `nim`, or `azure` with `parameters.base_url`; no custom provider needed. |
| LangChain `BaseLLM` / `BaseChatModel` | Set `NEMOGUARDRAILS_LLM_FRAMEWORK=langchain` and register the provider with the LangChain helpers (`register_llm_provider` / `register_chat_provider`). |
| Non-OpenAI backend you control directly | Implement the `LLMModel` contract and register it as a provider. |
| Replace the whole LLM stack | Register a custom framework and make it the default. |

### Provider registration

A provider is the class that constructs a model for an `engine:` name in `config.yml`.

```python
from nemoguardrails import register_provider, set_default_framework

class MyModel:
    ...

register_provider("my_engine", MyModel)
```

Use provider registration when you want a new engine name but the surrounding framework is still fine.

### Framework registration

Use a custom framework only when you need to replace how models are created, cached, and reset across the whole process.

```python
from nemoguardrails import register_framework, set_default_framework

register_framework("my_framework", framework_instance)
set_default_framework("my_framework")
```

A custom framework is rare; most tasks only need a provider.

## Custom embedding providers

There are two related extension points for embeddings:

1. **Embedding model providers** — build vector embeddings for model types such as `embeddings`.
2. **Embedding search providers** — store and search the vectors used by the knowledge base and canonical-form matching.

### Embedding model provider

Register a custom embedding model in `config.py`.

```python
from nemoguardrails import LLMRails


def init(app: LLMRails):
    app.register_embedding_provider(MyEmbeddingModel, "my_embedding_engine")
```

Then use it in `config.yml`:

```yaml
models:
  - type: embeddings
    engine: my_embedding_engine
    model: my-embedding-model
```

### Embedding search provider

Use `register_embedding_search_provider()` when you want a custom index or vector search backend.

```python
from nemoguardrails import LLMRails


def init(app: LLMRails):
    app.register_embedding_search_provider("my_search", MyEmbeddingSearchProvider)
```

Then select it in `config.yml`:

```yaml
core:
  embedding_search_provider:
    name: my_search
```

## Practical registration order

A safe order for a config folder is:

1. Declare models, rails, and prompts in `config.yml`.
2. Put action functions in `actions.py` or `actions/`.
3. Put shared resource setup and provider registration in `config.py`.
4. Load the config with `RailsConfig.from_path()`.
5. Instantiate `LLMRails` to trigger action loading, `config.py`, and provider setup.

## What not to use custom hooks for

- Do not use custom providers when a built-in OpenAI-compatible engine already fits.
- Do not add a custom framework just to wrap one backend unless the whole model stack needs replacement.
- Do not rely on a remote actions server for parameters that only exist locally.
- Do not make `init` async; the runtime will not await it.
