# Aim CLI and service troubleshooting

## `aim` or `aim-watcher` is not found

Symptoms:

- Shell prints `command not found`.
- A smoke script cannot locate the executable.

Checks:

```bash
python -m pip show aim
python -m pip install aim
python -m pip check
```

Then ensure the Python environment's console-script directory is on `PATH`, or pass an explicit executable path to the bundled smoke script with `--aim-bin` and `--watcher-bin`.

## `Cannot find repository ... Please init first`

Cause: the command constructed a `Repo` from a directory that does not contain `.aim`. This can happen even for nested converter help because the `convert` command group opens the repo before dispatching subcommands.

Fix:

```bash
mkdir -p <repo_dir>
aim init --repo <repo_dir> --skip-if-exists
aim convert --repo <repo_dir> tensorboard --help
```

Avoid using `-y` for initialization on an existing repo unless the user explicitly wants to clear and recreate it.

## UI does not start or exits immediately

Checks:

1. Verify the repo exists: `aim init --repo <repo_dir> --skip-if-exists`.
2. Run `aim up --help` to confirm the command is available.
3. Try a different port or `--port 0`.
4. Use `--log-level debug` only for diagnosis.
5. If using `--base-path`, test both the root proxy path and the service's printed URL.
6. If using `--ssl-keyfile`/`--ssl-certfile`, confirm the files are readable by the service process and match each other.

Remember that `aim up` is long-running. In automation, do not call it unless you also manage process lifetime and shutdown.

## Remote SDK client cannot connect

Symptoms may include connection errors that ask whether `aim server` is running, WebSocket failures, or version mismatch warnings/errors.

Checklist:

1. Confirm the server process is `aim server`, not only `aim up`.
2. Confirm the client URL uses the SDK form: `aim://host:port` or `aim://host:port/base-path`.
3. Check firewall/security-group rules for the server port.
4. If behind a reverse proxy, ensure it forwards WebSocket upgrades as well as HTTP requests.
5. If `--base-path` is used on the server, include the same path in the `aim://` URL.
6. Match client and server Aim versions when possible; the client checks remote compatibility.
7. For self-signed TLS, configure the client certificate bundle with `__AIM_CLIENT_SSL_CERTIFICATES_FILE__` and protect key material.

## UI behind a reverse proxy shows broken assets or wrong URLs

Use `aim up --base-path <path>` when the UI is mounted under a prefix. Examples:

```bash
aim up --repo <repo_dir> --host 127.0.0.1 --port 43800 --base-path /aim
```

Proxy `/aim/` to the service and preserve the path prefix. Do not reuse the UI base path as the tracking API base path unless the proxy routes both services intentionally.

## `aim convert ... --help` fails before showing subcommand help

Initialize a scratch repo and pass `--repo` before the converter subcommand:

```bash
aim init --repo <scratch_repo_dir> --skip-if-exists
aim convert --repo <scratch_repo_dir> tensorboard --help
```

For actual conversion, ensure the source logs and optional third-party credentials/dependencies are available. Route detailed TensorBoard/framework conversion work to `framework-integrations`.

## Storage appears slow, stale, or inconsistent

Start with non-destructive commands:

```bash
aim runs --repo <repo_dir> ls
aim runs --repo <repo_dir> ls --corrupted
```

Then choose the smallest maintenance action:

- stale active runs but processes are dead: `aim runs close <hashes>`;
- corrupted runs confirmed and backed up: `aim runs rm --corrupted` or `aim runs rm <hashes>`;
- deleted runs still appear in autocomplete metadata: `aim storage prune`;
- index inconsistency: `aim storage reindex`;
- old metric layout: `aim storage upgrade 3.11+ <hashes>`.

Stop writers and services before mutating commands. Do not use `aim init -y` as a repair operation because it reinitializes an empty repository.

## Read-only confusion

The CLI supports `aim up --read-only` for the UI. In the inspected package, opening `Repo(read_only=True)` from Python is not implemented. If the user asks about read-only SDK access patterns, route to `tracking-sdk` for the current API caveats.

## Watcher/notifier problems

- `aim-watcher start` is long-running and may prompt for notifier configuration.
- For safe local tests, configure a logger notifier rather than Slack or Workplace.
- Slack uses a webhook URL; Workplace uses a group ID and access token. Treat these as secrets.
- If notifier changes do not take effect, restart `aim-watcher start` after changing config.
- Use `aim-watcher --repo <repo_dir> notifiers list` and `get-log-level` to inspect state without sending notifications.

## Notebook UI issues

Notebook magic must be loaded first:

```jupyter
%load_ext aim
%aim version
%aim up --repo=./my-aim-repo --port=43801
```

The magic parser expects `--name=value` style options for supported fields. If an iframe is blank on a hosted notebook platform, use the platform's proxy URL option and verify that the selected port is reachable.

## Cleanup and temporary directories

When using Aim SDK objects, call `run.finalize()` before deleting a temporary repository. Do not remove a repository directory while a Python process may still hold RocksDB locks or background tracking/finalizer work. CLI-only `aim init` smoke checks are safe to run in a dedicated scratch directory.
