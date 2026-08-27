# CLI Reference

The `rocketride` command is shipped by both the Python SDK and the
TypeScript/Node package. The command name is the same, but the installed package
on `PATH` determines which implementation runs. When both SDKs are installed,
check `rocketride --help` and prefer an explicit environment/tooling choice for
repeatable automation.

## Environment variables

| Variable | Used by | Meaning |
| --- | --- | --- |
| `ROCKETRIDE_URI` | Python CLI, TypeScript CLI, SDKs | Base endpoint. Use `ws://localhost:5565` for a local engine; use `https://...` or `wss://...` for Cloud. |
| `ROCKETRIDE_APIKEY` | Python CLI, TypeScript CLI, SDKs | API key used for client auth. This is the primary SDK/CLI credential variable. |
| `ROCKETRIDE_AUTH` | MCP/Cloud-oriented examples; not primary SDK/CLI variable | If this is the only credential variable available, copy it to `ROCKETRIDE_APIKEY` or pass it as `--apikey` / `auth`. |
| `ROCKETRIDE_PIPELINE` | Python CLI, TypeScript CLI | Default pipeline path for `start` and `upload` when a pipeline flag/argument is omitted. |
| `ROCKETRIDE_TOKEN` | Python CLI, TypeScript CLI | Existing task token for token-bearing commands. Not an API key. |

Cloud caution: for any Cloud endpoint, set `ROCKETRIDE_URI` to an `https://` or
`wss://` URI. Do not use `http://`, `ws://`, or a bare Cloud hostname because
SDK normalization can downgrade to an unencrypted `ws://` connection.

## Command matrix

| Command | Python CLI | TypeScript CLI | Purpose |
| --- | --- | --- | --- |
| `start` | Yes | Yes | Start a pipeline and print/stream task information. |
| `upload` | Yes | Yes | Upload one or more local files through a new or existing task. |
| `status` | Yes | Yes | Monitor a running task by token. |
| `stop` | Yes | Yes | Terminate a running task by token. |
| `store` | Yes | Yes | File-store operations. |
| `events` | Yes | No | Stream raw task events; Python only. |
| `list` | Yes | No | List active tasks; Python only. |

## Common options

| Option | Python CLI | TypeScript CLI | Notes |
| --- | --- | --- | --- |
| Endpoint | `--uri <uri>` | `--uri <uri>` | Also reads `ROCKETRIDE_URI`. Explicitly set it instead of relying on defaults. |
| API key | `--apikey <key>` | `--apikey <key>` | Also reads `ROCKETRIDE_APIKEY`. Avoid passing secrets in shell history when possible. |
| Task token | `--token <token>` | `--token <token>` | Also reads `ROCKETRIDE_TOKEN`. Needed for `status`, `stop`, and token-based `upload`. |
| Pipeline | positional for `start`; `--pipeline_path` for `upload` | `--pipeline` for `start` and `upload` | Main flag difference between implementations. |
| Threads | `--threads <n>` | `--threads <n>` | Used when starting a new pipeline. |
| Pipeline args | `--args ...` (remainder) | `--args <args...>` | Passes arguments to pipeline execution. |
| Upload concurrency | Not exposed as `--max-concurrent` | `--max-concurrent <n>` | TypeScript CLI only; default `5`. |

## Start a pipeline

TypeScript CLI:

```bash
rocketride start --pipeline ./rag.pipe --uri "$ROCKETRIDE_URI"
```

Python CLI:

```bash
rocketride start ./rag.pipe --uri "$ROCKETRIDE_URI"
```

Both commands print a task token. Save it for upload/status/stop.

Notes:

- Python `start` takes the pipeline path as an optional positional argument,
  falling back to `ROCKETRIDE_PIPELINE`.
- TypeScript `start` requires `--pipeline` unless `ROCKETRIDE_PIPELINE` is set.
- `--token` attaches/resumes control of an existing task where supported by the
  implementation.

## Upload files

TypeScript CLI:

```bash
rocketride upload --pipeline ./extract.pipe ./docs/*.pdf --max-concurrent 4
rocketride upload --token "$ROCKETRIDE_TOKEN" ./report-q1.pdf ./report-q2.pdf
```

Python CLI:

```bash
rocketride upload --pipeline_path ./extract.pipe ./invoice.pdf
rocketride upload --token "$ROCKETRIDE_TOKEN" ./report-q1.pdf ./report-q2.pdf
```

Rules:

- Use a pipeline path when starting a new task for the upload.
- Use `--token` when feeding an already running task.
- TypeScript `upload` accepts files, wildcards, and directories, then uses
  `sendFiles(..., maxConcurrent)` internally.
- Python `upload` also accepts multiple file path arguments and uploads through
  the Python client's file upload pipeline.

## Monitor and stop

```bash
rocketride status --token "$ROCKETRIDE_TOKEN"
rocketride stop --token "$ROCKETRIDE_TOKEN"
```

`status` watches until interrupted or complete. Pressing `Ctrl+C` stops the
watcher; it does not necessarily stop the remote task. Use `stop` to terminate.

## Python-only event and task listing commands

```bash
rocketride events --token "$ROCKETRIDE_TOKEN"
rocketride events --token "$ROCKETRIDE_TOKEN" DETAIL,SUMMARY,OUTPUT --log events.log
rocketride list
rocketride list --json
```

Use `events` for raw event debugging when `status` is too summarized. Use `list`
when a token was lost but active tasks are visible to the authenticated account.

## File store commands

Both CLIs expose store operations:

```bash
rocketride store dir /
rocketride store type /pipeline-outputs/result.json
rocketride store write /pipeline-inputs/source.txt --file ./local-source.txt
rocketride store write /pipeline-inputs/prompt.txt --content "Summarize this document"
rocketride store rm /pipeline-outputs/old-result.json
rocketride store mkdir /pipeline-outputs/archive
rocketride store stat /pipeline-outputs/result.json
```

CLI docs and examples use `/` for store root. SDK `fs_*` / `fs*` methods are
stricter and expect relative paths without leading `/`; do not copy CLI store
paths blindly into SDK calls.

## Default URI caution

Documentation and package sources have used different defaults across surfaces
(local engine versus Cloud package default). Do not depend on the default in
production instructions. Always show the endpoint explicitly:

```bash
# Local engine
export ROCKETRIDE_URI=ws://localhost:5565

# Cloud or remote HTTPS/WSS endpoint
export ROCKETRIDE_URI=https://api.rocketride.ai
export ROCKETRIDE_APIKEY=your-api-key
```

If a command reports auth failure while `ROCKETRIDE_AUTH` is set, also set:

```bash
export ROCKETRIDE_APIKEY="$ROCKETRIDE_AUTH"
```

## Quick CLI triage

1. `rocketride --help` — identify which implementation and commands are present.
2. `echo "$ROCKETRIDE_URI"` — confirm secure Cloud scheme or local engine URI.
3. Confirm the credential path: `ROCKETRIDE_APIKEY` or `--apikey`.
4. Confirm token origin: token from `start`/`use`, not an API key.
5. Re-run with the implementation-specific pipeline flag (`--pipeline` vs
   `--pipeline_path`/positional).
