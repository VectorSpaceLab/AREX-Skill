# W&B Local Configuration

## Settings Sources to Inspect

For local CLI work, inspect these sources before changing behavior:

- Active environment variables beginning with `WANDB_`.
- Workspace settings in the active W&B directory, typically `wandb/settings` or `.wandb/settings` under the project root.
- System/user credential sources such as `.netrc`, without printing secrets.
- Current CLI-resolved settings via `wandb status`.

Use the bundled inspector for a read-only view:

```bash
python sub-skills/cli-and-local-workflows/scripts/inspect_wandb_local_state.py --root .
```

## Important Environment Variables

Authentication and server selection:

- `WANDB_API_KEY`: API key used by login and SDK authentication. Never print its raw value.
- `WANDB_BASE_URL`: target W&B API/server URL, especially for self-hosted or dedicated deployments.
- `WANDB_IDENTITY_TOKEN_FILE`: identity-token based auth path; when set, explicit API-key login can be a no-op in Python login flows.
- `WANDB_CREDENTIALS_FILE`: alternate credentials file path.
- `NETRC`: alternate `.netrc` path used by credential lookup.

Project/run routing:

- `WANDB_ENTITY`: default user or team.
- `WANDB_PROJECT`: default project.
- `WANDB_RUN_ID`: explicit run ID.
- `WANDB_RESUME`: resume behavior.
- `WANDB_RUN_GROUP`: run grouping.
- `WANDB_JOB_TYPE`: job type.
- `WANDB_TAGS`: run tags.

Local paths and caches:

- `WANDB_DIR`: root directory for local W&B run data.
- `WANDB_CONFIG_DIR`: configuration directory override.
- `WANDB_DATA_DIR`: data directory override.
- `WANDB_CACHE_DIR`: cache directory override.
- `WANDB_ARTIFACT_DIR`: artifact download/logging directory override.
- `WANDB_RUN_DIR`: explicit run directory override.

Behavior controls:

- `WANDB_MODE`: common values are `online`, `offline`, and `disabled`.
- `WANDB_SILENT` / `WANDB_QUIET`: reduce terminal output.
- `WANDB_DISABLE_CODE`: disable code saving.
- `WANDB_DISABLE_GIT`: disable git probing.
- `WANDB_IGNORE_GLOBS`: ignore files matching globs.
- `WANDB_HTTP_TIMEOUT`: HTTP timeout.
- `WANDB_INIT_TIMEOUT`: init startup timeout.
- `WANDB_INSECURE_DISABLE_SSL`: disables SSL verification; avoid except for explicit debugging in trusted environments.

## Modes

Prefer the CLI mode commands when changing the current workspace:

```bash
wandb offline
wandb online
wandb disabled
wandb enabled
```

- Offline mode is recoverable: runs still write local `.wandb` transaction logs and can be uploaded later with `wandb sync`.
- Disabled mode is not a local queue: W&B functionality is off, so there may be no run data to recover.
- Online mode restores normal syncing for future runs but does not automatically upload old offline runs; run `wandb sync` for that.
- Environment variable `WANDB_MODE` can override persisted settings for the current process or shell.

## Workspace Settings Files

The SDK computes the workspace settings path as `settings` under the active W&B directory. The active W&B directory is normally:

- `wandb/` under the project root, or
- `.wandb/` when dot-W&B mode is in use or that directory already exists.

Common layout:

```text
project-root/
  wandb/
    settings
    offline-run-YYYYMMDD_HHMMSS-RUN_ID/
      run-RUN_ID.wandb
    run-YYYYMMDD_HHMMSS-RUN_ID/
      run-RUN_ID.wandb
    latest-run -> ...
```

`wandb init` may write a `wandb/.gitignore` that ignores generated run data while preserving the settings file.

## Offline Run Layout

Offline runs use directory names beginning with `offline-run-`; online or incomplete run directories commonly begin with `run-`. Each run directory contains a binary transaction log named `run-<RUN_ID>.wandb`. `wandb sync` accepts either the run directory or the `.wandb` file.

Before syncing:

1. Run the inspector or list candidate directories.
2. Run `wandb sync` with no arguments to summarize local candidates.
3. Confirm `WANDB_BASE_URL`, entity, and project.
4. Sync one explicit run path first when possible.
5. Avoid `--clean` until the upload has been verified externally.

## Non-Interactive CI Setup

A safe CI pattern for self-hosted W&B:

```bash
export WANDB_BASE_URL="https://wandb.example.com"
export WANDB_ENTITY="my-team"
export WANDB_PROJECT="my-project"
export WANDB_MODE="online"
# Inject WANDB_API_KEY through the CI secret manager, not source files.
wandb login --host "$WANDB_BASE_URL" --verify
wandb status
```

For offline CI that uploads later:

```bash
export WANDB_MODE="offline"
python train.py
wandb sync
```

Then in an authorized upload step:

```bash
export WANDB_BASE_URL="https://wandb.example.com"
wandb login --host "$WANDB_BASE_URL" --verify
wandb sync --sync-all --project "$WANDB_PROJECT" --entity "$WANDB_ENTITY"
```

## Redaction Rules

When reporting local state to a user or another agent:

- Redact `WANDB_API_KEY`, credential file contents, `.netrc`, tokens, cookies, and authorization headers.
- Prefer showing whether a credential source is present rather than its value.
- Show server URLs, modes, entity, project, and path existence when useful.
- Do not copy machine-specific paths into reusable skill content or documentation.
