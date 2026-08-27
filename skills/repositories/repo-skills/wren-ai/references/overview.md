# WrenAI Overview

## When to read

Read this before combining Wren's CLI, Python SDK, agent-framework adapters,
MCP server, GenBI flow, or browser runtime. It clarifies which layer owns a
particular operation.

## Architecture at a glance

WrenAI separates business context from execution:

1. A **Wren project** stores MDL source files, business rules, and confirmed
   NL→SQL pairs.
2. The **CLI and Python SDK** load that context, plan SQL through the Rust
   semantic engine, and send the planned SQL to a selected connector.
3. **Memory** retrieves schema and accepted query examples. Its semantic index
   is optional; the project knowledge files remain the durable source.
4. **Agent-facing access modes** layer on top: CLI-served workflow guides,
   LangChain/Pydantic AI toolkits, an MCP server, or browser-side WASM.

A simplified query path is:

```text
SQL against MDL models/views
  -> SQL parsing, policy checks, and manifest scoping
  -> wren-core semantic expansion and CTE rewrite
  -> target-dialect SQL
  -> connector execution
  -> PyArrow result table or CLI output
```

## Package map

| Surface | Public package or command | Best use |
| --- | --- | --- |
| CLI and Python orchestrator | `wrenai`, `wren` | Project lifecycle, profiles, planning, execution, memory, agent workflows, GenBI, MCP |
| Semantic core binding | `wren-core-py`, `wren_core` | Low-level `SessionContext`, manifest conversion, local file registration, cube SQL |
| LangChain/LangGraph adapter | `wren-langchain` | Tools and prompts bound to a prepared Wren project |
| Pydantic AI adapter | `wren-pydantic` | Typed toolset and retry-aware errors bound to a prepared project |
| Browser runtime | `@wrenai/wren-core-wasm` | Client-side MDL-aware queries over registered or remote static data |

## Project context versus profile

- **Project**: version-controlled source such as `wren_project.yml`, MDL model
  YAML, relationships, cubes, and `knowledge/`. The compiled MDL lives at
  `target/mdl.json` and is reproducible from the source project.
- **Profile**: environment-specific connection settings, usually with secret
  placeholders. It selects a datasource and is resolved at query time.

A project can bind a profile, but it should never embed plaintext credentials.
The project exposes business meaning; the profile supplies the current execution
connection.

## Selecting an interface

| Need | Use |
| --- | --- |
| Create, inspect, validate, or execute a Wren project | CLI first |
| Embed governed SQL in Python code | `WrenEngine` |
| Build a LangChain/LangGraph agent | `wren_langchain.WrenToolkit` |
| Build a Pydantic AI agent | `wren_pydantic.WrenToolkit` |
| Expose a prepared project to an MCP client | `wren serve mcp` with the `mcp` extra |
| Run an MDL-aware dashboard entirely in the browser | `@wrenai/wren-core-wasm` |
| Generate a static analytics app from a project | `wren genbi` |

## Cross-cutting constraints

- Most database connectors need an explicit package extra and a reachable,
  credentialed service; their imports are not proof of a usable connection.
- The semantic-memory extra pulls a substantial local ML stack. Without it,
  stored query pairs remain usable through the lightweight fallback, while
  semantic schema retrieval is unavailable.
- The MCP server needs a compiled MDL and the `mcp` extra. `--no-connect`
  deliberately exposes planning/context without database execution tools.
- The WASM runtime is browser-focused, single-threaded, and has no memory
  module. It is not a replacement for server-side connector execution.
