# Runner Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ValueError: Unknown argument: 'pylint'` from `runner.run` | A top-level flow CLI option was passed to the run subcommand | Pass `pylint=False` to `Runner(...)`, not `runner.run(...)`. |
| `Metaflow could not determine your user name` | Runner subprocess lacks identity env | Pass `env={"USERNAME": "disco"}` for local smoke tests or configure organization identity. |
| `ExecutingRun.status == "failed"` | Flow subprocess failed | Inspect `executing.stdout`, `executing.stderr`, and `executing.returncode` before cleanup. |
| Timeout while reading runner attribute file | Flow failed before writing metadata, wrong cwd, or a long startup | Set `cwd` intentionally, check stderr, and increase `file_read_timeout` only after confirming the flow is alive. |
| Returned `Run` cannot be queried | Metadata provider or namespace mismatch | Use `_namespace_check=False` only when appropriate and read `client-and-data` for metadata/namespace diagnosis. |
| Async result is incomplete | Code read artifacts before `await wait(...)` | Await process completion before reading `run` artifacts. |
