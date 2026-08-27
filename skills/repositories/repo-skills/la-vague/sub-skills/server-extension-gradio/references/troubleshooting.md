# Troubleshooting Gradio and Chrome-extension server workflows

Start with the safe probe. It does not launch a UI or server:

```bash
python sub-skills/server-extension-gradio/scripts/lavague_ui_server_probe.py --check both --port 8000
```

## `lavague-gradio` missing

Symptom examples:

- `ImportError: No module named 'lavague.gradio'`
- `WebAgent.demo()` raises: `` `lavague-gradio` package not found, please run `pip install lavague-gradio` ``

Fix:

```bash
python -m pip install lavague-gradio
python sub-skills/server-extension-gradio/scripts/lavague_ui_server_probe.py --check gradio
```

Notes:

- `WebAgent.demo()` imports Gradio support lazily; the rest of `lavague-core` can import successfully while the demo still fails.
- The demo is live/interactive. Do not call `agent.demo()` just to prove the import works; use the probe script.

## `agent.demo` import or launch error

Likely causes:

1. `lavague-gradio` or `gradio` is not installed.
2. The installed Gradio dependency stack is incompatible, for example an older Gradio path expecting `HfFolder` from `huggingface_hub` after that symbol was removed.
3. The base `WebAgent`, driver, or `ActionEngine` was not constructed correctly.
4. A browser dependency is unavailable for the selected driver.
5. The selected model context requires missing credentials.
6. Another process is already using the Gradio port.

Triage:

```bash
python sub-skills/server-extension-gradio/scripts/lavague_ui_server_probe.py --check gradio
```

If the failure mentions `cannot import name 'HfFolder' from 'huggingface_hub'`, repair the Gradio dependency stack in the active environment: use a `huggingface_hub` version compatible with the installed Gradio release, or upgrade Gradio/lavague-gradio together in a clean environment, then rerun `--check gradio`.

Then route by failing layer:

- Missing browser or WebDriver: route to `../browser-drivers/`.
- Missing provider keys or custom context issues: route to `../contexts-and-retrievers/`.
- Agent construction or run-loop issues: route to `../core-web-agent/`.

## `lavague-serve` vs stale command typo

The extension server command is:

```bash
lavague-serve --port 8000
```

Do not use `lavague-server 8001`; that spelling is a stale documentation typo and is not the console script. The port must be passed with `--port` or `-p`.

## Stale `DriverServer` import path

Some older Chrome-extension snippets use a stale path:

```python
from lavague.drivers.driverserver import DriverServer  # stale; do not use
```

Use the installed server package path instead:

```python
from lavague.server.driver import DriverServer
from lavague.server import AgentServer, AgentSession
```

The bundled probe and templates use the corrected imports.

## Extension cannot connect

Common causes:

- Server is not running.
- Server and extension are using different ports.
- The port is already used by another process.
- The extension is open on a different browser profile/session than expected.
- A stale server process is running an old custom factory.

Triage checklist:

1. Run the safe server probe for the intended port:

   ```bash
   python sub-skills/server-extension-gradio/scripts/lavague_ui_server_probe.py --check server --port 8000
   ```

2. Start or restart the live server only after confirming the port:

   ```bash
   LAVAGUE_TELEMETRY=NONE lavague-serve --port 8000
   ```

3. In the extension, open the Connection tab and confirm the same port.
4. If the main chat still does not respond, open the Logs tab and inspect connection messages and agent logs.
5. Stop duplicate servers before retrying.

## Port mismatch or port busy

Symptoms:

- Extension says it cannot connect.
- Server appears healthy but receives no extension messages.
- Probe says `127.0.0.1:<port>` is not bindable.

Fix:

- Use one agreed port in both places: `lavague-serve --port 8001` and extension Connection tab `8001`.
- Choose a new port when the old one is occupied.
- Stop stale Python/server processes before restarting.

## Logs tab shows agent errors

The extension's Logs tab is the first place to distinguish connection errors from LaVague agent errors. Use it to identify whether the failure happens before or after the server receives the objective.

- Connection/log messages only: check port, server process, extension Connection tab.
- Import/model errors after objective submission: check provider package and credentials via `../contexts-and-retrievers/`.
- Driver-command errors such as screenshot, HTML, or tab operations: check browser/extension state and route driver details to `../browser-drivers/`.
- Navigation/output errors: route WebAgent and engine behavior to `../core-web-agent/`.

## Custom `AgentServer` factory with contexts

The server factory must accept `session: AgentSession` and return a `WebAgent`. Build provider contexts outside the `DriverServer` itself, then pass context fields into `WorldModel` and `ActionEngine`.

Pattern:

```python
from lavague.core.agents import WebAgent
from lavague.core import ActionEngine, WorldModel
from lavague.server import AgentServer, AgentSession
from lavague.server.driver import DriverServer


def create_agent(session: AgentSession):
    driver = DriverServer(session)
    # context = ...  # Build through the contexts-and-retrievers sub-skill.
    # world_model = WorldModel.from_context(context)
    # action_engine = ActionEngine.from_context(context, driver)
    world_model = WorldModel()
    action_engine = ActionEngine(driver)
    return WebAgent(world_model, action_engine)


server = AgentServer(create_agent, port=8000)
server.serve()
```

If the custom context requires API keys, validate the keys before starting a persistent server. Do not print or persist secret values.

## Persistent server not started by default

The bundled script is intentionally a probe/template tool. These commands do **not** start a server or UI:

```bash
python sub-skills/server-extension-gradio/scripts/lavague_ui_server_probe.py --check both
python sub-skills/server-extension-gradio/scripts/lavague_ui_server_probe.py --print-server-template
python sub-skills/server-extension-gradio/scripts/lavague_ui_server_probe.py --print-gradio-template
```

Live commands are separate and should only be run after explicit user intent:

```bash
lavague-serve --port 8000
# or in Python:
# server = AgentServer(create_agent, port=8000)
# server.serve()
# or for Gradio:
# agent.demo("...")
```

## NLTK, telemetry, and import-time warnings

LaVague imports can emit telemetry notices or dependency warnings during safe checks. Prefer:

```bash
LAVAGUE_TELEMETRY=NONE python sub-skills/server-extension-gradio/scripts/lavague_ui_server_probe.py --check both
```

If an environment blocks automatic NLTK data fetches, pre-seed NLTK data through the organization's approved process rather than allowing unreviewed network fetches. If `pkg_resources` import errors appear under a very new `setuptools`, use an environment compatible with the installed LaVague dependency stack.
