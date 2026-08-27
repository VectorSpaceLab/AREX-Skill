# CLI and SDK Troubleshooting

Use this page when a future task is a bug report, failed test, or unclear behavior across the CLI, SDK, storage context, or remote wrapper.

## Quick triage matrix

| Symptom | Likely surface | First checks |
|---|---|---|
| `Missing required configuration keys` | CLI config/profile | Active profile, `server`, `team_id`, `user_email`, root flag ordering |
| API request has auth but no team context | CLI auth/config | `X-Team-Id` header requires `team_id` in active profile config |
| JSON output contains Rich table/spinner/update text | CLI output formatting | Root `--format json`, command uses `cli_state.output_format`, no `console.status` in JSON branch |
| `--profile` appears ignored | Root option ordering/profile selection | `--profile` must be before subgroup; `LAB_PROFILE` only used without root override |
| `lab team setup --format json` fails or prompts | Root option ordering | Use `lab --format json --no-interactive team setup ...` |
| `job artifacts` or logs exit `2` | No-results behavior | Empty final result uses `exit_with_no_results`; retryable not-ready logs exit `0` |
| Textual monitor hangs automation | Wrong interface | Use JSON Typer commands instead of `job monitor` |
| `lab.finish(score=0.7)` does not show score | SDK score shape | Score must be a dict, e.g. `{"score": 0.7}` |
| Storage unexpectedly falls back or errors | SDK dirs/storage context | Check organization context, `TFL_STORAGE_PROVIDER`, `TFL_STORAGE_URI`, and credentials |
| Remote job has no provider logs | `tfl-remote-trap` / storage | Check `_TFL_JOB_ID`, `_TFL_EXPERIMENT_ID`, storage write access, and wrapper invocation |

## Missing server, API key, or team

The CLI request layer needs three pieces of profile state:

- `server` for the base API URL.
- Profile-scoped API key credentials for `Authorization: Bearer ...`.
- `team_id` for `X-Team-Id` on protected routes.

Diagnosis:

1. Confirm root option ordering: `lab --profile <name> profile show` or `lab --format json profile show`.
2. If the profile has no credentials, run `lab --profile <name> login --api-key <key> --server <url>` for CI/headless flows or use the normal login flow for users.
3. If `team_id` or `user_email` is missing, login may have failed to fetch user/team data. Retry login or set only documented config keys through `lab config set` when you know the values.
4. If `server` changed recently, expect `current_experiment` to be cleared; set it again or pass `--experiment` on the command.
5. For API-key auth issues, verify the key against the configured server, not another profile's server.

Common pitfall: a named profile can have valid config but no credentials. `profile list` reports credential presence; `profile show` reports config values.

## Global option ordering failures

Typer root options belong immediately after `lab`:

```bash
# Correct
lab --format json job list
lab --profile prod config get server
lab --no-interactive team setup --name local --type local --no-check

# Wrong
lab job list --format json
lab config get server --profile prod
lab team setup --no-interactive   # this may be command-local only, not the root flag
```

When adding docs or tests, use root flags in `runner.invoke` arrays before the command group:

```python
runner.invoke(app, ["--format", "json", "task", "list"])
runner.invoke(app, ["--profile", "prod", "--format=json", "config", "get", "server"])
```

## JSON output contamination

If JSON tests fail with parse errors:

1. Verify the invocation used root `--format json`, not a command-specific flag except for command-local JSONL options such as `job metrics --json`.
2. Ensure command code branches on `cli_state.output_format` or an explicit format value before entering `console.status`.
3. Do not print config header tables in JSON mode. Config validation intentionally returns without rendering headers for JSON callers.
4. Do not let version/update checks run for JSON mode.
5. For errors, print a single JSON object and exit with `typer.Exit(1)` or `SystemExit(2)` for no-results.
6. For JSONL commands such as `job metrics --json`, emit one JSON object per line and avoid an enclosing array.

Regression assertion:

```python
payload = json.loads(result.output.strip())
assert result.exit_code == 0
```

This catches spinners, Rich formatting, and stray warning lines.

## CLI test dependency drift

Symptoms:

- A focused CLI test around interactive task editing fails before the command runs with an error like `module 'typer' has no attribute 'edit'`.
- The installed Typer version satisfies a loose package constraint but no longer exposes an API that current source or tests monkeypatch.

Recovery:

1. Treat this as dependency drift, not as proof that the CLI command route is wrong.
2. Inspect the current `transformerlab-cli` dependency constraints and the Typer version in the test environment.
3. Prefer pinning or constraining Typer to a version that provides the API expected by the source/tests, or refactor the command/tests to use a supported editor abstraction.
4. Re-run the focused CLI tests after the dependency or source fix. Do not hide Rich prompts or interactive editor calls in `--format json` or `--no-interactive` automation paths.

## Profile config and `LAB_PROFILE`

Expected precedence is root `--profile` > `LAB_PROFILE` > `default`.

Failure modes:

- Invalid profile names should fail before command execution and print JSON if root format is JSON.
- Blank `LAB_PROFILE` should fall through to `default`.
- There is no `profile use`; selection is per process only.
- Profile initialization resets cached config. If a test mutates active profile state manually, reset caches or invoke through the root app callback.

Tests should isolate the config root and environment. When a test reads another profile, use profile path helpers rather than switching process-wide active state unless that is exactly what the test covers.

## No-results and retryable-not-ready behavior

No-results is a distinct outcome from API failure:

- Use exit code `2` for empty final results such as no artifacts or unmatched artifact patterns.
- JSON no-results output is `{"error": message}`.
- Pretty no-results output is a simple warning-like line.

Do not use exit code `2` for logs that are still expected to appear. If the API returns a retryable not-ready payload, preserve the retry message and metadata and exit `0`.

## Textual monitor is not an automation interface

`lab job monitor` is for a human terminal session. It has background workers, interval refresh, keyboard bindings, modals, and a live Rich/Textual layout.

For agents and scripts, replace monitor usage with:

- `lab --format json job list --running`
- `lab --format json job info <job_id>`
- `lab --format json job machine-logs <job_id>`
- `lab --format json job task-logs <job_id>`
- `lab --format json job request-logs <job_id>`
- `lab job metrics <job_id> --json`
- `lab --format json job artifacts <job_id>`

If the monitor itself fails to refresh, check the API wrapper's transport re-raise state and the monitor's experiment override. It should restore both when exiting.

## Task queue payload bugs

When queue behavior is wrong, inspect the launch payload rather than guessing provider internals.

Checklist:

- Did `resolve_experiment_id` select the expected experiment?
- Did queue validate the experiment exists before fetching the task?
- Did non-interactive provider selection choose pinned provider id, default provider, or first provider as intended?
- Does `--provider` resolve by exact id or case-insensitive name?
- Are `--param` values parsed as YAML scalars and merged into `config`?
- Are unknown parameters rejected before launch?
- Are `--spot` and `--image` merged into the same `config` object without clobbering user params?
- Does `--enable-profiling-torch` fail unless base profiling is enabled?
- Does `-m -` fail with a clear error when stdin is a TTY?

Patch `launch_task_on_provider` or the module's API post helper in tests and assert the exact payload.

## Job logs, metrics, and artifacts

Log confusion is common:

- Machine/provider logs come from the remote wrapper and launch/provider layer.
- Task logs come from SDK `lab.log` / `Job.log_info` output.
- Request logs are provider request/launch diagnostics.
- Metrics rows come from SDK `update_progress(..., metrics=..., step=...)`, not final score.
- Final score comes from SDK `finish(score={...})` and appears in job list/info score fields.

If logs are missing:

1. Check whether the job is still launching and the API returned retryable metadata.
2. Check the correct log command. Do not use machine logs when you need SDK task output.
3. For remote wrapper logs, confirm the command was launched through `tfl-remote-trap` and has `_TFL_JOB_ID` plus experiment id in the environment.
4. Confirm storage writes are possible for the job directory.
5. If stdout/stderr is huge, remember remote trap periodically appends and finally overwrites provider logs with full content.

If metrics are missing:

- The task may only call `lab.update_progress(progress)` without a metrics dict.
- `job metrics --json` emits JSONL, not an array.
- `job list` score column uses `job_data.score`, not metrics JSONL.

If artifacts are missing:

- `lab.save_artifact` may not have been called after `lab.init`.
- Save helper may have failed path existence checks.
- For model/dataset artifacts, inspect job data fields such as generated models/datasets as well as generic artifacts.
- `job artifacts` exits `2` for no artifacts; handle that separately from API failures.

## SDK score scalar bug and final score issues

Symptom: a job completes successfully, but `lab job list` and `lab job info` show no score or only `discard=False`.

Cause: `Lab.finish` only copies score values when `score` is a dict. A scalar is ignored by the merge step.

Fix task code:

```python
# Wrong
lab.finish(score=0.82)

# Right
lab.finish(score={"score": 0.82})
# Better when metric name is known
lab.finish(score={"accuracy": 0.82})
```

