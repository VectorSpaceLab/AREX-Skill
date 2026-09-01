# Automation workflows

These recipes keep command selection, structured output, credentials, and
mutation gates explicit. Replace placeholders only after the target and
permissions are confirmed. Read [CLI reference](cli-reference.md) for
release-specific flags.

## Preflight a script

Use an executable, version, and help probe before any networked command. The
probe below disables the once-per-day PyPI/skill hint so diagnostics do not
pollute a parser:

```bash
set -eu
export HF_HUB_DISABLE_UPDATE_CHECK=1
command -v hf
hf version
hf download --help >/dev/null
hf repos delete --help >/dev/null
```

`hf --help` and `hf version` should exit 0. If `hf` and `huggingface-cli`
resolve to different installations, use `hf` and report the mismatch. Do not
replace a broken install with a network installer inside an automation script.

## Parse JSON while preserving diagnostics

Structured data is on stdout. Warnings, hints, and errors are on stderr. Keep
stderr visible while parsing stdout:

```bash
set -o pipefail
hf models ls --limit 10 --format json \
  2> >(tee ./hf-query.stderr >&2) \
  | jq -r '.[].id' > ./model-ids.txt
```

The output file contains only IDs; `hf-query.stderr` contains diagnostics and
must be treated as potentially sensitive. If a warning is unacceptable, fail
on a non-empty stderr only after deciding that warnings are not expected for
the workflow; the CLI itself can return success with warnings.

Portable Python equivalent:

```python
import json
import subprocess
import sys

run = subprocess.run(
    ["hf", "models", "ls", "--limit", "10", "--format", "json"],
    check=False,
    capture_output=True,
    text=True,
)
if run.stderr:
    print(run.stderr, end="", file=sys.stderr)
if run.returncode:
    raise SystemExit(run.returncode)
rows = json.loads(run.stdout)
```

Never parse `CompletedProcess.output`
when the API combines streams; use `stdout` and `stderr` separately. Use
`--format agent` when TSV is sufficient and the command's columns are known;
use JSON when fields may be added or nested.

Quiet mode is for IDs, not arbitrary messages:

```bash
hf repos ls --limit 0 --quiet | while IFS= read -r repo_id; do
  printf 'candidate: %s\n' "$repo_id"
done
```

Do not feed quiet output from a command that might print a secret. Do not use
`--no-truncate` as a substitute for structured output.

## Authentication without leakage

Prefer a secret manager to export a token for one process:

```bash
HF_TOKEN="$(secret-tool lookup service huggingface token)" \
  hf models info <namespace>/<model> --format json
```

The secret-manager command is environment-specific; do not commit it or log
its output. In CI, mask `HF_TOKEN`, disable shell tracing, and avoid printing
environment dumps. `HF_TOKEN` overrides the stored token. Use explicit
`--token "$HF_TOKEN"` only when the leaf requires a token option and accept
that process arguments may be observable on the host.

For a browser login, run `hf auth login` interactively. For an automated login,
pass `--token "$HF_TOKEN"`; do not automate the browser/device code. Avoid
`--add-to-git-credential` unless Git integration is an explicit requirement.
`hf auth whoami --format json` is a safe authenticated state check; it can
still expose account metadata.

`hf auth token` prints the secret itself and is not a health check. If a
workflow must use it, constrain the receiving process to a trusted endpoint,
keep the pipe ephemeral, and ensure shell/debug logs cannot capture argv or
stdout.

## Download with a dry-run gate

A dry run checks metadata and selected file sizes without transferring file
payloads. It may still contact the Hub and require read access:

```bash
set -o pipefail
hf download <namespace>/<model> \
  --include '*.safetensors' --exclude '*.tmp' \
  --dry-run --format json > ./download-plan.json
jq 'map(select(.will_download == true)) | {files: length, bytes: map(.file_size) | add}' \
  ./download-plan.json
```

The exact dry-run keys are returned by the installed implementation; inspect
`hf download --help` and one representative response before hard-coding a
schema. Do not use `--local-dir` and `--cache-dir` together. Pin a revision
for reproducibility, and keep the repository type explicit for datasets or
Spaces.

After review, remove `--dry-run` and run the same command with the approved
revision and destination. A real download can write cache/local files, so
choose a dedicated directory and check free space. `HF_HUB_OFFLINE=1` changes
this into a cache-only operation and cannot satisfy a metadata preflight for a
missing cache entry.

## Copy one file safely

`hf cp` uses `hf://` for a Hub endpoint and `-` for stdin/stdout. It is not a
local `cp`, and a binary stream must not be mixed with JSON or log output:

```bash
hf cp hf://datasets/<namespace>/<dataset>@<revision>/data.json ./scratch/data.json
```

For stdout, redirect bytes directly:

