---
name: server-configuration-and-memory-engines
description: "Use the MemMachine server, configuration, REST API, MCP entry
  points, memory engines, storage/provider resources, Docker/Helm deployment
  shape, and backend troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Server Configuration And Memory Engines

Use this sub-skill when a task names `memmachine-server`, MemMachine REST API,
MCP stdio/HTTP, `cfg.yml`, Docker Compose, Helm, storage resources, provider
resources, episodic memory, semantic memory, short-term memory, retrieval-agent
mode, or server startup/troubleshooting.

## Route Within This Sub-skill

- Read [server-configuration.md](references/server-configuration.md) for
  configuration sections, startup modes, environment variables, and safe
  validation.
- Read [storage-and-providers.md](references/storage-and-providers.md) for
  database/vector/graph stores, embedders, language models, rerankers, optional
  extras, and credential boundaries.
- Read [rest-and-mcp.md](references/rest-and-mcp.md) for REST endpoint families,
  health/metrics, MCP tools, and context parameters.
- Read [memory-engines.md](references/memory-engines.md) for event vs
  declarative long-term memory, short-term memory, semantic/profile memory, and
  retrieval-agent behavior.
- Read [troubleshooting.md](references/troubleshooting.md) for server startup,
  config, Docker, storage, provider, MCP, and optional dependency failures.
- Run [server_config_doctor.py](scripts/server_config_doctor.py) to validate a
  MemMachine YAML config shape without starting services.
- Run [mcp_entrypoint_smoke.py](scripts/mcp_entrypoint_smoke.py) to inspect MCP
  entry-point availability and context parameters without launching a listener.

## Safe Startup Checks

A local server task usually starts with read-only checks:

```bash
memmachine-server --help
memmachine-mcp-http --help
python scripts/server_config_doctor.py --config cfg.yml
python scripts/mcp_entrypoint_smoke.py --check-imports
```

Only start or stop services after the user confirms the desired deployment and
side effects. Docker Compose and Helm workflows can create volumes, containers,
network listeners, and persistent data.

## Configuration Shape

A typical server config has these top-level sections:

```yaml
logging: {}
episode_store: {}
episodic_memory: {}
retrieval_agent: {}
semantic_memory: {}
session_manager: {}
resources:
  databases: {}
  embedders: {}
  language_models: {}
  rerankers: {}
```

Important backend decision:

- `episodic_memory.long_term_memory.backend: declarative` uses a
  `vector_graph_store` resource such as Neo4j/Nebula.
- `backend: event` uses a `vector_store` plus a `segment_store` resource.

## Server Commands And Entry Points

- `memmachine-server --help` shows server flags including `--stdio`,
  `--version`, and `--with-config-api`.
- `memmachine-mcp-stdio` runs MCP in stdio mode for local MCP clients.
- `memmachine-mcp-http --host HOST --port PORT` runs MCP over HTTP.
- `memmachine-configure` is interactive; do not run it in automation unless the
  user explicitly wants an interactive installer/configurer.

## Cross-links

- Use [python-sdk-and-cli](../python-sdk-and-cli/SKILL.md) for application-side
  Python client calls, `mem-cli`, and LangGraph helper usage.
- Use [integrations-and-migration](../integrations-and-migration/SKILL.md) for
  framework/platform recipes and conversation import tools.
- Use [typescript-rest-client](../typescript-rest-client/SKILL.md) for Node/TS
  client calls against a MemMachine server.
- Use the root [REST API and data models](../../references/rest-api-and-data-models.md)
  reference when translating endpoint payloads across clients.

## Verification Boundaries

- Import and help checks prove packages and entry points are available; they do
  not prove databases, providers, or MCP clients are configured.
- Docker, Neo4j, Postgres, Qdrant, Milvus, Nebula, OpenAI, AWS Bedrock, Cohere,
  and Ollama/OpenAI-compatible endpoints are optional external dependencies.
- The optional spaCy multi-hop decomposer may be absent in base installs. Do not
  classify its warning as a fatal server failure unless the user specifically
  needs spaCy-based decomposition.
