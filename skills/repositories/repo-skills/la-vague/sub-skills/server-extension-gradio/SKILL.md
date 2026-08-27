---
name: server-extension-gradio
description: "Operate LaVague Gradio demos, Chrome extension server workflows,
  lavague-serve, AgentServer, and DriverServer safely."
disable-model-invocation: true
metadata:
  disco-role: operating
  root-skill: la-vague
  sub-skill: server-extension-gradio
license: Apache 2.0
---

# LaVague server, extension, and Gradio workflows

Use this sub-skill when the user wants to run or debug LaVague's interactive surfaces:

- `WebAgent.demo()` and the optional `lavague-gradio` package.
- The Chrome extension server started by `lavague-serve`.
- Custom extension agents using `AgentServer`, `AgentSession`, and `DriverServer`.
- Extension connection, port, and logs troubleshooting.

Do **not** start a persistent UI, websocket server, browser, provider API call, or public Gradio share link unless the user explicitly asks for a live run. Start with the safe probe:

```bash
python sub-skills/server-extension-gradio/scripts/lavague_ui_server_probe.py --check both --port 8000
```

## Route by user intent

| User intent | Use this path |
| --- | --- |
| "Check whether Gradio/server pieces are installed" | Run the safe probe script with `--check gradio`, `--check server`, or `--check both`. |
| "Show me how to launch the Gradio demo" | Use [references/ui-and-server-workflows.md](references/ui-and-server-workflows.md#gradio-demo-workflow) and optionally print the template with `--print-gradio-template`. |
| "Run the Chrome extension backend" | Confirm the target port, model credentials, and that the browser extension will connect; then use [references/cli-reference.md](references/cli-reference.md). |
| "Customize the extension agent" | Use the `AgentServer(create_agent)` factory recipe in [references/ui-and-server-workflows.md](references/ui-and-server-workflows.md#custom-agentserver-factory). Route provider selection to `../contexts-and-retrievers/`. |
| "The extension cannot connect" | Follow [references/troubleshooting.md](references/troubleshooting.md#extension-cannot-connect). |
| "The browser driver itself fails" | Route to `../browser-drivers/`. |
| "The WebAgent construction or run loop fails" | Route to `../core-web-agent/`. |

## Safety defaults

1. Treat Gradio and Chrome extension flows as **interactive/live** workflows.
2. Probe imports, signatures, and port availability before live launch.
3. Prefer `LAVAGUE_TELEMETRY=NONE` for checks and reproducible debugging.
4. Use `lavague-serve`, not the stale `lavague-server` command spelling.
5. Use `from lavague.server.driver import DriverServer`; do not use stale `lavague.drivers.driverserver` snippets.
6. Keep extension port values synchronized between the server and the extension Connection tab.
7. For custom model contexts, construct the context through `../contexts-and-retrievers/` and pass it into `WorldModel.from_context(context)` and `ActionEngine.from_context(context, driver)`.

## Deep references

- [UI and server workflows](references/ui-and-server-workflows.md)
- [CLI reference](references/cli-reference.md)
- [Troubleshooting](references/troubleshooting.md)
- [Safe probe script](scripts/lavague_ui_server_probe.py)
