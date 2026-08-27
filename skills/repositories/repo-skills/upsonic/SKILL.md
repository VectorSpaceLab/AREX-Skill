---
name: upsonic
description: "Guides Upsonic Python agent-framework workflows, including agents,
  models, tools, memory, RAG, teams, autonomous agents, CLI projects,
  interfaces, skills, and safety governance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Upsonic Repo Skill

Use this skill for tasks that involve the Upsonic Python package or repository. It routes by workflow, not by source-folder shape, so future agents can answer common user requests without reopening the repo.

## Route map

| If the user asks about... | Read |
| --- | --- |
| `Agent`, `Task`, `Direct`, `Graph`, execution, streaming, structured output, run control | [sub-skills/agent-runtime/SKILL.md](sub-skills/agent-runtime/SKILL.md) |
| provider/model strings, provider inference, profiles, model selection, credentials | [sub-skills/models-and-providers/SKILL.md](sub-skills/models-and-providers/SKILL.md) |
| custom tools, `@tool`, `ToolConfig`, MCP, tool orchestration, agent-as-tool | [sub-skills/tools-and-mcp/SKILL.md](sub-skills/tools-and-mcp/SKILL.md) |
| `Chat`, `Memory`, session history, storage backends, user/session persistence | [sub-skills/chat-memory-storage/SKILL.md](sub-skills/chat-memory-storage/SKILL.md) |
| `KnowledgeBase`, loaders, splitters, embeddings, vector DBs, OCR, RAG | [sub-skills/knowledge-rag/SKILL.md](sub-skills/knowledge-rag/SKILL.md) |
| `Team`, `AutonomousAgent`, prebuilt agents, `RalphLoop`, `Simulation` | [sub-skills/teams-autonomous-prebuilt/SKILL.md](sub-skills/teams-autonomous-prebuilt/SKILL.md) |
| safety policies, anonymization, reflection, reliability, eval, tracing | [sub-skills/quality-safety-governance/SKILL.md](sub-skills/quality-safety-governance/SKILL.md) |
| `Skill` / `Skills`, loaders, validation, dependency resolution, caching | [sub-skills/skills-system/SKILL.md](sub-skills/skills-system/SKILL.md) |
| `upsonic` CLI projects, `upsonic_configs.json`, FastAPI `/call`, interfaces | [sub-skills/project-cli-interfaces/SKILL.md](sub-skills/project-cli-interfaces/SKILL.md) |

## Install and smoke check

```bash
python -m pip install upsonic
python scripts/check_upsonic_install.py
```

If you need a backend-specific workflow, install the smallest matching extra instead of all optional groups.

## Shared references

- [references/repo-provenance.md](references/repo-provenance.md) for source snapshot freshness.
- [references/package-overview.md](references/package-overview.md)
- [references/optional-extras.md](references/optional-extras.md)
- [references/optional-extras-snapshot.json](references/optional-extras-snapshot.json)
- [references/troubleshooting.md](references/troubleshooting.md)
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json)

## Shared scripts

- [scripts/check_upsonic_install.py](scripts/check_upsonic_install.py)
- [scripts/list_optional_extras.py](scripts/list_optional_extras.py)

## Guardrails

- Do not assume live API keys, databases, vector stores, OCR engines, or MCP servers are available.
- Do not leak local checkout paths, conda prefixes, or private environment details in runtime guidance.
- Prefer import/signature/CLI checks before optional service-backed checks.
- Keep cross-cutting troubleshooting in the root references and workflow-specific troubleshooting near the owning sub-skill.
