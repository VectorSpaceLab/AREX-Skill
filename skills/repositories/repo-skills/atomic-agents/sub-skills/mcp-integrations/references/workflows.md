# MCP Workflows

## 1) Discover tools from a server

Use `fetch_mcp_tools(...)` when you want to turn a server's tool list into Atomic Agent-compatible tool classes.

Typical flow:

1. Choose a transport type: `STDIO`, `SSE`, or `HTTP_STREAM`.
2. Provide the endpoint or command string.
3. Call `fetch_mcp_tools(...)` or `fetch_mcp_tools_async(...)`.
4. Inspect the generated classes and wire them into your orchestration logic.

## 2) Generate resource and prompt classes

Use `fetch_mcp_resources(...)` and `fetch_mcp_prompts(...)` when the server exposes more than plain tools.

- Resources expose read-only data surfaces.
- Prompts expose reusable prompt templates.
- The generated classes follow the same schema-driven pattern as tool classes.

## 3) Build an orchestrator schema

Use `create_mcp_orchestrator_schema(...)` when the agent should choose among multiple remote tools.

This is the MCP-side counterpart to a choice agent:

- fetch server metadata first
- build a lightweight orchestrator schema
- only load the tools needed for the current task

## 4) Persistent sessions and client reuse

For long-lived or high-throughput scenarios:

- pass a `client_session` and `event_loop` into `MCPFactory`
- reuse the session for multiple calls instead of opening a fresh connection each time
- keep the event loop explicit so the runtime does not guess

## 5) Progressive disclosure

The `atomic-examples/progressive-disclosure` example demonstrates why you should avoid loading every tool schema up front.

- use a discovery step to select relevant tools
- load only the selected subset
- keep the orchestrator context smaller and more focused

## When to read this file

Read this file when you need a concrete MCP connection pattern or when you need to map a server's tool/resource/prompt surface into Atomic Agent workflows.
