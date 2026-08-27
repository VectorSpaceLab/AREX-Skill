---
name: core-runtime
description: "Guides agents working with CrewAI core runtime objects, including
  agents, tasks, crews, processes, kickoff modes, outputs, guardrails,
  callbacks, planning, reasoning, checkpoint basics, and JSONC crew
  definitions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Core Runtime

Use this sub-skill when the task is to design, debug, migrate, or validate CrewAI `Agent`, `Task`, `Crew`, `Process`, `CrewOutput`, or `TaskOutput` usage in direct Python code or JSONC crew projects.

## Route First

- For object signatures, required fields, process values, kickoff variants, outputs, callbacks, guardrails, planning, reasoning, and checkpoint basics, read [references/api-reference.md](references/api-reference.md).
- For direct-code assembly, sequential and hierarchical crews, output handling, guardrails, callback placement, planning/reasoning, and checkpoint-safe patterns, read [references/workflows.md](references/workflows.md).
- For JSONC project runtime fields, agent files, task entries, callback/custom-tool trust boundaries, and migration between Python and JSONC, read [references/jsonc-projects.md](references/jsonc-projects.md).
- For common symptoms and fixes, including missing agent/task fields, forward task context, hierarchical manager requirements, output model confusion, guardrail retries, callback trust, and checkpoint/training mixups, read [references/troubleshooting.md](references/troubleshooting.md).
- To statically check a JSONC crew definition without importing project tools or running LLMs, run [scripts/validate_crew_definition.py](scripts/validate_crew_definition.py) with `--help` first.

## Boundaries

- Stay here for core runtime composition, kickoff behavior, task dependencies, outputs, guardrails, callbacks, planning/reasoning, security/checkpoint basics, and JSONC-vs-code construction choices.
- Use [../flows-and-events/SKILL.md](../flows-and-events/SKILL.md) for `Flow`, `@start`, `@listen`, `@router`, event graph routing, flow persistence, and flow plotting.
- Use [../cli-and-projects/SKILL.md](../cli-and-projects/SKILL.md) for project scaffolding, `crewai run`, `crewai train`, `crewai test`, `crewai replay`, `crewai checkpoint`, and other CLI command details.
- Use [../tools-and-mcp/SKILL.md](../tools-and-mcp/SKILL.md) for official tools, custom tools, MCP adapters, and tool publishing.
- Use [../llm-and-providers/SKILL.md](../llm-and-providers/SKILL.md) for provider credentials, `LLM` provider options, model IDs, base URLs, streaming provider compatibility, and LiteLLM migration details.
- Use [../memory-knowledge-and-rag/SKILL.md](../memory-knowledge-and-rag/SKILL.md) for memory scopes, knowledge sources, embeddings, RAG clients, vector stores, and retrieval depth.
- Return to [../../SKILL.md](../../SKILL.md) when a request spans multiple CrewAI capability areas and needs root routing context.
