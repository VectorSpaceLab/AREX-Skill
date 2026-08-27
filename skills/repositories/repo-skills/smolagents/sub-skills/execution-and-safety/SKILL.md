---
name: execution-and-safety
description: "Configure smolagents CodeAgent execution safely: local imports,
  executor_type choices, remote sandboxes, PythonInterpreterTool, and sandbox
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Execution and Safety

Use this sub-skill when a task involves how `CodeAgent` executes Python, how to limit or authorize imports, how to choose `executor_type`, or how to troubleshoot local and remote execution failures.

Route elsewhere when the request is mainly about:
- Model/API/provider configuration: use `model-providers`.
- CLI flags or web UI behavior: use `cli-and-ui`.
- Agent control flow, planning, multi-step runs, or managed agents: use `agent-workflows`.
- Tool schemas, `Tool` subclasses, MCP, or tool serialization: use `tools-and-integrations`.

## Safety-first defaults

Prefer this decision order:
1. Use `CodeAgent(..., executor_type="local")` only for trusted tasks and low-risk code, because `LocalPythonExecutor` is a restricted AST interpreter but not a complete security sandbox.
2. Add `additional_authorized_imports` narrowly, one package or submodule at a time; avoid `"*"` unless the user explicitly accepts local execution risk.
3. Use `executor_type="docker"`, `"e2b"`, `"modal"`, or `"blaxel"` for untrusted prompts, web-browsing contexts, public-facing agents, or higher-risk code.
4. Use a context manager or call `agent.cleanup()` for remote executors so sandboxes/containers terminate promptly.
5. Do not pass destructive, credential-printing, filesystem-mutating, or network-scanning snippets as examples.

## Quick local configuration

```python
from smolagents import CodeAgent

agent = CodeAgent(
    tools=[],
    model=model,
    executor_type="local",
    additional_authorized_imports=["math", "statistics"],
    max_print_outputs_length=10_000,
    executor_kwargs={"timeout_seconds": 10},
)
```

Key points:
- `additional_authorized_imports` extends smolagents' built-in safe module list for local code execution.
- Submodules are explicit: authorizing `"numpy"` allows `import numpy`; use `"numpy.random"` for that submodule or `"numpy.*"` for the package tree.
- `LocalPythonExecutor` checks that authorized modules are importable during initialization, except wildcard `"*"`.
- `max_print_outputs_length` truncates captured stdout, not the returned Python value.
- `executor_kwargs={"timeout_seconds": N}` sets the local execution timeout; `None` disables it and should be avoided for untrusted code.

For exact constructor behavior, see [executor-reference.md](references/executor-reference.md). For risk patterns and sandbox selection, see [security-workflows.md](references/security-workflows.md). For errors, see [troubleshooting.md](references/troubleshooting.md).

## Remote executor choices

`CodeAgent` accepts exactly these executor names:

| `executor_type` | Best fit | Extra |
| --- | --- | --- |
| `"local"` | Trusted local workflows, fastest setup | base package |
| `"docker"` | Self-hosted isolation, local container control | `smolagents[docker]` |
| `"e2b"` | Managed cloud sandbox with E2B account/API setup | `smolagents[e2b]` |
| `"modal"` | Managed Modal sandbox with Modal account/API setup | `smolagents[modal]` |
| `"blaxel"` | Managed Blaxel sandbox, fast hibernating VMs | `smolagents[blaxel]` |

Remote executor pattern:

```python
from smolagents import CodeAgent

with CodeAgent(
    tools=[],
    model=model,
    executor_type="docker",
    additional_authorized_imports=["numpy"],
    executor_kwargs={"build_new_image": False},
) as agent:
    result = agent.run("Compute a small numeric result without writing files.")
```

Remote execution details:
- `additional_authorized_imports` becomes the list of packages installed in the remote environment.
- Tool requirements are also installed remotely when tools are sent to the executor.
- Variables are serialized with safe JSON-compatible serialization by default.
- `allow_pickle=True` enables pickle fallback for complex objects but can execute arbitrary code during deserialization; use it only in fully trusted environments.
- Managed agents are not supported with snippet-level remote execution; run the whole agentic system in a sandbox for multi-agent isolation.

## PythonInterpreterTool

Use `PythonInterpreterTool` when a tool-calling agent needs a calculator-like Python tool rather than CodeAgent code actions:

```python
from smolagents import PythonInterpreterTool

python_tool = PythonInterpreterTool(
    authorized_imports=["math"],
    timeout_seconds=10,
)
```

The tool returns a string containing captured stdout and the final output. Its `authorized_imports` follows the same allow-list idea as `LocalPythonExecutor` and includes base built-in modules automatically.

## Bundled helper

Use the bundled helper for safe local validation before constructing a real agent:

```bash
python sub-skills/execution-and-safety/scripts/check_executor_config.py --executor-type local --imports math statistics --tiny-local-check
python sub-skills/execution-and-safety/scripts/check_executor_config.py --executor-type docker --imports numpy --explain-only
```

The helper performs parser-only checks by default. It never starts Docker, Modal, E2B, or Blaxel, never reads credentials, and never runs network calls. `--tiny-local-check` executes only a tiny in-process local interpreter smoke test.
