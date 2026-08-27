# Security Workflows

Use these workflows to choose the least risky execution configuration that still satisfies the user request.

## Choose an executor

| Scenario | Recommended choice | Why |
| --- | --- | --- |
| Deterministic local calculation, trusted prompt, no external data | `executor_type="local"` with no or minimal `additional_authorized_imports` | Fast and simple; local AST evaluator blocks many unsafe operations. |
| Needs one safe library such as `math`, `statistics`, or a known data library | `executor_type="local"` with narrow imports such as `["statistics"]` or `["numpy.random"]` | Keeps local attack surface smaller than `"*"`. |
| Untrusted prompt, web browsing, public-facing agent, or prompt-injection exposure | Remote executor: `"docker"`, `"e2b"`, `"modal"`, or `"blaxel"` | Isolates generated code from the main environment better than local execution. |
| Self-hosted environment with Docker available | `executor_type="docker"` | Keeps control local while moving code into a container. |
| Managed cloud sandbox preferred | `"e2b"`, `"modal"`, or `"blaxel"` | Avoids local container operations, but requires service setup. |
| Managed agents plus strong isolation | Run the entire agentic system inside a sandbox | Snippet-level remote execution does not support managed agents. |

## Local trusted workflow

1. Start with no extra imports.
2. Add only the imports needed by the prompt.
3. Prefer submodule authorization over broad package trees: `"numpy.random"` before `"numpy.*"`.
4. Keep `timeout_seconds` finite.
5. Lower `max_print_outputs_length` when the task may generate large stdout.
6. Do not include tools that expose dangerous functions unless the user explicitly requests them and accepts the risk.

Example:

```python
agent = CodeAgent(
    tools=[],
    model=model,
    executor_type="local",
    additional_authorized_imports=["statistics"],
    executor_kwargs={"timeout_seconds": 8},
    max_print_outputs_length=8_000,
)
```

## Local import review checklist

Before adding an import, ask:
- Is the package installed and necessary for the requested work?
- Can a narrower submodule be authorized instead?
- Does the package expose filesystem, process, network, shell, or dynamic import capabilities?
- Will the agent process untrusted text, web content, uploaded files, or public input?
- Would the user be safer with Docker/E2B/Modal/Blaxel instead?

High-risk local imports include modules or packages that touch processes, shells, sockets, broad filesystem APIs, dynamic imports, or deserialization. smolagents has built-in dangerous module/function checks, but a package can still have unsafe high-level APIs.

## Remote snippet workflow

Use this when you want the model and agent loop local, but generated Python snippets isolated in a sandbox.

```python
with CodeAgent(
    tools=[],
    model=model,
    executor_type="e2b",
    additional_authorized_imports=["numpy"],
) as agent:
    answer = agent.run("Solve the task with a short numeric computation.")
```

Operational notes:
- Install the relevant extra first: `smolagents[e2b]`, `smolagents[modal]`, `smolagents[blaxel]`, or `smolagents[docker]`.
- Configure the provider account or Docker daemon outside the skill instructions.
- Keep `additional_authorized_imports` minimal because remote executors may install those packages in the sandbox.
- Use `with CodeAgent(...) as agent:` or call `agent.cleanup()`.
- Expect some state transfer between local agent and remote executor.
- Do not use snippet-level remote execution with `managed_agents`; smolagents rejects this combination.

## Whole-system sandbox workflow

Use this when managed agents, model calls, tools, and code execution all need isolation.

1. Build or provision a sandbox/container that contains `smolagents` and only required dependencies.
2. Pass only the secrets required for that sandboxed app.
3. Run the full Python process inside the sandbox rather than using `CodeAgent(executor_type=...)` from the host.
4. Apply resource limits: memory, CPU, process count, timeout, and network restrictions where your sandbox supports them.
5. Clean up the sandbox even when the task fails.

This is more work than snippet-level remote execution but avoids the limitation that remote snippet executors cannot use managed agents.

## Serialization and pickle policy

Remote executors send variables and final answers across a boundary. The default safe mode serializes JSON-compatible structures and selected common Python objects. If a value cannot be safely serialized, prefer simplifying the value into primitives.

Use `allow_pickle=True` only when all of these are true:
- The code, tools, model outputs, and remote environment are fully trusted.
- You need compatibility with complex custom Python objects.
- The user understands that pickle deserialization can execute arbitrary code.

Do not recommend pickle fallback as a routine fix for serialization errors.

## Unsafe operation avoidance

Avoid generating examples or recommending snippets that:
- Delete, overwrite, chmod, or recursively traverse user files.
- Print, upload, or copy environment variables, tokens, keys, or credentials.
- Run shell commands, spawn processes, open sockets, scan networks, or install arbitrary packages locally.
- Disable timeouts for untrusted code.
- Authorize all imports to bypass an error without reviewing the import.
- Use public web content as instructions for code execution without sandboxing.

## Adapting sandboxed execution examples

The repository's sandboxed execution example demonstrates all remote executor names with a web-search task. For public skill content, prefer dry-run configuration snippets instead of copying that example literally because Docker, cloud services, network access, credentials, and web search may be unavailable.

Safe adaptation pattern:

```python
agent_kwargs = {
    "tools": [],
    "model": model,
    "executor_type": "docker",
    "additional_authorized_imports": ["math"],
}
```

Then let the user choose when to actually instantiate the agent in an environment where Docker or the selected cloud sandbox is configured.
