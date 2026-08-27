# Tools and MCP troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `No MCP servers are configured` | No URL, config, or connection object was supplied | Pass `mcp_url`, `mcp_urls`, `mcp_config`, or `mcp_configs`. |
| Tool list is empty | The server is unreachable or exposed no tools | Check the server URL, transport, and auth mode. |
| `No configured MCP server exposes a tool named ...` | Wrong tool name or wrong server route | Confirm the tool name returned by `get_tools()` or `list_tool_names()`. |
| `401` / unauthorized responses | Missing or mismatched auth header | Match the server’s expected header, prefix, and token style. |
| OAuth cache or callback issues | Browser flow, redirect URI, or token cache problem | Use the configured redirect URI and check token-cache permissions. |
| `streamable_http` vs `sse` confusion | The server supports a different transport than the client assumed | Set `transport` explicitly when auto-detection is ambiguous. |
| Local server start-up fails | Missing `uvicorn`, `mcp`, or another server dependency | Install the missing package in the inspection environment and retry the local smoke script. |
| Tool execution returns an error object | The tool itself raised or the arguments were malformed | Inspect the tool arguments, then retry with a tiny fixed payload. |

## Recovery order

1. Confirm the server is reachable with the intended transport.
2. Match the auth style to the server’s actual header or token requirement.
3. Verify the tool name list before attempting a call.
4. Try a local server helper before a remote MCP endpoint.
