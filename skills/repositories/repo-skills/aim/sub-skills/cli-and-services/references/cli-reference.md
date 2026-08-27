# Aim CLI reference for safe operation

This reference covers the installed console scripts `aim` and `aim-watcher`. The verified Aim CLI exposes version `Aim v3.29.1` and the command groups below.

## Entry points

| Entry point | Purpose | Safe default checks |
| --- | --- | --- |
| `aim` | Main CLI for repository initialization, UI/server, conversion discovery, run management, and storage maintenance. | `aim --help`, `aim version`, `aim <group> --help` |
| `aim-watcher` | Long-running watcher service and notifier configuration for stuck/failed runs. | `aim-watcher --help`, `aim-watcher --repo <repo> notifiers --help` |

Always pass an explicit `--repo <repo_dir>` when the command acts on an Aim repository. Aim stores data in a `.aim` directory under that repository directory.

## `aim` top-level commands

`aim --help` lists these commands:

- `init` — initialize a repository.
- `version` — print the installed Aim version.
- `up` — run the local web UI.
- `server` — run the remote tracking server.
- `runs` — manage run data.
- `storage` — maintain/update repository data formats and indexes.
- `convert` — discover conversion commands for third-party logs.

The global `-v, --verbose` flag prints that verbose mode is on; it is not a substitute for service log-level flags.

## Safe repository initialization

Use the non-destructive initialization form when automation may rerun:

```bash
aim init --repo <repo_dir> --skip-if-exists
```

Available flags:

- `--repo DIRECTORY` — parent directory where `.aim` lives or will be created. The directory itself must already exist.
- `-y, --yes` — automatically confirm prompts. Dangerous when the repo already exists because reinitialization clears old Aim data.
- `-s, --skip-if-exists` — skip initialization if `.aim` already exists. Prefer this for smoke checks and setup scripts.

Avoid `aim init --repo <repo_dir> -y` on a directory that may already contain important Aim data unless the user explicitly asked for reinitialization.

## Version and help discovery

Safe checks:

```bash
aim version
aim up --help
aim server --help
aim runs --help
aim storage --help
aim convert --help
aim-watcher --help
```

Some nested `aim convert ... --help` calls construct a repository before showing help. If the current directory is not an initialized Aim repo, pass `--repo <initialized_repo>` before the converter subcommand.

## `aim up`: local UI command

`aim up` starts a long-running web UI. Do not run it as a background side effect of a skill smoke test.

Verified options:

- `-h, --host TEXT` — host interface. Default is local loopback for UI operation.
- `-p, --port INTEGER` — UI port. Default is `43800`; `0` requests a free port.
- `-w, --workers INTEGER` — Uvicorn worker count.
- `--uds FILE` — serve on a Unix domain socket instead of host/port.
- `--repo DIRECTORY` — repository directory.
- `--tf_logs PATH` — path to TensorFlow/TensorBoard logs for UI-side use.
- `--dev` — development mode; enables debug logging/reload behavior.
- `--ssl-keyfile FILE`, `--ssl-certfile FILE` — TLS key/certificate files.
- `--base-path TEXT` — mount UI under a path prefix for reverse proxy/notebook-style hosting. Aim normalizes a missing leading slash and removes a trailing slash.
- `--profiler` — enable API profiling; writes profiler output into the Aim repository.
- `--log-level TEXT` — Python logging level, such as `info`, `warning`, or `debug`.
- `-y, --yes` — confirm repository initialization prompt.
- `--read-only` — run the UI in read-only mode.

Safe pattern before launch:

```bash
aim init --repo <repo_dir> --skip-if-exists
aim up --repo <repo_dir> --host 127.0.0.1 --port 43800 --log-level warning
```

Use `--host 0.0.0.0` only when the machine is intended to accept external traffic and access is controlled by firewall, VPN, or a reverse proxy.

## `aim server`: remote tracking command

`aim server` starts a long-running remote tracking API for SDK clients that send data to `aim://...` URLs.

Verified options:

- `-h, --host TEXT` — bind host. Default is `0.0.0.0` for the tracking server.
- `-p, --port INTEGER` — tracking server port. Default is `53800`; `0` requests a free port.
- `--repo DIRECTORY` — repository directory.
- `--ssl-keyfile FILE`, `--ssl-certfile FILE` — TLS key/certificate files.
- `--base-path TEXT` — mount the API under a path prefix.
- `--log-level TEXT` — Python logging level.
- `--dev` — development mode.
- `-y, --yes` — confirm repository initialization prompt.

Safe pattern before launch:

```bash
aim init --repo <repo_dir> --skip-if-exists
aim server --repo <repo_dir> --host 0.0.0.0 --port 53800 --log-level warning
```

Run `aim up --repo <repo_dir>` separately when users also need the browser UI.

## `aim runs`: run management

Top-level option:

- `--repo TEXT` — repository directory or supported remote repository URL.

Subcommands from verified help:

| Command | Purpose | Safety notes |
| --- | --- | --- |
| `aim runs ls` | List run hashes. | Safe; add `--corrupted` to list only corrupted runs. |
| `aim runs rm [HASHES]...` | Permanently remove run data. | Destructive; requires hashes or `--corrupted`; use `-y` only after explicit confirmation. |
| `aim runs cp --destination <dest> [HASHES]...` | Copy runs to another repo. | Mutating at destination; verify source/destination and hashes. |
| `aim runs mv --destination <dest> [HASHES]...` | Move runs to another repo. | Destructive at source; copy first if unsure. |
| `aim runs upload <bucket>` | Upload a repository backup snapshot to S3. | Requires `boto3` and AWS credentials; do not run without credential and bucket confirmation. |
| `aim runs close [HASHES]...` | Force-close failed/stalled runs. | Mutating; ensure runs are not active. |
| `aim runs update-metrics` | Separate sequence metadata for optimal reads. | Mutating; stop active writers and UI first. |

Hash arguments may use shell globs such as `'*'`, but quote them so the shell does not expand them before Aim sees them.

## `aim storage`: repository storage maintenance

Top-level option:

- `--repo TEXT` — repository directory.

Subcommands from verified help:

| Command | Purpose | Safety notes |
| --- | --- | --- |
| `aim storage upgrade 3.11+ [HASHES]...` | Optimize run metric data for read access. | Mutating; backs up per-run data internally, but still create an external backup first. |
| `aim storage restore [HASHES]...` | Restore backed-up run metric data. | Mutating; match only intended backup hashes. |
| `aim storage prune` | Remove dangling/orphan params/sequences with no referring runs. | Mutating; backup first. |
| `aim storage reindex` | Recreate index database from scratch. | Mutating; stop UI and writers first. |

## `aim convert`: conversion command discovery

Top-level option:

- `--repo DIRECTORY` — initialized Aim repository to write converted data into.

Verified subcommands and flags:

| Command | Required options | Other options | Notes |
| --- | --- | --- | --- |
| `aim convert tensorboard` | `--logdir PATH` | `-f, --flat`; `--no-cache` | Converts TensorBoard event logs. Detailed event-log workflows route to `framework-integrations`. |
| `aim convert tf` | `--logdir PATH` | `-f, --flat` | Deprecated alias for TensorBoard conversion. Prefer `tensorboard`. |
| `aim convert mlflow` | none if `MLFLOW_TRACKING_URI` is set | `--tracking_uri TEXT`; `-e, --experiment TEXT` | Requires MLflow source access. |
| `aim convert wandb` | `--entity TEXT`; `--project TEXT` | `--run-id TEXT` | Requires Weights & Biases source access/credentials if private. |

This sub-skill should identify the correct converter and flags. For framework-specific logging/callback conversion details, route to `framework-integrations`.

## `aim-watcher`: watcher and notifier CLI

Top-level option:

- `--repo DIRECTORY` — repository whose run statuses should be watched.

Commands:

- `aim-watcher --repo <repo_dir> start` — starts a long-running watcher service. It may prompt to configure notifiers or use a default logger notifier.
- `aim-watcher --repo <repo_dir> notifiers list` — list configured notifiers.
- `aim-watcher --repo <repo_dir> notifiers add` — interactive notifier setup.
- `aim-watcher --repo <repo_dir> notifiers add logger [--message TEXT]` — stdout logger notifier; safest for local testing.
- `aim-watcher --repo <repo_dir> notifiers add slack --webhook-url <url> [--message TEXT]` — Slack webhook notifier; credential-sensitive.
- `aim-watcher --repo <repo_dir> notifiers add workplace --group-id <id> --access-token <token> [--message TEXT]` — Workplace notifier; credential-sensitive.
- `aim-watcher --repo <repo_dir> notifiers enable <notifier-id>` / `disable <notifier-id>` / `remove <notifier-id>` — mutate notifier state.
- `aim-watcher --repo <repo_dir> notifiers get-log-level` — show notification log level.
- `aim-watcher --repo <repo_dir> notifiers set-log-level {CRITICAL|ERROR|WARNING|INFO|DEBUG}` — set notification log level.

For tests and examples, use the logger notifier only. Never include real webhook URLs or access tokens in saved commands.
