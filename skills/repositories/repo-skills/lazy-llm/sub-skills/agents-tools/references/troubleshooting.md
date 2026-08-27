# Agents and Tools Troubleshooting

## Tool is not visible under `lazyllm.tool`

**Likely causes**: wrong registration group, duplicate process state, missing docstring/type hints for schema expectations, or registration code did not execute.

**Recovery**

- Use `@fc_register("tool")` or the intended group.
- Instantiate through `lazyllm.tool.<function_name>()` after registration.
- In a long-lived process, choose unique tool names or restart to clear globals.

## Sandbox metadata is wrong

**Likely causes**: omitted `execute_in_sandbox`, invalid `fc_register` parameter, or wrapper/rewrite changed metadata.

**Recovery**

- Run `python scripts/tool_agent_smoke.py`.
- Check `execute_in_sandbox`, `input_files_parm`, `output_files_parm`, and `output_files` on the instantiated tool.
- Unsupported registration kwargs should fail early with assertions.

## Agent call fails before tool execution

**Likely causes**: LLM/provider module not configured, missing API key, prompt/tool schema mismatch, max retries exhausted, or streaming/tool-call response format issue.

**Recovery**

- Validate tools independently first.
- Route provider/backend configuration to model-deployment.
- Use `return_trace` or `return_last_tool_calls` when debugging, but do not expose secrets.

## HTTP/search/SQL tool failure

**Likely causes**: network unavailable, provider quota, invalid URL, missing DB driver, schema mismatch, or production side effects.

**Recovery**

- Use local/temp fixtures for SQL and deterministic content contracts for search.
- Ask before hitting production URLs or databases.
- Keep timeouts and result schemas explicit.

## MCP server failure

**Likely causes**: missing `agent-advanced`/`mcp`, missing npm/npx, server command not approved, port conflict, server not stopped, or malformed tool schema.

**Recovery**

- Treat MCP as an external-process workflow.
- Ask for the exact command and approval.
- Verify tool listing before connecting an LLM agent.

## SkillManager mutation risk

`skills add`, `import`, `delete`, and `install` mutate skill directories or external agents. Use `skills list` for read-only inspection and ask before mutating.
