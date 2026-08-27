---
name: toolkits-integrations
description: "Guides SuperAGI built-in tools, custom toolkits, marketplace
  tools, tool execution, and toolkit configuration troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# SuperAGI Toolkits and Integrations

Use this sub-skill when the task is about SuperAGI tools, toolkits, marketplace
or external tool downloads, toolkit configuration keys, or tool execution
failures.

## Read First

- [references/toolkit-reference.md](references/toolkit-reference.md) for the
  BaseTool/BaseToolkit contract, toolkit config handling, and tool execution.
- [references/builtin-tools.md](references/builtin-tools.md) for the built-in
  toolkit inventory from the static source scan.
- [references/custom-and-marketplace-tools.md](references/custom-and-marketplace-tools.md)
  for external/marketplace tool discovery and installation behavior.
- [references/troubleshooting.md](references/troubleshooting.md) for import,
  config, dependency, download, and validation failures.
- [scripts/inspect_builtin_toolkits.py](scripts/inspect_builtin_toolkits.py) for
  a safe static inventory of tool and toolkit classes in a checkout.

## What This Sub-skill Covers

- Built-in toolkits and tool classes under `superagi/tools`.
- `ToolBuilder`, `ToolExecutor`, and toolkit config resolution.
- `tools.json` lookup and marketplace/external tool registration.
- Config-key handling and encrypted toolkit secrets.
- Safety rules around `install_tool_dependencies.sh` and network downloads.

## Safe Workflow

1. If a user asks about a tool or toolkit by name, check the built-in inventory
   first before looking at the dynamic registry.
2. If a tool is custom or marketplace-backed, distinguish between static source
   evidence and network-dependent installation behavior.
3. For an execution failure, determine whether the issue is tool selection,
   argument validation, missing config, missing dependency, or an external API
   error.
4. Avoid triggering marketplace downloads or apt/pip installers unless the
   downstream user explicitly wants that side effect.

## Boundary Notes

- Agent prompt generation and workflow looping belong to `agents-workflows`.
- Public API routes for toolkit CRUD belong to `api-service`.
- Resource/vector/provider setup that some tools consume belongs to
  `models-resources-vector`.
- Host deployment and Docker entrypoints that invoke toolkit installers belong
  to `deployment-configuration`.
