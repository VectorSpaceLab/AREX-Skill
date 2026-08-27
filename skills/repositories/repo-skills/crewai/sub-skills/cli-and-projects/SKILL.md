---
name: cli-and-projects
description: "Routes CrewAI CLI, project scaffolding, JSONC projects,
  run/train/test/replay/chat/checkpoint/deploy commands, and project template
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# CrewAI CLI and Projects

Use this sub-skill when a task involves the `crewai` command line, scaffolding a CrewAI crew or flow project, understanding JSON-first versus classic project layouts, validating deployment readiness, or diagnosing project-root command failures.

## Read First

- [CLI reference](references/cli-reference.md) for command groups, safe/default behavior, and command options.
- [Project templates](references/project-templates.md) for JSON-first crew, classic crew, and flow layouts plus `pyproject.toml` expectations.
- [Deployment](references/deployment.md) for `crewai deploy` routing, validation checks, lockfiles, and credential boundaries.
- [Troubleshooting](references/troubleshooting.md) for missing project roots, placeholder inputs, JSONC/classic confusion, unsafe custom references, `chat_llm`, deploy credentials, and `uv` wrapper issues.
- [CLI inspector script](scripts/inspect_crewai_cli.py) for safe local introspection of the installed `crewai_cli` command tree and lightweight project-layout checks.

## Route Across CrewAI Skills

- Use [../../SKILL.md](../../SKILL.md) first when the user needs overall CrewAI package routing or is not clearly asking about CLI/project files.
- Use [../core-runtime/SKILL.md](../core-runtime/SKILL.md) for `Agent`, `Task`, `Crew`, guardrails, callbacks, hierarchical process semantics, and JSONC object field meaning beyond project layout.
- Use [../flows-and-events/SKILL.md](../flows-and-events/SKILL.md) for `Flow`, `@start`, `@listen`, routers, plotting semantics, persistence, and event graph design beyond CLI invocation.
- Use [../tools-and-mcp/SKILL.md](../tools-and-mcp/SKILL.md) for built-in tool classes, `BaseTool`, MCP adapters, and custom tool implementation details referenced by project templates.
- Use [../memory-knowledge-and-rag/SKILL.md](../memory-knowledge-and-rag/SKILL.md) for memory stores, knowledge sources, RAG loaders, and reset-memory data behavior beyond CLI flags.
- Use [../observability-and-hooks/SKILL.md](../observability-and-hooks/SKILL.md) for tracing, hooks, `log-tasks-outputs` interpretation, and telemetry configuration beyond command syntax.

## Safe Operating Defaults

- Prefer read-only checks first: `crewai --help`, `crewai create --help`, `crewai version`, `crewai deploy validate`, and this sub-skill's inspector script.
- Do not run `crewai run`, `crewai train`, `crewai test`, `crewai replay`, `crewai chat`, `crewai checkpoint resume`, `crewai deploy create`, or `crewai deploy push` on an untrusted project without user approval; they may execute local Python, custom tools, callbacks, LLM calls, subprocesses, deployment actions, or destructive state changes.
- Treat `custom:<name>` tool references and JSONC `{"python": "module.attribute"}` references as executable local code; inspect before running.
- Keep exact installed-version assumptions fresh with `crewai version` or the bundled inspector when command signatures matter.
