# CLI Session Recipes

The Browser Use CLI is daemon-backed. The first command for a session starts a background browser daemon; later commands reuse it for fast stateful automation.

## Basic Session Loop

```bash
browser-use open https://example.com
browser-use state
browser-use click 0
browser-use screenshot example.png
browser-use close
```

Workflow:

1. Open or connect a browser.
2. Run `state` and copy only current element indices.
3. Interact with `click`, `input`, `keys`, waits, or JavaScript.
4. Capture evidence with `screenshot`, `get`, cookies, or `eval`.
5. Close the session when finished.

## Named Sessions for Parallel Tasks

```bash
browser-use --session research open https://news.ycombinator.com
browser-use --session app --headed open http://localhost:3000
browser-use sessions
browser-use --session research state
browser-use --session app screenshot app.png
browser-use --session research close
browser-use --session app close
```

Use named sessions when a user asks for parallel browsing contexts, multiple accounts, local app testing plus external research, or a cloud browser alongside a local browser.

Rules:

- Valid names use letters, digits, hyphens, and underscores.
- `BROWSER_USE_SESSION=work browser-use state` is an environment fallback.
- If a session is already running with a different explicit config, close it before changing `--headed`, `--profile`, `--cdp-url`, or cloud mode.

## Isolated Test Home

```bash
tmp_home="$(mktemp -d)"
BROWSER_USE_HOME="$tmp_home" browser-use --session smoke --json sessions
```

Use `BROWSER_USE_HOME` for tests or reproductions that should not touch the user’s normal CLI state. The CLI stores config, daemon state, tunnel metadata, and logs under this home.

## Visible Browser Debugging

```bash
browser-use --session debug --headed open https://example.com
browser-use --session debug state
browser-use --session debug screenshot debug.png
browser-use --session debug close
```

Use `--headed` when the user needs to watch automation, inspect a stuck UI, solve a manual login step, or compare CLI state with visual behavior.

## Real Chrome Profile

```bash
browser-use --session mail --profile "Default" open https://example.com
browser-use --session mail state
browser-use --session mail close
```

Use `--profile` when the user explicitly wants local Chrome cookies/extensions/profile state. The CLI resolves Chrome executable and profile directory. If profile lookup fails, it can list available profile display names/directories in the error.

Safety notes:

- Real profiles may contain logged-in sessions and sensitive cookies.
- Do not use a local profile in untrusted browsing tasks.
- If Chrome profile files are locked, close Chrome or use a separate session/profile.
- For Python profile parameters and browser profile hardening, route to `../../browser-control/SKILL.md`.

## Connect to Running Chrome

Start Chrome with remote debugging yourself, then connect:

```bash
browser-use --session local-cdp --cdp-url http://localhost:9222 open https://example.com
browser-use --session local-cdp state
browser-use --session local-cdp close
```

Or ask the CLI to discover a running Chrome CDP endpoint:

```bash
browser-use --session local-cdp connect
browser-use --session local-cdp state
```

Rules:

- Use `browser-use connect`, not deprecated `--connect`, for discovery.
- Use `--cdp-url` when the CDP endpoint is known.
- CDP URLs can be HTTP or WebSocket endpoints.
- Do not combine `--cdp-url` with `--profile`.

## Cloud Browser Session

```bash
browser-use cloud login <api-key>
browser-use --session cloud cloud connect
browser-use --session cloud open https://example.com
browser-use --session cloud state
browser-use --session cloud close
```

Behavior:

- `cloud login` saves the API key into CLI config.
- `cloud connect` creates or reuses `cloud_connect_profile_id` and starts the session in cloud mode.
- `open` may return a live viewer URL when the browser has a CDP URL.
- `close` disconnects the CLI session and stops the cloud browser for that session.

Config knobs:

```bash
browser-use config set cloud_connect_proxy us
browser-use config set cloud_connect_timeout 30
browser-use config set cloud_connect_recording true
```

Ask before provisioning cloud browsers, creating profiles, creating tasks, or changing persistent cloud config.

## Local App Through Tunnel and Cloud Browser

