# Browser Use CLI Reference

This reference covers the persistent `browser-use` CLI. `bu`, `browseruse`, and `browser` are aliases for the same entrypoint; use `browser-use` in instructions when clarity matters.

## Availability Checks

```bash
browser-use --help
browser-use init --help
browser-use cloud v2 --help
browser-use doctor
```

- `--help` is help-only and should not start a browser.
- `doctor` checks package import, browser profile construction, network connectivity, `cloudflared`, and `profile-use`.
- Use `--json` on supported commands when another program will parse output.

## Install, Setup, and Templates

| Command | Use |
| --- | --- |
| `browser-use install` | Install Chromium through Playwright; Linux adds system dependencies. |
| `browser-use setup` | Interactive setup for CLI home/config, Chromium, profile-use, cloudflared, and validation. |
| `browser-use setup --yes` | Non-interactive setup after user approval. |
| `browser-use doctor` | Health-check installation and optional helpers. |
| `browser-use init` | Interactive template selection. |
| `browser-use init --list` | List available templates. |
| `browser-use init --template <name>` | Generate a named template. |
| `browser-use init --output <file>` | Write a template to a chosen path. |
| `browser-use init --force` | Overwrite an existing output path. |

Template metadata/content is fetched at runtime, so offline environments can fail even when the package is installed.

## Global Options

| Option | Use |
| --- | --- |
| `--headed` | Show a visible browser window. |
| `--profile [NAME]` | Launch real Chrome with a profile; bare `--profile` means `Default`. |
| `--cdp-url <url>` | Connect to a known CDP endpoint, `http://...` or `ws://...`. |
| `--connect` | Deprecated compatibility flag; prefer `browser-use connect`. |
| `--session NAME` | Target a named persistent CLI daemon session. |
| `--json` | Emit JSON where the command supports structured output. |
| `--mcp` | Run the CLI MCP server over stdin/stdout. |
| `--template <name>` | Direct template-generation shortcut. |

Rules:

- `--cdp-url` and `--profile` are mutually exclusive.
- `browser-use cloud connect` is mutually exclusive with `--connect`, `--cdp-url`, and `--profile`.
- Session names should contain only letters, digits, hyphens, and underscores.

## Navigation and Interaction

| Command | Use |
| --- | --- |
| `open <url>` | Navigate; plain domains are treated as HTTPS. |
| `back` | Go back in browser history. |
| `scroll [up\|down] --amount <px>` | Scroll the page, default direction `down`, default amount `500`. |
| `state` | Print viewport, page, scroll, and indexed interactive element state. |
| `click <index>` | Click an indexed element from the latest state. |
| `click <x> <y>` | Click pixel coordinates. |
| `type "text"` | Insert text into the focused element. |
| `input <index> "text"` | Click an element and clear-then-type; pass `""` to clear only. |
| `keys "Enter"` | Send keyboard input, including combinations like `Control+a`. |
| `select <index> "value"` | Select a dropdown option by value. |
| `upload <index> <path>` | Upload a non-empty file through a file input or nearby file input. |
| `hover <index>` | Move mouse over an indexed element. |
| `dblclick <index>` | Double-click an indexed element. |
| `rightclick <index>` | Right-click an indexed element. |

Element indices come from the current DOM state. Rerun `state` after navigation, reloads, dynamic UI changes, modal dismissal, or failed element lookup.

## Inspection and Retrieval

| Command | Use |
| --- | --- |
| `screenshot [path]` | Save screenshot bytes or emit base64 if no path is given. |
| `screenshot --full path.png` | Capture full-page screenshot. |
| `get title` | Print the page title. |
| `get html` | Get full page HTML. |
| `get html --selector "main"` | Get scoped HTML. |
| `get text <index>` | Get element text. |
| `get value <index>` | Get input/textarea value. |
| `get attributes <index>` | Get element attributes. |
| `get bbox <index>` | Get element bounding box. |
| `eval "js"` | Execute JavaScript via CDP and return the value. |
| `extract "query"` | Parsed by CLI but not implemented; avoid for production workflows. |

Use `eval` only for trusted JavaScript. For LLM-backed extraction, route to Agent workflows in `../../agent-programming/SKILL.md` and model/output guidance in `../../llm-and-output/SKILL.md`.

## Tabs

| Command | Use |
| --- | --- |
| `tab list` | List tabs in the current browser session. |
| `tab new [url]` | Open a tab and focus it; defaults to `about:blank`. |
| `tab switch <index>` | Focus a tab by listed index. |
| `tab close [index...]` | Close listed tabs, or current tab when no index is provided. |

Tab indices are session-local and can change after tab creation/closure.

## Cookies

