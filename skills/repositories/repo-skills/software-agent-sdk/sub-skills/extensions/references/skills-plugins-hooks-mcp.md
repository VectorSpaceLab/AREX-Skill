# Skills, Plugins, Hooks, and MCP

## Skill loading models

```python
Skill(
    name="my-skill",
    content="...",
    trigger=None,
    source="SKILL.md",
    is_agentskills_format=True,
    disable_model_invocation=False,
)
SkillResources(skill_root="/path/to/skill", scripts=["scripts/a.py"], references=["references/b.md"], assets=[])
```

Important rules:

- `SKILL.md` directories are AgentSkills-format skills.
- `load_project_skills()` finds `AGENTS.md`, `.agents/skills`, `.openhands/skills`, and legacy `.openhands/microagents`.
- `load_public_skills()` loads marketplace skills and should be treated as a cache-backed network workflow.
- `disabled_skills` removes matching skills after loading.

## Plugins and marketplaces

```python
MarketplaceRegistration(name="team", source="/path/to/marketplace", ref="main", repo_path=None, auto_load=True)
PluginSource(source="https://github.com/org/repo", ref="main", repo_path="plugins/my-plugin")
```

- Plugins may bring skills, hooks, MCP config, agents, and commands.
- Plugin loading is lazy; inspect resolved skills only after the first `send_message()` or `run()`.

## Hooks

```python
HookConfig(stop=[HookMatcher(matcher="*", hooks=[HookDefinition(command="./check.sh", timeout=60)])])
```

- `HookDefinition` is command-based by default.
- Exit code `2` blocks the operation; exit code `1` is a non-blocking error.
- Hook `Stop` and `UserPromptSubmit` are the main policy points for gating work.

## MCP

`MCPServer` supports `command`/stdio style servers, HTTP/SSE transport, and authenticated header/env variants.
Use a flat `dict[str, MCPServer]` on `Agent` or settings models.

## Secret handling

- `LookupSecret` normalizes hostless URLs against the current agent-server instance.
- `serialize_secret()` handles redaction, plaintext exposure, and encrypted storage.
- `validate_secret()` and `validate_secret_dict()` handle decryption and redacted values.
