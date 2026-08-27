---
name: built-in-tools
description: "Routes OpenHands built-in tool names, default presets, tool
  registration, browser availability, workflow scripts, and sub-agent tool
  wiring."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Built-in Tools

Use this sub-skill for `openhands-tools`: tool names, registration, resolution, default presets, browser availability, workflow scripts, and the built-in sub-agent tool sets.

## What this route owns

- `register_tool`, `resolve_tool`, `list_registered_tools`, `list_usable_tools`, and module qualnames.
- `TerminalTool`, `FileEditorTool`, `TaskTrackerTool`, `BrowserToolSet`, `WorkflowToolSet`, `TaskToolSet`, and related helper tools.
- Default presets such as `get_default_tools()`, `get_default_agent()`, and `register_default_tools()`.
- Tool-set usability checks and the registry behavior that surfaces tool availability.
- Workflow tool validation and safe script execution constraints.

## Start here

Read [`references/tool-catalog.md`](references/tool-catalog.md) for the public tool names and their primary roles. Read [`references/workflow-tool.md`](references/workflow-tool.md) for the dynamic workflow script model. Read [`references/troubleshooting.md`](references/troubleshooting.md) when a tool is missing, browser support is unavailable, or a workflow script is rejected.

Run [`scripts/list_default_tools.py`](scripts/list_default_tools.py) to print the default tool names and registry state.

## Typical triggers

- "Which tool should I use for shell commands or file edits?"
- "Why is the browser tool missing?"
- "How do I register a custom tool?"
- "How do workflow scripts work?"
- "Why does `/server_info` omit a tool?"

## Cross-links

- For local agent lifecycle and `Conversation` creation, go to [`../agent-core/SKILL.md`](../agent-core/SKILL.md).
- For remote custom-tool imports on agent-server, go to [`../remote-runtime/SKILL.md`](../remote-runtime/SKILL.md).
- For maintainer checks on tool registration, go to [`../repo-development/SKILL.md`](../repo-development/SKILL.md).