```bash
hf cp hf://buckets/<namespace>/<bucket>/manifest.json - > ./scratch/manifest.json
```

The remote-to-local examples are read-only relative to the Hub but write the
chosen local path. Local-to-remote and remote-to-remote copies are mutations;
verify URI type, path, region, and destination before running. Use repository
upload/download or bucket sync for directories. Bucket-to-repo and
local-to-local copies are unsupported.

## Review then apply a bucket sync

A dry run emits JSONL to stdout and performs no transfer:

```bash
hf sync ./scratch/checkpoints hf://buckets/<namespace>/<bucket> \
  --exclude '*.tmp' --dry-run > ./sync-preview.jsonl
cat ./sync-preview.jsonl | jq -s 'length'
```

A saved plan provides a durable review artifact:

```bash
hf sync ./scratch/checkpoints hf://buckets/<namespace>/<bucket> \
  --exclude '*.tmp' --plan ./sync-plan.jsonl
```

Inspect every source, destination, action, filter, and deletion in the plan.
Do not assume a plan remains current; re-check the source and remote state.

**Mutation gate:** only after an operator has reviewed and approved the plan:

```bash
hf sync --apply ./sync-plan.jsonl
```

`--delete` is an additional destructive option: it removes destination files
not present in the source. Pair it with a reviewed plan and avoid combining
broad globs with an unbounded destination. Use `--existing` or
`--ignore-existing` when the transfer direction requires one-sided changes.

## Repository deletion refusal case

A safe automation wrapper must not add `--yes` simply because stdin is not a
TTY:

```bash
set +e
hf repos delete <namespace>/<repo> --repo-type model < /dev/null
status=$?
set -e
if [ "$status" -eq 0 ]; then
  echo 'unexpected deletion success' >&2
  exit 1
fi
```

The placeholder must not be replaced in a test against a live resource. In a
fake CLI/API fixture, assert that the command exits non-zero, emits a
confirmation error, and makes zero delete API calls. In human mode it prompts;
in agent/json/quiet modes the output confirmation helper raises a
confirmation error unless `-y/--yes` is supplied. `--yes` is a decision gate
bypass, never an authorization check.

## Jobs and Spaces as status gates

A detached job is intentionally asynchronous:

```bash
# MUTATION: launches hosted compute and may incur cost.
job_id=$(hf jobs run --detach python:3.12 python -c 'print("safe smoke")' --format quiet)
hf jobs inspect "$job_id" --format json
hf jobs wait "$job_id" --timeout 10m
```

Launching a Job is a paid/remote mutation; use this only in an authorized
sandbox or test account. The command shown is a mutation example, not a
free local smoke test. `jobs wait` exits non-zero when any job fails,
including canceled/error/deleted states. `jobs logs --follow` ending is not a
success signal; inspect or wait for the terminal state. Use `--secrets` or a
secret file for secret environment variables, not ordinary `--env`.

For a Space, `hf spaces wait <space> --timeout 5m` is a status gate: zero means
running and a settled error state is non-zero. Restart, pause, hardware,
settings, secrets, variables, volumes, SSH, and hot reload are remote effects
and require explicit authorization. A local directory mounted into a Job is
first synced to a bucket; check the volume's access mode.

## Difficult synthetic verification case

Implement this under the external verification artifact root, not as a runtime
script in this skill:

1. Put a fake executable named `hf` first on the fixture's private `PATH`. It
   must record invocations locally but make no network calls.
2. For exactly `download <placeholder> --dry-run --format json`, have it emit a
   realistic dry-run JSON array on stdout, one warning on stderr, and status 0.
   Run the documented Python wrapper and assert that JSON parsing uses stdout,
   the warning is preserved separately, and no payload-download marker exists.
3. For `repos delete <placeholder>` without `--yes`, have the fake adapter use
   the same confirmation contract as the CLI. Assert non-zero status, a
   confirmation refusal on stderr, and zero delete-API calls. Repeat in
   `agent` or `json` mode to prove non-human mode does not silently accept.
4. Add a second fake `hf` that reports an older version and whose help omits a
   requested 1.29.0 command or flag. Assert that diagnosis captures executable
   path plus version, runs root/group/leaf help only, reports the command as
   unsupported/version-skewed, suggests only a help-confirmed replacement, and
   does **not** invoke `hf update`, an installer, `--yes`, or any remote API.
5. Make the fixture fail if stdout and stderr are merged, a secret-shaped token
   appears in logs, the wrapper retries a refusal, or any unlisted argv is run.

This goes beyond broad native CLI tests: production-marked tests often mock
individual API calls or Click callbacks and do not prove the subprocess stream
boundary, flag placement, refusal status, zero destructive API calls, or
version-skew recovery at the process boundary.
