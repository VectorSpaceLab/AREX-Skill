# Sandbox and Security Troubleshooting

## `pandasai-docker` missing

**Symptom**: `ModuleNotFoundError: No module named 'pandasai_docker'`.

**Cause**: Docker sandbox is an optional extension.

**Fix**:

```bash
pip install pandasai-docker
```

If Docker is not required, use a custom `Sandbox` subclass or run without a
sandbox only for trusted local experiments.

## Docker daemon unavailable

**Symptom**: DockerSandbox construction or `start()` fails with daemon/permission
errors.

**Cause**: Docker is not running or the current user cannot access it.

**Fix**: Start Docker, check permissions, and retry. Do not silently fall back to
host execution for untrusted prompts.

## Base `Sandbox` methods raise `NotImplementedError`

**Symptom**: Calling `Sandbox().start()` or `_exec_code` raises
`NotImplementedError`.

**Cause**: The base class is abstract.

**Fix**: Use a concrete extension such as DockerSandbox or subclass `Sandbox` and
implement `start`, `stop`, `_exec_code`, and `transfer_file`.

## Sandbox never marks itself started

**Symptom**: Every `execute` call invokes `start()` again or state-dependent logic
is inconsistent.

**Cause**: Custom `start()` did not set `self._started = True`, or `stop()` did
not set it back to false.

**Fix**: Follow the minimal subclass pattern in `sandbox-workflows.md` and run the
bundled contract smoke.

## SQL extraction misses a query

**Symptom**: `_extract_sql_queries_from_code` returns no queries even though code
executes SQL.

**Cause**: The helper extracts obvious string constants assigned or passed to
calls. Dynamic string construction may not be visible.

**Fix**: Treat extraction as an inspection aid, not a complete parser. Review
constructed code before running it.

## `MaliciousQueryError`

**Symptom**: Query rejected before execution.

**Cause**: Non-SELECT SQL, dangerous keywords, comments, or unauthorized table
names.

**Fix**: Keep generated SQL read-only and use registered dataframe schema names.
Route result-shape errors to the conversational-analysis troubleshooting file.

## `transfer_file` failures

**Symptom**: Sandbox cannot move CSV/data into the execution environment.

**Cause**: The concrete sandbox did not implement transfer semantics for its
runtime.

**Fix**: Implement `transfer_file` for the concrete runtime or pass only data that
is already accessible inside the sandbox.
