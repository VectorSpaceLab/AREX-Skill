# UI and server workflows

This reference covers LaVague's two interactive surfaces: the Gradio demo attached to a `WebAgent`, and the Chrome extension server backed by `AgentServer` and `DriverServer`. Both are live workflows: they can keep a process running, open or control browser state, and call configured model providers. Use the bundled probe script before launch.

```bash
python sub-skills/server-extension-gradio/scripts/lavague_ui_server_probe.py --check both --port 8000
```

## Surface selection

| Surface | Primary API | Typical package | Live requirements | Safe preflight |
| --- | --- | --- | --- | --- |
| Gradio demo | `WebAgent.demo(objective="", user_data=None, screenshot_ratio=1)` | `lavague-gradio` plus `gradio` | Browser driver, model context/credentials, interactive UI; current Gradio launch path starts a persistent UI | `--check gradio` |
| Chrome extension server | `lavague-serve --port 8000` or `AgentServer(create_agent, port=8000).serve()` | `lavague-server` plus `websockets`/`click` | Local websocket port, installed Chrome extension, model context/credentials | `--check server --port 8000` |

## Gradio demo workflow

`WebAgent.demo()` imports `lavague.gradio.GradioAgentDemo` lazily. If `lavague-gradio` is not installed, it raises an import error asking for `pip install lavague-gradio`.

Minimal launch pattern:

```python
from lavague.core import ActionEngine, WorldModel
from lavague.core.agents import WebAgent
from lavague.drivers.selenium import SeleniumDriver


driver = SeleniumDriver(headless=True)
action_engine = ActionEngine(driver)
world_model = WorldModel()
agent = WebAgent(world_model, action_engine)

# Optional: navigate before starting the UI; replace only with a user-approved target URL.
# agent.get("about:blank")

# Starts a persistent Gradio UI. Do not call this in a dry-run check.
agent.demo("Describe the objective for the browser agent")
```

Operational notes:

- `agent.demo(objective, user_data=None, screenshot_ratio=1)` pre-populates the Objective box and can pass user data to the agent run.
- The Gradio UI has a URL tab, an Objective tab, a browser screenshot pane, and an agent-output chat history.
- The installed `GradioAgentDemo.launch(server_port=7860, share=True, debug=True)` implementation launches a Gradio app and currently passes `share=True` and `debug=True` internally. Treat this as a public/long-lived UI action and ask before running it.
- `WebAgent.demo()` does not expose a port argument. If a different Gradio port is mandatory, instantiate `GradioAgentDemo` directly and call `launch(server_port=...)`, after warning the user that the launch still starts an interactive service.
- For browser driver setup, headed/headless mode, Chrome/Chromedriver, and profile reuse, route to `../browser-drivers/`.
- For provider contexts, custom LLMs, and credentials, route to `../contexts-and-retrievers/`.

Safe template printing:

```bash
python sub-skills/server-extension-gradio/scripts/lavague_ui_server_probe.py --check gradio --print-gradio-template
```

## Chrome extension server workflow

The extension server bridges the browser extension to a LaVague `WebAgent`. The extension owns the active browser tab; `DriverServer(session)` forwards LaVague driver calls over the websocket session.

Fast default CLI:

```bash
LAVAGUE_TELEMETRY=NONE lavague-serve --port 8000
```

Then, in the browser extension:

1. Open the LaVague extension on the page to automate.
2. If using the default port, submit an objective from the main chat interface.
3. If using a custom port, open the Connection tab and set the same port used by `lavague-serve --port`.
4. Use the Logs tab to inspect thoughts, internal step instructions, outputs, and connection problems.

The CLI default agent uses `WorldModel()`, `DriverServer(session)`, `ActionEngine(driver)`, and `WebAgent(world_model, action_engine)`. That default model stack requires the package's default provider configuration and typically an OpenAI-compatible credential for live use.

## Custom `AgentServer` factory

Use a custom factory when the extension should use a non-default context, logging, memory, retriever configuration, or different model stack.

```python
from lavague.core import ActionEngine, WorldModel
from lavague.core.agents import WebAgent
from lavague.server import AgentServer, AgentSession
from lavague.server.driver import DriverServer


def create_agent(session: AgentSession):
    driver = DriverServer(session)

    # Default context-free construction. For provider-specific contexts, build the
    # context through the contexts-and-retrievers sub-skill and pass it into:
    #   world_model = WorldModel.from_context(context)
    #   action_engine = ActionEngine.from_context(context, driver)
    world_model = WorldModel()
    action_engine = ActionEngine(driver)
    return WebAgent(world_model, action_engine)


server = AgentServer(create_agent, port=8000)
server.serve()
```

Important details:

- The factory must accept one `AgentSession` argument and return a `WebAgent`.
- Use `from lavague.server import AgentServer, AgentSession`.
- Use `from lavague.server.driver import DriverServer`.
- Do not follow stale snippets that import `DriverServer` from `lavague.drivers.driverserver`.
- `AgentServer(...).serve()` is blocking and should be run in a terminal/session that the user expects to keep alive.
- `AgentServer.close()` closes the communication channel when the embedding application manages server lifetime itself.

Safe template printing:

```bash
python sub-skills/server-extension-gradio/scripts/lavague_ui_server_probe.py --check server --port 8000 --print-server-template
```

## What the server driver does

`DriverServer(session, url=None)` implements the browser-driver interface by sending commands to the extension session and waiting for responses. It supports operations used by LaVague navigation, including:

- `get_html`, `get_url`, `get`, `back`, `switch_tab`.
- `get_screenshot_as_png` and whole-page screenshot scanning.
- `get_possible_interactions`, `highlight_elem`, `exec_code`, `execute_script`.
- Navigation controls such as wait, scroll up/down, and tab switching.

Because these operations depend on an active extension websocket session, import/signature checks are safe but full behavior requires a live extension connection.

## Non-goals

- Do not use this sub-skill to modify or rebuild the Chrome extension front-end. This generated operating skill focuses on Python package operation and server integration.
- Do not run live web automation, provider calls, or public-share Gradio sessions during verification unless the user has explicitly authorized those live effects.
