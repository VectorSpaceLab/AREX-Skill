# Cross-Cutting Troubleshooting

## Install and import failures

- If `import atomic_agents` fails, confirm the package is installed in the active environment and rerun `python -m pip check`.
- Use the published install path for ordinary use: `pip install atomic-agents`.
- For checkout work, prefer `uv sync` or `pip install -e .` from the repo root.
- Do not treat the current working directory as proof of a healthy install; import from outside the checkout when possible.

## Version and dependency mismatch

- This repository snapshot is `2.10.0`.
- The MCP connector surface currently matches the lockfile-aligned `mcp 1.22.x` line. A newer `mcp 2.x` release can rename the streamable HTTP client symbol and break `atomic_agents.connectors.mcp` imports.
- Keep `rich` on the framework-compatible `13.x` line; newer `rich 15.x` conflicts with the framework and `instructor` requirements.

## Core API mistakes

- Every `BaseIOSchema` subclass must have a non-empty docstring.
- Wrap provider SDK clients with `instructor.from_*` before placing them in `AgentConfig.client`.
- Use `run` / `run_stream` only with sync clients and `run_async` / `run_async_stream` only with `AsyncInstructor` clients.
- If a custom history backend is used, make sure its `copy()` method preserves the backend type and state; `reset_history()` calls `copy()`.
- For Gemini-style backends (`assistant_role='model'`), keep the mid-conversation tool-result role on `user` unless you have a specific reason to override it.

## CLI and example failures

- If `atomic` is not found, reinstall the package into the active environment and rerun `atomic --help`.
- Example projects often require provider keys, network access, or optional extras. Treat them as recipes first and runnable demos second.
- Do not assume every example can be executed offline; many are intentionally interactive or key-backed.

## What this file does not cover

- Detailed agent API usage belongs to `sub-skills/agent-core/`.
- Tool, CLI, Forge, and orchestration details belong to `sub-skills/tooling-and-forge/`.
- MCP transport and schema details belong to `sub-skills/mcp-integrations/`.
- Example-specific dependency and key guidance belongs to `sub-skills/example-workflows/`.
- Checkout editing, tests, docs, and release guidance belong to `sub-skills/repo-development/`.
