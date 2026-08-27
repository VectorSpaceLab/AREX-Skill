---
name: service-mcp
description: "Data-Juicer FastAPI service, MCP server, operator discovery, and
  tool-routing workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# service-mcp

Use this sub-skill for Data-Juicer tasks that need the service surface, MCP tools, operator search, or API-style invocation.

## Start here
Read these references when the task is not a one-line command:
- `references/api-service.md`
- `references/mcp.md`
- `references/operator-discovery.md`
- `references/troubleshooting.md`

## Owns
- FastAPI service behavior adapted from `service.py`
- `dj-mcp` recipe-flow and granular-ops modes
- operator search and route/tool registration
- service transport, request encoding, and plugin-discovery guidance

## Excludes
- Local recipe syntax and dataset export basics -> `recipes-and-ops`
- Ray partition / checkpoint / recovery flows -> `ray-and-recovery`
- Heavy demo integrations or API-key workflows unless they are only mentioned as non-goals or troubleshooting notes

## Common flow
1. Decide whether the user wants a service endpoint or a CLI tool.
2. Read the operator discovery reference if they need search or plugin selection.
3. Use the bundled service script or `dj-mcp` path that matches the transport.
4. Troubleshoot encoding, transport, or registration issues before changing the recipe itself.

## Validation targets
- Can the service or MCP route be invoked without the source checkout?
- Are request parameters encoded the way the route expects?
- Are missing packages, invalid transports, or registration collisions explained clearly?

## When to route away
- Any mention of Ray recovery or partitioned jobs
- Any mention of plain dataset processing without service transport
