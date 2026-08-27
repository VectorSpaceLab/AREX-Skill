# Troubleshooting integrations

Use this checklist when Langroid integration code fails at MCP, search, file-tool, Chainlit, or output/logging boundaries.

## Event-loop failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `RuntimeError: asyncio.run() cannot be called from a running event loop` | Calling synchronous MCP helpers or using `@mcp_tool` inside async code, Chainlit handlers, notebooks, or async tests. | Use `await get_tool_async(...)` / `await get_tools_async(...)`. If customization is needed, subclass the generated base class inside the async setup function. |
| `RuntimeError: Event loop is closed` near stdio MCP code | A stdio transport or subprocess was constructed at import time or tied to a closed loop. | Move transport creation inside the async function, or pass a zero-argument factory such as `lambda: StdioTransport(...)`. |
| Chainlit handler hangs or crashes after a tool setup call | A nested event loop was started inside Chainlit's active loop. | Make `on_chat_start` / `on_message` async all the way down and await Langroid async APIs directly. |

## MCP subprocess and transport failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ClosedResourceError`, `Server session was closed unexpectedly`, or `Client failed to connect` | Stdio subprocess closed early, reused closed pipes, package download failed, or server booted slowly. | Use a transport factory, run a local command `--help` check first, add an explicit timeout, and retry only with a fresh transport. |
| External MCP command causes downloads or network access during setup | `npx`, `uvx`, or a command transport may install or fetch packages before listing tools. | Treat subprocess transports as side-effecting. Use local help/package checks and only run them when network/process side effects are allowed. |
| Stateful MCP server loses state between calls | A fresh client/session is created for each generated tool call. | Use `FastMCPClient(server, persist_connection=True)` around related calls, and close it with `async with` or `await close()`. |
| Tool listing is slow with many tools | One tool was fetched at a time or remote listing is expensive. | Use `await get_tools_async(server)` for one list round trip, or `FastMCPClient.tool_model_from_mcp_tool()` on an allow-listed raw tool list. |
| Tool output validation error mentions structured content | MCP server declares an output schema but returns plain text. | If supported by the server, set a structured response option such as `output_mode="structured"` before `await self.call_tool_async()`. Otherwise adapt to the server's declared output contract. |

Relevant environment knobs for MCP client startup are `LANGROID_MCP_READ_TIMEOUT`, `LANGROID_MCP_CONNECT_RETRIES`, and `LANGROID_MCP_CONNECT_BACKOFF_BASE`.

## MCP tool class surprises

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Instantiating generated tool rejects a value | MCP schema constraints were preserved as Pydantic validation. | Match the generated field types, enum literals, optionality, and nested object shapes. |
| Field names such as `request` or `name` do not work as expected | The MCP tool parameter collides with Langroid reserved fields. | Use the generated `__`-suffixed field names, e.g. `request__`, `purpose__`, `recipient__`, or `name__`. |
| Custom `handle_async()` receives a tuple from `call_tool_async()` | Recent Langroid converts raw MCP output to `(content, files)`. | Unpack defensively: `content = raw[0] if isinstance(raw, tuple) else raw`. |
| Images or blobs are missing from MCP results | Resource forwarding was disabled or the handler was not given an agent. | Use `FastMCPClient(..., forward_images=True, forward_text_resources=True, forward_blob_resources=True)` and call `await msg.handle_async(agent)` when file attachments should become a `ChatDocument`. |

## Search/API failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Missing credential error | Required provider key is not set. | Check `TAVILY_API_KEY`, `EXA_API_KEY`, `GOOGLE_API_KEY`, `GOOGLE_CSE_ID`, `SELTZ_API_KEY`, or the MCP provider's key before startup. |
| Import error for a search provider | Optional provider client is missing. | Install the matching optional dependency or avoid enabling that tool in this environment. |
| DuckDuckGo/search tests are flaky | Live search results and page fetches drift or network is blocked. | Mock provider functions for tests; in no-network checks assert imports, request names, and schema only. |
| Google search returns no usable results | Custom Search key or CSE ID is absent, wrong, or restricted. | Verify both environment variables and API/CSE configuration before enabling the tool. |
| Remote Twitter/X-over-MCP fails | API key/header, remote endpoint, or service policy issue. | Preflight key/header presence and endpoint reachability only when remote access is allowed. |

## File tool failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `is outside the allowed directory` appears | Parent traversal, absolute path, or symlink escape was blocked. | Pass relative paths inside the configured `get_curr_dir` boundary. Do not disable path safety. |
| Write succeeds but nothing is committed | `WriteFileTool.create(..., get_git_repo=None)` or git repo callback is missing. | Supply `get_git_repo` only when committed writes are desired and a repo is available. |
| Empty directory reports not found or empty | `ListDirTool` returns one combined message for missing/empty. | Treat the response as a user-facing diagnostic, not a precise filesystem enum. |

## Chainlit failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `chainlit` import error | Chainlit extra is not installed. | Verify with `python -c "import chainlit"`; install the optional UI dependency if Chainlit is required. |
| No UI messages from Langroid | Callbacks were not injected into the current agent/task instance. | Call `lr.ChainlitTaskCallbacks(task)` or `lr.ChainlitAgentCallbacks(agent)` before running the async task/agent call. |
| Nested sub-task responses do not appear | `show_subtask_response` disabled or callbacks not recursively injected. | Use `ChainlitTaskCallbacks(task, config=ChainlitCallbackConfig(show_subtask_response=True))`. |
| Chainlit app code starts a server recursively | App code tries to invoke the Chainlit launcher. | Keep app handlers in Python; start the app externally with the Chainlit launcher. |

## Logging, quiet mode, and status output

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| HTML log file missing | HTML logging disabled, loggers disabled, or log directory not writable. | Set `TaskConfig(enable_html_logging=True, logs_dir="logs")` and use a writable relative directory. |
| Too many local log files | HTML logging is enabled by default. | Disable with `TaskConfig(enable_html_logging=False)` for smoke tests or minimal runs. |
| Terminal/streaming output is silent | `settings.quiet`, `quiet_mode()`, or `async_stream_quiet=True` is active. | Inspect those settings; for Chainlit callbacks, ensure callback injection happened so streaming is re-enabled for UI. |
| Rich spinner output conflicts with LLM output | Long-running status and streaming both write to terminal. | Use `status()` or `quiet_mode()` around long operations; leave streaming on only for interactive displays. |

## Deterministic smoke baseline

When debugging MCP integration, first run the bundled no-network in-memory smoke script. If it fails, the local Langroid/FastMCP bridge is broken before any external process, API key, or network server is involved. If it passes, isolate the failure to transport construction, external process startup, credentials, server schema, or UI callback boundaries.
