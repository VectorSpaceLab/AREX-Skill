# Cognee Package Overview

Cognee is an open-source AI memory platform for agents. It ingests text, files,
URLs, documents, code, and structured sources; builds a graph/vector-backed
memory layer; and exposes SDK, CLI, FastAPI, MCP, UI, and Docker entry points.

## Package identity

- Distribution: `cognee`
- Main import: `import cognee`
- Console script: `cognee-cli`
- Python: `>=3.10,<3.15`
- Main optional sibling package in the repository: `cognee-mcp`

## Public surface groups

| Surface | Examples | Owning sub-skill |
| --- | --- | --- |
| Memory API | `remember`, `recall`, `improve`, `forget` | [core-memory](../sub-skills/core-memory/SKILL.md) |
| Pipeline API | `add`, `cognify`, `search`, `run_custom_pipeline` | [core-memory](../sub-skills/core-memory/SKILL.md), [advanced-graphs-pipelines](../sub-skills/advanced-graphs-pipelines/SKILL.md) |
| Retrieval | `SearchType`, graph/RAG/chunk/temporal/code/agentic search | [search-retrieval](../sub-skills/search-retrieval/SKILL.md) |
| Configuration | `cognee.config`, `LLMConfig`, `EmbeddingConfig`, database configs, `.env` variables | [configuration-backends](../sub-skills/configuration-backends/SKILL.md) |
| Agent/session memory | typed memory entries, session scopes, feedback, `agent_memory`, `cognee.agents` | [agent-session-memory](../sub-skills/agent-session-memory/SKILL.md) |
| Advanced graph workflows | `DataPoint`, custom graph models, ontology, `memify`, export, visualization, migration | [advanced-graphs-pipelines](../sub-skills/advanced-graphs-pipelines/SKILL.md) |
| Services | `cognee-cli`, FastAPI, MCP, Docker, UI, `serve`, `push`, `sync` | [api-cli-services](../sub-skills/api-cli-services/SKILL.md) |

## Default local stack

The base package is designed to start with file-backed local defaults:

- Relational database: SQLite
- Vector database: LanceDB
- Graph layer: Ladybug/Kuzu-compatible embedded storage

Provider-backed operations still need an LLM and embedding configuration. The
base install verifies import/CLI surfaces, but it does not prove that the user’s
chosen OpenAI/Anthropic/Ollama/Azure/etc. provider credentials are valid.

## Optional capabilities

Optional extras add provider or backend support. Install only what the task
needs. For example:

```bash
python -m pip install "cognee[postgres-binary]"
python -m pip install "cognee[neo4j]"
python -m pip install "cognee[fastembed]"
python -m pip install "cognee[aws]"
```

Use [configuration-backends](../sub-skills/configuration-backends/SKILL.md) for
the full matrix.

## Capability boundaries

- This skill teaches public Cognee operation, not internal release engineering.
- Frontend implementation details are intentionally shallow; service launch and
  UI build notes live in [api-cli-services](../sub-skills/api-cli-services/SKILL.md).
- Native examples that require API keys, cloud accounts, Docker, or database
  services are documented as optional rather than assumed runnable.
