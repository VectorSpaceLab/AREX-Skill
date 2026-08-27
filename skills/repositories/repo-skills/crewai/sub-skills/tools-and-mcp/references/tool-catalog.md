# CrewAI Tool Catalog

This reference summarizes the public `crewai_tools` export surface and category guidance. Use the bundled [`../scripts/list_tool_exports.py`](../scripts/list_tool_exports.py) script to inspect the exports installed in the current environment without instantiating tools.

## Install and Import

```bash
pip install 'crewai[tools]'
```

```python
from crewai import Agent
from crewai_tools import FileReadTool, SerperDevTool

agent = Agent(
    role="Research Analyst",
    goal="Read local notes and search approved sources.",
    backstory="Uses only tools that match the available credentials.",
    tools=[FileReadTool(), SerperDevTool()],
)
```

Verified package facts for this skill generation recorded `crewai_tools` version `1.14.8a2`, `109` public `__all__` exports, and sample exports including `FileReadTool`, `DirectoryReadTool`, `SerperDevTool`, `WebsiteSearchTool`, `MCPServerAdapter`, `S3ReaderTool`, `MongoDBVectorSearchTool`, `QdrantVectorSearchTool`, `ZapierActionTool`, and `EnterpriseActionTool`.

## Core Tool Fields

CrewAI tools are `BaseTool` instances with these important fields:

- `name`: unique model-facing tool name. CrewAI sanitizes some names for execution and descriptions.
- `description`: critical model-facing guidance for when and how to use the tool.
- `args_schema`: optional Pydantic model for input validation; if omitted on a `BaseTool` subclass, CrewAI infers it from `_run` or `_arun` signatures.
- `result_schema`: optional Pydantic model for structured results. If `_run` returns a Pydantic model, CrewAI can infer this schema and serialize agent-facing output as JSON.
- `env_vars`: list of `EnvVar` declarations describing required environment variables.
- `cache_function`: callable returning whether a tool result may be cached; the default returns `True`.
- `result_as_answer`: lets a tool result become the final answer.
- `max_usage_count`: positive integer limiting tool use; when exhausted, CrewAI returns a usage-limit message instead of running the tool.

## Practical Categories

### File and Document

Typical exports: `FileReadTool`, `FileWriterTool`, `DirectoryReadTool`, `DirectorySearchTool`, `CSVSearchTool`, `DOCXSearchTool`, `JSONSearchTool`, `MDXSearchTool`, `PDFSearchTool`, `TXTSearchTool`, `XMLSearchTool`, `OCRTool`, `FileCompressorTool`.

Use for local file reading, writing, directory inspection, document search, and compression. Prefer these when a user needs keyless local work. File tools validate paths to reduce path traversal risk; `FileWriterTool` rejects filenames that escape the target directory. Keep destructive writes explicit and scoped.

### Search and Research

Typical exports: `SerperDevTool`, `SerpApiGoogleSearchTool`, `SerpApiGoogleShoppingTool`, `BraveSearchTool`, `BraveWebSearchTool`, `BraveNewsSearchTool`, `BraveImageSearchTool`, `BraveVideoSearchTool`, `EXASearchTool`, `ExaSearchTool`, `TavilySearchTool`, `TavilyResearchTool`, `TavilyGetResearchTool`, `TavilyExtractorTool`, `ArxivPaperTool`, `GithubSearchTool`, `LinkupSearchTool`, `WebsiteSearchTool`, `YoutubeChannelSearchTool`, `YoutubeVideoSearchTool`, `CodeDocsSearchTool`.

Most search tools make network calls and require service-specific keys such as Serper, SerpAPI, Brave, Exa, Tavily, Linkup, GitHub, or YouTube-related credentials. When keys are absent, fall back to local files, user-provided URLs only after approval, or a custom keyless tool.

### Web Scraping and Browsing

