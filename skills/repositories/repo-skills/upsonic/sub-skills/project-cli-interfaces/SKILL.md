---
name: project-cli-interfaces
description: "Owns Upsonic's CLI project scaffolding, config files, API server
  launch, and interface/integration workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# project-cli-interfaces

Use this route for the `upsonic` CLI, `upsonic_configs.json`, API serving, project initialization, and interface wiring.

## Include

- `upsonic init`, `add`, `remove`, `install`, `run`, and `zip` command workflows.
- `upsonic_configs.json` layout, validation, and project scaffolding.
- FastAPI `/call` serving and `InterfaceManager` detection.

## Exclude

- Core model/provider selection → [models-and-providers](../models-and-providers/SKILL.md)
- Core agent execution → [agent-runtime](../agent-runtime/SKILL.md)
- Tool schema and MCP mechanics → [tools-and-mcp](../tools-and-mcp/SKILL.md)

## Start here

- [references/cli-reference.md](references/cli-reference.md)
- [references/interfaces-and-integrations.md](references/interfaces-and-integrations.md)
- [references/troubleshooting.md](references/troubleshooting.md)
- [scripts/validate_upsonic_config.py](scripts/validate_upsonic_config.py)
