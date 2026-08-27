# CLI and Session Troubleshooting

Use this when `browser-use`/`bu` commands fail, sessions become stale, cloud/config is confusing, or a user needs concrete debug steps.

## First Response Checklist

Collect:

- Exact command and shell/OS.
- Exit code, stdout, and stderr.
- Whether the command used `browser-use`, `bu`, `browseruse`, or `browser`.
- Whether the session is default or named with `--session`/`BROWSER_USE_SESSION`.
- Whether it uses local Chromium, `--headed`, `--profile`, CDP, cloud, tunnel, or `python --file`.
- Whether running browser launch, cloud provisioning, profile sync, or setup/install is safe in the current environment.

Then run the least invasive checks first:

```bash
browser-use --help
browser-use init --help
browser-use cloud v2 --help
browser-use sessions
```

Run `browser-use doctor` when environment checks and network probes are acceptable.

## Command Not Found

Symptoms:

- `browser-use: command not found`
- `bu: command not found`
- Shell cannot find the command after install.

Fixes:

```bash
python -m browser_use.skill_cli.main --help
uv pip install "browser-use[cli]"
```

- If the module command works but console scripts do not, the environment’s script directory is not on `PATH` or the wrong virtual environment is active.
- Restart the terminal after installer-based PATH changes.
- Prefer `uv` for environment management in this repository.
- On Windows, Git Bash/PowerShell path differences can require restarting the shell or invoking through Git Bash.

## CLI Addon or Import Failure

Symptoms:

- Legacy TUI reports `CLI addon is not installed`.
- Import errors for CLI dependencies.
- Help command fails in a minimal environment.

Fixes:

```bash
uv pip install "browser-use[cli]"
browser-use --help
browser-use doctor
```

Notes:

- The fast persistent CLI entrypoint is `browser_use.skill_cli.main`.
- The legacy TUI entrypoint is separate and may require heavier dependencies.
- For package-level Python imports, route to root installation guidance or Python API sub-skills.

## Chromium or Browser Startup Failure

Symptoms:

- Browser will not launch.
- `doctor` warns browser may not be available.
- Playwright browser missing.

Fixes:

```bash
browser-use install
browser-use doctor
browser-use --session debug --headed open https://example.com
```

- `browser-use install` uses `uvx playwright install chromium`; Linux includes `--with-deps`.
- In headless servers, visible `--headed` mode requires display support.
- If the user wants a faster production browser and has a Browser Use API key, suggest cloud browser options and route Python `Browser(use_cloud=True)` guidance to `../../production-integrations/SKILL.md`.

## Stale Session, Socket, or Daemon

Symptoms:

- `Failed to start daemon`.
- Session says it is alive but socket unreachable.
- Command reports session already running with different config.
- Browser died but session files remain.

Fixes:

```bash
browser-use sessions
browser-use --session NAME close
browser-use --session NAME --headed open https://example.com
```

If many sessions are stale and the user accepts closing all CLI browsers:

```bash
browser-use close --all
```

Why this works:

- Each session has its own daemon PID, socket/TCP port, token, and state files.
- Explicit config changes require a fresh session when the existing daemon has different `--headed`, `--profile`, `--cdp-url`, or cloud settings.
- Session names must contain only letters, digits, hyphens, and underscores; invalid names fail early.

## Element Index Changed

Symptoms:

- `Element index N not found - page may have changed`.
- Click/input/select/upload targets the wrong element.
- Modal or auto-dismissed dialog changed the page.

Fixes:

```bash
browser-use wait selector "main" --timeout 10000
browser-use state
browser-use click <new-index>
```

- Re-run `state` after navigation, reload, tab switch, modal close, DOM mutation, or scroll.
- Use `wait selector` or `wait text` before collecting state on dynamic apps.
- Use coordinate clicks only when indices are impossible and the page layout is stable.

## Upload Failure

Symptoms:

- `File not found`.
- `Not a file`.
- `File is empty (0 bytes)`.
- `Element N is not a file input`.

Fixes:

```bash
ls -l path/to/file
browser-use state
browser-use upload <file-input-index> path/to/file
```

- The CLI requires the upload path to exist, be a file, and be non-empty.
- If the chosen element is not a file input, the CLI may report nearby file input indices; use those.
- For secure file tooling inside Agent workflows, route to `../../tools-and-actions/SKILL.md`.

## CLI `extract` Fails

Symptom:

- `extract is not yet implemented`.

Fix:

- Use `get`, `eval`, or `screenshot` for deterministic CLI retrieval.
- For LLM-backed extraction, route to `../../agent-programming/SKILL.md` and `../../llm-and-output/SKILL.md`.

## Cloud API Key Missing

Symptoms:

- `Error: No API key found.`
- Stderr says `BROWSER_USE_API_KEY env var is set but not used by the CLI`.

Fixes:

```bash
browser-use cloud login <api-key>
# or, if the env var is already set and should be used by the CLI:
browser-use config set api_key "$BROWSER_USE_API_KEY"
browser-use config list
```