Typical exports: `ScrapeWebsiteTool`, `ScrapeElementFromWebsiteTool`, `FirecrawlSearchTool`, `FirecrawlScrapeWebsiteTool`, `FirecrawlCrawlWebsiteTool`, `BrightDataSearchTool`, `BrightDataDatasetTool`, `BrightDataWebUnlockerTool`, `BrowserbaseLoadTool`, `HyperbrowserLoadTool`, `SeleniumScrapingTool`, `ScrapegraphScrapeTool`, `ScrapflyScrapeWebsiteTool`, `SpiderTool`, `StagehandTool`, Oxylabs scraper tools, and Serper/Jina scrape tools.

These usually perform HTTP requests, browser automation, or paid service calls. `ScrapeWebsiteTool` validates URLs and rejects unsafe schemes and private/reserved IP targets by default. For local development, avoid opening broad crawlers or browser sessions unless the user has approved network and automation side effects.

### Database and Data

Typical exports: `MySQLSearchTool`, `NL2SQLTool`, `SnowflakeSearchTool`, `SnowflakeConfig`, `SingleStoreSearchTool`, `MongoDBVectorSearchTool`, `MongoDBVectorSearchConfig`, `QdrantVectorSearchTool`, `WeaviateVectorSearchTool`, `CouchbaseFTSVectorSearchTool`, `DatabricksQueryTool`.

Use only with explicit connection details and approval. These tools can query remote data stores or require vector/embedding credentials. Route persistent RAG storage design and embedding provider setup to [`memory-knowledge-and-rag`](../../memory-knowledge-and-rag/SKILL.md).

### AI and Machine Learning

Typical exports: `DallETool`, `VisionTool`, `LlamaIndexTool`, `RagTool`, `DaytonaExecTool`, `DaytonaFileTool`, `DaytonaPythonTool`, `E2BExecTool`, `E2BFileTool`, `E2BPythonTool`, `AIMindTool`, Patronus evaluation tools, contextual AI tools.

These may execute code, use sandboxes, call model APIs, or depend on optional packages. Do not run code interpreter or sandbox tools without explicit user approval and safety boundaries. Route model-provider configuration to [`llm-and-providers`](../../llm-and-providers/SKILL.md).

### Cloud and Storage

Typical exports: `S3ReaderTool`, `S3WriterTool`, `BedrockInvokeAgentTool`, `BedrockKBRetrieverTool`.

These use AWS credentials, regions, buckets, Bedrock agent IDs, or knowledge base IDs. Reads and writes can incur costs or access private data; confirm scope before use.

### Automation and Integrations

Typical exports: `ApifyActorsTool`, `ComposioTool`, `MultiOnTool`, `ZapierActionTool`, `ZapierActionTools`, `CrewaiPlatformTools`, `GenerateCrewaiAutomationTool`, `InvokeCrewAIAutomationTool`, `EnterpriseActionTool`, `MergeAgentHandlerTool`.

These connect to third-party platforms or CrewAI-hosted systems. They usually need API keys, OAuth, platform tokens, or enterprise action tokens. Treat them as credential-bound and network-bound.

### MCP

Typical export: `MCPServerAdapter` from `crewai_tools`; native MCP config classes live in `crewai.mcp`: `MCPServerStdio`, `MCPServerHTTP`, and `MCPServerSSE`.

Use [`mcp-reference.md`](mcp-reference.md) for transport choices, tool filtering, timeouts, and cleanup.

## Safe Tool Selection Pattern

```python
from crewai_tools import DirectoryReadTool, FileReadTool

safe_local_tools = [
    DirectoryReadTool(directory="./docs"),
    FileReadTool(),
]
```

Use this kind of local list when the user asks for research but no approved API key is available. Escalate to network-backed tools only after the user provides credentials and confirms the data source.

## Export Inspection

```bash
python ../scripts/list_tool_exports.py --format table
python ../scripts/list_tool_exports.py --format json --include-private
```

The script imports `crewai_tools`, reads `__all__` when available, classifies names with conservative heuristics, and can emit JSON for debugging. It does not import the original repository, instantiate tools, run network calls, or read secrets.

## Source Evidence Notes

This catalog distills CrewAI tool docs, public exports, and source signatures into runtime guidance. Original repository docs and source files are not runtime dependencies for future agents. Tool repository templates were treated as reference-only; the reusable publishing structure is summarized in [`custom-tools.md`](custom-tools.md) instead of copying a full template.
