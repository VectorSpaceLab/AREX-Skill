---
name: mem-machine
description: "Use MemMachine to build, configure, troubleshoot, and integrate
  persistent memory for AI agents through the Python SDK, REST API, CLI, MCP
  server, TypeScript client, self-hosted server, and framework integrations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MemMachine

Use this skill when a task names MemMachine, `memmachine-client`,
`memmachine-server`, `memmachine_common`, `@memmachine/client`, `mem-cli`,
`memmachine-server`, persistent agent memory, episodic memory, semantic/profile
memory, MemMachine MCP, or a self-hosted MemMachine API server.

MemMachine is a client-server memory layer for AI agents. The server stores and
retrieves memories; application code usually talks to it through the Python SDK,
TypeScript REST client, CLI, REST API, or MCP tools.

## First Steps

1. Decide whether the user is using MemMachine as a package or configuring a
   server. Package-only tasks need a running MemMachine API server; server tasks
   need configuration, storage resources, and provider credentials.
2. If a Python environment is available, run the bundled read-only checker from
   this skill directory:
   ```bash
   python scripts/check_memmachine_install.py --summary
   ```
3. Route to the focused sub-skill before giving detailed commands.
4. Do not expose API keys, provider credentials, database passwords, or local
   memory contents in answers. Use placeholders when showing commands.

## Route By Task

- **Python SDK and CLI**: use
  [python-sdk-and-cli](sub-skills/python-sdk-and-cli/SKILL.md) for
  `MemMachineClient`, `Project`, `Memory`, `Config`, `mem-cli`, `memmachine`,
  project context, add/search/list/delete memory, semantic categories/tags,
  filters, formatted output, and LangGraph tool helpers.
- **Server, configuration, REST, MCP, and memory engines**: use
  [server-configuration-and-memory-engines](sub-skills/server-configuration-and-memory-engines/SKILL.md)
  for `memmachine-server`, YAML configuration, Docker Compose/Helm deployment,
  storage backends, provider resources, REST endpoint families, MCP stdio/HTTP,
  event/declarative long-term memory, semantic memory, and retrieval-agent
  behavior.
- **Integrations and migration**: use
  [integrations-and-migration](sub-skills/integrations-and-migration/SKILL.md)
  for LangGraph/LangChain/LlamaIndex/CrewAI/AWS Strands/OpenClaw/Dify/n8n/FastGPT
  integrations, example-agent adaptation, and ChatGPT/OpenAI/LoCoMo conversation
  export migration.
- **TypeScript REST client**: use
  [typescript-rest-client](sub-skills/typescript-rest-client/SKILL.md) for
  `@memmachine/client`, Node/TypeScript install/build/test, `MemMachineClient`,
  `MemMachineProject`, `MemMachineMemory`, Axios/API errors, and TS examples.

## Shared References And Scripts

- Read [repo-provenance.md](references/repo-provenance.md) to check the source
  commit, package-version baseline, and refresh triggers before relying on this
  skill for a changed MemMachine release.
- Read [package-overview.md](references/package-overview.md) for package names,
  version baseline, install variants, runtime architecture, and safe smoke
  checks.
- Read [rest-api-and-data-models.md](references/rest-api-and-data-models.md)
  when translating between SDK calls, CLI commands, REST payloads, and shared
  data models.
- Read [troubleshooting.md](references/troubleshooting.md) for cross-cutting
  install/import, server, auth, provider, storage, optional dependency, and
  API-path failures.
- Run [check_memmachine_install.py](scripts/check_memmachine_install.py) to
  inspect installed Python packages, public entry points, and key signatures
  without starting a server.
- Run [memmachine_server_doctor.py](scripts/memmachine_server_doctor.py) to
  inspect server prerequisites, optional Docker availability, and config-file
  shape without starting or stopping services.

## Package And Runtime Boundaries

Install only the surface needed for the task:

```bash
python -m pip install memmachine-client      # application/client code
python -m pip install memmachine-server      # self-hosted server workflows
npm install @memmachine/client               # TypeScript applications
```

- Python package names: `memmachine-client`, `memmachine-common`,
  `memmachine-server`, and meta package `memmachine`.
- TypeScript package name: `@memmachine/client`.
- Python client calls require a MemMachine API base URL. Use
  `http://localhost:8080` only when a local server is actually running.
- Cloud or secured deployments may require a bearer API key; never print the
  key after loading it from an environment variable or secret store.
- Self-hosted server workflows may require PostgreSQL/pgvector, Neo4j, Qdrant,
  Milvus, Nebula, provider credentials, or Docker. Treat those as explicit
  prerequisites, not as implicit side effects.
- Optional local NLP/model features, including spaCy multi-hop decomposition and
  sentence-transformer embeddings, require extra dependencies. Do not claim GPU
  or external-provider behavior is verified from a plain import check.

## Minimal Python Usage Shape

```python
from memmachine_client import MemMachineClient

client = MemMachineClient(base_url="http://localhost:8080", api_key=None)
project = client.get_or_create_project(org_id="my-org", project_id="my-project")
memory = project.memory(metadata={"user_id": "alice", "agent_id": "assistant"})
memory.add("Alice prefers aisle seats.", metadata={"category": "travel"})
result = memory.search("What seating does Alice prefer?", limit=5)
client.close()
```

For CLI usage, put global client flags before the subcommand and project context
on the project or memory command:

```bash
mem-cli --base-url "http://localhost:8080" memory search \
  "What seating does Alice prefer?" \
  --org-id "my-org" --project-id "my-project" --limit 5
```

## Verification Notes

Prefer read-only checks first: imports, `--help`, health checks, config parsing,
and mocked/unit-level command construction. Only start Docker services, call LLM
providers, upload memories, or run integration benchmarks after the user has
provided the required credentials, service endpoints, and permission for side
effects.
