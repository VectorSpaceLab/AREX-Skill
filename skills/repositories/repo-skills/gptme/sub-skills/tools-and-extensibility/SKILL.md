---
name: tools-and-extensibility
description: "Operate gptme tools and extensibility surfaces: built-in tools,
  allowlists, PTC formats, plugins, hooks, MCP, browser/computer caveats,
  skills, and lessons."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# tools-and-extensibility

Use this sub-skill when the task is about gptme's tool system or extension points: choosing built-in tools, configuring tool allowlists/formats, explaining Programmatic Tool Calling, writing or reviewing custom `ToolSpec` tools, packaging plugins, registering hooks or commands, using MCP, or deciding between skills, lessons, and plugins.

## Route first

- For built-in tool selection, allowlists, tool formats, PTC dispatch, or subagent isolation: read [references/tools-reference.md](references/tools-reference.md).
- For custom tools, plugin structure, entry-point plugins, hook signatures, commands, skills, lessons, or the plugin-vs-skill-vs-lesson decision: read [references/extensibility.md](references/extensibility.md).
- For MCP client/server usage, browser backend environment, and computer-use safety/system dependencies: read [references/mcp-browser-computer.md](references/mcp-browser-computer.md).
- For failures involving unavailable tools, denied allowlists, plugin discovery, hook signatures, MCP, browser, computer use, skills, or lessons: read [references/troubleshooting.md](references/troubleshooting.md).

## Safe helper scripts

- Inventory installed gptme tools without running them:
  - `python scripts/list_gptme_tools.py --help`
  - `python scripts/list_gptme_tools.py --format text --check-browser`
- Validate a plugin directory statically, without importing plugin code:
  - `python scripts/validate_plugin_skeleton.py --help`
  - `python scripts/validate_plugin_skeleton.py PATH_TO_PLUGIN`

## Boundary

- Provider credentials, user provider keys, model routing, and auth helpers belong to the configuration-and-providers sub-skill.
- `gptme-server`, HTTP REST/SSE APIs, Web UI, TUI, ACP, deployment, and server security belong to the server-webui-and-protocols sub-skill.
- Eval suites, SWE-bench/T-bench, leaderboard processing, Docker eval isolation, and pass-rate gates belong to the evals-and-benchmarks sub-skill.
- Maintainer-only pytest, lint, typecheck, documentation, or release work requires a gptme checkout; this sub-skill only describes the relevant tool/plugin/hook tests as evidence candidates.

## Quick operating pattern

1. Start with a static inventory: run `scripts/list_gptme_tools.py` in the target environment and note unavailable tools plus hints.
2. Pick the smallest extension mechanism:
   - script tool for standalone shell-callable helpers,
   - custom `ToolSpec` for a single runtime action,
   - plugin for tools plus hooks or commands,
   - skill for explicit portable workflow guidance,
   - lesson for auto-loaded guidance,
   - MCP when another process or language should expose tools.
3. Keep browser/computer/MCP actions opt-in and document optional system dependencies before asking an agent to use them.
4. When validating extension code, prefer static skeleton checks and help commands before running any plugin code, MCP server, browser, desktop automation, or networked workflow.
