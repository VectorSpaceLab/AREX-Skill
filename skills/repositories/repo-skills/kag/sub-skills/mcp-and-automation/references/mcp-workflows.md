# MCP Workflows

## Purpose

Read this when you need to launch or validate KAG's MCP server or the MCP-related executor/config surface.

## Server entry point

The server CLI is `kag mcp-server`.

### Flags

- `--transport sse|stdio`
- `--port <int>`
- `--enabled-tools qa-pipeline,kb-retrieve`
- `all` as a convenience value for both supported tools

### Supported tools

- `qa-pipeline`
- `kb-retrieve`

## When to use each transport

- `stdio` is usually the safest choice for an agent-driven local workflow.
- `sse` is better when you want a networked server on a specific port.

## MCP executor config shape

The solver-side MCP executor uses a config block with fields like:

- `store_path`
- `name`
- `description`
- `llm`
- `prompt`
- `env`

The executor loads a local file when `store_path` is a URL and then talks to the MCP client with the configured LLM and prompt.

## Related surfaces

- The solver pipeline can include an `mcp_pipeline` route.
- Example MCP clients wrap a chat loop around the configured executor.
- `kb-retrieve` depends on graph/query access, not only on the server flag.

## Safe preflight

Always run `scripts/check_mcp_config.py` before starting a server or exposing a tool set. It should tell you whether the launch plan is incomplete without actually opening a port.
