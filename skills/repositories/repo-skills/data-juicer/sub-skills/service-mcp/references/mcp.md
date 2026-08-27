# MCP reference

## Main entrypoints
- `dj-mcp recipe-flow`
- `dj-mcp granular-ops`

## Transports
The CLI supports multiple transport styles, including:
- `stdio`
- `sse`
- `streamable-http`

Choose the simplest transport that matches the caller.
For local debugging, `stdio` is usually easiest.

## Tool families
- recipe-flow: higher-level recipe execution and analysis
- granular-ops: smaller operator- or utility-focused actions

## Common checks
- Confirm `DJ_OPS_LIST_PATH` if the tool cannot find the operator list.
- Confirm that the selected transport matches the client.
- Confirm that the route or tool name matches the mode you launched.

## Good habit
Use `dj-mcp --help` first when you are unsure whether the request belongs in recipe-flow or granular-ops.
