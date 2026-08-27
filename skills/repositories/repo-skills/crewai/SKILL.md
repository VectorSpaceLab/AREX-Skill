---
name: crewai
description: "Routes agents using or contributing to CrewAI, including crews,
  flows, CLI projects, tools, MCP, memory, RAG, LLM providers, observability,
  files, multimodal inputs, and repo development."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# CrewAI

Use this repo skill when the task involves CrewAI, the `crewai` Python package, the `crewai` CLI, official CrewAI tools, CrewAI Flows, memory/knowledge/RAG, multimodal file inputs, observability hooks, or contributing to the CrewAI monorepo.

## Start Here

- Read [Repository provenance](references/repo-provenance.md) before deciding whether this skill matches a current CrewAI checkout or needs refresh.
- Read [Installation and dependencies](references/installation-and-dependencies.md) when choosing package extras, optional dependencies, Python versions, or inspection commands.
- Read [Troubleshooting](references/troubleshooting.md) for cross-cutting install/import, optional dependency, credentials, CLI/project-root, telemetry, and repo-development failures.
- Run [check_crewai_environment.py](scripts/check_crewai_environment.py) for a safe local import/version/CLI diagnostic; it does not run crews, call LLMs, start MCP servers, or use credentials.

## Route by Task

- Use [core-runtime](sub-skills/core-runtime/SKILL.md) for `Agent`, `Task`, `Crew`, `Process`, kickoff modes, outputs, guardrails, callbacks, planning, reasoning, checkpoint basics, JSONC crew definitions, and direct-code crew design.
- Use [flows-and-events](sub-skills/flows-and-events/SKILL.md) for `Flow`, `@start`, `@listen`, `@router`, state, routing labels, plotting, persistence, checkpointing, human feedback, event listeners, and event ordering.
- Use [cli-and-projects](sub-skills/cli-and-projects/SKILL.md) for `crewai create`, JSON-first and classic project scaffolds, `crewai run`, `train`, `test`, `replay`, `chat`, `deploy`, `uv`, project templates, and CLI troubleshooting.
- Use [tools-and-mcp](sub-skills/tools-and-mcp/SKILL.md) for official `crewai_tools`, custom `BaseTool` or `CrewStructuredTool` work, MCP adapters, tool publishing, integration tools, optional packages, and credential boundaries.
- Use [memory-knowledge-and-rag](sub-skills/memory-knowledge-and-rag/SKILL.md) for `Memory`, `Knowledge`, `knowledge_sources`, RAG loaders, embedding providers, vector stores, `RagTool`, and `reset-memories` behavior.
- Use [llm-and-providers](sub-skills/llm-and-providers/SKILL.md) for `LLM`, provider model strings, API keys, base URLs, Azure/OpenAI-compatible/Anthropic/Bedrock/Google/Snowflake settings, streaming, tool calls, response models, custom LLMs, and LiteLLM migration.
- Use [observability-and-hooks](sub-skills/observability-and-hooks/SKILL.md) for tracing, telemetry, observability providers, event listeners, LLM/tool hooks, kickoff hooks, output logs, task outputs, and security fingerprints.
- Use [files-and-multimodal](sub-skills/files-and-multimodal/SKILL.md) for `crewai-files`, `input_files`, file source resolution, provider file constraints, multimodal agents, upload cache, and file/document tool adjacency.
- Use [repo-development](sub-skills/repo-development/SKILL.md) only for contributing to this CrewAI checkout: focused tests, docs versioning, Edge docs edits, frozen snapshot rules, workspace metadata, and safe native verification selection.

## Common Decisions

- Prefer JSON-first projects from `crewai create crew <name>` unless the user is maintaining an existing classic Python/YAML crew or needs decorator-heavy customization.
- Treat `custom:<name>` tools and `{"python": "module.attribute"}` JSONC references as trusted-code boundaries; inspect before running projects from untrusted sources.
- Do not run LLM-backed crews, hosted deploy/login commands, MCP servers, network-backed tools, or credential-bound integrations just to inspect a project. Use the bundled diagnostic scripts first.
- Use provider-specific sub-skills for optional dependency and credential choices instead of installing all extras or assuming all integrations are available.
- For repo docs edits, modify only `docs/edge/<lang>/...`; do not edit `docs/v*/` frozen snapshots or delete/rename `docs/images/` assets outside release-freeze work.

## Safe Diagnostics

- `python scripts/check_crewai_environment.py --json` reports installed CrewAI package versions, top-level import results, and CLI command names.
- `python sub-skills/core-runtime/scripts/validate_crew_definition.py --help` explains static JSONC crew checks without importing project custom code.
- `python sub-skills/flows-and-events/scripts/validate_flow_graph.py --help` explains static flow graph checks without calling `kickoff()`.
- `python sub-skills/cli-and-projects/scripts/inspect_crewai_cli.py --help` explains CLI/project layout checks that avoid running crews or deploy/login flows.
- `python sub-skills/repo-development/scripts/select_native_tests.py --help` suggests focused maintainer checks from changed paths without running them.

## Refresh Triggers

Run `refresh-repo-skill` before relying on this skill if the current CrewAI checkout has a different commit than [Repository provenance](references/repo-provenance.md), package versions or CLI entry points changed, `docs/edge/en/` workflows changed materially, or major source roots such as `lib/crewai/src/crewai`, `lib/cli/src/crewai_cli`, `lib/crewai-tools/src/crewai_tools`, or `lib/crewai-files/src/crewai_files` moved.
