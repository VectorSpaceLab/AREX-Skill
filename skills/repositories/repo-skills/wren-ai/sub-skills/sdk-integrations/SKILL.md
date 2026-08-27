---
name: sdk-integrations
description: "Guide Wren LangChain, LangGraph, and Pydantic AI integrations
  through WrenToolkit, project prerequisites, tool contracts, memory controls,
  and error recovery."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Wren Framework SDKs

Use this sub-skill when an application agent should consume an existing,
CLI-prepared Wren project through LangChain/LangGraph or Pydantic AI.

## Shared Preconditions

1. Install the framework package and the datasource/memory extras actually used.
2. Prepare the project first:
   ```bash
   wren context validate
   wren context build
   ```
3. Ensure `wren_project.yml` and `target/mdl.json` are present before calling
   `WrenToolkit.from_project(...)`.
4. Keep connection configuration in the Wren profile plus environment-backed
   values. The toolkit reads the project and resolves profile state; it does not
   invent a database connection.

## LangChain / LangGraph

```python
from wren_langchain import WrenToolkit
from langchain.agents import create_agent

toolkit = WrenToolkit.from_project("analytics-project")
tools = toolkit.get_tools(include_memory_write=False)
agent = create_agent("openai:gpt-4o", tools=tools, system_prompt=toolkit.system_prompt(tools=tools))
```

Use `get_tools(..., raise_on_error=True)` only when the host loop should receive
exceptions instead of an LLM-readable error envelope.

## Pydantic AI

```python
from wren_pydantic import WrenToolkit
from pydantic_ai import Agent

toolkit = WrenToolkit.from_project("analytics-project")
toolset = toolkit.toolset(include_memory_write=False)
agent = Agent("openai:gpt-4o", instructions=toolkit.instructions(toolset=toolset), toolsets=[toolset])
```

Set `takes_ctx=True` only when combining Wren tools with a deps-typed Pydantic
AI toolset.

## Tool Selection Rules

- Keep `wren_dry_plan` available when an agent may generate nontrivial SQL; it
  is the cheap semantic check before `wren_query`.
- Keep `wren_list_models` available so an agent can inspect its modeled surface
  instead of hallucinating table names.
- Allow memory writes only when the host has an explicit policy for persisting
  accepted user questions and SQL; otherwise set `include_memory_write=False`.
- Do not reuse a toolkit after intentionally switching project/profile context;
  create a new instance so connection and project assumptions are explicit.

## References and Helper

- Read `references/langchain.md` for tool names, envelopes, and prompt behavior.
- Read `references/pydantic-ai.md` for typed tools and retry behavior.
- Read `references/tool-contracts.md` to keep the agent prompt synchronized
  with the tools actually supplied.
- Read `references/troubleshooting.md` for project, profile, memory, and
  framework errors.
- Run `scripts/sdk_project_probe.py --project <directory>` to check project
  prerequisites and import available framework packages without making a query.

## Guardrails

- A toolkit is one project context. Use separate toolkits for separate Wren
  projects rather than assuming profile changes hot-swap an existing toolkit.
- Memory tools are auto-detected from project state. Do not promise fetch/recall
  or memory write tools when the relevant backend/path is absent.
- LLM-facing query tools cap output. Write aggregation SQL rather than asking a
  tool for an unbounded extract.
