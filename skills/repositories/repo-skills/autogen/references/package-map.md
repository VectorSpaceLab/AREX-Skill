# AutoGen Package Map

## Current Package Family

| Distribution | Import roots / commands | Role | Notes |
| --- | --- | --- | --- |
| `autogen-core` | `autogen_core` | Low-level runtimes, routed agents, messages, tools, model interfaces, component config | Use with `core-runtime`. |
| `autogen-agentchat` | `autogen_agentchat` | High-level agents, teams, termination, streaming, state, UI helpers | Depends on matching `autogen-core`. |
| `autogen-ext` | `autogen_ext` | Optional provider clients, tools, code executors, memory/cache, runtimes, helper agents | Install only required extras. |
| `pyautogen` | `pyautogen` | Compatibility/proxy package for current AgentChat | Legacy v0.2 code may need old pins and migration. |
| `agbench` | `agbench` command | Benchmark CLI and result tools | Help/lint are safe; benchmark runs may need Docker/network/credentials. |
| `autogenstudio` | `autogenstudio` command | Studio UI/server tooling | Check dependency range before mixing with 0.7.x libraries. |
| `magentic-one-cli` | `m1` command | Magentic-One CLI runner | This snapshot's package metadata targets older AutoGen ranges. |

## Minimal Install Patterns

Use the narrowest install that satisfies the task:

```bash
pip install -U autogen-agentchat autogen-core
pip install -U "autogen-ext[openai]"          # only for OpenAI-compatible clients
pip install -U "autogen-ext[mcp]"             # only for MCP workbenches/tools
pip install -U "autogen-ext[docker]"          # only for Docker code execution
pip install -U agbench                         # only for benchmark CLI work
```

Avoid `all`-style extras unless the user explicitly needs many integrations and accepts the dependency footprint.

## Safe Import Checks

```bash
python - <<'PY'
import importlib.metadata as md
for dist, mod in [
    ("autogen-core", "autogen_core"),
    ("autogen-agentchat", "autogen_agentchat"),
    ("autogen-ext", "autogen_ext"),
    ("pyautogen", "pyautogen"),
    ("agbench", "agbench"),
]:
    try:
        __import__(mod)
        print(dist, md.version(dist), "ok")
    except Exception as exc:
        print(dist, "failed:", type(exc).__name__, exc)
PY
```

## Version Boundaries

- Keep `autogen-core`, `autogen-agentchat`, and `autogen-ext` versions aligned for 0.7.x maintenance work.
- Treat `pyautogen` 0.10.x as a current compatibility/proxy package, not the old 0.2 API surface.
- AutoGen Studio and Magentic-One CLI may require older `autogen-core`, `autogen-agentchat`, and `autogen-ext` ranges than 0.7.x. Prefer a separate environment when the user needs those tools and current libraries in the same project.
- AG Bench can be inspected with `agbench --help` safely, but actual benchmark runs need explicit preparation of model credentials, Docker/native execution policy, network access, and output directories.

## Routing by Dependency Symptom

- `ModuleNotFoundError: autogen_agentchat` or team/agent imports: route to `sub-skills/agentchat-workflows/`.
- `ModuleNotFoundError: autogen_core` or runtime/topic/handler imports: route to `sub-skills/core-runtime/`.
- Optional provider/tool/executor import failures: route to `sub-skills/extensions-integrations/`.
- CLI commands missing or package resolver conflicts involving `autogenstudio`, `m1`, `agbench`, or `pyautogen`: route to `sub-skills/tools-studio-bench/`.
