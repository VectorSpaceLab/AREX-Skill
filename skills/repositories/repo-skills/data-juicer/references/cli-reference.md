# CLI reference

## Console scripts
- `dj-process`: run a data recipe.
- `dj-analyze`: analyze dataset quality and operator stats.
- `dj-install`: inspect operator dependency guidance.
- `dj-mcp`: launch the MCP server in recipe-flow or granular-ops mode.

## Common behavior
- The three main recipe commands share the same core config family.
- `dj-mcp` supports `granular-ops` and `recipe-flow` modes with `stdio`, `sse`, and `streamable-http` transports.
- Use the CLI help text before adding flags one by one.

## Route-aware usage
- Local recipe flags and dataset settings belong to `recipes-and-ops`.
- Ray executor flags, job IDs, checkpointing, and tracer toggles belong to `ray-and-recovery`.
- Service transport, `DJ_OPS_LIST_PATH`, search modes, and request encoding belong to `service-mcp`.

## Debug habit
If a command fails, rerun it with `--help`, then reduce the config to the smallest valid example before changing multiple flags at once.
