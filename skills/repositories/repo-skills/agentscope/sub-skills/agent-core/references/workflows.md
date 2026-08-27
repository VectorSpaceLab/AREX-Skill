# Agent Workflows

## Purpose

Read this for an end-to-end path from model selection to a working AgentScope agent with tools, permissions, and local skills.

## Canonical workflow

1. Pick a provider model and credential from `provider-connectors`.
2. Assemble a `Toolkit` with only the tools you need.
3. Add local skills through `skills_or_loaders` if the workflow depends on reusable instructions.
4. Tune `ContextConfig`, `ReActConfig`, `InjectionConfig`, or `ModelConfig` only when the defaults do not match the task.
5. Call `reply()` for a single final response or `reply_stream()` when you need live tool/model events.
6. Handle interruption and confirmation events explicitly if the workflow can pause for a user or external action.

## Minimal shape

```python
from agentscope.agent import Agent
from agentscope.tool import Toolkit, Bash, Read, Write
from agentscope.skill import LocalSkillLoader

agent = Agent(
    name="Friday",
    system_prompt="You are a helpful assistant.",
    model=...,  # supply a provider model from provider-connectors
    toolkit=Toolkit(
        tools=[Bash(), Read(), Write()],
        skills_or_loaders=[LocalSkillLoader("/path/to/skill")],
    ),
)

reply = await agent.reply(user_msg)
```

## When to use `reply_stream`

Use `reply_stream()` when you need to observe:

- the start or end of a reply,
- model-call boundaries,
- streaming text / thinking / hint / data blocks,
- tool-call and tool-result boundaries,
- interruption or confirmation events.

The stream is the best fit when you are debugging a tool loop, a permission failure, or a structured-output turn.

## Local skills

A local skill is just a directory with a valid `SKILL.md`. The `LocalSkillLoader` scans the directory and returns `Skill` objects that `Toolkit` turns into skill instructions.

Useful checks:

- Does the directory contain `SKILL.md`?
- Does the frontmatter include `name` and `description`?
- Is `scan_subdir=True` actually needed, or is the root directory enough?

## Built-in tools

The core built-ins cover the common coding-agent surface:

- `Bash` / `PowerShell` for shell commands
- `Read`, `Write`, `Edit` for filesystem work
- `Glob`, `Grep` for search
- `TaskCreate`, `TaskList`, `TaskGet`, `TaskUpdate` for planning
- `ResetTools` for tool-group reset flows

Use the filesystem tools with care: they intentionally guard a set of common secret and repo paths.

## Common decision points

- If the task needs structured output, provide `structured_schema` to `reply()` or `reply_stream()`.
- If the task needs runtime-state reminders, adjust `InjectionConfig` rather than trying to fake the state in the prompt.
- If the task needs different retry or iteration behavior, tune `ModelConfig` and `ReActConfig`.
- If the task should be read-only, use permission settings and tool-group composition rather than hoping the model behaves conservatively.

## Related references

- `references/api-reference.md` for constructor signatures.
- `references/troubleshooting.md` for common permission, stream, and skill-loading failures.
