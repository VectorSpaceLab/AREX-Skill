---
name: python-sdk-and-cli
description: "Use the MemMachine Python SDK and CLI for project context, memory
  add/search/list/delete, semantic profile operations, filters, formatting,
  config API wrappers, and LangGraph tool helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Python SDK And CLI

Use this sub-skill when a task names `memmachine_client`, `MemMachineClient`,
`Project`, `Memory`, `Config`, `mem-cli`, `memmachine`, Python memory add or
search, semantic categories/tags/features, metadata filters, `agent_mode`, or
LangGraph memory tools.

## Route Within This Sub-skill

- Read [python-sdk-reference.md](references/python-sdk-reference.md) for the
  verified Python object model, method signatures, and return-shape notes.
- Read [memory-workflows.md](references/memory-workflows.md) for project/context
  setup, add/search/list/delete, semantic feature/category/tag workflows,
  filters, and validation patterns.
- Read [cli-reference.md](references/cli-reference.md) for `mem-cli` and
  `memmachine` command shapes, environment variables, JSON flags, and safe
  examples.
- Read [troubleshooting.md](references/troubleshooting.md) when imports,
  base URLs, project context, filters, closed clients, or server responses fail.
- Run [mem_cli_smoke.py](scripts/mem_cli_smoke.py) to inspect CLI parser/help or
  build safe command examples without contacting a server.
- Run [python_client_recipe.py](scripts/python_client_recipe.py) to print a
  minimal Python SDK recipe or optionally run a live health/add/search demo only
  when explicit live arguments are supplied.

## Quick Python Pattern

```python
from memmachine_client import MemMachineClient

client = MemMachineClient(base_url="http://localhost:8080", api_key=None)
try:
    project = client.get_or_create_project(org_id="my-org", project_id="my-project")
    memory = project.memory(
        metadata={"user_id": "alice", "agent_id": "assistant", "session_id": "demo"}
    )
    memory.add("Alice prefers aisle seats.", metadata={"category": "travel"})
    results = memory.search("What seating does Alice prefer?", limit=5)
finally:
    client.close()
```

Use explicit `org_id`, `project_id`, and memory metadata instead of relying on
ambient defaults. Keep API keys in environment variables or secret stores.

## Quick CLI Pattern

```bash
mem-cli --base-url "http://localhost:8080" memory add \
  "Alice prefers aisle seats." \
  --org-id "my-org" --project-id "my-project" \
  --metadata user_id=alice --metadata agent_id=assistant \
  --metadata category=travel

mem-cli --base-url "http://localhost:8080" memory search \
  "What seating does Alice prefer?" \
  --org-id "my-org" --project-id "my-project" --limit 5
```

Global flags such as `--base-url` and `--api-key` come before the subcommand.
Project context flags belong on `projects` or `memory` subcommands.

## Decision Points

- **SDK or CLI?** Use SDK for application code and tests; use CLI for ad-hoc
  inspection, shell workflows, and agent memory retrieval/addition.
- **Filter style?** Use modern `filter="metadata.category = 'travel'"` for
  boolean logic. Use `filter_dict` only for simple legacy equality filters.
- **Semantic or episodic?** `MemoryType` supports `episodic` and `semantic`.
  Adding to both may be useful, but verify the server configuration supports
  both before assuming results appear in both surfaces.
- **Agent mode?** `agent_mode=True` asks the server retrieval agent to do richer
  query handling. It needs server-side LLM/reranker resources; use ordinary
  search first for simple lookups.
- **LangGraph tools?** Use `MemMachineTools` or helper factories when an agent
  runtime expects callable add/search tools. Ensure framework dependencies are
  installed separately.

## Non-goals And Cross-links

- Server YAML, storage/provider resources, Docker, MCP, and REST deployment
  details belong in
  [server-configuration-and-memory-engines](../server-configuration-and-memory-engines/SKILL.md).
- Framework adapters beyond the Python LangGraph helper surface belong in
  [integrations-and-migration](../integrations-and-migration/SKILL.md).
- `@memmachine/client` belongs in
  [typescript-rest-client](../typescript-rest-client/SKILL.md).
- Endpoint/model translation details shared across SDKs are in the root
  [REST API and data models reference](../../references/rest-api-and-data-models.md).