Notes:

- Do not print the key in logs.
- `config list` should display sensitive values as set/redacted rather than exposing the key.
- Cloud REST commands read API key from CLI config.

## Cloud REST Error

Symptoms:

- `HTTP 400`/`401`/`404` with exit code `2`.
- `poll` shows `failed`.
- Invalid JSON response.

Fixes:

```bash
browser-use cloud v2 --help
browser-use cloud v2 GET /tasks/<task-id>
browser-use cloud v2 POST /tasks '{"task":"Search for AI news","url":"https://google.com"}'
```

- Confirm API version (`v2` or `v3`) and path.
- Quote JSON bodies correctly for the user’s shell.
- On 4xx, the CLI may print an expected body example from OpenAPI; adapt the body rather than guessing.
- Ask before creating tasks or polling long-running cloud tasks.

## Cloud Connect Conflict

Symptoms:

- `--connect and cloud connect are mutually exclusive`.
- `--cdp-url and cloud connect are mutually exclusive`.
- `--profile and cloud connect are mutually exclusive`.

Fix:

```bash
browser-use --session cloud cloud connect
```

Do not combine cloud connect with local Chrome connection modes. Use separate named sessions if the user needs both local and cloud browsers.

## Local CDP Connection Failure

Symptoms:

- `No Chrome CDP endpoint found`.
- Cannot connect to `http://localhost:9222`.
- Browser state unavailable after `connect`.

Fixes:

```bash
browser-use --session cdp connect
browser-use --session cdp state
# or with a known endpoint:
browser-use --session cdp --cdp-url http://localhost:9222 state
```

- Ensure Chrome was started with remote debugging enabled if using a known CDP URL.
- Use only one connection mode: CDP or profile, not both.
- For Python CDP/browser session parameters, route to `../../browser-control/SKILL.md`.

## Profile Failure

Symptoms:

- Could not find Chrome executable.
- Unknown profile name.
- `profile-use` missing in doctor.
- Profile sync asks for auth or fails.

Fixes:

```bash
browser-use doctor
browser-use profile update
browser-use profile list
browser-use --profile "Default" open https://example.com
```

- Real Chrome profile names can be display names or directory names; if unknown, use the profiles listed by the tool.
- Close Chrome if profile files are locked.
- Ask before syncing local profiles/cookies to cloud.

## Tunnel Failure

Symptoms:

- `cloudflared not installed`.
- No `trycloudflare.com` URL appears.
- Local app is unreachable from cloud browser.
- Tunnel survives after the shell exits.

Fixes:

```bash
browser-use doctor
browser-use tunnel list
browser-use tunnel stop <port>
browser-use tunnel stop --all
browser-use tunnel <port>
```

- Install `cloudflared` only with user approval.
- Confirm the local app is listening on the expected port before starting the tunnel.
- Tunnels are independent daemon processes tracked by port metadata; stop them explicitly.

## Config Validation Error

Symptoms:

- `Unknown config key`.
- Invalid value for boolean/integer config.
- Cloud connect ignores expected value.

Fixes:

```bash
browser-use config list
browser-use config set cloud_connect_proxy us
browser-use config set cloud_connect_timeout 30
browser-use config set cloud_connect_recording false
browser-use config unset cloud_connect_timeout
```

Valid keys are `api_key`, `cloud_connect_profile_id`, `cloud_connect_proxy`, `cloud_connect_timeout`, and `cloud_connect_recording`.

## Init/Template Failure

Symptoms:

- `init --list` cannot fetch templates.
- Template generation fails with network error.
- Output file already exists.

Fixes:

```bash
browser-use init --list
browser-use init --template basic --output browser_use_basic.py
browser-use init --template basic --output browser_use_basic.py --force
```

- `init` fetches template list/content at runtime, so offline environments can fail.
- Use `--force` only after confirming overwrite is acceptable.
- If templates are unavailable, write a minimal Python Agent script via `../../agent-programming/SKILL.md` instead.

## `browser-use python` Error

Symptoms:

- `No code provided`.
- `File not found` or path is a directory for `--file`.
- Python traceback from the persistent namespace.
- Browser wrapper timeout or no active browser session.

Fixes:

```bash
browser-use --session py open https://example.com
browser-use --session py python "print(browser.url)"
browser-use --session py python --vars
browser-use --session py python --reset
```

- Open/connect a browser before browser-dependent Python code.
- `--file` executes local code; inspect the file and avoid untrusted scripts.
- Use `--reset` when namespace state causes confusing behavior.

## Security Guardrails

- Do not log API keys, cookie JSON contents, local profile paths with sensitive usernames, or browser live URLs unless the user requests them for debugging.
- Ask before `cloud signup`, `cloud connect`, `cloud v* POST`, profile sync, tunnel creation, broad `close --all`, setup/install that mutates the machine, or recording authenticated browsing.
- Avoid `eval` with untrusted JavaScript.
- Treat screenshots, videos, cookies, profile sync, and cloud live URLs as potentially sensitive.
