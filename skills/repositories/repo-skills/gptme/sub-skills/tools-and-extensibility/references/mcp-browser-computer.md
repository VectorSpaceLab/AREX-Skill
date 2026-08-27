# MCP, browser, and computer-use reference

This reference covers optional and higher-risk tool surfaces. Use it with [tools-reference.md](tools-reference.md) for allowlists and [troubleshooting.md](troubleshooting.md) for repair paths.

## MCP in gptme

gptme can act as both:

- an MCP client, consuming tools from configured external MCP servers through the `mcp` tool and `gptme-util mcp` commands;
- an MCP server, exposing selected gptme tools to other MCP-compatible clients through `gptme-mcp-server` or `gptme-util mcp serve`.

Treat each MCP server as an external program or HTTP service with the same privileges as the launching user. Do not auto-start unknown MCP servers in sensitive workspaces.

### MCP client configuration

Typical config shape:

```toml
[mcp]
enabled = true
auto_start = true

[[mcp.servers]]
name = "local-sqlite"
enabled = true
command = "uvx"
args = ["mcp-server-sqlite", "--db-path", "./mcp-store.sqlite"]
env = {}

[[mcp.servers]]
name = "docs-http"
enabled = true
url = "MCP_HTTP_ENDPOINT"
headers = { Authorization = "Bearer ${TOKEN_FROM_SAFE_CONFIG}" }
```

Fields:

| Field | Applies to | Meaning |
| --- | --- | --- |
| `enabled` under `[mcp]` | client | Enables MCP support. |
| `auto_start` | client | Allows configured stdio servers to start when needed. |
| `name` | each server | Stable prefix used for tool names, such as `server.tool`. |
| `enabled` | each server | Turns an individual server on/off. |
| `command` and `args` | stdio server | Process to launch. Use pinned, trusted commands where possible. |
| `url` | HTTP server | Remote MCP endpoint. |
| `headers` | HTTP server | Header map for HTTP transport. Keep secrets in secure config, not logs. |
| `env` | stdio server | Explicit environment variables passed to the server. Avoid broad host env inheritance. |

MCP tools appear as `<server-name>.<tool-name>`. Allowlist them explicitly with exact names or globs, for example `--tools read,local-sqlite.*`.

### MCP management commands

Use these before enabling MCP tools in an agent run:

```bash
gptme-util mcp --help
gptme-util mcp list
gptme-util mcp info SERVER_NAME
gptme-util mcp test SERVER_NAME
```

Conversation-level MCP tool commands include:

- `/search [query]`: search MCP registries;
- `/info <server-name>`: inspect a server;
- `/load <server-name>`: load a server into the current session;
- `/unload <server-name>`: unload it;
- `/list`: list configured and loaded servers.

Registry search and third-party server installation can require network and untrusted code review. Keep them user-authorized.

### gptme as an MCP server

Expose a bounded set of gptme tools to another MCP client:

```bash
gptme-mcp-server --tools shell,ipython,save,append,read --workspace .
```

Equivalent utility command:

```bash
gptme-util mcp serve --tools shell,ipython,save,append,read --workspace .
```

Important server behavior:

- Default exposed tools are `shell`, `ipython`, `save`, `append`, and `read`.
- `subagent` and `mcp` are excluded from MCP server exposure even if requested.
- The server is session-backed: shell and Python state can persist across calls in one MCP connection.
- Tool calls are serialized to avoid races on stateful shells and Python sessions.
- Logs should go to stderr; stdout is protocol transport.
- Use `--workspace` to bind relative file operations to the intended directory.

Example client config shape for another MCP client:

```json
{
  "mcpServers": {
    "gptme": {
      "command": "gptme-mcp-server",
      "args": ["--tools", "shell,ipython,save,read", "--workspace", "."]
    }
  }
}
```

Review the selected tools as if granting them to the external client. Exposing `shell` and `ipython` is equivalent to granting code execution in the workspace.

## Browser tool

The browser tool can read pages, search, extract PDF text, take screenshots, inspect page accessibility snapshots, interact with forms, and read browser logs. Availability depends on optional backends.

### Backends

| Backend | Capability | Install/runtime requirement | Caveat |
| --- | --- | --- | --- |
| Playwright | Full page automation, screenshots, ARIA snapshots, clicking/filling/scrolling. | gptme browser extra plus matching Playwright browser binaries. | Browser binaries are not installed by Python package install alone in many environments. |
| Lynx | Text-only reading/search fallback. | `lynx` executable on `PATH`. | No screenshots or interactive browser automation. |
| Provider-native web search | Search through a provider feature for supported models. | Provider support and explicit setting. | Provider/model configuration is routed to configuration-and-providers. |
| Existing browser over CDP | Reuse a running Chromium-compatible browser session. | Start browser with remote debugging and set CDP URL. | CDP mode is Chromium-only and ignores the Playwright engine setting. |