| Command | Use |
| --- | --- |
| `cookies get` | Print current cookies. |
| `cookies get --url <url>` | Filter cookies for a URL/domain. |
| `cookies set <name> <value>` | Set a cookie on the current host when no domain is provided. |
| `cookies set name val --domain .example.com --secure` | Set cookie options. |
| `cookies set name val --same-site Strict` | Set SameSite to `Strict`, `Lax`, or `None`. |
| `cookies clear` | Clear all current browser cookies. |
| `cookies clear --url <url>` | Clear matching domain cookies. |
| `cookies export <file>` | Write cookies to JSON. |
| `cookies import <file>` | Load cookies from JSON. |

Treat cookie JSON files as credentials. Avoid committing them or printing them into logs.

## Waits

| Command | Use |
| --- | --- |
| `wait selector "css"` | Wait for a CSS selector to become visible. |
| `wait selector ".loading" --state hidden` | Wait for hidden/detached/attached/visible state. |
| `wait selector "h1" --timeout 5000` | Set timeout in milliseconds. |
| `wait text "Success"` | Wait for visible text. |

Use waits before `state`, `click`, or `input` on pages with asynchronous rendering.

## Recording

| Command | Use |
| --- | --- |
| `record start out.mp4` | Start recording the session to an MP4 file. |
| `record start out.mp4 --framerate 15` | Override framerate. |
| `record status` | Check active recording status. |
| `record stop` | Stop recording and print saved path. |

Recording can require browser/video dependencies and disk space; ask before enabling in constrained environments.

## Persistent Python

| Command | Use |
| --- | --- |
| `python "x = 42"` | Execute code in the session namespace. |
| `python "print(x)"` | Reuse variables from previous executions in the same CLI session. |
| `python "print(browser.url)"` | Access the injected browser wrapper. |
| `python --vars` | Show user-defined variables and their types. |
| `python --reset` | Clear namespace and history. |
| `python --file script.py` | Execute a local file in the session namespace. |

The namespace includes `json`, `re`, `os`, `Path`, and `asyncio`. The injected `browser` wrapper provides synchronous methods for common browser actions. Review `--file` scripts before execution.

## Cloud CLI

| Command | Use |
| --- | --- |
| `cloud login <api-key>` | Save Browser Use Cloud API key into CLI config. |
| `cloud logout` | Remove saved API key. |
| `cloud connect` | Provision/connect a cloud browser and start the daemon in cloud mode. |
| `cloud v2 GET /browsers` | REST passthrough to API v2. |
| `cloud v2 POST /tasks '{...}'` | REST passthrough with JSON body. |
| `cloud v2 poll <task-id>` | Poll a task until `finished` or `failed`. |
| `cloud v2 --help` | Show OpenAPI-driven help or static fallback. |
| `cloud v3 ...` | Same REST passthrough pattern for API v3. |

Important behavior:

- The cloud REST passthrough reads the API key from CLI config. If only `BROWSER_USE_API_KEY` is set, run `browser-use config set api_key "$BROWSER_USE_API_KEY"` or `browser-use cloud login <key>`.
- 4xx responses return exit code `2`; 5xx and invalid JSON are command failures.
- `poll` prints progress to stderr and final JSON to stdout on success.
- Do not run signup, task creation, profile creation, or browser provisioning without user approval.

## Tunnels

| Command | Use |
| --- | --- |
| `tunnel <port>` | Start a Cloudflare quick tunnel for `http://localhost:<port>`. |
| `tunnel list` | List active tunnel metadata. |
| `tunnel stop <port>` | Stop one tunnel. |
| `tunnel stop --all` | Stop all CLI-managed tunnels. |

Tunnels require `cloudflared`. They are independent of browser sessions and can outlive the launching shell until stopped.

## Profile Management

| Command | Use |
| --- | --- |
| `profile` | Run the profile-use interactive wizard. |
| `profile list` | List detected browsers/profiles through profile-use. |
| `profile sync --all` | Sync all supported local profiles. |
| `profile sync --browser "Google Chrome" --profile "Default"` | Sync a specific profile. |
| `profile auth --apikey <key>` | Configure profile-use authentication. |
| `profile inspect --browser "Google Chrome" --profile "Default"` | Inspect local cookies. |
| `profile update` | Download/update the managed profile-use binary. |

Profile sync can expose cookies/auth state to cloud services. Ask for explicit approval before syncing.

## Config

| Key | Type | Meaning |
| --- | --- | --- |
| `api_key` | string, sensitive | Browser Use Cloud API key used by CLI cloud commands. |
| `cloud_connect_profile_id` | string | Cloud profile ID used by `cloud connect`; created automatically when missing. |
| `cloud_connect_proxy` | string, default `us` | Cloud proxy country code. |
| `cloud_connect_timeout` | integer | Cloud browser timeout in minutes. |
| `cloud_connect_recording` | boolean, default `true` | Enables cloud session recording setting. |

```bash
browser-use config list
browser-use config set cloud_connect_proxy us
browser-use config set cloud_connect_timeout 30
browser-use config set cloud_connect_recording false
browser-use config unset cloud_connect_timeout
```

Unknown keys or invalid boolean/integer values fail validation.
