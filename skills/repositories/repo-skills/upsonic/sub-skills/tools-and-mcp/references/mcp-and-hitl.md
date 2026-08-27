# MCP and HITL Notes

## MCP connections

Upsonic supports MCP tools over multiple transports, but the `mcp` extra is optional. The import can succeed without the SDK, yet actual MCP handler construction requires the extra.

## Security reminders

- Stdio MCP servers can execute arbitrary local processes.
- Treat command strings as untrusted input and keep them free of shell metacharacters.
- Prefer the simplest transport that satisfies the workflow.

## HITL patterns

| Flag | Meaning |
| --- | --- |
| `requires_confirmation` | Pause before execution and ask the user to approve the tool call. |
| `requires_user_input` | Pause and collect the missing inputs from the user. |
| `external_execution` | Delegate execution to an external process. |

Only one HITL pattern should be active on a single tool.

## Good debugging sequence

1. Verify the function tool schema without MCP.
2. Confirm the MCP extra is installed if an MCP handler is needed.
3. Validate the command string with the bundled helper script.
4. Only then connect to a real server.
