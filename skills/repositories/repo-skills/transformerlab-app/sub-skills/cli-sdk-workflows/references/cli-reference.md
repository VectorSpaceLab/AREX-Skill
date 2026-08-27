# Transformer Lab CLI Reference

This reference distills the CLI behavior needed to modify or debug command flows without depending on the original repository checkout. It assumes the `transformerlab-cli` package version `0.0.68` and Typer entry point `lab`.

## Architecture and boundaries

- The CLI is a Typer application with Rich output. It is an HTTP client for the Transformer Lab API and does **not** import or depend on the Python SDK.
- Most commands are non-interactive Typer commands. They take options, call the API wrapper, and render pretty or JSON output.
- The job monitor (`lab job monitor`) is a Textual application for humans. Use it only for live terminal navigation, not scripted automation.
- CLI changes that require server route semantics, storage layout, job scheduling, or provider orchestration should be coordinated with the backend/API and task-execution sub-skills.

## Root app, global flags, and command groups

The root app registers these command groups: `version`, `config`, `status`, `login`, `logout`, `whoami`, `task`, `job`, `notes`, `provider`, `server`, `dataset`, `model`, `experiment`, `team`, and `profile`.

Root callback state:

- `--format pretty|json` writes `cli_state.output_format`.
- `--profile <name>` chooses the active profile for this process.
- `--no-interactive` writes `cli_state.no_interactive`; JSON format implies `no_interactive=True`.
- The update-available check is skipped for `version` and for JSON format to keep machine output clean.

Typer root options must be placed before the command group:

```bash
lab --format json job list
lab --profile staging task list
lab --no-interactive team setup --name local --type local --no-check
```

Do not write documentation or tests that place root flags after the subgroup, such as `lab team --format json secret list`. Some subcommands also have command-local `--no-interactive` flags; those flags belong after the subgroup and affect only that command.

Per-command experiment overrides use `--experiment` / `-e` on experiment-scoped commands. The helper resolves an explicit experiment by first validating config and base URL, otherwise it requires `current_experiment` from config.

## Profiles, config, and authentication

Profile selection is per process; there is no stored current-profile pointer.

Precedence:

1. root `--profile <name>`
2. `LAB_PROFILE`
3. `default`

Profile names must contain only letters, digits, `.`, `_`, and `-`, and cannot be blank or dot-only. The default profile uses the legacy root config/credentials location. Named profiles are isolated under a per-profile directory. Profile commands:

- `lab profile list` shows all profiles, marks the active one, and records whether credentials exist.
- `lab profile show [name]` renders a profile's server, team, user, current experiment, and credential presence.
- `lab profile delete <name>` removes a named profile; `default` cannot be deleted.

Valid config keys are `server`, `team_id`, `team_name`, `user_email`, and `current_experiment`. Required config keys are `server`, `team_id`, and `user_email`. `server` values must be valid HTTP(S) URLs and are normalized without a trailing slash. Changing `server` clears `current_experiment`.

Auth model:

- The CLI uses API-key auth, not browser cookies.
- `lab login` can use `--api-key` for CI/headless workflows, a browser loopback flow for normal users, or paste mode for SSH/headless sessions.
- Successful login validates the API key, writes profile-scoped credentials, fetches `/users/me` and `/users/me/teams`, and stores user/team config.
- All normal API requests include `Authorization: Bearer <api_key>` and, when configured, `X-Team-Id: <team_id>`.
- `lab status` validates config in JSON-compatible mode and prints `/healthz`.

## API wrapper and output conventions

The HTTP utility provides sync helpers: `get`, `post`, `post_json`, `post_text`, `put`, `put_json`, `patch`, `delete`, and `check_server_status`.

Transport behavior:

- Normal Typer commands catch HTTP transport errors, print a formatted or JSON error, and exit `1`.
- The Textual monitor enables transport re-raise so background workers can fail quietly and keep the UI alive.
- Timeout messages should mention that the API may be unreachable, slow, or waiting on a backend service.

Output behavior:

- Pretty mode uses the shared Rich console, `render_table`, `render_object`, panels, progress bars, and spinners.
- JSON mode must print only JSON or JSONL to stdout. Avoid Rich status contexts and update-check output in JSON mode.
- `render_table(..., format_type="json")` dumps the raw list; pretty mode renders Rich tables.
- `exit_with_no_results(format_type, message)` exits with code `2`. In JSON mode it prints `{"error": message}`; in pretty mode it prints a warning-like message.
- For retryable empty logs, log commands return exit `0` with retry metadata instead of using no-results exit.

## Task command workflows

Task commands operate on REMOTE tasks under the resolved experiment.

### `lab task list`

- Without `--subtype`, calls a REMOTE task list endpoint.
- With `--subtype interactive`, calls the subtype-filtered endpoint.
- Unknown subtype values are rejected locally before hitting the API.
- JSON output must be a clean array.

### `lab task init`

Default mode creates `task.yaml` and, if absent, `main.py` in the current directory.

