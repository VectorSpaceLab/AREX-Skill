# SwanLab Modes and Credentials

Use this reference to choose run modes, configure login, avoid credential leaks, and handle custom or self-hosted hosts. Route actual offline-run upload to `sync-and-converters` and normal training-loop instrumentation to `experiment-tracking`.

## Mode selection

| Mode | Network / credential behavior | File behavior | Best fit |
| --- | --- | --- | --- |
| `disabled` | No cloud login or upload. | Returns a usable `Run` object for API compatibility but should not create log directories or persist run data. | Unit tests, examples, CI smoke checks, docs that must run without credentials. |
| `offline` | Does not require login at run creation. | Writes local run records for later upload. | Training now without network/API key, then syncing later from the run directory. |
| `local` | Does not require cloud login for the run. | Writes local run records and local-dashboard artifacts. | Local dashboard workflows and no-cloud tracking. |
| `online` | Requires a valid API key/client. May prompt only when `interactive=True` and a TTY is available. | Writes local support files and uploads to the configured API host. | Cloud or self-hosted server tracking with credentials. |

Quick choices:

```python
# Safe in tests and snippets; no credentials or network.
run = swanlab.init(mode="disabled", project="smoke")

# Produce local records now; sync later in a separate step.
run = swanlab.init(mode="offline", project="train")

# Use local dashboard behavior.
run = swanlab.init(mode="local", project="train")

# Cloud/self-hosted upload; ensure credentials first.
swanlab.login(api_key="...", host="https://api.example.internal")
run = swanlab.init(mode="online", project="train")
```

## How mode is chosen at runtime

For a run, effective settings are merged in this order from lower to higher priority:

1. Config sources loaded by `Settings()`.
2. Process-global settings changed with `swanlab.merge_settings(...)`.
3. The `settings=Settings(...)` object passed to `swanlab.init(...)`.
4. Explicit `swanlab.init(...)` keyword arguments such as `mode="disabled"`.
5. Online-mode prompt fallback: if `mode="online"`, no client exists, no API key is available, and the process is interactive, a user can choose to enter a key, register, or continue in offline mode.

Use explicit `mode=` in reusable examples when the desired behavior is important. Use persisted CLI mode defaults only for a user's own machine or project.

## Persisting mode with the CLI

SwanLab provides four mode commands:

```bash
swanlab disabled
swanlab local
swanlab offline
swanlab online
```

Add `--local` to write the setting for only the current working directory:

```bash
swanlab offline --local
```

Behavior:

- Without `--local`, the command writes the selected `mode` into the user configuration root.
- With `--local`, it writes the selected `mode` into the current directory's `.swanlab/config.yaml` and creates `.swanlab` plus a `.gitignore` helper when needed.
- The CLI mode file is a low-priority source compared with a current-directory `swanlab.yaml`, `.env`, configured secrets, and environment variables. If a mode command appears ineffective, inspect higher-priority sources first.
- Use `Settings(...).to_yaml("mode")` to inspect what would be written without creating files.

## Python login API

```python
import swanlab

swanlab.login(
    api_key="your-api-key",     # optional if already configured or stored
    relogin=False,              # True forces a new login when a client exists
    host="https://api.example", # optional custom API host
    save=False,                 # False, True, "root", or "local"
    timeout=10,
)
```

Key rules:

- `swanlab.login` must run before `swanlab.init`; it is blocked while a run is active.
- If a client already exists and `relogin=False`, login returns `True` without a new network request.
- Explicit `api_key` and `host` override environment variables and stored netrc credentials for that call.
- If no `api_key` is supplied, SwanLab tries the current settings snapshot. If no stored/configured key exists, it raises an authentication error instead of prompting in the non-CLI API path.
- If `host` changes and SwanLab only has an old stored key, login raises an authentication error rather than reusing a key for the wrong host.
- `save=False` keeps the credential in the current process settings after successful login but does not write a credential file.
- `save=True` and `save="root"` write to the user credential store; `save="local"` writes to the current directory's `.swanlab` credential store.

## CLI login and auth commands

```bash
# Interactive login; saves to the user credential store.
swanlab login

# Non-interactive login; recommended for CI when a key is injected securely.
swanlab login --api-key "$SWANLAB_API_KEY"

# Custom host and forced re-login.
swanlab login --api-key "$SWANLAB_API_KEY" --host https://api.example.internal --relogin

# Directory-local credential file.
swanlab login --api-key "$SWANLAB_API_KEY" --local

# Check or clear stored credentials.
swanlab verify
swanlab logout --force
```

