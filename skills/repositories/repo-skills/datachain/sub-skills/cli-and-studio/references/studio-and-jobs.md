# Studio Auth, Jobs, and Pipelines

## Purpose

Read this reference when a task involves DataChain Studio authentication, remote
job execution, job logs, clusters, dataset-update pipelines, scheduling, remote
requirements, or Studio team selection. Treat every command here as contacting
Studio except local help output and config-only auth commands.

## Studio Prerequisites and Identity

- Studio operations need a Studio URL, token, and team. The URL defaults to the
  public Studio service unless configuration or `DATACHAIN_STUDIO_URL` overrides
  it.
- A token can come from `datachain auth login`, `DATACHAIN_STUDIO_TOKEN`, or a
  config file. A team can come from `datachain auth team`, `--team`,
  `DATACHAIN_STUDIO_TEAM`, or config.
- `--team TEAM` is safest when the user is operating across multiple teams.
- Studio client creation checks remote dependencies; if the client reports a
  missing dependency such as `msgpack` or `requests`, install the remote-capable
  DataChain package variant suggested by the error.
- Never include real token values in examples, logs, committed files, or job
  environment snippets.

## Authentication Commands

### `auth login`

```bash
datachain auth login [-H HOSTNAME] [-s SCOPES] [-n NAME] [--no-open] [--local] \
  [--team TEAM ...] [--expires-in DAYS]
```

Purpose: obtains a Studio token and saves it to DataChain configuration.

- `--hostname` selects a Studio instance.
- `--scopes` narrows token scopes. The documented scopes are `EXPERIMENTS`,
  `DATASETS`, and `MODELS`; omit for the default scope set.
- `--name` names the token as shown in Studio.
- `--no-open` uses code-based auth when a browser should not be opened.
- `--local` saves to project-local config rather than global config.
- `--team` can be repeated to scope the token to one or more teams.
- `--expires-in` defaults to `365` days.
- If a token for the same host already exists, log out before logging in with a
  different token.
- A single `--team` value is also saved as the default team; multiple teams or
  no team leave default-team selection to `auth team`.

### `auth team`

```bash
datachain auth team [TEAM_NAME] [--local]
```

With a team name, sets the default team globally or project-locally. Without a
team name, prints the current default team or raises an error if no team is set.
Use `--local` for project-specific defaults.

### `auth token`

```bash
datachain auth token
```

Prints the current Studio token. This is intentionally sensitive output; use it
only when the user explicitly needs to copy or verify a token, and do not echo it
back unnecessarily.

### `auth logout`

```bash
datachain auth logout [--local]
```

Revokes/removes the stored token for the selected config level and clears the
associated default team. If Studio cannot be reached or returns a server error,
logout aborts and leaves the local token in place so the user can retry.

## Job Commands

### `job run` — submit a Studio job

```bash
datachain job run QUERY_FILE [--team TEAM] [--env-file ENV_FILE] [--env KEY=VALUE ...] \
  [--cluster CLUSTER] [--credentials-name NAME] [--workers N] [--files FILE ...] \
  [--python-version 3.10|3.11|3.12|3.13] [--repository URL[@REV]] \
  [--req-file REQUIREMENTS] [--req PACKAGE ...] [--priority 0-5] \
  [--start-time WHEN] [--cron CRON] [--no-wait] [--no-follow] [--ignore-checkpoints]
```

Purpose: reads a local query file and submits its content to Studio. A `.py`
file is sent as a Python query; other file extensions are treated as shell
queries. Treat the command as mutating remote Studio state.

Important routing and payload details:

- `--env-file` content is prepended to inline `--env` values. Repeated `--env`
  flags are flattened, so both `--env A=1 B=2` and `--env A=1 --env B=2` work.
- `--req-file` content is prepended to inline `--req` package names.
- `--files` uploads additional files and sends their Studio file IDs with the
  job. Do not attach secrets unless the user has explicitly approved that.
- `--repository` asks Studio to clone a repository before running the job.
  Supported examples include HTTPS URLs with optional `@branch`/revision suffix
  and Git-style URLs with a revision suffix.
- `--python-version`, `--workers`, `--priority`, `--cluster`, and
  `--credentials-name` configure the remote job environment. Priority is in the
  `0`-to-`5` CLI range, where lower values are higher priority and the default
  is `5`.
- `--ignore-checkpoints` resets the checkpoint link for this remote execution.

Immediate run behavior:

- Without scheduling flags, the command prints the job ID and Studio URL, then
  follows logs and status unless `--no-wait` is used.
- `--no-wait` returns after job creation and does not wait for completion.
- `--no-follow` waits for status while suppressing live log text.
- Completion exit codes are `0` for `COMPLETE`, `1` for `FAILED`, and `2` for
  `CANCELED`. A lost connection while the job still appears active returns
  nonzero and tells the user to resume monitoring with `job logs`.
- After a finished job, the CLI prints dataset versions created during the job
  when Studio reports them.

Scheduling behavior:

- `--start-time` schedules a one-time future task. It accepts ISO-like datetimes
  and natural-language phrases such as `tomorrow 3pm`, `in 2 hours`, or
  `monday 9am`.
