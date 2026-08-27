# Pydantic AI Toolkit

## When to read

Read this when exposing a Wren project through `wren-pydantic` and a Pydantic AI
`Agent`.

## Initialize and attach

```python
from pydantic_ai import Agent
from wren_pydantic import WrenToolkit

toolkit = WrenToolkit.from_project("analytics-project", profile=None)
toolset = toolkit.toolset(include_memory_write=True, takes_ctx=False)
agent = Agent(
    "openai:gpt-4o",
    instructions=toolkit.instructions(toolset=toolset),
    toolsets=[toolset],
)
```

The project must already contain `wren_project.yml` and `target/mdl.json`.

## Tool contract

The base toolset provides `wren_query`, `wren_dry_plan`, and `wren_list_models`.
When project memory is enabled, it additionally registers context fetch, query
recall, and query storage tools. `include_memory_write=False` suppresses only
the storage tool.

The tool APIs are synchronous because the underlying engine is synchronous.
Pydantic AI bridges them into its run loop; do not add fake async wrappers that
misrepresent the execution model.

## Error behavior

Query/planning errors that an LLM can repair are converted to `ModelRetry` with
phase-aware feedback. Infrastructure errors remain ordinary Wren errors for the
host application to handle. Query output uses typed models and enforces a hard
LLM-facing maximum of 1000 rows.

## `takes_ctx`

Use `takes_ctx=True` only when the Wren functions need to coexist with other
Pydantic AI tools that use `RunContext` and a typed dependency object. The Wren
toolkit itself already captures project state; it does not use that context.
