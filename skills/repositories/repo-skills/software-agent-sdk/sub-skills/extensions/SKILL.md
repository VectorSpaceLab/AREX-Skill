---
name: extensions
description: "Routes OpenHands AgentSkills, project and public skill loading,
  plugins, marketplaces, hooks, MCP configuration, memory, and secret-handling
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Extensions

Use this sub-skill for everything that extends the agent prompt or runtime: `Skill` loading, `AgentContext` skill flags, project/user/public skills, `.mcp.json`, plugins and marketplaces, hooks, memory, secrets, and prompt suffixes.

## What this route owns

- `Skill`, `SkillResources`, `load_skills_from_dir`, and AgentSkills `SKILL.md` discovery.
- `load_project_skills`, `load_public_skills`, `load_user_skills`, and `disabled_skills` precedence.
- `Plugin`, `PluginSource`, `MarketplaceRegistration`, and marketplace auto-loading.
- `HookConfig`, `HookDefinition`, `HookMatcher`, and hook exit-code behavior.
- `MCPServer`, MCP config maps, and `.mcp.json` expansion.
- Secret models such as `LookupSecret`, `StaticSecret`, and secret redaction/serialization.

## Start here

Read [`references/skills-plugins-hooks-mcp.md`](references/skills-plugins-hooks-mcp.md) for the concrete loading and configuration patterns. Read [`references/troubleshooting.md`](references/troubleshooting.md) for naming, precedence, hook, and `.mcp.json` failures.

## Typical triggers

- "Load skills from this repository."
- "Why did this project skill not appear?"
- "How do I attach a plugin marketplace or MCP server map?"
- "Why did my hook return 2 and block the stop action?"
- "How should secrets be serialized or redacted?"

## Cross-links

- For conversation and prompt-flow behavior, go to [`../agent-core/SKILL.md`](../agent-core/SKILL.md).
- For tool names and tool resolution, go to [`../built-in-tools/SKILL.md`](../built-in-tools/SKILL.md).
- For remote custom tool import path behavior, go to [`../remote-runtime/SKILL.md`](../remote-runtime/SKILL.md).