- `--cron` schedules a recurring task. Standard five-field cron expressions and
  Vixie-style keywords such as `@hourly`, `@daily`, `@weekly`, `@monthly`,
  `@yearly`, `@annually`, and `@midnight` are supported.
- Combining `--start-time` and `--cron` starts the cron schedule after the start
  time. With `--cron` alone, the CLI sends the current time as the start point.
- Scheduled jobs are created as Studio tasks and do not stream logs immediately.
  Use Studio UI or job listing/log commands after an actual job run exists.

Checkpoint behavior:

- Remote `job run` records the job under the absolute local script path in the
  local metastore.
- Re-running the same script path can set `rerun_from_job_id` to the previous
  remote execution so Studio can reuse checkpoints.
- Moving or renaming the script changes that lookup key. Use
  `--ignore-checkpoints` when the user wants a fresh run even with a previous
  job for the same script path.

### `job logs` — monitor an existing Studio job

```bash
datachain job logs [--team TEAM] JOB_ID
```

Shows logs and current status for a Studio job. Closing the command stops local
monitoring only; it does not cancel the job. The log follower filters websocket
ping messages, deduplicates repeated log IDs across reconnects, fetches log blob
content when available, and falls back to REST status checks after websocket
closure.

### `job cancel` — cancel a running job

```bash
datachain job cancel [--team TEAM] JOB_ID
```

Cancels a Studio job. This is the proper way to stop execution; do not treat
Ctrl+C in a log window as cancellation. Confirm the job ID and team before
running.

### `job ls` — list Studio jobs

```bash
datachain job ls [--status STATUS] [--team TEAM] [--limit N]
```

Lists recent jobs for the selected team. Default limit is `20`. Useful status
filters include `CREATED`, `SCHEDULED`, `QUEUED`, `INIT`, `RUNNING`, `COMPLETE`,
`FAILED`, `CANCELING_SCHEDULED`, `CANCELING`, `CANCELED`, `ACTIVE`, and
`INACTIVE`.

### `job clusters` — list compute clusters

```bash
datachain job clusters [--team TEAM]
```

Lists Studio compute clusters available to the selected team, including ID,
name, status, cloud provider, credentials label, active/default flags, and max
workers when Studio returns those fields. Use this before choosing
`job run --cluster`.

## Pipeline Commands

Pipelines are Studio-managed dependency graphs for updating datasets. They are
not the same as writing DataChain Python SDK pipeline code; route SDK authoring
to `../sdk-pipelines/`.

### `pipeline create` — create a paused pipeline for review

```bash
datachain pipeline create DATASET [DATASET ...] [-t TEAM]
```

Creates a Studio pipeline to update one or more datasets and automatically
include jobs for their dependencies. Dataset names can be fully qualified, such
as `@namespace.project.dataset`, or short names that use Studio's default
namespace/project. Names can include version suffixes like `dataset@1.0.9`; no
suffix means latest. The new pipeline is created **paused** for review. Resume it
only after checking its planned jobs.

### `pipeline list`

```bash
datachain pipeline list [-t TEAM] [-s STATUS] [-l LIMIT] [-S SEARCH]
```

Lists pipelines. `--status` accepts values such as `PENDING`, `RUNNING`,
`COMPLETED`, `FAILED`, `PAUSED`, and `CANCELED`; `--limit` defaults to `20`;
`--search` filters by pipeline name or target dataset.

### `pipeline status`

```bash
datachain pipeline status NAME [-t TEAM]
```

Shows pipeline name, status, progress as completed/total jobs, error message if
present, and a job-run table with job names, statuses, and created job IDs. Use
this before pausing/resuming/removing jobs.

### `pipeline pause`

```bash
datachain pipeline pause NAME [-t TEAM]
```

Pauses a Studio pipeline. Running jobs continue to completion, but new jobs are
not started even when dependencies are met. Confirm that this is what the user
wants; it is not a hard stop for already-running jobs.

### `pipeline resume`

```bash
datachain pipeline resume NAME [-t TEAM]
```

Resumes a paused pipeline. Studio identifies dependency-ready jobs that have not
run and starts them.

### `pipeline remove-job`

```bash
datachain pipeline remove-job NAME JOB_ID [-t TEAM]
```

Removes a specific job from a pipeline before it runs. This requires a paused
pipeline and a pending job; it cannot remove jobs from running or completed
pipelines. Use `pipeline status` first to identify the job ID and status.

## Studio Job Troubleshooting Checklist

1. Confirm token/team with `auth team`, explicit `--team`, or environment
   variables; do not expose token values.
2. For run failures during initialization, inspect requirements from
   `--req-file` and `--req`, Python version, cluster availability, and any file
   attachments.
3. For storage failures, check that team storage credentials exist and that the
   script uses reachable storage paths.
4. For apparent hangs after log disconnects, run `datachain job logs JOB_ID` or
   inspect Studio UI; the job may still be running.
5. For scheduled jobs, do not expect immediate logs. List jobs or use Studio task
   views after the schedule starts.
6. For checkpoint surprises, check whether the same local script path was used
   before and whether `--ignore-checkpoints` is appropriate.
