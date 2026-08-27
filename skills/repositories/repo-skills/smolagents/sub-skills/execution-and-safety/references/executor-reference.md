# Executor Reference

This reference summarizes the smolagents execution classes and parameters that matter when configuring safe Python execution.

## CodeAgent execution parameters

`CodeAgent` is the agent class that asks the model to emit Python code actions. Execution-related constructor parameters include:

| Parameter | Use |
| --- | --- |
| `additional_authorized_imports` | Extra imports/packages that generated code may use. For local execution these extend the built-in allow-list; for remote execution these are installed in the remote environment. |
| `executor` | A custom `PythonExecutor` instance. If provided, it overrides `executor_type`. |
| `executor_type` | One of `"local"`, `"blaxel"`, `"e2b"`, `"modal"`, or `"docker"`. Defaults to `"local"`. |
| `executor_kwargs` | Keyword arguments forwarded to the selected executor constructor. |
| `max_print_outputs_length` | Local executor stdout capture limit. Passed into `LocalPythonExecutor`; defaults to smolagents' internal default when unset. |
| `stream_outputs` | Streams step outputs when the model supports `generate_stream`; this is not a sandbox setting. |
| `use_structured_outputs_internally` | Changes model generation format for code steps; this is not a sandbox setting. |

`CodeAgent.create_python_executor()` rejects unknown executor names and raises `ValueError("Unsupported executor type: ...")`.

## LocalPythonExecutor

`LocalPythonExecutor(additional_authorized_imports, max_print_outputs_length=None, additional_functions=None, timeout_seconds=30)` executes code by parsing Python into an AST and evaluating supported nodes under smolagents controls.

Capabilities and limits:
- Maintains state between calls and initializes `state["__name__"]` to `"__main__"`.
- Combines agent tools, base Python tools, and `additional_functions` when `send_tools()` is called.
- Captures `print()` output separately from returned output in `CodeOutput.logs`.
- Truncates print logs with `max_print_outputs_length`; default internal cap is `50_000` characters.
- Enforces a timeout by default; pass `timeout_seconds` through `executor_kwargs` to change it.
- Blocks unsupported syntax and unsupported operations with `InterpreterError`.
- Is not a full security sandbox; use remote execution for untrusted code.

Example:

```python
from smolagents.local_python_executor import LocalPythonExecutor

executor = LocalPythonExecutor(
    additional_authorized_imports=["math"],
    max_print_outputs_length=5_000,
    timeout_seconds=5,
)
executor.send_tools({})
result = executor("import math\nprint('ok')\nmath.sqrt(81)")
assert result.output == 9
assert "ok" in result.logs
```

## evaluate_python_code

`evaluate_python_code(code, static_tools=None, custom_tools=None, state=None, authorized_imports=..., max_print_outputs_length=50000, timeout_seconds=30)` is the low-level evaluator used by `LocalPythonExecutor` and `PythonInterpreterTool`.

Use it only for focused local interpreter checks. Prefer `LocalPythonExecutor` when you need stateful execution, tool registration, or parity with `CodeAgent` local behavior.

Important behavior:
- Parses code first and raises `InterpreterError` on syntax errors.
- Places captured stdout in `state["_print_outputs"]`.
- Returns `(output, is_final_answer)`.
- Uses `authorized_imports` directly, so include all needed import names.
- Applies stdout truncation even when execution raises.
- Wraps runtime failures with the source segment that failed.

## Import allow-list semantics

Local import checks use tree-like matching:
- `"math"` authorizes `import math`.
- `"numpy.random"` authorizes `import numpy.random` and implies the parent package path needed for that import.
- `"numpy.*"` authorizes the package tree below `numpy`.
- `"*"` authorizes any import that is installed, but it greatly increases risk.

Do not assume that authorizing a package makes every accessed attribute safe. smolagents also checks for dangerous modules/functions, dunder access, and unsafe results, but authorized packages can still perform harmful work through their own APIs.

## PythonInterpreterTool

`PythonInterpreterTool(authorized_imports=None, timeout_seconds=30)` is a tool wrapper around `evaluate_python_code`.

Use it for `ToolCallingAgent` or other tool-centric workflows that need small calculations. It is not a replacement for `CodeAgent`'s code-action executor.

Behavior:
- `authorized_imports=None` means only smolagents' base built-in modules are allowed.
- Passing `authorized_imports=[...]` unions those imports with the base built-in modules.
- `forward(code)` returns a string with `Stdout:` and `Output:` sections.
- Each call starts with a fresh local `state` dictionary.

## RemotePythonExecutor base behavior

`RemotePythonExecutor` powers `BlaxelExecutor`, `E2BExecutor`, `ModalExecutor`, and `DockerExecutor`.

Common behavior:
- Constructor receives `additional_imports`, `logger`, and `allow_pickle=False`.
- `send_tools()` installs package requirements from tool definitions in the remote environment, excluding packages already installed and excluding `smolagents`.
- `send_variables()` serializes variables safely by default using JSON-compatible encodings.
- `allow_pickle=True` enables pickle fallback for values that cannot be represented safely; this is a trust boundary decision.
- `cleanup()` is implementation-specific; use `with CodeAgent(...) as agent:` where possible.

## Remote executor constructor kwargs

Pass these through `CodeAgent(..., executor_kwargs={...})`.

### DockerExecutor

Useful kwargs:
- `host`: bind host, default `"127.0.0.1"`.
- `port`: host port for Jupyter Kernel Gateway, default `8888`.
- `image_name`: local image tag, default `"jupyter-kernel"`.
- `build_new_image`: whether to build the kernel image, default `True`.
- `container_run_kwargs`: additional Docker SDK container run kwargs. smolagents ensures port mapping and detached mode.
- `dockerfile_content`: full Dockerfile content; if omitted, smolagents uses a Python/Jupyter kernel gateway image definition.
- `allow_pickle`: inherited remote serialization option; keep `False` unless trusted.

Failure to connect to Docker raises a message that the Docker daemon may not be running.

### E2BExecutor

Useful kwargs:
- Any extra keyword arguments accepted by the E2B `Sandbox` constructor or `Sandbox.create()`.
- `allow_pickle`: inherited remote serialization option; keep `False` unless trusted.

Requires the `smolagents[e2b]` extra and E2B account/API configuration.

### ModalExecutor

Useful kwargs:
- `app_name`: Modal app name, default `"smolagent-executor"`.
- `port`: Jupyter port inside the sandbox, default `8888`.
- `create_kwargs`: extra kwargs for `modal.Sandbox.create`; smolagents adds a Jupyter/IPython image, timeout, encrypted port, and kernel gateway token defaults.
- `allow_pickle`: inherited remote serialization option; keep `False` unless trusted.

Requires the `smolagents[modal]` extra and Modal account/API configuration.

### BlaxelExecutor

Useful kwargs:
- `sandbox_name`: optional sandbox name; smolagents generates one when omitted.
- `image`: sandbox image, default `"blaxel/jupyter-notebook"`.
- `memory`: memory in MB, default `4096`.
- `ttl`: sandbox time-to-live string.
- `region`: deployment region.
- `allow_pickle`: inherited remote serialization option; keep `False` unless trusted.

Requires the `smolagents[blaxel]` extra and Blaxel account/API configuration.
