---
name: cli-and-sessions
description: "Use the persistent browser-use/bu CLI for browser automation,
  named sessions, profiles, cloud connect, tunnels, config, doctor/setup/init,
  and CLI failure recovery."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# CLI and Sessions

Use this sub-skill when the user wants terminal-first Browser Use automation: `browser-use` or `bu` commands, persistent browser sessions, local/remote Chrome connection, cloud browser connection from the CLI, template generation, config, setup/doctor checks, tunnels, profile sync, or `browser-use python`.

## Route First

- Use this sub-skill for CLI commands, daemon/session lifecycle, `browser-use cloud ...`, `browser-use tunnel`, `browser-use profile`, `browser-use config`, `browser-use doctor`, `browser-use setup`, `browser-use init`, and `browser-use python`.
- Route Python `Agent(...)` workflows, `agent.run()`, history objects, callbacks, prompt design, and initial actions to `../agent-programming/SKILL.md`.
- Route Python `Browser`, `BrowserSession`, `BrowserProfile`, CDP/profile/session constructor parameters, downloads, HAR/video, domain filters, and direct browser control to `../browser-control/SKILL.md`.
- Route custom actions, default tool behavior inside an Agent, file tools, sensitive data, and tool validation to `../tools-and-actions/SKILL.md`.
- Route LLM provider selection, `ChatBrowserUse`, model credentials for Agents, structured output, extraction LLMs, and cost tracking to `../llm-and-output/SKILL.md`.
- Route production `@sandbox`, Python `Browser(use_cloud=True)`, MCP deployment, skills loading, telemetry, and broader cloud integrations to `../production-integrations/SKILL.md`.

## Safe Defaults

- Prefer `browser-use` in docs and scripts; `bu`, `browseruse`, and `browser` are aliases for the same fast CLI entrypoint.
- Start with help-only validation before launching browsers: `browser-use --help`, `browser-use init --help`, `browser-use cloud v2 --help`, then `browser-use doctor` if environment checks are acceptable.
- Use `--json` for coding-agent parsers when command output must be consumed programmatically.
- Use named sessions for parallel work: `browser-use --session NAME ...`; names should contain only letters, digits, hyphens, and underscores.
- Close sessions explicitly with `browser-use --session NAME close` or `browser-use close --all` to avoid stale daemons.
- Do not paste real API keys into logs. For cloud CLI, use `browser-use cloud login <key>` or `browser-use config set api_key "$BROWSER_USE_API_KEY"`; the CLI reads cloud API keys from its config file, not directly from `BROWSER_USE_API_KEY`.
- Use `BROWSER_USE_HOME` only for isolation/testing; otherwise the CLI stores state under the user’s Browser Use home.

## Install and Health Checks

```bash
uv pip install "browser-use[cli]"
browser-use install
browser-use doctor
```

- `browser-use install` installs Chromium through Playwright and includes Linux system dependencies when needed.
- `browser-use setup` creates CLI home/config state, offers Chromium/profile-use/cloudflared setup, and prints config status.
- `browser-use setup --yes` is suitable for non-interactive setup when the user approved dependency installation.
- `browser-use doctor` checks package import, browser profile availability, network connectivity, `cloudflared`, and `profile-use`.
- If only command availability needs verification, run `scripts/cli_smoke.sh --help-only` from this sub-skill.

## Core Browser Commands

```bash
browser-use open https://example.com
browser-use state
browser-use click 5
browser-use input 3 "john@example.com"
browser-use keys "Enter"
browser-use screenshot page.png
browser-use close
```

- `open` auto-prefixes plain domains with `https://`.
- `state` prints page/viewport/scroll details plus indexed interactive elements; rerun it after navigation or page mutation because indices can change.
- `click` accepts either one element index or two pixel coordinates: `browser-use click 5` or `browser-use click 120 240`.
- `input` clicks an indexed element and clear-then-types text; pass `""` when you need to clear only.
- `screenshot` writes bytes to a path or emits base64 when no path is provided; use `--full` for full-page capture.
- See `references/cli-reference.md` for the command matrix.

## Sessions and Browser Modes

```bash
browser-use --session work --headed open https://example.com
browser-use --session work state
browser-use sessions
browser-use --session work close
```

- The first command for a session starts a background daemon; subsequent commands talk to that daemon over a socket/TCP channel.
- Each named session has separate PID/socket/token/state files and keeps the browser alive across CLI calls.
- `--headed` starts a visible browser; omit it for headless Chromium.
- `--profile "Default"` launches real Chrome with a local profile; bare `--profile` uses `Default`.
- `browser-use connect` discovers a running local Chrome CDP endpoint; `--cdp-url http://...` or `--cdp-url ws://...` connects to a known CDP endpoint.
- `--cdp-url` and `--profile` are mutually exclusive; cloud connect also conflicts with `--connect`, `--cdp-url`, and `--profile`.
- See `references/session-recipes.md` for multi-session, CDP, profile, tunnel, cloud, and `python` recipes.

