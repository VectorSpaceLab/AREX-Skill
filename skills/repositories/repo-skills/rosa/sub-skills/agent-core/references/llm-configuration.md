# ROSA model and provider configuration

ROSA does not choose a provider itself. Pass an already-configured LangChain
`BaseChatModel` to `ROSA`; the model must support tool calling because ROSA
builds the agent with LangChain's tool-calling agent constructor.

## Provider choices

| Provider/model | Package status | Runtime prerequisites | Token/streaming notes |
|---|---|---|---|
| `ChatOpenAI` | Included through the base `jpl-rosa` dependencies | A valid OpenAI API key, a reachable service, and a tool-capable model configured through the provider's current API | Supported by ROSA's token callback when non-streaming; streaming requires a model/provider that emits stream chunks. |
| `AzureChatOpenAI` | Included through the base dependencies | Azure endpoint, deployment/model configuration, API version/identity and credentials, plus a reachable Azure service | Also supported by ROSA's token callback when non-streaming; token display is forced off when streaming. |
| `ChatAnthropic` | Optional: `python -m pip install 'jpl-rosa[anthropic]'` | `langchain-anthropic`, an Anthropic API key, reachable service, and a tool-capable model | Provider can be used for invocation/streaming when configured, but ROSA does not report token usage for it. |
| `ChatOllama` | Optional: `python -m pip install 'jpl-rosa[ollama]'` | `langchain-ollama`, a running reachable Ollama service, an installed model that supports tool calling, and the selected base URL/model | Local service availability and model streaming behavior determine whether `astream()` is useful; ROSA does not report token usage for it. |

`jpl-rosa[all]` installs both optional provider integrations. The package's
demo helper uses `LLM_PROVIDER` values `openai`, `anthropic`, and `ollama`, plus
provider-specific model variables and keys, but those are helper conventions,
not ROSA constructor arguments. An invalid helper provider value fails early;
ROSA itself receives only the model object.

## Tool-calling requirement

The public runtime type is broad (`BaseChatModel`), but ordinary chat text is
not enough. LangChain's `create_tool_calling_agent` needs a model that can bind
and emit tool calls in the format expected by the installed LangChain versions.
A custom `BaseChatModel` may therefore pass type checking yet fail during
construction or execution if it lacks compatible tool binding, schemas, or
stream events. Verify this capability with a harmless, deterministic tool
before connecting to live robot operations.

ROSA also applies `.with_config({"streaming": streaming})` to the model. The
provider must tolerate that configuration and must actually support streaming
when `streaming=True` is selected.

## Credentials and services

- Keep API keys, Azure identity details, endpoints, and Ollama URLs out of
  prompts, skill files, logs, and source control.
- Configure provider clients through their supported constructor/environment
  mechanisms before passing them to ROSA. Do not rely on a missing optional
  extra being installed transitively.
- A successful `import rosa` proves only that the base Python package imports;
  it proves neither provider credentials nor a running provider service.
- Model setup is separate from ROS middleware setup. The selected
  `ros_version` still determines which ROS Python modules are needed at ROSA
  construction time.

## Streaming and token usage

Choose one primary mode per instance:

- `streaming=False`: call `invoke()` for a complete string. Set
  `show_token_usage=True` only when the object is a `ChatOpenAI` or
  `AzureChatOpenAI`; ROSA uses the OpenAI callback and prints prompt tokens,
  completion tokens, and total USD cost.
- `streaming=True`: consume `astream()` asynchronously. ROSA forces token
  display off in this mode, regardless of `show_token_usage`, and exposes
  token/tool/final/error events instead of a token-usage report.

Anthropic, Ollama, and other custom model classes can still be used when they
support the required tool-calling and streaming contracts, but ROSA's built-in
token reporting is disabled for them. Do not infer provider billing or usage
from the number of streamed token events.

For detailed lifecycle examples, read [workflows.md](workflows.md). For
construction failures, read [troubleshooting.md](troubleshooting.md).
