# W&B CLI Reference for Local Workflows

## Entrypoints and Safe Discovery

- Use `wandb` as the primary CLI. `wb` is installed as an equivalent console script in supported installs.
- `python -m wandb` routes through the same Click CLI, which is useful when the console script path is uncertain.
- Safe non-mutating discovery commands:
  - `wandb --help`
  - `wandb <command> --help`
  - `wandb status`
  - `wandb sync` with no path or `--sync-all`; this prints a summary and does not upload.
- CLI failures write detailed tracebacks to a `debug-cli.<user>.log` file under the active W&B directory when possible, or a temporary directory fallback.

## Authentication

`wandb login [OPTIONS] [KEY]...` stores credentials for future CLI and SDK calls.

Important options:

- `--host` / `--base-url <url>`: authenticate against a self-hosted or dedicated W&B instance.
- `--cloud`: use the public W&B cloud and conflicts with `--host`.
- `--relogin`: ignore existing credentials and force a fresh login path.
- `--verify` / `--no-verify`: verify credentials after storing them.

Credential lookup order when no key argument is supplied:

1. `WANDB_API_KEY` environment variable.
2. API key in system or workspace settings.
3. `.netrc` (`~/.netrc`, `~/_netrc`, or `NETRC`).
4. Interactive prompt when a TTY is available.

Safer patterns:

```bash
WANDB_API_KEY="$WANDB_API_KEY" wandb login --host https://wandb.example.com --verify
wandb login --cloud --verify
wandb login --relogin --verify
```

Avoid placing literal API keys in shell history, process lists, CI logs, issue comments, or skill content.

## Workspace Initialization

`wandb init` creates or updates local W&B settings for the current directory.

Non-interactive forms:

```bash
wandb init --project my-project --entity my-team
wandb init --project my-project --entity my-team --mode offline
wandb init --reset
```

Behavior to remember:

- `--project`, `--entity`, `--mode`, and `--reset` take the non-interactive path.
- `--reset` clears local `entity`, `project`, and `mode` settings.
- Without options, `wandb init` may prompt, authenticate if needed, query the viewer, ask for entity/project, and write local settings.
- Initialization also ensures the local W&B directory exists and writes a `.gitignore` that ignores generated run data while preserving settings.

## Mode Commands

Use mode commands to control future runs launched from the configured directory.

```bash
wandb offline
wandb online
wandb disabled
wandb enabled
```

- `wandb offline`: sets local mode to `offline`; future runs write metadata and history locally without uploading.
- `wandb online`: clears the offline mode setting so future runs sync normally.
- `wandb disabled`: sets mode to `disabled`; future SDK calls do not log or sync run data.
- `wandb enabled`: sets mode to `online`; it does not recover anything skipped while disabled.
- Hidden legacy aliases `wandb off` and `wandb on` route to offline/online.

Use offline mode when the user wants recoverable local data. Use disabled mode only when logging should be completely turned off.

## Status

`wandb status` prints resolved active settings as formatted JSON, including values such as base URL, entity, project, mode, and credential-related fields.

Safety notes:

- Treat `wandb status` output as potentially sensitive.
- Redact credential-like fields before sharing logs.
- Run it before and after `wandb init`, `wandb offline`, `wandb online`, `wandb disabled`, or self-hosted login changes.

## Offline Run Sync

`wandb sync [PATH]...` uploads existing local run data when given paths or `--sync-all`.

Safe inspection first:

```bash
wandb sync
wandb sync --show 20
```

The no-argument form summarizes synced and unsynced local runs without uploading. It searches for a local W&B directory and reports candidates.

Typical paths:

```text
./wandb/offline-run-YYYYMMDD_HHMMSS-RUN_ID/run-RUN_ID.wandb
./wandb/run-YYYYMMDD_HHMMSS-RUN_ID/run-RUN_ID.wandb
./wandb/run-YYYYMMDD_HHMMSS-RUN_ID/
```

Sync explicit paths when possible:

```bash
wandb sync ./wandb/offline-run-YYYYMMDD_HHMMSS-abcd1234/run-abcd1234.wandb \
  --project my-project --entity my-team
```

Use broad sync only after review:

```bash
wandb sync --sync-all --project my-project --entity my-team
```

Useful sync options:

- `--include-offline` / `--no-include-offline`: include or exclude offline runs.
- `--include-online` / `--no-include-online`: include or exclude online runs.
- `--include-synced` / `--no-include-synced`: include or exclude already-synced runs.
- `--include-globs` and `--exclude-globs`: filter by comma-separated glob patterns.
- `--id <run-id>`: upload a single local run to an existing run ID.
- `--append`: append to an existing run instead of creating a new run.
- `--skip-console`: omit console logs during sync.
- `--replace-tags old=new,...`: rename tags during sync.
- `--mark-synced` / `--no-mark-synced`: control whether local records are marked synced after upload.
- `--sync-tensorboard` / `--no-sync-tensorboard`: specific paths default to TensorBoard sync on; `--sync-all` defaults off.

Destructive cleanup:

```bash
wandb sync --clean
wandb sync --clean --clean-old-hours 48
wandb sync --clean --clean-old-hours 48 --clean-force
```

- `--clean` deletes local data for synced runs only.
- With explicit paths, `--clean` removes those resolved run directories after confirmation.
- Without paths, `--clean` selects synced runs older than `--clean-old-hours`.
- Never add `--clean-force` unless the user explicitly accepts deletion.

## Cache Cleanup

`wandb purge-cache` deletes files from the local W&B cache by age.

```bash
wandb purge-cache --age 7d
wandb purge-cache --age 7d --force
```

- `--age` accepts durations such as `10s`, `5m`, `8h`, `7d`, `6M`, or `1y`.
- Without `--force`, the CLI prompts for each file.
- This targets cache files, not active run directories; still treat it as destructive.

## Docker Wrapping

W&B provides two Docker helpers:

```bash
wandb docker-run <docker-run-args...>
wandb docker [OPTIONS] [docker-run-args...] [docker-image]
```

`wandb docker-run` wraps an existing `docker run` invocation and may inject:

- `WANDB_API_KEY` when the host is logged in.
- `WANDB_DOCKER` when the image can be resolved.
- `--runtime nvidia` automatically when `nvidia-docker` is detected and no runtime is set.

`wandb docker` starts a configured container, mounts the current directory at `/app` by default, injects W&B Docker metadata, and can run a shell, command, or JupyterLab.

Safety notes:

- Run `wandb docker --help` or `wandb docker-run --help` before constructing commands.
- Confirm Docker is installed/running before recommending these commands.
- Avoid echoing API keys; let the CLI inject credentials when present.
- Use `--no-dir` when the current directory should not be mounted.

## Self-Hosted Verification

`wandb verify --host <url>` runs integration checks against a self-hosted W&B instance and exits non-zero on critical failures.

```bash
wandb verify --host https://wandb.example.com
```

Behavior and caveats:

- The command sets verification-specific environment values and runs in a temporary working directory.
- If `--host` differs from the configured base URL, the CLI resets its internal API object for the target host.
- It performs networked checks including login, GraphQL/upload URL, HTTPS/security, run, artifact, and sweep checks.
- Do not use it as a dry-run against the public cloud; it is intended for self-hosted or dedicated deployments.
- Do not run it when uploads or test objects are disallowed by the user's environment.