Browser environment variables:

| Variable | Meaning |
| --- | --- |
| `GPTME_BROWSER_ENGINE` | `chromium` by default; can be `firefox`, a browser executable name on `PATH`, or a custom executable path. Custom executables are launched through the Firefox Playwright engine. |
| `GPTME_BROWSER_CDP_URL` | Chrome DevTools Protocol endpoint for an already-running Chromium-compatible browser, for example a local debugging endpoint on port `9222`. When set, CDP mode takes precedence over engine selection. |
| `GPTME_BROWSER_STORAGE_STATE` | Path to a Playwright storage-state JSON file for persistent cookies/local storage. |
| `GPTME_ANTHROPIC_WEB_SEARCH` | Enables Anthropic native web search for supported Claude models. |
| `GPTME_ANTHROPIC_WEB_SEARCH_MAX_USES` | Optional bound on provider-native search uses. |

Common browser operating patterns:

```bash
# Prefer Firefox for sites that block headless Chromium.
export GPTME_BROWSER_ENGINE=firefox
gptme --tools +browser "read this site and summarize it"

# Reuse an already-authenticated Chromium session.
chromium --remote-debugging-port=9222
export GPTME_BROWSER_CDP_URL=CDP_URL_FOR_RUNNING_CHROMIUM
gptme --tools +browser "inspect the current app"
```

When diagnosing browser failures, separate three layers:

1. Python package availability (`playwright` import or `lynx` binary).
2. Browser binary availability (`chromium-headless-shell` or `firefox` installed for the matching Playwright version).
3. Site behavior (bot detection, CAPTCHAs, auth, CSP, or local network access).

Difficult case: a browser task fails on a site that works in the user's real browser. First try a different Playwright engine (`GPTME_BROWSER_ENGINE=firefox`). If the task requires an existing logged-in session or full GUI browser fingerprint, use CDP mode with a running Chromium browser. If the site still blocks headless automation, consider the computer tool in a full desktop environment, but only with explicit user authorization.

## Computer tool

The computer tool controls a real desktop through keyboard, mouse, screen capture, and accessibility operations. It is powerful and risky: typing, clicking, and drag operations can affect anything visible in the desktop session.

### Capabilities

| Capability | Actions |
| --- | --- |
| Keyboard | `key`, `type`, semicolon-separated sequences like `ctrl+l;t:text;Return`. |
| Mouse | `mouse_move`, `left_click`, `right_click`, `middle_click`, `double_click`, `triple_click`, `left_click_drag`, `scroll`. |
| Screen | `screenshot`, `cursor_position`, `wait_for_change`. |
| Window/accessibility | `window_focus`, `accessibility_tree`, `click_accessible_element`. |

### System dependencies

| Platform | Requirement | Notes |
| --- | --- | --- |
| Linux/X11 | `DISPLAY`, `xdotool`, screenshot support, optional AT-SPI2/`pyatspi` for accessibility tree/clicks. | Default display is commonly `:1` in containerized desktop setups. Wayland-only sessions may not work with X11 tooling. |
| macOS | native `screencapture`, `cliclick` for input, accessibility and screen-recording permissions, optional Quartz bindings for scroll. | Permission prompts must be handled by the user. |
| Docker/VNC desktop | Browser/desktop image with VNC and X11 tools. | Useful for full GUI browser workflows, but Docker/VNC setup is host-specific and should not be launched without user consent. |

Computer-use environment variables:

| Variable | Meaning |
| --- | --- |
| `DISPLAY` | X11 display to target on Linux. |
| `WIDTH` / `HEIGHT` | API-space screen size used for screenshot scaling and coordinate mapping. |
| `GPTME_COMPUTER_CONFIRM_SENSITIVE` | Sensitive action gate. `1` prompts in interactive sessions and blocks non-interactive sensitive actions; `auto-allow` approves silently for controlled automation. |

Safety pattern:

1. Observe first: take a screenshot or accessibility tree.
2. Plan one bounded action at a time.
3. Use coordinates only after confirming current resolution and screen state.
4. Prefer accessibility names (`click_accessible_element`) over raw coordinates when available.
5. Verify after each action with `wait_for_change` or a fresh screenshot.
6. Enable sensitive-action confirmation for tasks that type secrets, click payments, drag files, or operate outside a disposable environment.

Avoid computer use for tasks that can be solved with `browser`, `shell`, `ipython`, or an API. Use it when a visible GUI is truly required.
