# Sandboxed execution workflows

`dbgpt-sandbox` exposes a runtime/session abstraction and an optional standalone FastAPI service. Treat every execution as untrusted input until an approved runtime, policy, workspace, timeout, and cleanup plan are established.

## Runtime selection

The public factory is `dbgpt_sandbox.sandbox.execution_layer.runtime_factory.RuntimeFactory`. It selects in this order:

1. Docker, after SDK/daemon availability is detected;
2. Podman;
3. Nerdctl;
4. Local only when explicitly enabled.

A forced preference can be supplied as `RuntimeFactory.create("docker" | "podman" | "nerdctl" | "local")`. `SANDBOX_RUNTIME` overrides a passed preference when set. The runtime configuration is read when the module is imported, so set environment variables before importing the factory or pass a preference for a controlled test.

Automatic selection fails closed when no container runtime is available and local execution is not opted in. Local execution requires both:

```text
SANDBOX_RUNTIME=local
SANDBOX_ALLOW_LOCAL_RUNTIME=true
```

The local factory may also be called with `RuntimeFactory.create("local")` after `SANDBOX_ALLOW_LOCAL_RUNTIME=true`; the environment variable is still the clearest operational declaration. `SANDBOX_ALLOW_LOCAL_RUNTIME` is not a security boundary: local code runs as a host process.

Container images selected by the current implementation include Python 3.11 slim, Node 18 slim, OpenJDK 11 JRE slim, GCC, Go, Rust, and a VNC image for `python-vnc`. Image availability, daemon permissions, registry access, and image trust are deployment prerequisites. Missing image/runtime is a bounded startup failure, not a reason to silently fall back to host execution.

## Direct Python API

Core types are importable from `dbgpt_sandbox.sandbox.execution_layer.base`:

```text
ExecutionStatus: SUCCESS | ERROR | TIMEOUT | RESOURCE_LIMIT
ExecutionResult(status, output="", error="", execution_time=0.0,
                memory_usage=0, exit_code=0)
SessionConfig(language="python", timeout=30, max_memory=268435456,
              max_cpus=1, working_dir="/workspace",
              environment_vars=None, network_disabled=False)
```

A minimal controlled lifecycle is:

```python
from dbgpt_sandbox.sandbox.execution_layer.base import SessionConfig
from dbgpt_sandbox.sandbox.execution_layer.runtime_factory import RuntimeFactory

runtime = RuntimeFactory.create("local")  # only after explicit local opt-in
session = await runtime.create_session(
    "approved-task-id",
    SessionConfig(language="python", timeout=30, working_dir="/workspace"),
)
try:
    result = await session.execute('print("deterministic")')
    # inspect result.status, result.output, result.error, result.exit_code
finally:
    await runtime.destroy_session("approved-task-id")
```

`SandboxRuntime` provides `create_session`, `destroy_session`, `list_sessions`, `get_session`, `cleanup_expired_sessions`, `health_check`, and `supports_language`. A duplicate session ID raises `ValueError`. Destroying a missing session returns `False` for the local runtime.

`SandboxSession` provides `start`, `stop`, `execute`, `get_status`, and optional `install_dependencies`. A session is stateful: repeated execution and dependency installation use the same session. Use a unique session ID and destroy it in a `finally` block. `cleanup_expired_sessions(max_idle_time=3600)` destroys idle sessions; it is not a substitute for per-request cleanup.

## Configuration and result semantics

- Default language is `python`, default timeout is 30 seconds, default memory is 256 MiB, default CPU count is 1, and the conceptual working directory is `/workspace`.
- The control layer uses a 512 MiB connection memory setting, while the application `shell_interpreter` integration explicitly uses 256 MiB and 30 seconds. Do not conflate these limits; report the layer that enforced a limit.
- `network_disabled` is passed to Docker and Podman when supported. The current Nerdctl path does not enforce the flag, and `LocalRuntime` does not provide network isolation. For a no-network guarantee use a verified container runtime with network isolation and test the deployment, or reject the operation.
- The local runtime creates an automatic temporary directory when `working_dir` is `/workspace` or absent, adds `input` and `output` directories, and removes that directory on `stop`. An explicit absolute working directory is treated as custom and is not removed on stop.
- Local execution writes a temporary code file, scans source for known dangerous patterns, runs a subprocess, captures stdout/stderr, and kills the process tree on timeout/error. Pattern scanning is not a language sandbox and can be bypassed by obfuscation or unlisted operations.
- `SecurityUtils.validate_code` flags common Python/other-language patterns such as `import os`, subprocess, `exec`, `eval`, `open`, sockets, URL/request libraries, file removal, and pickle; Bash checks include root deletion, disk writes/formatting, fork bombs, recursive global chmod, and curl/wget piped to a shell. A flagged dangerous operation returns `ExecutionStatus.ERROR` before execution.
- A nonzero child exit is `ERROR`, a timeout is `TIMEOUT`, and result fields include output/error and exit code. Do not treat a text output containing an error as success.
- `MAX_FILE_SIZE` is 10 MiB, `MAX_DEPENDENCY_INSTALL_TIME` is 300 seconds, `MAX_DEPENDENCY_INSTALL_SIZE` is 200 MiB, and `MAX_PROCESSES` is 10 in the runtime configuration. Not every runtime enforces every constant uniformly; verify the selected backend before promising a limit.

