---
name: atomic-agents
description: "Use Atomic Agents to build schema-driven agents, integrate tools
  and MCP connectors, adapt example applications, and maintain the monorepo
  safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Atomic Agents

Use this skill when a task mentions Atomic Agents, `atomic-agents`, `atomic-assembler`, Atomic Forge, MCP connectors, the example projects, or editing this repository.

## Start here

1. Read `references/package-summary.md` for the monorepo map, package names, and core terminology.
2. Read `references/repo-provenance.md` before deciding whether this skill matches the current checkout or needs refresh.
3. Read `references/troubleshooting.md` for cross-cutting install, import, CLI, and version-mismatch issues.
4. Use the route map below. Each subskill owns deeper references and any helper scripts.

## Install and smoke check

- Public use: `pip install atomic-agents`
- Checkout work: `uv sync` or `pip install -e .`
- Smoke check: `python -c "import atomic_agents, atomic_assembler; print(atomic_agents.__version__)"`
- CLI check: `atomic --help`

## Route map

| User task | Use subskill | Why |
| --- | --- | --- |
| Build, run, stream, or debug a typed `AtomicAgent` with schemas, history, prompts, hooks, token counting, or multimodal content | `sub-skills/agent-core/SKILL.md` | Owns the core agent API, memory, context providers, hooks, and the fundamental schema contract. |
| Define tools/resources/prompts, reason about Atomic Forge tool families, use the `atomic` CLI, or adapt tool-selection patterns | `sub-skills/tooling-and-forge/SKILL.md` | Owns `BaseTool`, `BaseResource`, `BasePrompt`, Atomic Forge, Atomic Assembler, and tool orchestration surfaces. |
| Connect to MCP servers or troubleshoot dynamic MCP-generated tools, resources, and prompts | `sub-skills/mcp-integrations/SKILL.md` | Owns the MCP transport, schema transformation, and generated tool/resource/prompt factory surface. |
| Adapt a concrete example project such as quickstart, multimodal, RAG, orchestration, memory, hooks, YouTube, DSPy, FastAPI, progressive disclosure, or `mcp-agent` | `sub-skills/example-workflows/SKILL.md` | Owns the example catalog, dependencies, and recipe-level guidance. |
| Modify this checkout, run focused tests, update docs, or reason about release/CI behavior | `sub-skills/repo-development/SKILL.md` | Owns monorepo development commands, packaging conventions, docs checks, and maintainer workflow guidance. |

## Shared references and helpers

- `references/repo-routing-metadata.json` records the router metadata consumed during import into the repo-skills router.
- `scripts/check_atomic_agents_env.py` performs a safe import/version/CLI smoke check.
- Read each subskill's `references/` and `scripts/` for workflow-specific guidance.
