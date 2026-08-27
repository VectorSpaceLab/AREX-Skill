---
name: "cognee"
description: "Routes Cognee AI memory platform tasks across SDK memory APIs,
  graph/RAG retrieval, configuration, custom pipelines, session memory, CLI,
  API, MCP, and deployment workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Cognee Repo Skill

Use this skill when the user asks about Cognee, AI memory, persistent agent memory, graph RAG, Cognee SDK/CLI/API/MCP usage, Cognee configuration, custom graph extraction, session memory, or self-hosted Cognee services.

Cognee is a Python package and service stack for ingesting data, building a graph/vector-backed memory layer, and recalling knowledge for agents.

## First checks

For a safe installed-package check:

```bash
python scripts/check_install.py --help
python scripts/check_install.py --json
```

Minimal package install:

```bash
python -m pip install "cognee"
python - <<'PY'
import cognee
print(cognee.__version__)
print(cognee.SearchType.GRAPH_COMPLETION)
PY
```

Do not assume provider credentials or optional databases are configured. Most real ingestion/search workflows need an LLM and embedding provider; backend-specific workflows need matching extras and services.

## Route map

| User intent | Read |
| --- | --- |
| Store, build, recall, improve, or delete memory with SDK calls | [sub-skills/core-memory/SKILL.md](sub-skills/core-memory/SKILL.md) |
| Choose `SearchType`, tune recall/search, handle empty results or invalid query knobs | [sub-skills/search-retrieval/SKILL.md](sub-skills/search-retrieval/SKILL.md) |
| Configure LLMs, embeddings, database/storage backends, optional extras, env vars, and paths | [sub-skills/configuration-backends/SKILL.md](sub-skills/configuration-backends/SKILL.md) |
| Define custom graph schemas, custom tasks/pipelines, ontology workflows, memify, migration, export, or visualization | [sub-skills/advanced-graphs-pipelines/SKILL.md](sub-skills/advanced-graphs-pipelines/SKILL.md) |
| Use session memory, feedback entries, agent memory decorators, agent identities, or multi-agent isolation | [sub-skills/agent-session-memory/SKILL.md](sub-skills/agent-session-memory/SKILL.md) |
| Operate Cognee through CLI, FastAPI, MCP, Docker Compose, UI, cloud/local service connection, or push/sync | [sub-skills/api-cli-services/SKILL.md](sub-skills/api-cli-services/SKILL.md) |

## Shared references

- [references/package-overview.md](references/package-overview.md) — package identity, public surface, and sub-skill boundaries.
- [references/troubleshooting.md](references/troubleshooting.md) — cross-cutting install/import/credential/backend issues.
- [references/repo-provenance.md](references/repo-provenance.md) — source snapshot and refresh baseline.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json) — structured router placement used by DisCo repo-skills import tooling.

## Operating rules

- Prefer `remember`/`recall` for memory-shaped user requests; prefer `add`/`cognify`/`search` for explicit pipeline control.
- Before diagnosing workflow failures, separate three causes: package install, provider credentials, and database/storage backend state.
- Never tell a future agent to open original Cognee docs, examples, notebooks, tests, or scripts. Use the bundled references and scripts in this skill tree.
- Keep real API keys, cloud tokens, local filesystem paths, and service URLs in the user’s runtime configuration, not in copied guidance.
- Treat Docker, MCP, UI, and API servers as long-running services; run only `--help`, version, or check scripts unless the user asks to start them.
- If a current checkout has changed from the provenance snapshot, refresh this skill before relying on implementation-specific details.
