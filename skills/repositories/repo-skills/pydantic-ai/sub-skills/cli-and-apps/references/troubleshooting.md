# CLI and App Troubleshooting

Use this guide for symptoms around `clai`, `pai`, `clai web`, `Agent.to_cli()`, `Agent.to_web()`, installed examples, and app scaffolds.

## CLI Is Not Installed or Imports Fail

Symptoms:

- `clai: command not found`
- `No module named clai`
- Import error mentioning `rich`, `prompt-toolkit`, `pyperclip`, or `argcomplete`

Checks:

1. From this sub-skill directory, run the bundled helper: `python scripts/check_cli_help.py`.
2. For standalone CLI usage, install `clai`.
3. For slim package CLI usage, install `pydantic-ai-slim[cli]`.
4. If only `pai` works, treat it as a compatibility entry point and prefer installing/using `clai` for new workflows.

## Missing API Keys

Symptoms:

- Provider SDK authentication error after the CLI banner.
- OpenAI error saying the API key client option must be set or `OPENAI_API_KEY` must be configured.
- A custom agent imports successfully but fails on first model request.

Fix pattern:

1. Identify the model actually being used: CLI `--model`, the custom agent's configured model, or the CLI default.
2. Route model string and credential lookup to `../models-and-providers/SKILL.md`.
3. Set the provider's environment variable or configure a provider object in the agent module.
4. For tests and demos, replace the live provider with `TestModel` rather than adding fake secrets.

## Wrong Custom Agent Path

Symptoms:

- `Error: Could not load agent from ...`
- `--agent assistant_app` fails but `assistant_app:agent` was intended.
- The module imports in Python but `clai` refuses it.

Fix pattern:

1. Use `module:variable` for Python agents, for example `assistant_app:agent`.
2. Run from a current working directory where the module is importable, or install the app package.
3. Ensure the variable is an actual `pydantic_ai.Agent` instance, not a factory, wrapper, string, or FastAPI app.
4. If using a YAML/JSON AgentSpec, pass a real `.yml`, `.yaml`, or `.json` file path and route spec validation to `../agent-core/SKILL.md`.
5. Keep app import side effects minimal; importing the agent module should not start servers, run prompts, connect to databases, or require live credentials unless unavoidable.

## Model Flag Confusion with Custom Agents

Symptoms:

- `clai --agent assistant_app:agent --model ...` appears to override the agent model.
- `clai web --agent assistant_app:agent -m ...` adds choices rather than replacing everything.

Current behavior:

- Chat mode: `--model` sets or overrides the agent's model for the session.
- Web mode: the agent's configured model is included; repeated `-m/--model` values are additional UI choices.
- Without a model and without an agent model, CLI/web commands fall back to the installed default model, which may require credentials.

## `clai web` Port or Host Conflict

Symptoms:

- `Error starting server: [Errno 98] address already in use`
- Browser cannot connect to `127.0.0.1:7932`.
- A remote user cannot reach a server bound to localhost.

Fix pattern:

1. Prefer local-only binding during development: `--host 127.0.0.1`.
2. Change the port: `clai web --port 7940 -m openai:gpt-5.2`.
3. Bind to `0.0.0.0` only when the user explicitly wants network exposure and understands firewall/security implications.
4. Confirm `uvicorn` is installed via the `web` extra or app dependencies.
5. If embedding with `Agent.to_web()`, run with an ASGI server such as `uvicorn module:app --host 127.0.0.1 --port 7932`.

## Browser or Web UI HTML Problems

Symptoms:

- Server starts but the browser page fails to load.
- Offline environment cannot fetch the default UI HTML.
- `Local UI file not found` for `html_source`.

Fix pattern:

1. Install `pydantic-ai-slim[web]` or full app dependencies.
2. Use `--html-source ./pydantic-ai-ui.html` or `Agent.to_web(html_source='...')` for an offline/local HTML file.
3. Check that the local file exists and is readable from the app process.
4. Do not mount custom routes over `/`, `/{id}`, `/api/chat`, `/api/configure`, or `/api/health` on the generated web app.
5. For production UIs, switch to the UI event stream or AG-UI adapters rather than patching the bundled local development page.

## Native Tool Flag Problems

Symptoms:

- `clai web -t memory` warns that the tool requires configuration.
- A native tool appears for one model but not another.
- A provider rejects a native tool at request time.

Fix pattern:

1. Use `clai web --help` to see CLI-supported native tool IDs.
2. Configure tools that need setup directly on the `Agent` using capabilities such as `NativeTool(...)`, then serve with `--agent`.
3. Remember that UI tool availability is filtered by each selected model profile.
4. Route provider-native tool support, optional extras, and SDK limitations to `../models-and-providers/SKILL.md`.
5. Route capability-based native/local fallback design to `../mcp-and-integrations/SKILL.md`.

## `pai` Legacy and Deprecation Context

Symptoms:

- Existing docs or scripts mention `pai` instead of `clai`.
- Both `pai --help` and `clai --help` appear to work.

Guidance:

- `pai` is still exposed by the Pydantic AI package as a compatibility CLI entry point.
- New runtime instructions should prefer `clai` because it is the standalone CLI package.
- When maintaining old scripts, keep `pai` only if changing the command would break users; otherwise migrate examples to `clai`.

## Installed Example Failures

Symptoms:

- `No module named pydantic_ai_examples`.
- Example imports fail for FastAPI, asyncpg, Gradio, DuckDB, datasets, AG-UI, or other extras.
- Example starts but fails due to missing PostgreSQL, pgvector, browser frontend, or API keys.
- Example makes many embedding/model calls unexpectedly.

Fix pattern:

1. Install the examples extra only if the user wants runnable examples: `pydantic-ai[examples]`.
2. Read the recipe in [example-app-recipes.md](example-app-recipes.md) before running anything with external services.
3. Confirm provider credentials and costs before model or embedding calls.
4. Confirm local service startup before database examples; do not start Docker or mutate databases without user approval.
5. For scaffolding tasks, copy the pattern into a new app and replace live services with deterministic test seams.

## Clipboard or Terminal Rendering Problems

Symptoms:

- `/cp` fails or no clipboard backend exists.
- Markdown/code highlighting is hard to read.
- Streaming output looks broken in a non-interactive terminal.

Fix pattern:

1. Use `/markdown` to reprint the last response.
2. Use `--code-theme light`, `--code-theme dark`, or a Pygments theme name.
3. Use `--no-stream` for terminals or logs that do not handle live updates well.
4. Treat clipboard support as best-effort; it depends on OS clipboard utilities.

## App Scaffold Import Side Effects

Symptoms:

- `clai --agent` starts a web server while importing the module.
- Importing the app connects to a database or calls a provider.
- `uvicorn module:app` and `clai --agent module:agent` need different objects.

Fix pattern:

1. Keep `agent = Agent(...)` and `app = ...` definitions import-safe.
2. Put server startup under `if __name__ == '__main__':`.
3. Put database and HTTP client lifecycles in FastAPI lifespan or explicit async context managers.
4. Keep credentials read at request/runtime boundaries where possible, not at import time.
5. Expose separate variables when needed: `agent` for CLI loading and `app` for ASGI serving.
