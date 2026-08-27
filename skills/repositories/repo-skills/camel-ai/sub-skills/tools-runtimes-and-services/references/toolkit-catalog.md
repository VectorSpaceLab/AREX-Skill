# Toolkit Catalog and Selection Guide

CAMEL toolkits are Python classes that expose one or more `FunctionTool` instances through `get_tools()`. Install optional dependencies only for the toolkit family you actually use; many toolkits require API credentials, browser binaries, Docker, external services, or network access.

## Install Extras

Start with the base package for simple custom functions:

```bash
pip install camel-ai
```

Install the general tools extra when using built-in toolkits that need optional packages:

```bash
pip install 'camel-ai[tools]'
```

Some integrations still need separate system services, browser installs, Docker daemon access, or API keys. Treat import errors as a signal to install the narrow optional package or service for that toolkit rather than all development dependencies.

## Common Toolkit Families

| Task | Toolkit | Typical requirements | Notes |
| --- | --- | --- | --- |
| Custom callable | `FunctionTool`, `@tool()` | `docstring_parser`, type hints | Use first when the tool is your own Python function. |
| Search and web fetch | `SearchToolkit`, `WebFetchToolkit`, `BrowserToolkit`, `AsyncBrowserToolkit`, `HybridBrowserToolkit`, `HeadlessBrowserSearchToolkit` | Network, API keys for some engines, browser/playwright deps for browser toolkits | Browser tools can open pages and execute actions; use safe scopes and timeouts. |
| Terminal and files | `TerminalToolkit`, `FileToolkit`, `PlanningWorktreeToolkit` | Local workspace or Docker container; filesystem permissions | Treat as high-impact tools and restrict working directories. |
| Code execution | `CodeExecutionToolkit` | Chosen interpreter backend; Docker/Jupyter/E2B/MicroSandbox as needed | Choose sandbox deliberately; avoid `unsafe_mode=True` for untrusted code. |
| MCP | `MCPToolkit`, `NotionMCPToolkit`, `PlaywrightMCPToolkit`, `GoogleDriveMCPToolkit`, `EdgeOnePagesMCPToolkit`, `OrigeneToolkit`, `MinimaxMCPToolkit` | `mcp`, server commands/URLs, optional auth headers | Use async context management and `skip_failed=True` for robust startup. |
| OpenAPI/REST | `OpenAPIToolkit` | `prance`, `openapi-spec-validator`, `requests`, API auth env vars | Requires OpenAPI 3.0/3.1 specs with summaries/descriptions. |
| Math and symbolic | `MathToolkit`, `SymPyToolkit` | SymPy for symbolic operations | Low side effects; good smoke-test candidates. |
| Data and documents | `ExcelToolkit`, `PPTXToolkit`, `MarkItDownToolkit`, `MinerUToolkit`, `DataCommonsToolkit`, `OpenBBToolkit` | File parsers or service credentials | Check whether operations read/write local files. |
| Messaging/productivity | `GmailToolkit`, `GoogleCalendarToolkit`, `IMAPMailToolkit`, `SlackToolkit`, `NotionToolkit`, `DingtalkToolkit`, `OutlookMailToolkit`, `ResendToolkit`, `WhatsAppToolkit` | OAuth/API tokens, network | High side effects; prefer read-only methods first. |
| Developer platforms | `GithubToolkit`, `KlavisToolkit`, `ZapierToolkit`, `ACI Toolkit` | API tokens and scopes | Scope tokens narrowly; confirm mutating operations. |
| Media and multimodal | `ImageAnalysisToolkit`, `ImageGenToolkit`, `AudioAnalysisToolkit`, `VideoAnalysisToolkit`, `VideoDownloaderToolkit`, `ScreenshotToolkit`, `PyAutoGUIToolkit` | Vision/audio deps, browser/GUI/display, model APIs | GUI and media operations often need OS/browser/display setup. |
| Retrieval and memory | `MemoryToolkit`, `RetrievalToolkit` | Memory/vector stores | Route deeper retrieval design to the memory/RAG sub-skill. |

## BaseToolkit Rules

- Construct a toolkit, then pass `toolkit.get_tools()` into `ChatAgent(tools=...)`.
- `BaseToolkit(timeout=...)` requires a positive timeout or `None`.
- Toolkit subclass methods are automatically timeout-wrapped unless they use `@manual_timeout` or already accept a `timeout` parameter.
- Toolkit methods exposed as tools should have stable names, type hints, and docstrings. Schema quality affects tool-calling quality.
- Some toolkits inherit `RegisteredAgentToolkit`; these need the owning `ChatAgent` registered before methods that inspect or act on the current agent can work.

## Choosing Between Tool Surfaces

| If you have... | Prefer... | Why |
| --- | --- | --- |
| One local Python function | `FunctionTool(func)` or `@tool()` | Smallest surface and easiest schema debugging. |
| Several related Python methods | `BaseToolkit` subclass | Keeps timeout, docs, and `get_tools()` organized. |
| A remote MCP server | `MCPToolkit(config_path=... or config_dict=...)` | Handles discovery and converts MCP tools to CAMEL tools. |
| An OpenAPI spec | `OpenAPIToolkit` | Generates functions from OpenAPI operations and security schemes. |
| Untrusted code execution | `CodeExecutionToolkit` with sandbox backend or runtime | Keeps execution isolated when configured correctly. |
| Shell/file operations | `TerminalToolkit` or `FileToolkit` with strict working directory | Provides explicit command/file tool surfaces for agents. |
| Long-running remote function execution | `DockerRuntime` or `RemoteHttpRuntime` | Wraps functions as runtime-served tools and handles lifecycle. |

## Verification Candidate Guidance

After the full skill is integrated, prefer native verification candidates that exercise function-tool schema generation, MCP config and connection behavior, runtime utilities, and terminal/runtime examples. Keep Docker, Daytona, MicroSandbox, browser, and service examples as reference-only unless the verifier has explicit daemon, browser, network, service, and credential approval.
