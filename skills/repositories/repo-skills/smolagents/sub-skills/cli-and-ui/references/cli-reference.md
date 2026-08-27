# CLI Reference

## `smolagent`

`smolagent` maps to `smolagents.cli:main`. It loads environment variables from `.env`, builds a model, resolves requested tools, creates an agent, then calls `agent.run(prompt)`.

### Positional Prompt

```bash
smolagent "How many seconds would it take for a leopard at full speed to run through Pont des Arts?"
```

- If a prompt is provided, the CLI runs non-interactively.
- If no prompt is provided, interactive mode starts and asks for configuration step by step.

### Main Flags

| Flag | Default | Meaning |
| --- | --- | --- |
| `--model-type` | `InferenceClientModel` | One of the supported model loader names. Non-interactive help mentions `InferenceClientModel`, `OpenAIModel`, `LiteLLMModel`, and `TransformersModel`. Interactive choices include `InferenceClientModel`, `OpenAIServerModel`, `LiteLLMModel`, and `TransformersModel`; check installed-version help before relying on aliases. |
| `--model-id` | `Qwen/Qwen3-Next-80B-A3B-Thinking` | Model identifier passed to the selected model class. |
| `--action-type` | `code` | `code` creates `CodeAgent`; `tool_calling` creates `ToolCallingAgent`. Other values raise `Unsupported action type`. |
| `--tools` | `web_search` | Space-separated default tool names or Hugging Face Space IDs containing `/`. Unknown names raise a tool recognition error. |
| `--imports` | empty list | Space-separated module names authorized for the `CodeAgent` local Python executor. Applies to `CodeAgent`; not used by `ToolCallingAgent`. |
| `--verbosity-level` | `1` | Parsed by the CLI but current non-interactive construction does not pass it through to the agent. Use Python construction if exact verbosity is required. |
| `--provider` | `None` | Provider passed to `InferenceClientModel`. |
| `--api-base` | unset | Base URL passed to API-backed models when supported. |
| `--api-key` | unset | API key passed to model construction; may override environment defaults. |

### Model Loader Behavior

- `InferenceClientModel` receives `model_id`, `provider`, and token from `--api-key` or `HF_API_KEY`.
- `OpenAIModel` uses `--api-key` or `FIREWORKS_API_KEY`, defaulting `api_base` to `https://api.fireworks.ai/inference/v1` if none is supplied.
- `LiteLLMModel` receives `model_id`, `api_key`, and `api_base`.
- `TransformersModel` loads local transformers with `device_map="auto"`; this can be heavy and should be routed through model/environment setup guidance.
- Unsupported model type names raise `ValueError: Unsupported model type: ...`.

### Tool Resolution

- Built-in tool names are looked up in the package default tool mapping.
- Tool strings containing `/` are treated as Hugging Face Space IDs and loaded with `Tool.from_space(...)`; the generated tool name is the final path segment lowercased with `-` and `.` converted to `_`.
- Unknown non-Space names raise `ValueError: Tool ... is not recognized either as a default tool or a Space.`

### Interactive Mode

Run:

```bash
smolagent
```

The wizard displays available default tools, accepts space-separated tool names, asks for model type and model ID, optionally collects provider/API/import settings, and finally asks for the task prompt. Use this for exploration, not for reproducible scripts; for automation, prefer explicit flags.

## `webagent`

`webagent` maps to `smolagents.vision_web_browser:main`. It is a specialized browser automation demo, not the general way to add web tools to an agent.

### Main Flags

| Flag | Default | Meaning |
| --- | --- | --- |
| positional `prompt` | a Wikipedia browser-search task | Browser automation objective. |
| `--model-type` | `LiteLLMModel` | Passed to the same model loader used by `smolagent`. |
| `--model-id` | `gpt-4o` | Model identifier; use a model capable of interpreting screenshots for difficult pages. |
| `--provider` | unset | Provider for compatible model loaders. |
| `--api-base` | unset | API base for compatible model loaders. |
| `--api-key` | unset | API key for compatible model loaders. |

### Runtime Behavior

`webagent` starts Chrome through Helium/Selenium with a visible browser window, defines browser tools (`go_back`, `close_popups`, `search_item_ctrl_f`), adds screenshot callbacks to the agent memory, authorizes the `helium` import, primes the Python executor with `from helium import *`, and appends browser-use instructions to the prompt.

### When To Prefer Python Code

Prefer explicit Python construction over `webagent` when you need headless browser options, custom Chrome flags, extra web tools, authentication handling, non-Chrome drivers, custom screenshot retention, or strict lifecycle control for the browser process.
