---
name: tools-and-mcp
description: "Owns Upsonic's tool system, ToolConfig, function tools, MCP
  handlers, agent-as-tool bridging, and orchestration helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# tools-and-mcp

Use this route for `@tool`, `ToolConfig`, `FunctionTool`, MCP handlers, tool orchestration, HITL pauses, and agent-as-tool patterns.

## Include

- `ToolConfig`, `tool`, `ToolHooks`, and function-tool wrappers.
- MCP clients/servers/handlers and the `Agent.as_mcp()` bridge.
- Tool orchestration helpers such as `plan_and_execute`.
- Sanitized command handling and the built-in safety warning around untrusted MCP servers.

## Exclude

- Core model selection → [models-and-providers](../models-and-providers/SKILL.md)
- Core task execution → [agent-runtime](../agent-runtime/SKILL.md)
- Skills loading and validation → [skills-system](../skills-system/SKILL.md)
- Policy definitions and governance → [quality-safety-governance](../quality-safety-governance/SKILL.md)

## Start here

- [references/tool-reference.md](references/tool-reference.md)
- [references/mcp-and-hitl.md](references/mcp-and-hitl.md)
- [references/troubleshooting.md](references/troubleshooting.md)
- [scripts/inspect_tool_schema.py](scripts/inspect_tool_schema.py)