## Stateful session workflow

1. **Connect:** create a session with a unique user/task-derived ID and a supported language. Reject unknown languages before creating a session.
2. **Configure:** install only reviewed, pinned dependencies. Container runtimes invoke `pip install --no-input --disable-pip-version-check` for Python or initialize npm and install packages for JavaScript. Local dependency installation is not implemented by `LocalSandboxSession` and returns an error for nonempty dependencies.
3. **Execute:** pass code only after policy review. Keep sensitive host paths and credentials out of `environment_vars`; environment variables are copied into the process/container context.
4. **Observe:** inspect structured status, output, error, execution time, memory, and exit code. Generated files stay within the session workspace only if the runtime itself enforces that boundary.
5. **Retrieve:** retrieve only named, expected artifacts. Container file retrieval returns base64 content in a display result; a missing file is an error. Validate filename containment before any client-side use.
6. **Disconnect:** destroy the session and confirm it no longer appears in `list_sessions`. Remove any host-side temporary upload or extraction files separately.

Do not use a persistent session for unrelated users/tasks. Expire sessions and erase artifacts containing sensitive data.

## Standalone HTTP workflow

The standalone sandbox service can be registered onto an existing FastAPI app with `initialize_sandbox(app=existing_app)`. Calling it without `app` creates an app and starts Uvicorn; never do that in an import probe or a library helper. The standalone server's route prefix is `/api` when it owns the app.

Request sequence:

```text
POST /api/connect
{"user_id":"u", "task_id":"t", "image_type":"python"}

POST /api/configure
{"user_id":"u", "task_id":"t", "config_info":{"language":"python", "dependencies":[]}}

POST /api/execute
{"session_id":"u_t", "code_type":"python", "code_content":"print(1)"}

POST /api/status
{"session_id":"u_t"}
POST /api/get_file
{"session_id":"u_t", "file_name":"report.csv"}
POST /api/disconnect
{"user_id":"u", "task_id":"t"}
```

Additional read-only routes are `GET /api/health`, `GET /api/sessions`, and `GET /api/methods`. The user layer maps `user_id` and `task_id` to a session and returns `{status, output, error}`. It stores an in-process active-session map; this is not a distributed session store or authentication system.

## DB-GPT application integration

The application-side shell tool currently uses `LocalRuntime` directly for one call, sets a per-conversation work directory, applies 256 MiB/30-second limits, executes, and destroys the session in `finally`. It is stateless between calls even though the general sandbox runtime supports stateful sessions. Treat the application tool's phrase “sandboxed” as bounded process execution with pattern checks, not container isolation.

For a report or image artifact, return a logical artifact reference or use the approved app download route. The app's agent-file download route only allows server-approved temporary/root directories and responds 403/404 for disallowed or missing files. Do not expose arbitrary filesystem paths or allow a generated code string to choose a download path.

## Safe checks

- Run `python -m dbgpt_sandbox.sandbox.main --help` only when the installed CLI is explicitly available; help parsing must not invoke the server. The bundled wrapper is safer for request/policy validation.
- Import `RuntimeFactory`, `SessionConfig`, and `ExecutionStatus` without calling the factory's auto-detect path if Docker daemon probing is undesirable.
- For a tiny fixture, explicitly opt into local runtime in a temporary test process, print a constant, assert a known dangerous pattern is rejected, destroy the session, and assert its auto-created directory is gone.
- Mock container detection to false and assert automatic selection fails closed. Then assert explicit local selection fails without opt-in and succeeds only with opt-in.
- Do not test live Docker/Podman/Nerdctl, image pulls, package installation, network access, or GUI/VNC unless an operator has explicitly provisioned and approved that external service.
