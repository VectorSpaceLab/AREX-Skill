# MCP and Agent Integrations

## Supported integration families

- Claude Code cloud memory wiring.
- Hermes memory provider setup.
- OpenClaw persistent-memory plugin setup.
- Generic MCP clients that can send HTTP headers.

## Common MCP header pattern

```bash
claude mcp add --transport http memori https://api.memorilabs.ai/mcp/   --header "X-Memori-API-Key: ${MEMORI_API_KEY}"   --header "X-Memori-Entity-Id: your_username"   --header "X-Memori-Process-Id: claude-code"
```

## What to remember

- The API key and entity/process identifiers are the minimum routing context.
- The memory service is not a generic tool server; it is an application memory
  endpoint with attribution, project, and session semantics.
- Client-specific setup pages may add process names, config files, or startup
  steps, but the header contract above is the common baseline.

## Best use

Read this file when the user is connecting Memori to another agent, IDE, or MCP
client and wants the shortest correct setup path.
