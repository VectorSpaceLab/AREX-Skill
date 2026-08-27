# Settings and Modes Troubleshooting

This guide focuses on configuration, mode, credential, host, terminal, and probe failures. For tracking API misuse, media objects, sync/upload, Open API calls, or integrations, route to the corresponding sibling sub-skill.

## Fast diagnosis checklist

1. What is the effective mode? Explicit `init(mode=...)` wins over most config sources.
2. Is a run already active? `swanlab.login`, `swanlab.merge_settings`, and `swanlab.require` must run before `swanlab.init` or after `swanlab.finish`.
3. Are there higher-priority config files? Check current-directory `swanlab.yaml`, `.env`, configured secrets, and `SWANLAB_*` env vars before blaming user config files.
4. Is this a credential problem or a host problem? Verify `api_host`, `web_host`, and whether the API key belongs to that host.
5. Is this environment non-interactive? Avoid prompts; provide `api_key`, choose `offline`, or choose `disabled`.
6. Could a probe or terminal capture be optional? Disable the relevant `Settings.Probe` or `Settings.Terminal` field instead of blocking the whole run when cloud upload is not the issue.

## Common failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `No API key provided and no stored API key found` | `swanlab.login()` or an online path has no explicit/configured/stored key. | Pass `api_key`, set `SWANLAB_API_KEY`, run `swanlab login --api-key ...`, or use `mode="offline"` / `mode="disabled"`. |
| `Failed to initialize SwanLab in online mode: no API key was provided, and interactive prompts are disabled` | `mode="online"`, no key, and `Settings.interactive=False`. | Provide a key explicitly or switch to `offline`/`disabled` for the run. |
| `Failed to initialize SwanLab in online mode: no TTY is available for interactive login` | Online init tried to prompt in a non-TTY job. | Use `swanlab login --api-key ...` before the job, set env/config credentials, or use non-online mode. |
| `Cannot prompt for API Key in no-tty environment` | CLI login needs masked input but stdin is not an interactive terminal. | Use `swanlab login --api-key "$SWANLAB_API_KEY"` or a config/env key. |
| `API Key not provided and interactive mode is disabled` | CLI prompt path is disabled by settings. | Set a key explicitly. Do not pass `interactive=` to `swanlab.login`; configure `Settings.interactive` or `SWANLAB_INTERACTIVE`. |
| `Stored API key is for ... but you are logging in to ...` | Host changed, but only an old key is available. | Provide the API key for the new host and use `relogin=True` if a client already exists. |
| `Host cannot be empty or whitespace` | `host`, `api_host`, or `web_host` was an empty string after stripping. | Omit the field to use defaults, or pass a real base host. Do not pass `""` as a placeholder. |
| Login succeeds but displayed run URL points at the API host | `web_host` was derived from `api_host`, or a stored credential has the wrong web host. | Set both `api_host` and `web_host` explicitly in a high-priority config source; re-apply `web_host` after `swanlab.login(host=...)` when API and web domains differ. |
| `merge_settings` / `login` / `require` complains about an active run | These functions are guarded to run only outside an active run. | Call `swanlab.finish()` first or move the call before `swanlab.init()`. |
| Mode CLI command seems ignored | A higher-priority source overrides the CLI-written config file. | Inspect current-directory `swanlab.yaml`, `.env`, secrets, and `SWANLAB_MODE`; remove or update the higher-priority source. |
| `Settings(log_dir=...)` or `merge_settings({"log_dir": ...})` raises `exists but is not a directory` | The selected log directory path already exists as a file. | Remove/rename the file or choose a directory path. |
| `probe.monitor_interval` validation error | The interval is below 5 seconds. | Use `monitor_interval >= 5` or disable `probe.monitor`. |
| `probe.monitor_disk_dir` validation error | The path does not exist or is not a directory. | Create the directory first, point to an existing directory, or avoid overriding this field. |
| Unknown requirement token | `swanlab.require(...)` received something other than `core`, `probe`, `core_python`, or `probe_python`. | Use a valid token. `SWANLAB_REQUIRE` accepts comma-separated valid tokens. |

## Blank or missing API key

Do not hard-code real API keys in examples or reusable scripts. Use one of these patterns:

```python
# CI/cloud upload: fail clearly when the secret is not injected.
import os
import swanlab
from swanlab import Settings

api_key = os.environ.get("SWANLAB_API_KEY")
if not api_key:
    raise RuntimeError("Set SWANLAB_API_KEY for online SwanLab upload, or run with mode='offline'.")

swanlab.init(mode="online", settings=Settings(interactive=False, api_key=api_key))
```

```python
# No-credential smoke test.
import swanlab

run = swanlab.init(mode="disabled", project="smoke")
swanlab.log({"ok": 1})
swanlab.finish()
```

```python
# Train now, upload later.
run = swanlab.init(mode="offline", project="train")
```

If a user says they already logged in, remember that Python `swanlab.login(save=False)` affects the current process but does not persist credentials for future processes. Use `save=True`, `save="root"`, `save="local"`, or the CLI if persistence is intended.

## Host cannot be empty

Host inputs are normalized, not treated as optional strings. These fail:

```python
Settings(api_host="")
Settings(web_host="   ")
swanlab.login(host="")
```

Use `None`/omit the argument for defaults:

```python
swanlab.login(api_key=api_key)  # default official host
```

Or pass a real base host:

```python
swanlab.login(api_key=api_key, host="https://api.example.internal")
```

Do not include `/api`, `/login`, query strings, or run paths; SwanLab strips routes and appends its own API paths.

## Custom/self-hosted host mismatch

Typical mismatch:

1. A key was saved for `https://api.old.example`.
2. The user now calls `swanlab.login(host="https://api.new.example")` without a key.
3. SwanLab refuses to reuse the old key.

Fix:

```python
swanlab.login(
    api_key=os.environ["SWANLAB_API_KEY_FOR_NEW_HOST"],
    host="https://api.new.example",
    relogin=True,
    save=True,
)
```

For split API/web domains, configure both hosts:

```python
from swanlab import Settings

settings = Settings(
    api_host="https://api.new.example",
    web_host="https://swanlab.new.example",
)
```

If `swanlab.login(host=...)` derives the web host incorrectly for the current process, merge the desired display host afterward:

```python
swanlab.login(api_key=api_key, host="https://api.new.example", save=False)
swanlab.merge_settings({"web_host": "https://swanlab.new.example"})
```

For persistent split-host setup, store `web_host` in a higher-priority config source. Stored netrc credentials alone may not preserve a distinct web domain after a `login(host=...)` call.

## Non-interactive login and init

Batch jobs should not wait for a prompt. Recommended patterns:

```bash
# Shell setup before Python starts.
export SWANLAB_API_KEY="..."
export SWANLAB_INTERACTIVE=false
python train.py
```

```python
# Inside train.py
import os
import swanlab
from swanlab import Settings

mode = "online" if os.environ.get("SWANLAB_API_KEY") else "offline"
swanlab.init(
    mode=mode,
    settings=Settings(interactive=False, api_key=os.environ.get("SWANLAB_API_KEY")),
)
```

If the code should never upload from CI, use `mode="disabled"` for smoke tests or `mode="offline"` for local records.

## Env/YAML/secret precedence surprises

Symptoms:

- `SWANLAB_MODE=offline` is set, but `Settings().mode` is still `online`.
- `swanlab disabled --local` was run, but training still uploads.
- A secret-injected API key is ignored.

Check sources from high to low:

1. Explicit `Settings(...)`, `merge_settings(...)`, or `init(...)` kwargs.
2. Current-directory `swanlab.yaml` / `swanlab.yml`.
3. System config YAML files selected by `SWANLAB_CONFIG_DIR` or the default system config directory.
4. Current-directory `.env`.
5. Secret files selected by `SWANLAB_SECRETS_DIR`.
6. `SWANLAB_*` environment variables.
7. Current-directory `.swanlab/config.yaml` / `.swanlab/config.yml`.
8. User configuration root `config.yaml` / `config.yml`.
9. Defaults and matching netrc fallback.

Useful probes:

```python
from swanlab import Settings

s = Settings()
print(s.to_yaml("mode", "api_host", "web_host", "probe.monitor", "terminal.proxy_type"))
print("explicit fields:", sorted(s.__pydantic_fields_set__))
```

The `__pydantic_fields_set__` output is a diagnostic aid: fields populated by high-priority sources or fallback credential loading often appear there and can affect merge behavior.

## Unexpected config or credential writes

`Settings()` itself should not write files. These operations intentionally write:

| Operation | Writes |
| --- | --- |
| `Settings(...).save_to_yaml(target_dir, ...)` | `target_dir/config.yaml`; creates `target_dir`. |
| `swanlab disabled`, `swanlab offline`, `swanlab local`, `swanlab online` | User config root `config.yaml`. |
| Same mode commands with `--local` | Current directory `.swanlab/config.yaml` and helper ignore file. |
| `swanlab login` CLI | User credential store by default; current directory `.swanlab` credential store with `--local`. |
| `swanlab.login(..., save=True)` / `save="root"` | User credential store. |
| `swanlab.login(..., save="local")` | Current directory `.swanlab` credential store. |
| Non-disabled `swanlab.init(...)` | Run directories under `log_dir`. |

If a user needs a no-write check, use the bundled checker or run `swanlab.init(mode="disabled")` with a temporary `log_dir` and assert that the directory remains absent.

## Optional hardware/environment probe failures

Hardware and environment probes are useful metadata, but many pieces are optional. Vendor accelerators, Conda export, Git discovery, package snapshots, and disk/terminal capture can fail or be undesirable in constrained environments.

Mitigations:

```python
from swanlab import Settings

safe_probe = Settings.Probe(
    hardware=False,
    runtime=False,
    requirements=False,
    conda=False,
    git=False,
    swanlab=False,
    monitor=False,
)

safe_terminal = Settings.Terminal(proxy_type="none")
```

Then pass or merge:

```python
swanlab.init(mode="offline", settings=Settings(probe=safe_probe, terminal=safe_terminal))
```

Boundaries:

- Disabling `hardware` alone does not necessarily prevent monitor internals from inspecting hardware if `monitor=True`.
- Disabling `runtime` avoids recording hostname/current working directory/command metadata.
- Disabling `requirements` avoids dependency snapshots.
- Disabling `git` avoids Git branch/commit/remote metadata.
- Disabling terminal proxying does not disable experiment metric logging; it only stops stdout/stderr capture.
