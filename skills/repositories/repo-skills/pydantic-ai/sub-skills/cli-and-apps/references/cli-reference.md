# CLI Reference

This reference covers installed command-line and local web UI surfaces for Pydantic AI. Commands here use installed packages and do not require an original source checkout.

## Installation Choices

- `pip install clai` or `uv tool install clai` installs the standalone CLI package and the `clai` console command.
- `pip install "pydantic-ai-slim[cli]"` installs the slim package plus terminal dependencies used by the legacy `pai` entry point and `python -m pydantic_ai`.
- `pip install "pydantic-ai-slim[web]"` installs Starlette, HTTPX, and Uvicorn support needed for `clai web` and `Agent.to_web()`.
- `pip install "pydantic-ai[examples]"` installs the example package and its extras; many examples still require provider credentials, databases, or external APIs.

Use the smallest install that matches the task. Route provider-specific extras such as OpenAI, Anthropic, Google, Bedrock, embeddings, or native-tool SDKs to `../models-and-providers/SKILL.md`.

## Chat Commands

| Task | Command | Notes |
| --- | --- | --- |
| Start interactive chat | `clai` | Prompts as `clai ➤`; conversation state is kept in memory for the session. |
| Ask one question | `clai "Summarize this error"` | Positional prompt triggers one-shot mode. |
| Select a model | `clai -m openai:gpt-5.2 "Explain this trace"` | Use provider-prefixed strings. |
| Disable streaming | `clai --no-stream "Explain this trace"` | Useful when terminal streaming breaks formatting. |
| List known models | `clai --list-models` | Prints qualified model names from the installed package. |
| Show version | `clai --version` | Confirms CLI import and package version. |
| Compatibility entry point | `pai --help` or `python -m pydantic_ai --help` | Same CLI family, retained for existing installs; prefer `clai` in new instructions. |

Interactive slash commands:

- `/exit` exits the session.
- `/markdown` reprints the last model text as markdown.
- `/multiline` toggles multiline input; submit with Ctrl+D.
- `/cp` copies the last text response to the system clipboard when clipboard support is available.

## Models and Credentials

`clai` defaults to an OpenAI chat model if neither an agent nor a model is supplied. A missing credential usually appears as a provider SDK authentication error, not as a CLI parser error.

Common checklist:

1. Choose a provider-prefixed model string, for example `openai:gpt-5.2`, `anthropic:claude-sonnet-4-6`, or `google:gemini-3-pro-preview`.
2. Install the provider extra or the full `pydantic-ai` package.
3. Set the provider environment variable expected by that provider SDK.
4. Run `clai --list-models` to check names, then run a small prompt only after credentials are intentionally configured.

## Custom Agent Loading

Use `--agent` when the task already has an `Agent` instance or declarative spec.

### Python Module Agent

Create a normal importable module:

```python
# assistant_app.py
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2', instructions='Reply in concise markdown.')
```

Run a one-shot prompt or interactive session from the directory where the module is importable:

```bash
clai --agent assistant_app:agent "Draft a release note"
clai --agent assistant_app:agent
```

The value must resolve to a `pydantic_ai.Agent` instance. If `assistant_app:agent` imports but is not an `Agent`, the CLI returns `Could not load agent`.

### AgentSpec File

`--agent` also accepts a `.yml`, `.yaml`, or `.json` AgentSpec file path. Use this when the app is already declarative; route spec authoring and validation details to `../agent-core/SKILL.md`.

## Web Chat UI

`clai web` starts a local Uvicorn server for a browser chat UI. Default address: `http://127.0.0.1:7932`.

| Task | Command | Notes |
| --- | --- | --- |
| Generic UI with one model | `clai web -m openai:gpt-5.2` | First `-m` is the default UI model. |
| Custom agent UI | `clai web --agent assistant_app:agent` | Agent model is default; CLI models are additional options. |
| Multiple UI models | `clai web --agent assistant_app:agent -m openai:gpt-5.2 -m anthropic:claude-sonnet-4-6` | UI lets the user choose among supported models. |
| Extra instructions | `clai web -m openai:gpt-5.2 -i "Answer like a support engineer"` | With `--agent`, these are extra run instructions, not a replacement for the agent configuration. |
| Supported native tools | `clai web -m openai:gpt-5.2 -t web_search -t code_execution` | CLI tool flags create optional UI tools only when supported by the selected model profile. |
| Custom bind | `clai web --host 127.0.0.1 --port 7940 -m openai:gpt-5.2` | Use a different port if `7932` is busy. |
| Custom HTML source | `clai web -m openai:gpt-5.2 --html-source ./pydantic-ai-ui.html` | Use a local file or URL for the chat UI HTML. |

The `memory` native tool requires agent-side configuration and is intentionally not enabled by `-t memory`. Put `MemoryTool` or other configured native tools on the `Agent` and serve it with `--agent`.

## Programmatic CLI

Expose an existing agent as a terminal app:

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2', instructions='Reply in concise markdown.')
agent.to_cli_sync(prog_name='assistant')
```

For async code:

```python
import asyncio
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2')

async def main() -> None:
    await agent.to_cli(prog_name='assistant')

asyncio.run(main())
```

`Agent.to_cli()` and `Agent.to_cli_sync()` accept `deps`, `message_history`, `model_settings`, and `usage_limits`. Route history serialization and storage choices to `../outputs-and-messages/SKILL.md`.

## Programmatic Web UI

Create a Starlette app from an agent:

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2', instructions='You are a helpful assistant.')
app = agent.to_web(
    models=['anthropic:claude-sonnet-4-6'],
    instructions='Answer in a friendly tone.',
)
```

Run it with an ASGI server:

```bash
uvicorn assistant_app:app --host 127.0.0.1 --port 7932
```

`Agent.to_web()` can take `models` as a list or as a label-to-model mapping. The agent's configured model is always included. The generated app reserves `/`, `/{id}`, `/api/chat`, `/api/configure`, and `/api/health`; do not mount conflicting routes on that app.

For production frontends, use UI event stream adapters instead of treating the built-in browser chat UI as a complete product UI; route that work to `../mcp-and-integrations/SKILL.md`.
