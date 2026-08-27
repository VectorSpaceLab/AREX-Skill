# Tools and MCP Troubleshooting

Use this matrix when CrewAI tools, custom tools, or MCP integrations fail. Start with the symptom, then check the likely boundary: import, schema, credential, network, path safety, lifecycle, or routing.

## Quick Triage

1. Identify whether the failing object is an official `crewai_tools` export, a custom `BaseTool`, a decorator tool, a `CrewStructuredTool`, native `Agent.mcps`, or `MCPServerAdapter`.
2. Confirm the failure happens during import, instantiation, discovery, argument validation, tool execution, or crew/task assignment.
3. Inspect tool metadata (`name`, `description`, `args_schema`, `result_schema`, `env_vars`, `max_usage_count`) without printing secrets.
4. Prefer a safe local fallback when credentials, optional packages, or network access are unavailable.

## Missing API Keys or Tokens

Symptoms:

- Tool constructor raises `ValueError` about an API key.
- Tool call returns an authentication error.
- MCP catalog slug resolves no tools or config fetch fails.
- Hosted integration returns HTTP `401` or `403`.

Checks:

- Inspect `tool.env_vars` if the object can be constructed safely.
- Check documented variables such as `TAVILY_API_KEY`, `LINKUP_API_KEY`, `COMPOSIO_API_KEY`, `ZAPIER_API_KEY`, `CREWAI_PLATFORM_INTEGRATION_TOKEN`, or cloud/database-specific credentials.
- Confirm whether the tool expects constructor credentials instead of environment variables.
- Never echo secret values; only report whether a required variable is set.

Fixes:

- Ask the user to provide or configure the specific missing credential.
- Use a keyless local tool (`FileReadTool`, `DirectoryReadTool`, custom parser) when possible.
- For LLM provider keys, route to [`llm-and-providers`](../../llm-and-providers/SKILL.md).

## Optional Package Missing

Symptoms:

- `ImportError` mentioning an optional extra or SDK.
- Tool import works, but construction fails because a parser/browser/database package is absent.
- MCP usage reports missing `mcp` packages.

Fixes:

- Install only the necessary extra after user approval, for example `uv add mcp` or `uv pip install 'crewai-tools[mcp]'` for MCP.
- For scraping tools, install the parser/browser dependency named in the error.
- If installation is not allowed, switch to a local/custom tool that does not require the optional package.

## Network Calls or Paid Side Effects

Symptoms:

- Tool hangs, times out, or returns provider quota/rate-limit errors.
- Tool starts browser automation or a sandbox unexpectedly.
- A database/cloud tool asks for connection details.

Fixes:

- Confirm user approval for network, browser, cloud, database, sandbox, or paid API side effects.
- Set tool-specific timeouts where available.
- Use `max_usage_count` to cap repeated tool calls.
- Narrow task instructions so the agent does not call tools opportunistically.
- Substitute a dry-run custom tool when the user only needs payload validation.

## Tool Schema Validation Errors

Symptoms:

- `Tool '<name>' arguments validation failed`.
- `Arguments validation failed` from `CrewStructuredTool`.
- Agent passes JSON with missing required keys or wrong types.

Checks:

- Print the schema shape, not secrets: `tool.args_schema.model_json_schema()`.
- Ensure a `BaseTool` subclass has type annotations on `_run` parameters or an explicit `args_schema`.
- Ensure a `@tool` function has a docstring and typed parameters.
- Ensure a `CrewStructuredTool` callable has a docstring or explicit description.

Fixes:

- Add a Pydantic `args_schema` with field descriptions.
- Make task instructions name the exact argument keys.
- Convert stringified JSON into a dict before invoking `CrewStructuredTool`.
- Avoid `*args`/`**kwargs` as the only schema source unless explicitly handled.

## Typed Output Problems

Symptoms:

- Agent sees unstable string output instead of predictable JSON.
- Runtime warning says result schema validation failed and CrewAI fell back to `str(raw_result)`.

Fixes:

- Return a Pydantic model that matches `result_schema`, or set `result_schema` explicitly for dict returns.
- Override `format_output_for_agent` when the agent needs a concise summary.
- Keep direct Python return values useful for tests and callers.

## Unsafe File Paths

Symptoms:

- Error says a path is outside the allowed directory.
- File write returns an invalid path or overwrite warning.
- URL validation rejects `file://`, private IPs, or unsafe schemes.

Fixes:

- Use relative paths inside the intended working directory.
- For writes, keep `filename` from escaping `directory`; do not pass `../` targets.
- Do not set `CREWAI_TOOLS_ALLOW_UNSAFE_PATHS=true` unless the user explicitly approves the risk.
- For file input and multimodal handling, route to [`files-and-multimodal`](../../files-and-multimodal/SKILL.md) when available.

## Custom Tool Import Path Mistakes

Symptoms:

- JSONC project or Python module cannot import a custom tool class.
- Published package installs but `from package import ToolClass` fails.
- Serialized checkpoint cannot resolve a tool type.

Fixes:

- Put the tool class in an importable package/module.
- Re-export public classes from package `__init__.py` and define `__all__`.
- Use PascalCase class names ending in `Tool` for published packages.
- Install the package into the runtime environment before referencing it.
- Avoid defining reusable tool classes only inside a function or notebook cell when they must be imported later.

## MCP Transport and Timeout Failures

Symptoms:

- No tools discovered from MCP server.
- Specific `#tool` reference does not resolve.
- Stdio command never starts or remains running.
- SSE/HTTP connection times out.
- Adapter raises initialization failure.

Checks:

- Confirm `mcp` dependencies are installed.
- Confirm stdio `command` and `args` are trusted and available.
- Confirm remote URL, headers, and auth are correct without printing secret values.
- Check `tool_filter` is not excluding every tool.
- For `MCPServerAdapter`, remember construction starts the adapter and default `connect_timeout` is `30` seconds.

Fixes:

- Use native `Agent(mcps=[MCPServerStdio(...)] )` for normal use.
- Add a static allow-list filter and remove broad dangerous tools.
- Increase `connect_timeout` only for known slow startup.
- Wrap `MCPServerAdapter` in `with`, or call `stop()` in `finally`.
- Bind local SSE development servers to `127.0.0.1` and require server-side origin validation.

## Crew Assignment Boundary

Symptoms:

- Tool is defined correctly but an agent never uses it.
- Tool is added to a task when it should be added to an agent, or vice versa.
- Hierarchical crews or planning change tool usage unexpectedly.

Route these questions to [`core-runtime`](../../core-runtime/SKILL.md). This sub-skill covers tool construction and MCP integration, not crew process semantics.

## Safe Fallback Recipe

When a third-party search tool cannot run because the API key is missing:

1. Tell the user which credential is missing without printing secret values.
2. Offer a local alternative based on user-provided files or directories.
3. Use `FileReadTool`, `DirectoryReadTool`, or a small custom `BaseTool`.
4. Keep the final answer clear that no live web/API call was made.

When an MCP stdio server needs migration:

1. Use `MCPServerStdio` with explicit `command`, `args`, and minimal `env`.
2. Add `create_static_tool_filter` with only required tool names.
3. Prefer `Agent(mcps=[...])` unless manual lifecycle is required.
4. If using `MCPServerAdapter`, use context manager cleanup and a bounded `connect_timeout`.
