# Execution Troubleshooting

Use this guide to diagnose Python execution errors without weakening safety by default.

## Unauthorized import errors

Common messages include `Import of X is not allowed` or a CodeAgent warning suggesting `additional_authorized_imports`.

Safe response:
1. Confirm the import is required for the user task.
2. Prefer the narrowest import: `"package.submodule"` before `"package.*"`; avoid `"*"`.
3. Check whether the import is safe for local execution. If it exposes filesystem, shell, process, network, or deserialization APIs, prefer a remote executor.
4. Add the import at agent construction time:

```python
agent = CodeAgent(
    tools=[],
    model=model,
    additional_authorized_imports=["numpy.random"],
)
```

If initialization raises `Non-installed authorized modules`, install the package in the environment or remove the import. The local executor checks base modules with `importlib.util.find_spec()` during initialization.

## Blocked builtins, dunder attributes, or dangerous functions

Errors such as `Forbidden access to function`, `Forbidden access to module`, or `Forbidden access to dunder attribute` are safety controls, not schema bugs.

Do not bypass by exposing `exec`, `eval`, `compile`, `__import__`, shell helpers, or raw builtins as tools. If the user truly needs high-risk operations, move the whole workflow into a properly isolated sandbox and get explicit approval for the risk.

## Timeout errors

Local execution has a finite timeout by default. Long loops, sleeps, or heavy calculations can raise an execution timeout.

Safe fixes:
- Rewrite generated code to use a bounded algorithm.
- Increase timeout modestly with `executor_kwargs={"timeout_seconds": 60}` for trusted workloads.
- Keep a finite timeout for untrusted code.
- Avoid `timeout_seconds=None` unless the environment and prompt are trusted.

`evaluate_python_code(..., timeout_seconds=None)` and `LocalPythonExecutor(..., timeout_seconds=None)` disable the timeout.

## Print truncation

Very large stdout is truncated using `max_print_outputs_length`; the default local cap is `50_000` characters.

Safe fixes:
- Ask the agent to summarize instead of printing full data.
- Lower the cap for public or noisy workloads.
- Raise the cap only when the user needs logs and the output is non-sensitive.

```python
agent = CodeAgent(
    tools=[],
    model=model,
    max_print_outputs_length=20_000,
)
```

## Docker errors

### Missing package extra

If `DockerExecutor` cannot import the Docker SDK, install the Docker extra: `smolagents[docker]`.

### Docker daemon unavailable

`DockerExecutor` raises a runtime error when it cannot connect to Docker. Check that Docker is installed, running, and available to the current user before retrying. Do not attempt privileged daemon changes from an agent unless the user explicitly requests them.

### Image build or port conflicts

Safe mitigations:
- Use a different `port` in `executor_kwargs` when `8888` is occupied.
- Use `build_new_image=False` only when the expected image already exists.
- Keep `container_run_kwargs` conservative: resource limits and reduced privileges are good; broad host mounts or privileged mode are risky.
- Always call `cleanup()` or use a context manager.

## E2B errors

### Missing package extra

If E2B imports fail, install `smolagents[e2b]`.

### Account/API setup

E2B requires service credentials/configuration outside smolagents. If the sandbox cannot be created, verify the account setup and environment variables in the user's runtime environment without printing secrets.

### SDK version behavior

smolagents supports E2B SDK variants that expose `Sandbox.create(...)` or `Sandbox(...)`. Pass service-specific kwargs through `executor_kwargs`.

## Modal errors

### Missing package extra

If Modal imports fail, install `smolagents[modal]`.

### Account/API setup

Modal requires account login/configuration outside smolagents. If sandbox creation or tunnel startup fails, verify Modal setup and service status without exposing credentials.

### Startup timeout

Modal waits for a Jupyter kernel gateway. If it cannot connect, check sandbox image dependencies, network availability, `port`, and any custom `create_kwargs`.

## Blaxel errors

### Missing package extra

If Blaxel imports fail, install `smolagents[blaxel]`.

### Account/API setup

Blaxel requires service setup outside smolagents. If sandbox creation fails, verify account configuration, region, image, and quota without printing tokens.

### Custom sandbox settings

Review `sandbox_name`, `image`, `memory`, `ttl`, and `region`. Invalid image names, insufficient memory, or unsupported regions can prevent startup.

## Remote dependency handling

Remote executors install:
- `additional_authorized_imports` / `additional_imports` passed to the executor.
- Package requirements declared by sent tools.

Troubleshooting steps:
1. Keep the list minimal to reduce startup time and supply-chain exposure.
2. Use package names that pip can install in the sandbox; import names and package names are sometimes different.
3. Pin versions in the sandbox image or service configuration when reproducibility matters.
4. If a package requires system libraries, prefer a custom Docker image or service image rather than ad hoc runtime installs.

## Remote variable serialization errors

Default remote serialization rejects values that cannot be safely encoded. Prefer converting objects to dictionaries, lists, strings, numbers, booleans, or supported common types before sending them.

Avoid `allow_pickle=True` unless the environment is fully trusted and the user explicitly accepts the arbitrary-code-execution risk of pickle.

## Managed agents with remote snippet execution

If `CodeAgent` has `managed_agents` and `executor_type` is not `"local"`, smolagents raises an exception because managed agents are not supported with remote code execution. Use one of these approaches:
- Use local execution only for the manager/managed-agent setup when the prompt is trusted.
- Run the whole multi-agent application inside Docker/E2B/Modal/Blaxel manually.
- Redesign the task as a single `CodeAgent` with tools instead of managed agents.

## Helper script issues

The bundled `scripts/check_executor_config.py` is intentionally conservative:
- It validates executor names and import patterns.
- It can check whether local imports are installed.
- It can run a tiny `LocalPythonExecutor` smoke test only when `--tiny-local-check` is passed.
- It never starts remote sandboxes or containers.

If it reports high-risk imports, do not blindly suppress the warning; revisit executor choice and sandboxing.
