---
name: single-agent
description: "Guide one Swarms Agent, its memory, skills, marketplace, prompt
  caching, and support objects."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Single Agent

Use this sub-skill when the user wants to create, configure, inspect, or debug one Swarms `Agent` and the objects that travel with it.

## Owns these workflows

- Build a new `Agent` with the right model, loop count, tools, and output type.
- Attach skills from a `skills_dir` and decide when to load them statically or dynamically.
- Turn on or tune memory, context compression, fallback models, streaming, prompt caching, and multimodal input.
- Load or publish marketplace prompts.
- Work with the support objects that make a single agent usable: `Conversation`, `Artifact`, `SkillsManager`, `ContextCompressor`, `LLMManager`, and `AgentMarketplaceHandler`.

## Does not own

- CLI command parsing or YAML/markdown file loaders; use `cli-loaders` for those.
- Tool schema conversion, BaseTool, or MCP server/client details; use `tools-mcp`.
- Multi-agent orchestration, routing, debate, group chat, or swarm planning; use `multi-agent-workflows`.

## Read this sub-skill when the request mentions

- `Agent`, `run`, `run_stream`, `max_loops`, `interactive`, `autosave`, or `output_type`.
- `skills_dir`, `SkillsManager`, `persistent_memory`, `context_compression`, or `WORKSPACE_DIR`.
- `marketplace_prompt_id`, `SWARMS_API_KEY`, or prompt marketplace workflows.
- `prompt_caching`, `cache_config`, model fallback, or provider-specific parameter behavior.
- `Conversation`, `Artifact`, `add_memory`, or state save/load issues.

## Working shape

1. Decide whether the task is a minimal agent, a skills-enabled agent, a memory-backed agent, or a provider-specific live run.
2. Check the user’s model, key, and workspace assumptions before recommending runtime settings.
3. Prefer a minimal offline smoke check first; only move to live provider execution if the user has keys and wants a real model call.
4. Use the bundled references for constructor knobs, workflow examples, and failure recovery.

## What to read next

- `references/api-reference.md` for the confirmed `Agent` signature and the main support-object APIs.
- `references/workflows.md` for common single-agent recipes.
- `references/troubleshooting.md` for workspace, key, fallback, and marketplace failures.
- `scripts/agent_smoke.py` for a local offline import and support-object check.

## Typical user questions this sub-skill should answer

- How do I create one agent that remembers state across runs?
- How do I load a skill folder or choose relevant skills for a task?
- Why is my agent not writing memory files where I expect?
- Why did a prompt-caching or provider call fail even though the agent built successfully?
- How do I attach a marketplace prompt without hand-editing the system prompt?

## Route boundaries

- If the task starts with a command such as `swarms agent` or `swarms setup-check`, route to `cli-loaders`.
- If the user is really asking for a workflow of multiple agents, route to `multi-agent-workflows`.
- If the user is mainly converting functions to tools or attaching MCP, route to `tools-mcp`.

## Acceptance checklist

- The response should name the relevant `Agent` fields and support objects.
- The answer should mention any required env vars or workspace assumptions.
- The answer should give a concrete recovery path for missing keys, missing workspace, or invalid skill directories.
- If live execution is requested, the answer should say which provider credentials are required before a model call can succeed.
