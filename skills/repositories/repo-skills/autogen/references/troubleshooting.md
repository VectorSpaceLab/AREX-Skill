# Cross-Cutting Troubleshooting

## Install and Import Failures

| Symptom | Likely cause | First checks | Route |
| --- | --- | --- | --- |
| `ModuleNotFoundError: autogen_agentchat` | Missing high-level package or wrong environment | `python scripts/inspect_autogen_install.py --json`; install `autogen-agentchat` | `sub-skills/agentchat-workflows/` |
| `ModuleNotFoundError: autogen_core` | Missing base runtime package | Verify `autogen-core` metadata/import | `sub-skills/core-runtime/` |
| Optional module missing under `autogen_ext` | Needed extra was not installed | Identify exact surface and install narrow extra | `sub-skills/extensions-integrations/` |
| Resolver conflict with Studio or Magentic-One CLI | Tool package pins older AutoGen libraries | Read compatibility reference; use a separate env if needed | `sub-skills/tools-studio-bench/` |
| Legacy code imports `autogen` or old `pyautogen` APIs | v0.2-style code mixed with current 0.4+/0.7.x packages | Decide migrate vs pin old legacy package | `sub-skills/agentchat-workflows/` |

## Runtime Hangs and Async Issues

- Add `termination_condition` and/or `max_turns` for AgentChat teams before debugging model behavior.
- Do not replay full chat history into stateful agents or teams on every call; use `run` or `run_stream` with only the new task/message.
- Await async APIs and close model clients/workbenches/executors when they own network, subprocess, Docker, Jupyter, browser, or provider resources.
- For Core runtimes, confirm registration, subscriptions, runtime start, and `stop()`/`stop_when_idle()` sequencing.

## Credentials and Services

- Provider imports do not prove API keys, endpoints, deployment names, API versions, or model capabilities are valid.
- MCP servers, local command executors, Docker/Jupyter executors, Studio servers, browser tools, Redis/ChromaDB/mem0, and AG Bench runs can execute code or contact services; inspect help/config first.
- Never print real secrets from environment variables, serialized components, Studio app directories, benchmark configs, logs, or exception traces.

## Version and Maintenance Decisions

- AutoGen is in maintenance mode. For new greenfield work, recommend Microsoft Agent Framework unless the user explicitly wants AutoGen.
- For existing AutoGen systems, preserve the app's package family and version constraints before changing APIs.
- Keep root library packages aligned for 0.7.x; isolate tools whose metadata targets older ranges.
