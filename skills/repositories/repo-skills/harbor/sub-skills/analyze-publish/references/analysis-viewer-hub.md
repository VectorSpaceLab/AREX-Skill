# Analysis, viewer, and Hub inspection

## Local analysis and checks

First use the installed CLI help and set an explicit output directory when the
report must be reproducible:

```bash
harbor analyze --help
harbor check --help
harbor analyze jobs/<job> --rubric rubric.toml --agent <agent> --model <model> \
  --env <provider> --n-concurrent 4 --n-attempts 1 --jobs-dir jobs/analysis
harbor check tasks/<task> --rubric rubric.toml --agent <agent> --model <model> \
  --env <provider> --jobs-dir jobs/checks
```

`analyze` accepts one trial directory or a job directory, can filter to
`--passing` or `--failing` trials, limits with `--n-trials`, and writes a new
job containing per-trial analysis plus a top-level `analysis.json`. Its default
rubric checks reward-hacking and task-specification criteria; a custom
TOML/YAML/JSON rubric replaces or extends those criteria. `check` accepts a task
or directory of tasks and produces a quality-check report. Both operations may
run an evaluator agent in the chosen environment, consume model/API budget, and
write new local state even though they do not alter the source job/trials.
Capture the evaluator, model, provider, attempts, concurrency, rubric, and
report path in an audit record. A missing source trial or malformed result is an
analysis error, not evidence that the task failed.

Use local JSON and `result.json` parsing for deterministic score inspection. Use
analysis only for questions that require an evaluator reading the trajectory,
artifacts, task instruction, or verifier context. Route verifier defects to a
regrade or task authoring fix rather than treating prose analysis as a new score.

## Viewer

`harbor view <folder>` starts a local web server for a folder containing job
subdirectories or task definitions. It auto-detects the mode; use `--jobs` or
`--tasks` when detection is ambiguous. Bind to loopback by default and choose a
port or range with `--port 9000` or `--port 9000-9010`:

```bash
harbor view jobs --jobs --host 127.0.0.1 --port 8080-8089 --no-build
harbor view tasks --tasks
```

The viewer is a read-only presentation of local files. Inspect a job's summary,
trial reward/error, trajectory, verifier output, artifacts, and (when present)
analysis report. `--dev` and `--build` are development/build operations: they
can install frontend dependencies, compile assets, and replace packaged static
files, so do not use them for a read-only audit. If static assets are missing,
prefer a packaged viewer or `--no-build` and record that the frontend was not
built. Do not depend on frontend source internals for a CLI workflow.

## Hub read-only queries

After authentication, use Hub queries to inspect server records without
changing them. UUIDs are required for job/trial resource commands:

```bash
harbor hub job list --scope my|shared|all --json
harbor hub job show <job-id> --json
harbor hub job tasks <job-id> --json
harbor hub job trials <job-id> --failed-only --include-retries --json
harbor hub job shares <job-id> --json
harbor hub job compare <job-a> <job-b> [<job-c>] --json
harbor hub job status <job-id> --json
harbor hub trial show <trial-id> --json
```

`job list` filters by search, agent, provider, and model. `job tasks` gives the
per-task breakdown. `job trials` supports task/error/search/agent/provider/model
filters, latest-versus-all attempts, sorting, pagination, quiet IDs, and raw
JSON. Use `--page`, `--limit`, `--columns`, `--no-trunc`, and `--no-headers` to
make a human or machine report deterministic. `--json` is a raw API response;
check for missing/hidden records rather than interpreting an empty response as
zero trials. `status` reports pending/running/completed/failed/canceled counts
for hosted or uploaded jobs and is useful for polling.

Hub read-only commands may still require login and network access. An owner,
private visibility, explicit share, and public visibility are different access
states. Do not expose private task instructions, artifacts, traces, or tokens
in copied reports.

## Actions that look like inspection but mutate

- `harbor hub trial retry <trial-id> ...` or `--job <job-id>` requeues finished
  hosted attempts; preview with `job trials`, then confirm or pass `--yes`.
  Pending/running trials are skipped and only the latest attempt is selected.
- `harbor hub job cancel` and `harbor hub trial cancel` change hosted state and
  may record a reason.
- `harbor hub job copy` / `hub trial copy` create an independent, private by
  default snapshot in the caller's account. Copy is frozen at first capture;
  rerunning heals/resumes it, while `--overwrite` replaces it. Confirm target,
  visibility, shares, and overwrite before use.
- `harbor hub job delete` permanently removes an owned job, trials, and shares;
  it requires confirmation or `--yes` and is never part of an audit.

Treat these as mutations requiring explicit user approval, credentials, and an
exact-ID check even when invoked from a script or non-TTY.