- Refuses to overwrite `task.yaml` unless `--force` is passed.
- Skips an existing `main.py` rather than overwriting it.
- JSON mode prints created/skipped metadata and does not prompt.
- Interactive mode prompts for task name, resources, optional accelerators, setup, and run command. It writes only `task.yaml`; it does not create `main.py`.
- Interactive mode can use an editor for the setup/run YAML snippet when a TTY is available.

The bundled task-init template is reference material only: it demonstrates `lab.init()`, `lab.log()`, `lab.update_progress()`, `lab.save_artifact()`, `lab.finish()`, and `lab.error()`. If adapting it in future runtime material, keep it self-contained in the skill tree.

### `lab task add`, `validate`, `edit`, and `upload`

- `validate` parses YAML locally, then posts the raw YAML text for server validation. In JSON mode success is `{"ok": true, "path": ...}` and parse/API failures are structured errors.
- Adding from a directory requires `task.yaml`, validates it, shows file inventory, zips the directory, uploads it with the generic chunked-upload pipeline, then submits the upload id to the task create endpoint.
- `--dry-run` previews directory add/edit without submitting.
- `--from-git` submits the repository URL. If the server reports missing `task.yaml`, non-interactive mode retries with a default-template flag; pretty interactive mode asks first.
- `edit --from-file` replaces only YAML; `edit --from-dir` replaces YAML plus attachments by uploading a zipped directory. `--from-file` and `--from-dir` are mutually exclusive.
- `upload` zips a local file or directory, uses generic chunk upload, and attaches the upload to an existing task.

### `lab task queue`

Queueing is a CLI facade over provider launch. Route deep provider semantics to the task-execution sub-skill.

Steps:

1. Resolve and validate the experiment exists.
2. Fetch the task.
3. Optionally show current resources and prompt for overrides in interactive mode.
4. Fetch providers.
5. Provider selection:
   - `--provider` resolves by exact id or case-insensitive name and skips provider prompting.
   - Interactive mode prompts when no provider flag is supplied.
   - Non-interactive mode falls back to the task's pinned `provider_id`, then the provider with `is_default`, then the first provider.
6. Parameter handling:
   - `--param` / `-p` accepts repeatable `KEY=VALUE` strings.
   - Values are parsed as YAML scalars, so booleans/floats remain typed.
   - Split only on the first `=` so values may contain `=`.
   - Unknown parameter names fail; using `--param` on a task with no `parameters` block fails.
7. `--description` / `-m` becomes the launch payload description. `-m -` reads from stdin and fails if stdin is a TTY.
8. `--enable-profiling-torch` requires `--enable-profiling`.
9. `--spot` writes `use_spot=True` into the launch config and warns if the selected provider does not advertise spot support.
10. `--image` writes `docker_image` into the launch config.
11. The launch payload merges parameter overrides, spot, and image in `config`; resource fields are pulled from overrides, top-level task fields, or task config.

### Gallery and interactive tasks

- `task gallery` fetches either all gallery records or the interactive gallery; `--import <id>` imports directly.
- `task interactive` delegates to the interactive task flow and has many resource/env/provider/template options. Use `--format json` before `task` for machine-readable output where supported.

## Job command workflows

Jobs are experiment-scoped and should preserve JSON/pretty parity.

### Listing and details

- `job list` fetches REMOTE jobs, optionally filters active statuses (`WAITING`, `LAUNCHING`, `RUNNING`, `INTERACTIVE`), sorts by a `job_data.score` metric, and exposes a derived `discarded` boolean in JSON mode.
- Pretty rows include ID, experiment, task name, status, progress, completion status, description, score, and duration.
- `job info` returns details plus files; interactive jobs also fetch tunnel/connection info. JSON mode embeds files and tunnel info when available.
- Score formatting treats dict keys as named metrics and hides the internal `discard` flag from display.

### Logs

- `job machine-logs` reads provider/machine logs.
- `job task-logs` reads task SDK output and must use the one-shot task-log endpoint, not an SSE stream.
- `job request-logs` reads provider request/launch logs.
- Deprecated hidden `job logs` delegates to `machine-logs`.
- `--follow` on machine/task logs polls every two seconds, prints only new lines, and stops after the job leaves an active status.
- JSON log output is an object with `job_id`, `logs`, and `line_count`. Retryable not-ready responses preserve `message`, `retryable`, and `retry_after_seconds` and exit cleanly.
- Missing final logs use `exit_with_no_results`, giving exit code `2`.

### Metrics and artifacts

- `job metrics <job_id>` reads rows from the metrics endpoint. Pretty output is a table with time, step, progress, and selected metric keys. `--json` emits JSONL rows. `--keys a,b` filters metric columns. `--tail` applies only to non-follow mode.
- `job artifacts <job_id>` lists artifact filename/path/size and exits `2` if no artifacts exist.
- `job download <job_id>` downloads all artifacts as a zip by default. With repeated `--file` patterns, it first lists artifacts, fnmatch-filters filenames, downloads individual files when supported, and falls back to the all-artifacts zip if needed. No matches exit `2`; JSON mode prints downloaded file records.
- `job chart` requires `--output/-o` or `--share`. Chart export downloads PNG bytes. Sharing uses the share helper and JSON mode must not prompt.
- `job discard` toggles `job_data.score.discard` via a JSON update and returns JSON in JSON mode.
- `job publish dataset|model` publishes named job outputs to the registry. In JSON mode the asset name is required; pretty mode may prompt.
- `job stop` requests server stop and then best-effort provider-cluster stop to mirror GUI behavior.
- `job delete` and `job delete-all` support command-local `--no-interactive`; JSON success is `{"deleted": ...}`.

