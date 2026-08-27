---
name: swarms
description: "Route Swarms users to the right single-agent, CLI, workflow, or
  tool/MCP guidance."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Swarms

Use this repo skill for the `swarms` Python package when the task is about building,
routing, loading, or debugging Swarms agents and orchestrations.

## Start here

- If the user is creating or tuning one `Agent`, go to `sub-skills/single-agent/`.
- If the user is using the `swarms` CLI, YAML, or markdown loaders, go to `sub-skills/cli-loaders/`.
- If the user is combining many agents with a swarm, router, graph, debate, vote, or chat pattern, go to `sub-skills/multi-agent-workflows/`.
- If the user is converting callables to tools or connecting MCP servers, go to `sub-skills/tools-mcp/`.

## What this skill covers

- Single-agent construction, memory, skills, marketplace prompts, prompt caching,
  fallback models, and artifact handling.
- CLI commands and file-driven agent creation.
- Multi-agent orchestration patterns, routing, consensus, and collaboration.
- Tool schema conversion, BaseTool helpers, and MCP client/server workflows.

## What this skill does not cover

- Release automation, Docker packaging, or repo-maintenance scripts.
- Benchmark harnesses and expensive evaluation loops.
- Voice-agent demos and AOP demo trees.
- Private repo checkout paths or workflow instructions that depend on the original source tree.

## Quick install and smoke check

```bash
pip install swarms
swarms --help
python -c "from swarms import Agent; print(Agent.__name__)"
```

## Optional runtime signals

- `WORKSPACE_DIR` controls where agent memory and workspace files are stored.
- `SWARMS_API_KEY` is required for marketplace fetch/publish workflows.
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GROQ_API_KEY`, and similar provider keys are required only for live model-backed runs.
- `graphviz` and `rustworkx` are optional for graph-workflow variety.

## Read these next

- `references/overview.md` for the package map and route selection notes.
- `references/troubleshooting.md` for cross-cutting install, import, key, and backend issues.
- `scripts/smoke.sh` for a quick offline import and CLI check.

## Routing rule of thumb

Choose the narrowest sub-skill that owns the user-facing workflow. Use the root only when the request spans multiple families or is about the package as a whole.

- `single-agent` owns one-agent configuration and its direct support objects.
- `cli-loaders` owns command-line entry points and config/file loading.
- `multi-agent-workflows` owns swarm orchestration and routing patterns.
- `tools-mcp` owns tool schema helpers and MCP transport/auth workflows.
