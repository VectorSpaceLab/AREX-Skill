# MCP and Skills

## LazyLLM skills surfaces

LazyLLM includes skill management through both CLI and Python APIs:

- `lazyllm skills init`
- `lazyllm skills list`
- `lazyllm skills info <name>`
- `lazyllm skills delete <name>`
- `lazyllm skills add <path> [-n NAME] [--dir DIR]`
- `lazyllm skills import <path> [--dir DIR] [--names a,b,c] [--overwrite]`
- `lazyllm skills install --agent <name> [--project] [--timeout SEC]`
- `SkillManager(dir=None, skills=None, max_skill_md_bytes=None, fs=None, sandbox=None)`

`skills list` is safe as a smoke command. Add/import/delete/install can mutate user skill directories, so ask before running them.

## MCP boundaries

LazyLLM exposes MCP-related APIs and CLI deployment commands, but a real MCP workflow can require:

- the Python `mcp` package or `agent-advanced` extra,
- npm/npx or another external server command,
- network ports and server lifecycle management,
- tool schemas from a running MCP server,
- sandbox/workspace policy.

Do not run `npx`, start MCP servers, or deploy MCP commands unless the user approves the exact command and expected side effects.

## Safe MCP planning checklist

1. Identify the server command and whether it is local, npm/npx-based, or remote.
2. Confirm package/runtime requirements (`agent-advanced`, Node/npm if needed).
3. Decide where the server runs and how it is stopped.
4. Inspect expected tool names and argument schemas.
5. Wrap the MCP client in an agent only after a connection/tool-list smoke succeeds.
6. Keep credentials and network calls out of logs unless redacted.

## Skills-agent planning checklist

1. Confirm skill directory and max skill size limits.
2. Use `skills list` or `SkillManager` to inspect availability without mutation.
3. Add/import skills only after resolving overwrite policy.
4. When combining with `ReactAgent`, document which skills are enabled and how built-in tools interact with custom tools.
5. Treat skill installation into another agent as a separate import/export workflow, not a normal app runtime step.
