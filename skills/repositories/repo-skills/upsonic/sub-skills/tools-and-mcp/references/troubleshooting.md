# tools-and-mcp Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ToolConfig` validation fails | Multiple HITL modes were enabled at once. | Keep only one of confirmation, user input, or external execution active. |
| A function tool does not expose the expected schema | The callable docstring or signature is ambiguous. | Simplify the signature and use the bundled schema-inspection helper. |
| MCP handler import fails | The optional `mcp` SDK is missing. | Install `upsonic[mcp]` and retry. |
| A prepared MCP command is rejected | The command contains shell metacharacters or an unsafe executable. | Rewrite the command to a safe argv-style form. |
| A tool returns output that should have been hidden | `show_result` is configured incorrectly. | Toggle `show_result` and re-run the tool under a tiny fixture. |

## Smoke check

```bash
python sub-skills/tools-and-mcp/scripts/inspect_tool_schema.py
```