## Textual job monitor

`lab job monitor` launches a full-screen Textual app and is intentionally human interactive.

Key behavior:

- Loads config, sets base URL, and optionally passes the requested experiment through a temporary environment override.
- Enables transport-error re-raise while the app runs, then restores normal API behavior.
- Uses the Tokyo Night theme, a left job list, right job details, artifacts, connection info, and a log panel.
- Auto-refreshes job list every 10 seconds unless paused.
- Keyboard bindings: quit, refresh, set experiment, add task, task list, interactive task, gallery, and pause/resume.
- Log panel polls provider logs every 3 seconds for the selected job.
- Connection info for interactive jobs is fetched from tunnel info and retried for about a minute.

Do not drive this TUI from non-interactive agents. Prefer `lab --format json job list`, `job info`, `job machine-logs`, `job task-logs`, `job request-logs`, `job metrics --json`, and `job artifacts`.

## Asset upload/download helpers

Model and dataset upload/download commands share generic helpers.

Path walking:

- File input yields one file with basename as server relative path.
- Directory input walks recursively.
- Hidden entries are skipped.
- Symlinks are skipped, including top-level symlinks.
- Relative paths are normalized to POSIX-style, must be non-empty, non-absolute, not end in `/`, contain no NULs, and contain no empty, `.`, or `..` segments.

Upload helper:

1. `POST /upload/init` with filename and size.
2. `GET /upload/{upload_id}/status` to skip already-received chunk indices.
3. `PUT /upload/{upload_id}/chunk?chunk_index=N` with binary chunk bytes.
4. `POST /upload/{upload_id}/complete` with total chunk count.
5. Domain command posts the upload id plus relpath to its model/dataset/task endpoint.

Model upload finalizes the model after all files succeed and exits `2` if any file was skipped due to conflict. Dataset upload also exits `2` on skipped files. Use `--force` to overwrite server-side files.

Download helper:

- Uses authenticated HTTP Range requests.
- If the target file already has exactly the server size, it skips.
- If the target is smaller, it resumes from the local byte count.
- If the target is larger, it deletes and restarts.
- Size mismatch after download is a hard error.

## Provider, team, and server command surfaces

Provider commands include list/add/info/update/delete/check/gpus/verify-lifecycle/enable/disable/set-default/clear-default. Keep CLI validation/output here; provider health and lifecycle semantics belong to the task-execution sub-skill.

Team commands include setup, info, rename, secret management, members, invitations, and quota. `team setup` can be interactive or scripted with root `--no-interactive`; it delegates provider creation, can set provider default, stores secrets, and optionally runs provider health check.

Server commands:

- `server install` writes a server environment config and can run interactively, use `--config <file>` to install from a prewritten env file, or `--dry-run` to preview without writing. It refuses to run from inside the install source directory because installation replaces that directory.
- `server start --port N [--foreground]` checks the port, requires an installed `run.sh`, and starts foreground or background. Background mode logs to the product server log and only verifies the launcher did not exit immediately.
- `server stop --port N [--force]` finds listeners with platform tools and sends TERM or KILL.
- `server restart` stops then starts, escalating to KILL if needed.
- `server version` reports installed/latest and can emit JSON.
- `server update` checks latest release and reruns install after confirmation.

## CLI testing patterns

Use `typer.testing.CliRunner` and patch at the module seam that the command imports.

Common patterns:

```python
from typer.testing import CliRunner
from transformerlab_cli.main import app

runner = CliRunner()
result = runner.invoke(app, ["--format", "json", "job", "list"])
assert result.exit_code == 0
```

- Patch `transformerlab_cli.commands.task.api.get` when testing `task` code that imported `api` into that module.
- Patch `transformerlab_cli.util.api.httpx.Client` only for transport-layer tests.
- Patch experiment resolution helpers to avoid depending on local config.
- Assert JSON output with `json.loads(result.output.strip())` to catch Rich/spinner leakage.
- Assert no API call happens when local validation should fail.
- For prompts, pass `input="...\n"`; for non-interactive behavior, use root `--format json` or the command-local/global `--no-interactive` flag being tested.
- Keep tests idempotent and deterministic; do not require a live server except for explicitly marked integration routes.

High-value regression tests when adding a new non-interactive JSON task option:

1. Invoke as `lab --format json task <command> ...` and assert stdout is valid JSON with no Rich text or prompt text.
2. Invoke malformed input and assert a structured error, non-zero exit, and no API call.
3. If the option changes launch behavior, patch provider/task fetches and assert the exact launch payload field.