Test pattern:

1. Initialize a `Lab()` instance in an isolated workspace.
2. Call `finish(score={"accuracy": 0.95})`.
3. Assert status is `COMPLETE`, progress is `100`, completion status is `success`, and `job_data["score"] == {"accuracy": 0.95, "discard": False}`.

If you choose to harden implementation behavior, add a test for scalar input that either rejects with a clear `TypeError` or maps it deliberately to `{"score": value}`. Do not silently preserve the current ambiguous behavior in new examples.

## SDK called from async code

Sync facade methods deliberately fail when an event loop is already running.

Symptoms:

- Runtime error says a sync method cannot be used in an async context.
- Jupyter/async service code calls `lab.save_artifact` or `lab.get_job_data` from inside an async handler.

Fix:

- Use `await lab.async_save_artifact(...)`, `await lab.async_save_dataset(...)`, `await lab.async_save_checkpoint(...)`, `await lab.async_save_model(...)`, or other async variants.
- Keep examples for normal task scripts sync unless the script is explicitly async.

## Storage credentials and organization context

Storage errors often come from missing context rather than missing files.

Checklist:

1. Confirm storage provider mode and URI.
2. For API-server or background paths in multi-org storage, call `set_organization_id(team_id)` before storage access.
3. For code paths that require org context, use `require_organization_id()` early so failures are clear.
4. For remote pods, confirm `TFL_STORAGE_URI` is already an org/team-scoped workspace URI.
5. For localfs multi-org mode, expect paths under `TFL_STORAGE_URI/orgs/<team>/workspace`.
6. For JuiceFS mode, API-server context should map to a `workspace-<team>` bucket through the local gateway.
7. For cloud storage, verify provider-specific fsspec credentials (AWS profile, GCP project, Azure account/connection/SAS/key, or JuiceFS gateway credentials).
8. If stale listings appear, use uncached filesystem paths or resource methods that already request uncached reads.

Do not catch `Organization context is required` and fall back to single-tenant paths. That can leak data across teams.

## Asset transfer failures

Upload failures:

- Missing paths raise immediately.
- Hidden files/directories and symlinks are skipped; an all-skipped upload exits `1` with no files to upload.
- Invalid relpaths should be rejected before network calls.
- Chunk init/chunk/complete failures raise runtime errors; command code records failed relpaths and exits `1`.
- Server-side conflicts collect skipped files and exit `2`; use `--force` when overwrite is intended.
- Model upload finalization can warn even when files uploaded successfully; inspect finalize response before assuming complete model registration.

Download failures:

- Existing target with matching size is skipped by design.
- Existing target larger than server size is deleted and re-downloaded.
- HTTP status other than `200` or `206` is an error.
- Size mismatch after download is an error.
- Range-resume requests need the same auth headers as normal API calls.

## `tfl-remote-trap` status or log failures

The remote wrapper should not fail the user's command just because status/log callbacks fail. This means a job may appear to run but have incomplete live status or provider logs.

Diagnosis:

1. Confirm wrapper invocation includes a command after `--`.
2. Confirm `_TFL_JOB_ID` is present; without it, status/log helpers no-op.
3. Confirm `_TFL_EXPERIMENT_ID` or equivalent experiment id is present; helpers need it to fetch the job.
4. Confirm the job exists and storage can create/open the job directory.
5. Distinguish wrapper provider logs from SDK task logs.
6. If logs stop mid-run, check storage append support and the wrapper's periodic flush thresholds.
7. If nonzero command exit does not mark failed, inspect `_set_live_status_async` and `_set_status_async` behavior around job fetch and status writes.
8. If interactive jobs are involved, remember the wrapper avoids overriding `INTERACTIVE` jobs with `RUNNING`.
9. Profiling failures are best-effort and should not change command exit code; check profiling temp setup only when profiling output is the issue.

A focused regression case for remote logging should run the wrapper around a command that writes both stdout and stderr, exits nonzero, and has job env vars set against an isolated workspace. Assert returned exit code is the child exit code, provider logs contain both streams, live status ends crashed, and high-level status is failed.

## Editable SDK reinstall gotcha

The API and workers import the installed `transformerlab` package. Editing SDK source files is not enough in a running environment.

After SDK changes:

1. Reinstall the SDK in editable mode into the environment that runs the API/worker.
2. Restart the API server or worker process that imports `lab`.
3. Re-run targeted SDK tests and any CLI/task tests that exercise the modified behavior.

If a fix appears in tests but not in a launched job, suspect the running process still has an old installed SDK or an old module already imported in memory.