Behavior:

- CLI login always saves credentials (`root` by default, `local` with `--local`).
- Without `--api-key`, CLI login prompts with masked input only when `Settings.interactive` is true and a TTY is available.
- `swanlab verify --local` and `swanlab logout --local` target the directory-local credential store.
- `swanlab logout` asks for confirmation unless `--force` is used; in non-interactive settings, use `--force`.

## Credential storage and netrc fallback

SwanLab credential files use netrc-style fields:

| Netrc field | SwanLab meaning |
| --- | --- |
| `machine` | `api_host` |
| `login` | `web_host` |
| `password` | `api_key` |

Important details:

- Stored credentials are used only as a fallback when `api_key` was not explicitly provided through a higher-priority source.
- If `api_host` was explicitly set and does not match the stored credential host, SwanLab skips the stored key to avoid cross-host leakage.
- Credential writes use a single-login model: writing a new host/key replaces prior entries in that credential file.
- Credential writes reject whitespace and newlines in host, username/web host, and password/API key fields.
- New credential files are created owner-readable/writable only where the platform supports it.

For CI or shared scripts, prefer environment injection plus `interactive=False` and avoid writing credentials:

```python
import os
import swanlab
from swanlab import Settings

swanlab.merge_settings(Settings(
    interactive=False,
    api_key=os.environ.get("SWANLAB_API_KEY"),
    api_host=os.environ.get("SWANLAB_API_HOST", "https://api.swanlab.cn"),
))
```

## API host versus web host

`api_host` drives SDK HTTP calls. `web_host` is used for displayed browser URLs and login instructions.

Host normalization rules:

- `custom.example.com/api/v1?x=1` becomes `https://custom.example.com`.
- `http://10.0.0.1:8080/api/` becomes `http://10.0.0.1:8080`.
- Blank or whitespace-only hosts raise an immediate validation error.
- If only `api_host` is set, `web_host` is usually derived from it.
- If only `web_host` is set, `api_host` remains the official default.
- Official API host values keep the official web host instead of showing the API subdomain as the browser URL.

For custom or self-hosted deployments, pass the base API host, not a route such as `/api/login/api_key`:

```python
from swanlab import Settings

settings = Settings(
    api_host="https://api.swanlab.example",
    web_host="https://swanlab.example",
    mode="online",
)
```

If the API and web domains differ:

1. Set both `api_host` and `web_host` in a high-priority config source or explicit `Settings` object.
2. Login with an API key for the same `api_host`.
3. Do not reuse a credential saved for another host; force relogin with the correct key.
4. Remember that Python `swanlab.login(host=...)` derives `web_host` from the host argument for that login call. Re-apply a separate `web_host` setting afterward if your deployment uses different API and web domains.

## Non-interactive online initialization

Online `swanlab.init` fails early when all of these are true:

- mode is `online`;
- no authenticated client exists;
- no `api_key` is available from explicit settings, config, env, secret, or stored credential;
- prompts are disabled or no TTY is available.

Fix one of those conditions:

```python
# Prefer for CI with cloud upload.
swanlab.init(mode="online", settings=Settings(interactive=False, api_key=os.environ["SWANLAB_API_KEY"]))

# Prefer for CI without cloud upload.
swanlab.init(mode="disabled")

# Prefer when you need records for later upload.
swanlab.init(mode="offline")
```

## Safe privacy settings for probes and terminal capture

Use these settings when an environment should avoid hostname, command, dependency, Git, hardware, or terminal capture:

```python
from swanlab import Settings

privacy_settings = Settings(
    probe=Settings.Probe(
        hardware=False,
        runtime=False,
        requirements=False,
        conda=False,
        git=False,
        swanlab=False,
        monitor=False,
    ),
    terminal=Settings.Terminal(proxy_type="none"),
)
```

Notes:

- `probe.monitor=False` disables periodic utilization monitoring.
- `probe.hardware=False` disables static hardware persistence, but if `monitor=True`, monitor code may still inspect hardware to compute dynamic metrics.
- `probe.monitor_disk_dir` must be an existing directory.
- Resume of an existing online run may disable hardware collection, requirements, conda, Git, SwanLab metadata, monitoring, and terminal proxying for that resumed run.