```bash
# Terminal 1: run the app using the project’s normal command.
# Example only: npm run dev

browser-use tunnel 3000
browser-use tunnel list
browser-use --session cloud cloud connect
browser-use --session cloud open https://example.trycloudflare.com
browser-use --session cloud state
browser-use --session cloud screenshot cloud-local.png
browser-use --session cloud close
browser-use tunnel stop 3000
```

Use this when a cloud browser must reach a local development server. Replace the tunnel URL with the actual `trycloudflare.com` URL printed by `browser-use tunnel <port>`.

Troubleshooting:

- If `cloudflared` is missing, run `browser-use doctor`; install `cloudflared` only with approval.
- If the tunnel URL is unavailable, check `tunnel list`, stop stale tunnels, and retry.
- If the local app is not reachable through the tunnel, confirm it is listening on the expected local port.

## Deterministic Form Fill

```bash
browser-use --session form open https://example.com/contact
browser-use --session form wait selector "form" --timeout 10000
browser-use --session form state
browser-use --session form input 0 "Jane Doe"
browser-use --session form input 1 "jane@example.com"
browser-use --session form click 2
browser-use --session form wait text "Success" --timeout 10000
browser-use --session form screenshot submitted.png
browser-use --session form close
```

Use `state` after the page is ready and before relying on indices. If a click fails with “Element index not found”, rerun `state` and update the index.

## Data Retrieval Without an Agent

```bash
browser-use --session scrape open https://news.ycombinator.com
browser-use --session scrape wait selector ".titleline" --timeout 10000
browser-use --session scrape eval "Array.from(document.querySelectorAll('.titleline a')).slice(0,5).map(a => a.textContent)"
browser-use --session scrape get title
browser-use --session scrape screenshot hn.png
browser-use --session scrape close
```

Use CLI `eval` and `get` for deterministic page data. Avoid CLI `extract` for production because it is parsed but not implemented.

## Persistent Python Automation

```bash
browser-use --session py open https://example.com
browser-use --session py python "print(browser.title)"
browser-use --session py python "browser.scroll('down', 500)"
browser-use --session py python "browser.screenshot('scrolled.png')"
browser-use --session py python --vars
browser-use --session py python --reset
browser-use --session py close
```

The `browser` wrapper runs browser operations synchronously against the session daemon. Good uses:

- Quick loops over scroll/click/wait actions.
- Debugging current URL/title/HTML.
- Saving screenshots from a live session.
- Running a short trusted script with `--file`.

Poor uses:

- LLM-driven task planning; route to `../../agent-programming/SKILL.md`.
- Custom Agent tools or action schemas; route to `../../tools-and-actions/SKILL.md`.
- Long production workflows; convert to Python API or sandbox guidance.

## Cookies Between Sessions

```bash
browser-use --session a open https://example.com
browser-use --session a cookies export cookies.json
browser-use --session a close

browser-use --session b open https://example.com
browser-use --session b cookies import cookies.json
browser-use --session b state
browser-use --session b close
```

Treat `cookies.json` as sensitive. Do not commit it, attach it to reports, or print contents unless the user explicitly asks and understands the risk.

## Recording a Session

```bash
browser-use --session demo --headed open https://example.com
browser-use --session demo record start demo.mp4
browser-use --session demo click 0
browser-use --session demo record status
browser-use --session demo record stop
browser-use --session demo close
```

Use recording for demonstrations and UI bug reports. Confirm disk path and privacy expectations before recording authenticated sessions.

## Translate CLI Steps to Python

When a user asks to convert a CLI workflow to Python:

- Keep the CLI evidence here: commands, session mode, URLs, waits, element strategy, screenshots.
- Route the Python API implementation to `../../agent-programming/SKILL.md` for `Agent` workflows or `../../browser-control/SKILL.md` for direct `BrowserSession` control.
- Preserve safe defaults discovered via CLI: use current URLs, waits, domain restrictions, and explicit close/cleanup.

Example routing note:

```text
The CLI workflow uses a cloud session plus local tunnel. Use this sub-skill for the tunnel/cloud CLI validation, then use production/browser-control guidance for Python `Browser(use_cloud=True)` or sandbox code.
```
