---
name: teams-autonomous-prebuilt
description: "Owns Team coordination, AutonomousAgent, prebuilt autonomous
  agents, RalphLoop, and Simulation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# teams-autonomous-prebuilt

Use this route for multi-agent coordination, sandboxed autonomous agents, prebuilt agents, Ralph loops, and simulation workflows.

## Include

- `Team` coordination and routing modes.
- `AutonomousAgent` filesystem/shell sandboxing.
- `PrebuiltAutonomousAgentBase` and prebuilt agents such as `AppliedScientist`.
- `RalphLoop` and `Simulation` long-running workflows.

## Exclude

- Single-agent run semantics → [agent-runtime](../agent-runtime/SKILL.md)
- Provider/model selection → [models-and-providers](../models-and-providers/SKILL.md)
- Tool schema and MCP details → [tools-and-mcp](../tools-and-mcp/SKILL.md)

## Start here

- [references/team-workflows.md](references/team-workflows.md)
- [references/autonomous-and-prebuilt.md](references/autonomous-and-prebuilt.md)
- [references/troubleshooting.md](references/troubleshooting.md)
- [scripts/inspect_prebuilt_templates.py](scripts/inspect_prebuilt_templates.py)