## Tabs, Cookies, Waits, and Data

```bash
browser-use tab list
browser-use tab new https://example.org
browser-use tab switch 1
browser-use cookies export cookies.json
browser-use wait selector "h1" --timeout 5000
browser-use get html --selector "main"
browser-use eval "document.title"
```

- Use `tab` subcommands to manage pages in the current session without starting another browser.
- Use `cookies get/set/clear/export/import` for session cookie state; treat exported cookie files as secrets.
- Use `wait selector` or `wait text` before interacting with pages that load asynchronously.
- Use `get title/html/text/value/attributes/bbox` for deterministic data retrieval from the current page.
- Use `eval` for JavaScript snippets; avoid evaluating untrusted code.
- `extract` exists in the CLI parser but currently returns an implementation error, so route extraction workflows to Agent/Python guidance instead.

## Persistent Python Command

```bash
browser-use python "x = 42"
browser-use python "print(x)"
browser-use python "print(browser.url)"
browser-use python --vars
browser-use python --reset
browser-use python --file automate.py
```

- The CLI Python namespace persists per browser session and includes `json`, `re`, `os`, `Path`, `asyncio`, and a synchronous `browser` wrapper.
- The `browser` wrapper supports common browser actions such as `goto`, `click`, `type`, `input`, `upload`, `scroll`, `screenshot`, `keys`, and page properties like `url`, `title`, and `html`.
- Use `browser-use python` for quick session automation; use `../agent-programming/SKILL.md` when the user needs an LLM-driven `Agent` script.
- `--file` reads and executes a local Python file in the persistent namespace; review file contents before running.

## Cloud CLI, Profiles, and Tunnels

```bash
browser-use cloud login <api-key>
browser-use cloud connect
browser-use state
browser-use cloud v2 GET /browsers
browser-use cloud v2 POST /tasks '{"task":"Search for AI news","url":"https://google.com"}'
browser-use cloud v2 poll <task-id>
browser-use close
```

- `cloud login` stores the API key in CLI config with restricted permissions where supported.
- `cloud connect` provisions a cloud browser profile, starts the session daemon in cloud mode, and may print a live/CDP URL.
- `cloud v2` and `cloud v3` are generic REST passthroughs; 4xx responses exit with code `2` and may print an expected body suggestion from OpenAPI.
- `cloud signup` flows exist for account creation/claiming; do not run signup without explicit user approval.
- `profile` delegates to the managed `profile-use` binary for local cookie/profile sync; install or update it with `browser-use profile update` when doctor reports it missing.
- `tunnel <port>` starts a Cloudflare quick tunnel for local apps; `tunnel list`, `tunnel stop <port>`, and `tunnel stop --all` manage tunnel processes.
- For Python cloud browser parameters or `@sandbox`, route to `../production-integrations/SKILL.md` and `../browser-control/SKILL.md`.

## Config and Templates

```bash
browser-use config list
browser-use config set cloud_connect_proxy us
browser-use config set cloud_connect_timeout 30
browser-use config unset cloud_connect_timeout
browser-use init --list
browser-use init --template basic --output my_agent.py
```

- Valid config keys include `api_key`, `cloud_connect_profile_id`, `cloud_connect_proxy`, `cloud_connect_timeout`, and `cloud_connect_recording`.
- `config set` validates known keys and coerces integer/boolean values based on the schema.
- `init` fetches template metadata/content at runtime; offline failures usually mean network/template service access is unavailable.
- Use `--force` only when the user approved overwriting an existing generated file.

## Troubleshooting Protocol

1. Capture the exact command, exit code, stdout/stderr, OS, shell, and whether `browser-use` or `bu` was used.
2. Run `browser-use --help` and the specific subcommand help when possible.
3. Run `browser-use doctor` for install/browser/network/profile/tunnel checks if safe in the environment.
4. Inspect active sessions with `browser-use sessions`; close the affected session and retry with a fresh named session.
5. For config/cloud issues, run `browser-use config list` and verify `api_key` is set without printing secret values.
6. For page element failures, rerun `browser-use state` and update indices; page changes invalidate earlier indices.
7. For stale daemon/socket issues, run `browser-use --session NAME close`, then retry; use `browser-use close --all` only when the user accepts closing every CLI browser session.
8. Use `references/troubleshooting.md` for symptom-specific fixes.

## Verification Snippets

```bash
# Help-only smoke test; does not launch browsers or require credentials.
./scripts/cli_smoke.sh --help-only

# Isolated CLI home for a temporary session.
BROWSER_USE_HOME="$(mktemp -d)" browser-use --session smoke --json sessions
```

- Do not run browser-launching commands in restricted CI unless Chromium/browser dependencies are available and the user approved environment mutation.
- Do not run cloud commands that create browsers, tasks, profiles, or signup accounts without explicit user approval.
