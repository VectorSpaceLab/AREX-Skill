# Search and file tools

This reference covers Langroid's built-in external search tools and local file tools. These are `ToolMessage` classes that can be enabled on an agent without writing custom agent methods. For general custom tool design, route to `../agents-tasks-tools/SKILL.md`.

## Built-in web/search tools

Enable the desired search tool on a `ChatAgent`:

```python
import langroid as lr
from langroid.agent.tools.duckduckgo_search_tool import DuckduckgoSearchTool
from langroid.agent.tools.tavily_search_tool import TavilySearchTool
from langroid.agent.tools.exa_search_tool import ExaSearchTool
from langroid.agent.tools.google_search_tool import GoogleSearchTool
from langroid.agent.tools.seltz_search_tool import SeltzSearchTool

agent = lr.ChatAgent(lr.ChatAgentConfig(name="search-agent"))
agent.enable_message(DuckduckgoSearchTool)
```

Each tool asks the LLM to emit a JSON tool call with `query` and `num_results`. The tool handler calls the corresponding `langroid.parsing.web_search` function and returns formatted title/link/summary evidence.

| Tool class | Request name | Credentials | Notes |
| --- | --- | --- | --- |
| `DuckduckgoSearchTool` | `duckduckgo_search` | none in Langroid | Still performs live web access through DuckDuckGo and result-page fetches. |
| `TavilySearchTool` | `tavily_search` | `TAVILY_API_KEY` | Requires Tavily client package and key. |
| `ExaSearchTool` | `exa_search` | `EXA_API_KEY` | Requires Exa client package and key. |
| `GoogleSearchTool` | `web_search` | `GOOGLE_API_KEY`, `GOOGLE_CSE_ID` | Uses Google Custom Search. |
| `SeltzSearchTool` | `seltz_search` | `SELTZ_API_KEY` | Uses Seltz results directly rather than fetching page bodies. |

The lower-level `WebSearchResult` includes `title`, `link`, `summary`, and `full_content`. For most search providers, Langroid fetches linked pages with bounded HTTP requests, skips large files above the built-in size threshold, and skips non-HTML/non-text content types.

## Direct search tool usage

For a direct tool call without an LLM:

```python
tool = TavilySearchTool(query="recent Langroid releases", num_results=3)
try:
    result = tool.handle()
except Exception as exc:
    result = f"Search unavailable: {exc}"
```

Use direct calls for bounded diagnostics. Do not assume live search output is stable enough for exact assertions; network search tests should mock provider clients or assert only broad structure.

## Search integration guardrails

Before enabling live search in an app:

1. Check whether the required provider key is present.
2. Check whether the required optional client import is available.
3. Decide whether live web access is allowed in the runtime environment.
4. Keep task prompts explicit that search evidence is external and may drift.
5. Avoid placing credentials in system messages, logs, Chainlit UI messages, or HTML logs.

Example credential preflight:

```python
import os

missing = [name for name in ["TAVILY_API_KEY"] if not os.getenv(name)]
if missing:
    raise RuntimeError(f"Missing search credential(s): {', '.join(missing)}")
```

Provider/model credentials for LLM calls are a separate concern; route those to `../llm-provider-config/SKILL.md`.

## Twitter/X search through MCP

Langroid does not need a custom Twitter/X `ToolMessage` when a third-party MCP server exposes X search tools. Use the MCP workflow from [`mcp-workflows.md`](mcp-workflows.md): construct the provider's HTTP transport with the service API key in headers, call `await get_tools_async(transport)`, and enable the resulting tools on the agent. Check service terms and privacy rules before forwarding keys or queries to remote MCP servers.

## Safe local file tools

Langroid bundles three file tools:

```python
from langroid.agent.tools.file_tools import (
    ListDirTool,
    ReadFileTool,
    WriteFileTool,
)
```

They can be scoped to a current directory with factory methods:

```python
from pathlib import Path

root = Path("workspace")
ReadTool = ReadFileTool.create(get_curr_dir=lambda: root)
ListTool = ListDirTool.create(get_curr_dir=lambda: root)
WriteTool = WriteFileTool.create(
    get_curr_dir=lambda: root,
    get_git_repo=None,
)

agent.enable_message([ReadTool, ListTool, WriteTool])
```

`WriteFileTool.create()` accepts an optional `get_git_repo` callback. When present, successful writes are committed with the tool's commit message; when absent, files are written without committing.

## File tool behavior

- `ReadFileTool` reads a relative file path inside the configured current directory and includes line numbers by default.
- `WriteFileTool` writes verbatim content to a relative path inside the configured current directory; it creates parent directories as needed through Langroid's file creation utility.
- `ListDirTool` lists a relative directory path inside the configured current directory.
- All three tools call Langroid path-safety checks before accessing the filesystem.
- Parent traversal, absolute paths outside the sandbox, and symlink escapes are blocked with an error rather than exposing or writing outside the configured boundary.
- Reading a missing file returns a clear not-found message; listing a missing or empty directory returns a clear empty/not-found message.

## File tool prompt pattern

Make the system message explicit that the tool owns path resolution:

```python
agent = lr.ChatAgent(
    lr.ChatAgentConfig(
        system_message=f"""
        When asked to read, write, or list files, use one of these tools:
        {ReadTool.name()}, {WriteTool.name()}, {ListTool.name()}.
        Treat paths as relative to the configured workspace.
        """,
    )
)
```

## Local/no-network checks

For search tools in a no-network environment, check only imports, request names, and examples:

```python
assert DuckduckgoSearchTool.name() == "duckduckgo_search"
assert TavilySearchTool.examples()[0].num_results == 3
```

For file tools, direct handler checks can be fully local and deterministic by using a temporary directory and avoiding an LLM call.
