# MCP and Hosted Skills

Use this reference when Browser Use must be exposed to MCP clients, Browser Use should consume external MCP tools, or a workflow should call Browser Use hosted skills. For custom tool/action implementation details, read `../../tools-and-actions/SKILL.md`.

## MCP Modes

| Mode | Use when | Auth |
| --- | --- | --- |
| Cloud MCP HTTP | Claude Code, Claude Desktop, Cursor, or another MCP client should use hosted Browser Use tools | Browser Use API key header |
| Local MCP stdio | The MCP client should launch Browser Use locally | Local LLM provider key and installed MCP dependencies |
| Browser Use MCP client | A Browser Use `Agent` should call tools from an external MCP server | External MCP server command/env |

## Cloud MCP Server

Cloud MCP is the hosted option for external agents that support HTTP MCP.

Claude Code-style setup:

```bash
claude mcp add --transport http browser-use https://api.browser-use.com/mcp
```

MCP JSON configuration pattern:

```json
{
  "mcpServers": {
    "browser-use": {
      "type": "http",
      "url": "https://api.browser-use.com/mcp",
      "headers": {
        "x-browser-use-api-key": "${BROWSER_USE_API_KEY}"
      }
    }
  }
}
```

Do not hard-code the API key in committed config. Use the client’s supported secret/env mechanism when available.

Common cloud MCP tools include:

- `browser_task`: run a hosted browser automation task; pass concise task text, a small `max_steps`, and an optional profile id.
- `execute_skill`: execute a hosted Browser Use skill.
- `list_skills`: discover available skills.
- `get_cookies`: retrieve cookies when a workflow explicitly needs them.
- `list_browser_profiles`: find cloud profiles.
- `monitor_task`: check task progress.

## Local MCP Server

The local Browser Use MCP server exposes browser automation tools over stdio. The server code intentionally routes logs to stderr to avoid corrupting JSON-RPC stdout.

Typical command:

```bash
uvx --from 'browser-use[cli]' browser-use --mcp
```

Generic MCP client config:

```json
{
  "mcpServers": {
    "browser-use": {
      "command": "uvx",
      "args": ["--from", "browser-use[cli]", "browser-use", "--mcp"],
      "env": {
        "BROWSER_USE_LOGGING_LEVEL": "warning",
        "OPENAI_API_KEY": "${OPENAI_API_KEY}"
      }
    }
  }
}
```

If the MCP client cannot resolve `uvx`, use the absolute path returned by `which uvx`.

Local MCP tools exposed by the server include browser navigation, clicking, typing, state retrieval, extraction, HTML retrieval, scrolling, back navigation, tab management, session management, and a full-agent retry tool. Tool names are prefixed with `browser_` for direct browser control.

## Programmatic MCP Client Call

Use the MCP SDK directly when a Python integration needs to call Browser Use local MCP tools:

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def call_browser_use_mcp():
    params = StdioServerParameters(
        command="uvx",
        args=["--from", "browser-use[cli]", "browser-use", "--mcp"],
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await session.call_tool(
                "browser_navigate",
                arguments={"url": "https://example.com"},
            )
```

## Register External MCP Tools in Browser Use

`MCPClient` discovers tools from an external MCP server and registers them as Browser Use actions on a `Tools` registry.

```python
from browser_use import Agent, ChatBrowserUse, Tools
from browser_use.mcp.client import MCPClient

async def main():
    tools = Tools()
    mcp_client = MCPClient(
        server_name="docs",
        command="npx",
        args=["some-mcp-server@latest"],
        env={"API_TOKEN": "..."},
    )
    await mcp_client.register_to_tools(
        tools,
        tool_filter=["search_docs"],
        prefix="docs_",
    )
    agent = Agent(task="Use docs_search_docs to answer the question.", llm=ChatBrowserUse(), tools=tools)
    await agent.run(max_steps=8)
    await mcp_client.disconnect()
```

Operational notes:

- `connect()` waits for tool discovery and raises if the MCP server does not connect within its retry window.
- `register_to_tools()` can filter and prefix tool names to avoid collisions.
- MCP JSON Schema inputs are converted to Pydantic parameter models before registering actions.
- MCP tool results are converted into `ActionResult(extracted_content=...)`.
- Use `disconnect()` and call telemetry flush paths in long-running processes when appropriate.

## MCP Validation Checklist

```bash
python - <<'PY'
try:
    import mcp
    print('mcp import ok')
except Exception as exc:
    print(f'mcp import failed: {type(exc).__name__}: {exc}')
PY
```

For local MCP server launch issues:

- Confirm `uvx --from 'browser-use[cli]' browser-use --help` works.
- Confirm a provider key such as `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or Browser Use Cloud key is present depending on the configured model.
- Keep logs on stderr; stdout must remain JSON-RPC.
- Set `BROWSER_USE_LOGGING_LEVEL=DEBUG` only when debugging and the MCP client tolerates stderr logs.

## Hosted Browser Use Skills

Browser Use hosted skills are API-backed reusable actions. `SkillService` fetches enabled/finished skills, converts schemas into Pydantic models, validates parameters, and executes through the Browser Use API.

```python
from browser_use.skills.service import SkillService

async def run_skill(cookies):
    service = SkillService(skill_ids=["skill-uuid"])
    await service.async_init()
    skill = await service.get_skill("skill-uuid")
    if skill is None:
        raise RuntimeError("skill not found")
    result = await service.execute_skill(
        "skill-uuid",
        parameters={"query": "pricing"},
        cookies=cookies,
    )
    await service.close()
    return result
```

Requirements:

- `BROWSER_USE_API_KEY` must be set unless explicitly passed to `SkillService(..., api_key=...)`.
- `skill_ids` accepts explicit ids or `['*']`; wildcard is limited to the first page to avoid excessive prompt/tool load.
- Only available skills with status `finished` are cached.
- Parameters are validated with Pydantic before execution.
- Cookie parameters are filled from provided browser cookies. If a required cookie is missing, `MissingCookieException` reports the cookie name and description.

## Hosted Skills in an Agent

When the installed Agent supports hosted skills directly, use explicit ids rather than wildcard for production:

```python
from browser_use import Agent, ChatBrowserUse

agent = Agent(
    task="Analyze these profiles using the configured hosted skills.",
    llm=ChatBrowserUse(),
    skills=["skill-uuid-1", "skill-uuid-2"],
)
await agent.run(max_steps=20)
```

Guidance:

- Prefer explicit skill ids over `['*']` to keep prompts short and predictable.
- Use cloud profiles or browser login before skill execution when cookie parameters are required.
- Treat skill parameter validation errors as schema mismatches, not model failures.
- Do not expose raw cookies to users or logs.

## MCP and Skills Failure Signals

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `MCP SDK not installed` | Missing optional MCP dependency | Install Browser Use CLI/MCP environment or add `mcp` |
| MCP client hangs at startup | Server command cannot launch or stdout polluted | Use absolute command path; keep logs on stderr |
| No tools discovered | Wrong MCP command/args or server crashed | Run the command manually and inspect stderr |
| Action name collision | External tool name matches existing action | Use `prefix=` in `register_to_tools()` |
| `BROWSER_USE_API_KEY environment variable is not set` | Hosted skills or Cloud MCP lacks auth | Set env/header in the actual runtime process |
| `Skill ... not found in cache` | Wrong id, disabled skill, or pagination limit | Verify id via `list_skills` and use explicit ids |
| Missing cookie exception | Skill requires auth cookie | Use cloud profile sync or login before execution |
