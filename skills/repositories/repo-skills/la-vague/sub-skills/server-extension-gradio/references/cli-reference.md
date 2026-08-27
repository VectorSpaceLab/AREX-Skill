# `lavague-serve` CLI reference

`lavague-serve` is the console script installed by `lavague-server`. It starts a persistent websocket server for the LaVague Chrome extension. The command is **`lavague-serve`**, not `lavague-server`.

Verified help shape:

```text
Usage: lavague-serve [OPTIONS]

Options:
  -p, --port INTEGER  Server port
  --help              Show this message and exit.
```

## Safe commands

Show help without starting a server:

```bash
lavague-serve --help
```

Probe imports, signature compatibility, and port availability without starting a server:

```bash
python sub-skills/server-extension-gradio/scripts/lavague_ui_server_probe.py --check server --port 8000
```

Print a corrected Python server template without executing it:

```bash
python sub-skills/server-extension-gradio/scripts/lavague_ui_server_probe.py --check server --port 8000 --print-server-template
```

## Live server commands

Start the default extension server on port 8000:

```bash
LAVAGUE_TELEMETRY=NONE lavague-serve
```

Start on a custom port:

```bash
LAVAGUE_TELEMETRY=NONE lavague-serve --port 8001
# equivalent short form:
LAVAGUE_TELEMETRY=NONE lavague-serve -p 8001
```

After choosing a custom port, update the extension's Connection tab to the same value.

## Default CLI behavior

The CLI constructs an agent equivalent to this pattern:

```python
from lavague.core import ActionEngine, WorldModel
from lavague.core.agents import WebAgent
from lavague.server import AgentServer, AgentSession
from lavague.server.driver import DriverServer


def create_agent(session: AgentSession):
    world_model = WorldModel()
    driver = DriverServer(session)
    action_engine = ActionEngine(driver)
    return WebAgent(world_model, action_engine)


server = AgentServer(create_agent, port=8000)
server.serve()
```

Implications:

- `server.serve()` blocks until interrupted.
- The default port is `8000`.
- The server creates an agent per websocket session.
- The extension-controlled browser tab is accessed through `DriverServer(session)`.
- Live use may require model-provider credentials for the default context.

## When to use Python instead of the CLI

Use a Python `AgentServer` script when the user needs:

- Anthropic, Gemini, Fireworks, Azure OpenAI, cache, or custom LlamaIndex model contexts.
- Custom logging or token-counting setup.
- A customized `ActionEngine`, retriever, or `WorldModel` prompt configuration.
- Application-managed lifecycle with `server.close()`.

For context construction details, route to `../contexts-and-retrievers/`; for WebAgent run-loop details, route to `../core-web-agent/`.

## Exit and cleanup

- Stop a terminal-launched server with `Ctrl-C`.
- If embedding `AgentServer` inside another Python process, call `server.close()` when the application stops.
- If a port remains busy after interruption, verify no old Python process is still holding it before retrying.
